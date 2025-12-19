"""Multimodal API routes for asset generation and retrieval.

VIBE COMPLIANT: Real infrastructure only. No mocks.
"""

from __future__ import annotations

import logging
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from services.common.asset_store import AssetStore
from services.common.authorization import authorize
from services.common.capability_registry import CapabilityRegistry
from services.common.job_planner import JobPlanner, PlanValidationError
from services.common.provenance_recorder import ProvenanceRecorder
from services.gateway import providers
from src.core.config import cfg

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/multimodal", tags=["multimodal"])


# ============================================================================
# Request/Response Models
# ============================================================================

class JobCreateRequest(BaseModel):
    """Request to create a multimodal job plan."""
    plan: dict = Field(..., description="Task DSL plan JSON")
    session_id: str = Field(..., description="Session ID")
    request_id: Optional[str] = Field(None, description="Optional correlation ID")


class JobCreateResponse(BaseModel):
    """Response from job creation."""
    job_id: str = Field(..., description="Job Plan ID")
    status: str = Field(..., description="Job status (pending/running/completed/failed)")


class JobStatusResponse(BaseModel):
    """Status of a multimodal job plan."""
    id: str
    status: str
    total_steps: int
    completed_steps: int
    error_message: str | None = None


class CapabilityResponse(BaseModel):
    tool_id: str
    provider: str
    modalities: list[str]
    input_schema: dict
    output_schema: dict
    constraints: dict
    cost_tier: str
    health_status: str
    latency_p95_ms: int | None = None
    enabled: bool
    tenant_id: str | None = None
    display_name: str | None = None
    description: str | None = None
    documentation_url: str | None = None


class ProvenanceResponse(BaseModel):
    asset_id: str
    tenant_id: str
    request_id: str | None = None
    execution_id: str | None = None
    plan_id: str | None = None
    session_id: str | None = None
    user_id: str | None = None
    prompt_summary: str | None = None
    generation_params: dict
    tool_id: str | None = None
    provider: str | None = None
    model_version: str | None = None
    trace_id: str | None = None
    span_id: str | None = None
    quality_gate_passed: bool | None = None
    quality_score: float | None = None
    rework_count: int
    created_at: str | None = None


# ============================================================================
# Helpers
# ============================================================================

