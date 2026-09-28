"""Tenants API - Multi-tenant management.


Tenant lifecycle and configuration.

- PM: Tenant onboarding, management
- Security Auditor: Tenant isolation
- DevOps: Resource allocation
"""

from __future__ import annotations

import logging
from typing import Optional

from ninja import Router
from ninja.errors import HttpError
from pydantic import BaseModel

from admin.common.auth import AuthBearer

router = Router(tags=["tenants"])
logger = logging.getLogger(__name__)


def _tenant_to_api(tenant) -> "Tenant":
    """Map the real AAAS Tenant row onto this API's response shape."""
    return Tenant(
        tenant_id=str(tenant.id),
        name=tenant.name,
        slug=tenant.slug,
        status=tenant.status,
        plan=tenant.tier.name if tenant.tier_id else "free",
        created_at=tenant.created_at.isoformat() if tenant.created_at else "",
        owner_id=tenant.billing_email or "",
        settings=tenant.feature_overrides or {},
        limits={},
    )


# =============================================================================
# SCHEMAS
# =============================================================================


class Tenant(BaseModel):
    """Tenant definition."""

    tenant_id: str
    name: str
    slug: str
    status: str  # active, suspended, trial, canceled
    plan: str  # free, starter, pro, enterprise
    created_at: str
    owner_id: str
    settings: dict
    limits: dict


class TenantStats(BaseModel):
    """Tenant statistics."""

    total_users: int
    total_agents: int
    total_conversations: int
    storage_used_mb: float
    api_calls_this_month: int


class TenantInvite(BaseModel):
    """Tenant invitation."""

    invite_id: str
    email: str
    role: str
    status: str  # pending, accepted, expired
    created_at: str
    expires_at: str


# =============================================================================
# ENDPOINTS - Tenant CRUD
# =============================================================================


@router.get(
    "",
    summary="List tenants",
    auth=AuthBearer(),
)
async def list_tenants(
    request,
    status: Optional[str] = None,
    plan: Optional[str] = None,
    limit: int = 50,
) -> dict:
    """List all tenants (AAAS Admin).

    PM: Platform overview.
    """
    from admin.aaas.models import Tenant as AaasTenant

    qs = AaasTenant.objects.select_related("tier").all()
    if status:
        qs = qs.filter(status=status)
    tenants = [_tenant_to_api(t) for t in qs[:limit]]
    return {
        "tenants": [t.dict() for t in tenants],
        "total": len(tenants),
    }


@router.post(
    "",
    response=Tenant,
    summary="Create tenant",
    auth=AuthBearer(),
)
async def create_tenant(
    request,
    name: str,
    owner_email: str,
    plan: str = "trial",
) -> Tenant:
    """Create a new tenant.

    PM: Tenant onboarding.
    """
    raise HttpError(
        501,
        "Tenant creation is not implemented on this endpoint. "
        "Use the AAAS tenant administration API (admin.aaas.models.Tenant).",
    )


@router.get(
    "/{tenant_id}",
    response=Tenant,
    summary="Get tenant",
    auth=AuthBearer(),
)
async def get_tenant(request, tenant_id: str) -> Tenant:
    """Get tenant details."""
    from admin.aaas.models import Tenant as AaasTenant

    try:
        tenant = AaasTenant.objects.select_related("tier").get(id=tenant_id)
    except AaasTenant.DoesNotExist:
        raise HttpError(404, f"Tenant {tenant_id} not found")
    return _tenant_to_api(tenant)


@router.patch(
    "/{tenant_id}",
    summary="Update tenant",
    auth=AuthBearer(),
)
async def update_tenant(
    request,
    tenant_id: str,
    name: Optional[str] = None,
    settings: Optional[dict] = None,
) -> dict:
    """Update tenant settings."""
    raise HttpError(
        501,
        "Tenant update is not implemented on this endpoint. "
        "Use the AAAS tenant administration API (admin.aaas.models.Tenant).",
    )


