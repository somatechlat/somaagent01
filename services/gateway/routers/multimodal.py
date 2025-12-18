"""Multimodal API routes for asset generation and retrieval.

VIBE COMPLIANT: Real infrastructure only. No mocks.
"""

from __future__ import annotations

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from services.common.asset_store import AssetStore
from services.tool_executor.multimodal_executor import MultimodalExecutor
from services.gateway import providers

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/multimodal", tags=["multimodal"])


# ============================================================================
# Request/Response Models
# ============================================================================

class GenerateRequest(BaseModel):
    """Request to generate multimodal assets."""
    plan: dict = Field(..., description="Task DSL plan JSON")
    tenant_id: str = Field(..., description="Tenant ID")
    session_id: str = Field(..., description="Session ID")


class GenerateResponse(BaseModel):
    """Response from asset generation request."""
    job_id: str = Field(..., description="Job Plan ID")
    status: str = Field(..., description="Job status (pending/running/completed/failed)")


class PlanStatusResponse(BaseModel):
    """Status of a multimodal job plan."""
    id: str
    status: str
    total_steps: int
    completed_steps: int
    error_message: str | None = None


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/generate", response_model=GenerateResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_assets(
    request: GenerateRequest,
    executor: Annotated[MultimodalExecutor, Depends(providers.get_multimodal_executor)]
) -> GenerateResponse:
    """Trigger multimodal asset generation from a Task DSL plan.
    
    Args:
        request: Generation request with plan JSON
        executor: MultimodalExecutor instance (injected)
        
    Returns:
        Job ID and initial status
        
    Raises:
        HTTPException: If plan is invalid or execution fails to start
    """
    try:
        # Create plan in DB via JobPlanner
        from services.common.job_planner import JobPlanner, JobPlan
        from uuid import uuid4
        
        planner = JobPlanner(dsn=executor._dsn)
        plan_id = uuid4()
        
        # Parse plan JSON and create JobPlan
        job_plan = JobPlan.from_dict({
            "id": str(plan_id),
            "tenant_id": request.tenant_id,
            "session_id": request.session_id,
            **request.plan
        })
        
        # Store plan
        await planner.create(job_plan)
        
        # Execute plan asynchronously (fire and forget)
        # In production, this should be offloaded to a background worker/queue
        import asyncio
        asyncio.create_task(executor.execute_plan(plan_id))
        
        return GenerateResponse(
            job_id=str(plan_id),
            status="pending"
        )
        
    except ValueError as e:
        logger.error("Invalid plan JSON: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid plan: {str(e)}"
        )
    except Exception as e:
        logger.error("Failed to start job execution: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start asset generation"
        )


@router.get("/plans/{plan_id}", response_model=PlanStatusResponse)
async def get_plan_status(
    plan_id: UUID,
    executor: Annotated[MultimodalExecutor, Depends(providers.get_multimodal_executor)]
) -> PlanStatusResponse:
    """Get the status of a multimodal job plan.
    
    Args:
        plan_id: UUID of the job plan
        executor: MultimodalExecutor instance (injected)
        
    Returns:
        Plan status details
        
    Raises:
        HTTPException: If plan not found
    """
    try:
        from services.common.job_planner import JobPlanner
        
        planner = JobPlanner(dsn=executor._dsn)
        job_plan = await planner.get(plan_id)
        
        if not job_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plan {plan_id} not found"
            )
        
        return PlanStatusResponse(
            id=str(job_plan.id),
            status=job_plan.status.value,
            total_steps=job_plan.total_steps,
            completed_steps=job_plan.completed_steps,
            error_message=job_plan.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to fetch plan status: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve plan status"
        )


@router.get("/assets/{asset_id}")
async def get_asset(
    asset_id: UUID,
    store: Annotated[AssetStore, Depends(providers.get_asset_store)]
) -> StreamingResponse:
    """Retrieve a generated multimodal asset by ID.
    
    Args:
        asset_id: UUID of the asset
        store: AssetStore instance (injected)
        
    Returns:
        Asset content as streaming response with proper MIME type
        
    Raises:
        HTTPException: If asset not found
    """
    try:
        asset = await store.get(str(asset_id))
        
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asset {asset_id} not found"
            )
        
        if not asset.content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asset {asset_id} has no content"
            )
        
        # Stream the content
        return StreamingResponse(
            iter([asset.content]),
            media_type=asset.mime_type or "application/octet-stream",
            headers={
                "Content-Disposition": f"inline; filename={asset.original_filename or asset_id}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retrieve asset: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve asset"
        )