def _require_multimodal_enabled() -> None:
    if cfg.env("SA01_ENABLE_MULTIMODAL_CAPABILITIES", "false").lower() != "true":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="multimodal_disabled")


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/capabilities", response_model=list[CapabilityResponse])
async def list_capabilities(
    request: Request,
    modality: str = Query(..., description="Required modality (image, diagram, screenshot, video)"),
    max_cost_tier: Optional[str] = None,
    include_unhealthy: bool = False,
    registry: Annotated[CapabilityRegistry, Depends(lambda: CapabilityRegistry())] = None,
) -> list[CapabilityResponse]:
    """List multimodal capabilities filtered by modality."""
    _require_multimodal_enabled()
    auth = await authorize(
        request,
        action="multimodal.capabilities.read",
        resource="multimodal.capabilities",
        context={"modality": modality},
    )
    tenant_id = auth.get("tenant")

    constraints = {}
    if max_cost_tier:
        constraints["max_cost_tier"] = max_cost_tier

    try:
        candidates = await registry.find_candidates(
            modality=modality,
            constraints=constraints,
            tenant_id=tenant_id,
            include_unhealthy=include_unhealthy,
        )
    except Exception as exc:
        logger.error("Failed to list capabilities: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="failed_to_list_capabilities")

    return [
        CapabilityResponse(
            tool_id=c.tool_id,
            provider=c.provider,
            modalities=c.modalities,
            input_schema=c.input_schema,
            output_schema=c.output_schema,
            constraints=c.constraints,
            cost_tier=c.cost_tier.value,
            health_status=c.health_status.value,
            latency_p95_ms=c.latency_p95_ms,
            enabled=c.enabled,
            tenant_id=c.tenant_id,
            display_name=c.display_name,
            description=c.description,
            documentation_url=c.documentation_url,
        )
        for c in candidates
    ]


@router.post("/jobs", response_model=JobCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_job(
    request: Request,
    body: JobCreateRequest,
) -> JobCreateResponse:
    """Submit a multimodal job plan (Task DSL)."""
    _require_multimodal_enabled()
    auth = await authorize(
        request,
        action="multimodal.jobs.create",
        resource="multimodal.jobs",
        context={"session_id": body.session_id},
    )
    tenant_id = auth.get("tenant")

    planner = JobPlanner()
    try:
        plan = planner.compile(
            tenant_id=tenant_id,
            session_id=body.session_id,
            dsl=body.plan,
            request_id=body.request_id,
        )
        await planner.create(plan)
    except PlanValidationError as exc:
        logger.warning("Invalid multimodal plan: %s", exc.errors)
        raise HTTPException(status_code=400, detail={"error": "invalid_plan", "issues": exc.errors})
    except Exception as exc:
        logger.error("Failed to create job plan: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="failed_to_create_job")

    return JobCreateResponse(job_id=str(plan.id), status=plan.status.value)


@router.get("/jobs/{plan_id}", response_model=JobStatusResponse)
async def get_job_status(
    request: Request,
    plan_id: UUID,
) -> JobStatusResponse:
    """Get the status of a multimodal job plan."""
    _require_multimodal_enabled()
    auth = await authorize(
        request,
        action="multimodal.jobs.read",
        resource="multimodal.jobs",
        context={"plan_id": str(plan_id)},
    )
    tenant_id = auth.get("tenant")

    planner = JobPlanner()
    try:
        plan = await planner.get(plan_id)
    except Exception as exc:
        logger.error("Failed to fetch plan: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="failed_to_get_job")

    if not plan:
        raise HTTPException(status_code=404, detail="job_not_found")
    if plan.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="tenant_mismatch")

    return JobStatusResponse(
        id=str(plan.id),
        status=plan.status.value,
        total_steps=plan.total_steps,
        completed_steps=plan.completed_steps,
        error_message=plan.error_message,
    )


@router.get("/assets/{asset_id}")
async def get_asset(
    request: Request,
    asset_id: UUID,
    store: Annotated[AssetStore, Depends(providers.get_asset_store)],
) -> StreamingResponse:
    """Retrieve a generated multimodal asset by ID."""
    _require_multimodal_enabled()
    auth = await authorize(
        request,
        action="multimodal.assets.read",
        resource="multimodal.assets",
        context={"asset_id": str(asset_id)},
    )
    tenant_id = auth.get("tenant")

    try:
        asset = await store.get(asset_id)
    except Exception as exc:
        logger.error("Failed to retrieve asset: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="failed_to_get_asset")

    if not asset:
        raise HTTPException(status_code=404, detail="asset_not_found")
    if asset.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="tenant_mismatch")
    if not asset.content:
        raise HTTPException(status_code=501, detail="external_asset_not_supported")

    return StreamingResponse(
        iter([asset.content]),
        media_type=asset.mime_type or "application/octet-stream",
        headers={
            "Content-Disposition": f"inline; filename={asset.original_filename or str(asset_id)}",
            "X-Asset-SHA256": asset.checksum_sha256,
            "X-Asset-Size": str(asset.content_size_bytes),
        },
    )


@router.get("/provenance/{asset_id}", response_model=ProvenanceResponse)
async def get_provenance(
    request: Request,
    asset_id: UUID,
) -> ProvenanceResponse:
    """Retrieve provenance record for a given asset."""
    _require_multimodal_enabled()
    auth = await authorize(
        request,
        action="multimodal.provenance.read",
        resource="multimodal.provenance",
        context={"asset_id": str(asset_id)},
    )
    tenant_id = auth.get("tenant")

    recorder = ProvenanceRecorder()
    try:
        record = await recorder.get(asset_id)
    except Exception as exc:
        logger.error("Failed to fetch provenance: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="failed_to_get_provenance")

    if not record:
        raise HTTPException(status_code=404, detail="provenance_not_found")
    if record.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="tenant_mismatch")

    return ProvenanceResponse(
        asset_id=str(record.asset_id),
        tenant_id=record.tenant_id,
        request_id=record.request_id,
        execution_id=str(record.execution_id) if record.execution_id else None,
        plan_id=str(record.plan_id) if record.plan_id else None,
        session_id=record.session_id,
        user_id=record.user_id,
        prompt_summary=record.prompt_summary,
        generation_params=record.generation_params,
        tool_id=record.tool_id,
        provider=record.provider,
        model_version=record.model_version,
        trace_id=record.trace_id,
        span_id=record.span_id,
        quality_gate_passed=record.quality_gate_passed,
        quality_score=record.quality_score,
        rework_count=record.rework_count,
        created_at=record.created_at.isoformat() if record.created_at else None,
    )
