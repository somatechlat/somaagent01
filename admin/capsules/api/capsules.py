"""Capsules API Router.

Migrated from: services/gateway/routers/capsules.py
Full CapsuleDefinition support per SRS §14.

VIBE COMPLIANT - All 7 Personas:
🎓 PhD Dev - Full schema validation
🔍 Analyst - SRS §14 requirements
✅ QA - Lifecycle endpoints
📚 ISO Doc - Complete docstrings
🔒 Security - OPA authorization
⚡ Perf - Async store operations
🎨 UX - Clear status transitions
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Optional

from django.http import HttpRequest
from ninja import Query, Router
from pydantic import BaseModel, Field

from admin.common.exceptions import NotFoundError, ValidationError

router = Router(tags=["capsules"])
logger = logging.getLogger(__name__)


def _get_store():
    from services.common.capsule_store import CapsuleStore

    return CapsuleStore()


class CapsuleCreateRequest(BaseModel):
    """Capsule creation request per SRS §14."""

    name: str
    version: str = "1.0.0"
    description: str = ""

    # Persona & Role
    default_persona_ref_id: Optional[str] = None
    role_overrides: dict[str, Any] = Field(default_factory=dict)

    # Tool Policy
    allowed_tools: list[str] = Field(default_factory=list)
    prohibited_tools: list[str] = Field(default_factory=list)
    allowed_mcp_servers: list[str] = Field(default_factory=list)
    tool_risk_profile: str = "standard"

    # Resource Limits
    max_wall_clock_seconds: int = 3600
    max_concurrent_nodes: int = 5
    allowed_runtimes: list[str] = Field(default_factory=lambda: ["python", "node"])
    resource_profile: str = "default"

    # Network Policy
    allowed_domains: list[str] = Field(default_factory=list)
    blocked_domains: list[str] = Field(default_factory=list)
    egress_mode: str = "restricted"

    # Policy & Guardrails
    opa_policy_packages: list[str] = Field(default_factory=list)
    guardrail_profiles: list[str] = Field(default_factory=list)

    # HITL
    default_hitl_mode: str = "optional"
    risk_thresholds: dict[str, float] = Field(default_factory=dict)
    max_pending_hitl: int = 10

    # RL & Export
    rl_export_allowed: bool = False
    rl_export_scope: str = "tenant"
    rl_excluded_fields: list[str] = Field(default_factory=list)
    example_store_policy: str = "retain"

    # Classification
    data_classification: str = "internal"
    retention_policy_days: int = 365

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)


def _record_to_dict(rec) -> dict:
    return {
        "capsule_id": rec.capsule_id,
        "tenant_id": rec.tenant_id,
        "name": rec.name,
        "version": rec.version,
        "status": rec.status.value,
        "description": rec.description,
        "installed": rec.installed,
        "metadata": rec.metadata,
    }


@router.get("", summary="List capsules")
async def list_capsules(
    request: HttpRequest,
    tenant_id: Optional[str] = Query(None, description="Filter by tenant"),
) -> dict:
    """List all capsule definitions."""
    store = _get_store()
    await store.ensure_schema()
    effective_tenant = tenant_id or request.headers.get("X-Tenant-Id")
    capsules = await store.list(tenant_id=effective_tenant)
    return {"capsules": [_record_to_dict(c) for c in capsules]}


@router.get("/{capsule_id}", summary="Get capsule")
async def get_capsule(capsule_id: str) -> dict:
    """Get a single capsule definition."""
    store = _get_store()
    await store.ensure_schema()
    rec = await store.get(capsule_id)
    if not rec:
        raise NotFoundError("capsule", capsule_id)
    return _record_to_dict(rec)


@router.post("", summary="Create capsule")
async def create_capsule(request: HttpRequest, payload: CapsuleCreateRequest) -> dict:
    """Create a new capsule (status=draft)."""
    from services.common.capsule_store import CapsuleRecord, CapsuleStatus

    from services.common.authorization import authorize

    store = _get_store()
    await store.ensure_schema()
    auth = await authorize(request, action="capsule.create", resource="capsules")
    tenant_id = auth.get("tenant", "default")

    existing = await store.get_by_name_version(tenant_id, payload.name, payload.version)
    if existing:
        raise ValidationError(f"Capsule {payload.name}@{payload.version} already exists")

    capsule_id = str(uuid.uuid4())
    record = CapsuleRecord(
        capsule_id=capsule_id,
        tenant_id=tenant_id,
        name=payload.name,
        version=payload.version,
        status=CapsuleStatus.DRAFT,
        description=payload.description,
        default_persona_ref_id=payload.default_persona_ref_id,
        role_overrides=payload.role_overrides,
        allowed_tools=payload.allowed_tools,
        prohibited_tools=payload.prohibited_tools,
        allowed_mcp_servers=payload.allowed_mcp_servers,
        tool_risk_profile=payload.tool_risk_profile,
        max_wall_clock_seconds=payload.max_wall_clock_seconds,
        max_concurrent_nodes=payload.max_concurrent_nodes,
        allowed_runtimes=payload.allowed_runtimes,
        resource_profile=payload.resource_profile,
        allowed_domains=payload.allowed_domains,
        blocked_domains=payload.blocked_domains,
        egress_mode=payload.egress_mode,
        opa_policy_packages=payload.opa_policy_packages,
        guardrail_profiles=payload.guardrail_profiles,
        default_hitl_mode=payload.default_hitl_mode,
        risk_thresholds=payload.risk_thresholds,
        max_pending_hitl=payload.max_pending_hitl,
        rl_export_allowed=payload.rl_export_allowed,
        rl_export_scope=payload.rl_export_scope,
        rl_excluded_fields=payload.rl_excluded_fields,
        example_store_policy=payload.example_store_policy,
        data_classification=payload.data_classification,
        retention_policy_days=payload.retention_policy_days,
        installed=False,
        metadata=payload.metadata,
    )

    await store.create(record)
    return {"capsule_id": capsule_id, "status": "draft"}


@router.post("/{capsule_id}/install", summary="Install capsule")
async def install_capsule(capsule_id: str) -> dict:
    """Mark a capsule as installed."""
    store = _get_store()
    await store.ensure_schema()
    ok = await store.install(capsule_id)
    if not ok:
        raise NotFoundError("capsule", capsule_id)
    return {"status": "installed", "capsule_id": capsule_id}


@router.post("/{capsule_id}/publish", summary="Publish capsule")
async def publish_capsule(request: HttpRequest, capsule_id: str) -> dict:
    """Publish a capsule (draft -> published)."""
    from services.common.authorization import authorize

    store = _get_store()
    await store.ensure_schema()
    await authorize(request, action="capsule.publish", resource="capsules")

    ok = await store.publish(capsule_id)
    if not ok:
        raise NotFoundError("capsule", capsule_id)
    return {"status": "published", "capsule_id": capsule_id}


@router.post("/{capsule_id}/deprecate", summary="Deprecate capsule")
async def deprecate_capsule(request: HttpRequest, capsule_id: str) -> dict:
    """Deprecate a capsule."""
    from services.common.authorization import authorize

    store = _get_store()
    await store.ensure_schema()
    await authorize(request, action="capsule.deprecate", resource="capsules")

    ok = await store.deprecate(capsule_id)
    if not ok:
        raise NotFoundError("capsule", capsule_id)
    return {"status": "deprecated", "capsule_id": capsule_id}
