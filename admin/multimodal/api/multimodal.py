"""Multimodal API Router.

Migrated from: services/gateway/routers/multimodal.py
Django Ninja with streaming responses and OPA auth.

VIBE COMPLIANT - Django patterns, security-first.
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from django.conf import settings
from django.http import HttpRequest, StreamingHttpResponse
from ninja import Router, Query
from pydantic import BaseModel, Field

from admin.common.exceptions import NotFoundError, ForbiddenError, ServiceError

router = Router(tags=["multimodal"])
logger = logging.getLogger(__name__)

MULTIMODAL_ENABLED = getattr(settings, "SA01_ENABLE_MULTIMODAL_CAPABILITIES", False)


class JobCreateRequest(BaseModel):
    plan: dict = Field(..., description="Task DSL plan JSON")
    session_id: str = Field(..., description="Session ID")
    request_id: Optional[str] = Field(None, description="Correlation ID")


class JobCreateResponse(BaseModel):
    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    id: str
    status: str
    total_steps: int
    completed_steps: int
    error_message: Optional[str] = None


class CapabilityResponse(BaseModel):
    tool_id: str
    provider: str
    modalities: list[str]
    input_schema: dict
    output_schema: dict
    constraints: dict
    cost_tier: str
    health_status: str
    enabled: bool


class ProvenanceResponse(BaseModel):
    asset_id: str
    tenant_id: str
    generation_params: dict
    rework_count: int


def _require_multimodal_enabled():
    if not MULTIMODAL_ENABLED:
        raise ForbiddenError("Multimodal capabilities disabled")


@router.get("/capabilities", response=list[CapabilityResponse], summary="List capabilities")
async def list_capabilities(
    request: HttpRequest,
    modality: str = Query(..., description="Modality (image, diagram, screenshot, video)"),
    max_cost_tier: Optional[str] = None,
    include_unhealthy: bool = False,
) -> list[dict]:
    """List multimodal capabilities filtered by modality."""
    from services.common.authorization import authorize
    from services.common.capability_registry import CapabilityRegistry

    _require_multimodal_enabled()
    auth = await authorize(
        request, action="multimodal.capabilities.read", resource="multimodal.capabilities"
    )
    tenant_id = auth.get("tenant")

    registry = CapabilityRegistry()
    constraints = {"max_cost_tier": max_cost_tier} if max_cost_tier else {}

    candidates = await registry.find_candidates(
        modality=modality,
        constraints=constraints,
        tenant_id=tenant_id,
        include_unhealthy=include_unhealthy,
    )

    return [
        {
            "tool_id": c.tool_id,
            "provider": c.provider,
            "modalities": c.modalities,
            "input_schema": c.input_schema,
            "output_schema": c.output_schema,
            "constraints": c.constraints,
            "cost_tier": c.cost_tier.value,
            "health_status": c.health_status.value,
            "enabled": c.enabled,
        }
        for c in candidates
    ]


@router.post("/jobs", response=JobCreateResponse, summary="Create multimodal job")
async def create_job(request: HttpRequest, body: JobCreateRequest) -> dict:
    """Submit a multimodal job plan (Task DSL)."""
    from services.common.authorization import authorize
    from services.common.job_planner import JobPlanner, PlanValidationError

    _require_multimodal_enabled()
    auth = await authorize(request, action="multimodal.jobs.create", resource="multimodal.jobs")
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
        from admin.common.exceptions import ValidationError

        raise ValidationError(f"Invalid plan: {exc.errors}")

    return {"job_id": str(plan.id), "status": plan.status.value}


@router.get("/jobs/{plan_id}", response=JobStatusResponse, summary="Get job status")
async def get_job_status(request: HttpRequest, plan_id: str) -> dict:
    """Get the status of a multimodal job plan."""
    from services.common.authorization import authorize
    from services.common.job_planner import JobPlanner

    _require_multimodal_enabled()
    auth = await authorize(request, action="multimodal.jobs.read", resource="multimodal.jobs")
    tenant_id = auth.get("tenant")

    planner = JobPlanner()
    plan = await planner.get(UUID(plan_id))

    if not plan:
        raise NotFoundError("job", plan_id)
    if plan.tenant_id != tenant_id:
        raise ForbiddenError("Tenant mismatch")

    return {
        "id": str(plan.id),
        "status": plan.status.value,
        "total_steps": plan.total_steps,
        "completed_steps": plan.completed_steps,
        "error_message": plan.error_message,
    }


@router.get("/assets/{asset_id}", summary="Get asset")
async def get_asset(request: HttpRequest, asset_id: str):
    """Retrieve a generated multimodal asset by ID."""
    from services.common.authorization import authorize
    from services.gateway import providers

    _require_multimodal_enabled()
    auth = await authorize(request, action="multimodal.assets.read", resource="multimodal.assets")
    tenant_id = auth.get("tenant")

    store = providers.get_asset_store()
    asset = await store.get(UUID(asset_id))

    if not asset:
        raise NotFoundError("asset", asset_id)
    if asset.tenant_id != tenant_id:
        raise ForbiddenError("Tenant mismatch")

    return StreamingHttpResponse(
        iter([asset.content]),
        content_type=asset.mime_type or "application/octet-stream",
        headers={
            "Content-Disposition": f"inline; filename={asset.original_filename or asset_id}",
            "X-Asset-SHA256": asset.checksum_sha256,
        },
    )


@router.get("/provenance/{asset_id}", response=ProvenanceResponse, summary="Get provenance")
async def get_provenance(request: HttpRequest, asset_id: str) -> dict:
    """Retrieve provenance record for an asset."""
    from services.common.authorization import authorize
    from services.common.provenance_recorder import ProvenanceRecorder

    _require_multimodal_enabled()
    auth = await authorize(
        request, action="multimodal.provenance.read", resource="multimodal.provenance"
    )
    tenant_id = auth.get("tenant")

    recorder = ProvenanceRecorder()
    record = await recorder.get(UUID(asset_id))

    if not record:
        raise NotFoundError("provenance", asset_id)
    if record.tenant_id != tenant_id:
        raise ForbiddenError("Tenant mismatch")

    return {
        "asset_id": str(record.asset_id),
        "tenant_id": record.tenant_id,
        "generation_params": record.generation_params,
        "rework_count": record.rework_count,
    }
