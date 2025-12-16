"""Capsule endpoints with full CapsuleDefinition support per SRS §14."""

from __future__ import annotations

import uuid
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from services.common.capsule_store import CapsuleRecord, CapsuleStatus, CapsuleStore
from services.common.authorization import authorize

router = APIRouter(prefix="/v1/capsules", tags=["capsules"])
STORE = CapsuleStore()


class CapsuleCreateRequest(BaseModel):
    """Request body for creating a capsule definition."""
    name: str
    version: str = "1.0.0"
    description: str = ""
    
    # Persona & Role
    default_persona_ref_id: Optional[str] = None
    role_overrides: Dict[str, Any] = Field(default_factory=dict)
    
    # Tool Policy
    allowed_tools: List[str] = Field(default_factory=list)
    prohibited_tools: List[str] = Field(default_factory=list)
    allowed_mcp_servers: List[str] = Field(default_factory=list)
    tool_risk_profile: str = "standard"
    
    # Resource Limits
    max_wall_clock_seconds: int = 3600
    max_concurrent_nodes: int = 5
    allowed_runtimes: List[str] = Field(default_factory=lambda: ["python", "node"])
    resource_profile: str = "default"
    
    # Network Policy
    allowed_domains: List[str] = Field(default_factory=list)
    blocked_domains: List[str] = Field(default_factory=list)
    egress_mode: str = "restricted"
    
    # Policy & Guardrails
    opa_policy_packages: List[str] = Field(default_factory=list)
    guardrail_profiles: List[str] = Field(default_factory=list)
    
    # HITL
    default_hitl_mode: str = "optional"
    risk_thresholds: Dict[str, float] = Field(default_factory=dict)
    max_pending_hitl: int = 10
    
    # RL & Export
    rl_export_allowed: bool = False
    rl_export_scope: str = "tenant"
    rl_excluded_fields: List[str] = Field(default_factory=list)
    example_store_policy: str = "retain"
    
    # Classification & Retention
    data_classification: str = "internal"
    retention_policy_days: int = 365
    
    # Legacy
    metadata: Dict[str, Any] = Field(default_factory=dict)


@router.get("")
async def list_capsules(
    request: Request,
    tenant_id: Optional[str] = Query(None, description="Filter by tenant"),
):
    """List all capsule definitions, optionally filtered by tenant."""
    await STORE.ensure_schema()
    # Extract tenant from header if not provided
    effective_tenant = tenant_id or request.headers.get("X-Tenant-Id")
    capsules = await STORE.list(tenant_id=effective_tenant)
    return {"capsules": [_record_to_dict(c) for c in capsules]}


@router.get("/{capsule_id}")
async def get_capsule(capsule_id: str):
    """Get a single capsule definition by ID."""
    await STORE.ensure_schema()
    rec = await STORE.get(capsule_id)
    if not rec:
        raise HTTPException(status_code=404, detail="capsule_not_found")
    return _record_to_dict(rec)


@router.post("")
async def create_capsule(request: Request, payload: CapsuleCreateRequest):
    """Create a new capsule definition (status=draft)."""
    await STORE.ensure_schema()
    auth = await authorize(request, action="capsule.create", resource="capsules")
    tenant_id = auth.get("tenant", "default")
    
    # Check for duplicate
    existing = await STORE.get_by_name_version(tenant_id, payload.name, payload.version)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Capsule {payload.name}@{payload.version} already exists for tenant {tenant_id}"
        )
    
    # Create record
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
    
    await STORE.create(record)
    return {"capsule_id": capsule_id, "status": "draft"}


@router.post("/{capsule_id}/install")
async def install_capsule(capsule_id: str):
    """Mark a capsule as installed."""
    await STORE.ensure_schema()
    ok = await STORE.install(capsule_id)
    if not ok:
        raise HTTPException(status_code=404, detail="capsule_not_found")
    return {"status": "installed", "capsule_id": capsule_id}


@router.post("/{capsule_id}/publish")
async def publish_capsule(request: Request, capsule_id: str):
    """Publish a capsule (change status from draft to published)."""
    await STORE.ensure_schema()
    await authorize(request, action="capsule.publish", resource="capsules")
    
    ok = await STORE.publish(capsule_id)
    if not ok:
        raise HTTPException(status_code=404, detail="capsule_not_found")
    return {"status": "published", "capsule_id": capsule_id}


@router.post("/{capsule_id}/deprecate")
async def deprecate_capsule(request: Request, capsule_id: str):
    """Deprecate a capsule."""
    await STORE.ensure_schema()
    await authorize(request, action="capsule.deprecate", resource="capsules")
    
    ok = await STORE.deprecate(capsule_id)
    if not ok:
        raise HTTPException(status_code=404, detail="capsule_not_found")
    return {"status": "deprecated", "capsule_id": capsule_id}


def _record_to_dict(rec: CapsuleRecord) -> Dict[str, Any]:
    """Convert CapsuleRecord to dict for JSON response."""
    return {
        "capsule_id": rec.capsule_id,
        "tenant_id": rec.tenant_id,
        "name": rec.name,
        "version": rec.version,
        "status": rec.status.value,
        "description": rec.description,
        "default_persona_ref_id": rec.default_persona_ref_id,
        "role_overrides": rec.role_overrides,
        "allowed_tools": rec.allowed_tools,
        "prohibited_tools": rec.prohibited_tools,
        "allowed_mcp_servers": rec.allowed_mcp_servers,
        "tool_risk_profile": rec.tool_risk_profile,
        "max_wall_clock_seconds": rec.max_wall_clock_seconds,
        "max_concurrent_nodes": rec.max_concurrent_nodes,
        "allowed_runtimes": rec.allowed_runtimes,
        "resource_profile": rec.resource_profile,
        "allowed_domains": rec.allowed_domains,
        "blocked_domains": rec.blocked_domains,
        "egress_mode": rec.egress_mode,
        "opa_policy_packages": rec.opa_policy_packages,
        "guardrail_profiles": rec.guardrail_profiles,
        "default_hitl_mode": rec.default_hitl_mode,
        "risk_thresholds": rec.risk_thresholds,
        "max_pending_hitl": rec.max_pending_hitl,
        "rl_export_allowed": rec.rl_export_allowed,
        "rl_export_scope": rec.rl_export_scope,
        "rl_excluded_fields": rec.rl_excluded_fields,
        "example_store_policy": rec.example_store_policy,
        "data_classification": rec.data_classification,
        "retention_policy_days": rec.retention_policy_days,
        "installed": rec.installed,
        "metadata": rec.metadata,
    }