@router.delete(
    "/{tenant_id}",
    summary="Delete tenant",
    auth=AuthBearer(),
)
async def delete_tenant(request, tenant_id: str) -> dict:
    """Delete a tenant (GDPR).

    Security Auditor: Complete data deletion.
    """
    raise HttpError(
        501,
        "Tenant deletion is not implemented on this endpoint. "
        "Use the AAAS tenant administration API (admin.aaas.models.Tenant).",
    )


# =============================================================================
# ENDPOINTS - Status Management
# =============================================================================


@router.post(
    "/{tenant_id}/suspend",
    summary="Suspend tenant",
    auth=AuthBearer(),
)
async def suspend_tenant(
    request,
    tenant_id: str,
    reason: str,
) -> dict:
    """Suspend a tenant.

    Security Auditor: Abuse response.
    """
    raise HttpError(
        501,
        "Tenant suspend is not implemented on this endpoint. "
        "Use the AAAS tenant administration API (admin.aaas.models.Tenant).",
    )


@router.post(
    "/{tenant_id}/activate",
    summary="Activate tenant",
    auth=AuthBearer(),
)
async def activate_tenant(request, tenant_id: str) -> dict:
    """Activate a suspended tenant."""
    raise HttpError(
        501,
        "Tenant activate is not implemented on this endpoint. "
        "Use the AAAS tenant administration API (admin.aaas.models.Tenant).",
    )


# =============================================================================
# ENDPOINTS - Stats & Usage
# =============================================================================


@router.get(
    "/{tenant_id}/stats",
    response=TenantStats,
    summary="Get tenant stats",
    auth=AuthBearer(),
)
async def get_tenant_stats(request, tenant_id: str) -> TenantStats:
    """Get tenant statistics.

    PM: Usage overview.
    """
    return TenantStats(
        total_users=0,
        total_agents=0,
        total_conversations=0,
        storage_used_mb=0.0,
        api_calls_this_month=0,
    )


@router.get(
    "/{tenant_id}/limits",
    summary="Get tenant limits",
    auth=AuthBearer(),
)
async def get_tenant_limits(request, tenant_id: str) -> dict:
    """Get tenant resource limits.

    DevOps: Resource allocation.
    """
    raise HttpError(
        501,
        "Tenant limits are not implemented on this endpoint: " "no limit store is wired.",
    )


# =============================================================================
# ENDPOINTS - Users & Invites
# =============================================================================


@router.get(
    "/{tenant_id}/users",
    summary="List tenant users",
    auth=AuthBearer(),
)
async def list_tenant_users(
    request,
    tenant_id: str,
) -> dict:
    """List users in a tenant."""
    return {
        "tenant_id": tenant_id,
        "users": [],
        "total": 0,
    }


@router.post(
    "/{tenant_id}/invites",
    summary="Send invite",
    auth=AuthBearer(),
)
async def send_invite(
    request,
    tenant_id: str,
    email: str,
    role: str = "user",
) -> dict:
    """Invite user to tenant.

    PM: User onboarding.
    """
    raise HttpError(
        501,
        "Tenant invites are not implemented on this endpoint: no invite store is wired.",
    )


@router.get(
    "/{tenant_id}/invites",
    summary="List invites",
    auth=AuthBearer(),
)
async def list_invites(
    request,
    tenant_id: str,
) -> dict:
    """List pending invites."""
    return {
        "tenant_id": tenant_id,
        "invites": [],
        "total": 0,
    }


# =============================================================================
# ENDPOINTS - Plan Management
# =============================================================================


@router.post(
    "/{tenant_id}/upgrade",
    summary="Upgrade plan",
    auth=AuthBearer(),
)
async def upgrade_plan(
    request,
    tenant_id: str,
    new_plan: str,
) -> dict:
    """Upgrade tenant plan.

    PM: Plan management.
    """
    raise HttpError(
        501,
        "Tenant plan changes are not implemented on this endpoint. "
        "Use the AAAS subscription API.",
    )


@router.post(
    "/{tenant_id}/downgrade",
    summary="Downgrade plan",
    auth=AuthBearer(),
)
async def downgrade_plan(
    request,
    tenant_id: str,
    new_plan: str,
) -> dict:
    """Downgrade tenant plan."""
    raise HttpError(
        501,
        "Tenant plan changes are not implemented on this endpoint. "
        "Use the AAAS subscription API.",
    )
