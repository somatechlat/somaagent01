"""
Tenants API Router
CRUD operations for tenant management.

Per SRS Section 5.1 - Tenant Management.
"""

from typing import Optional
from uuid import uuid4

from django.db import transaction
from django.utils.text import slugify
from ninja import Query, Router

from admin.aaas.api.schemas import (
    MessageResponse,
    TenantCreate,
    TenantListResponse,
    TenantOut,
    TenantUpdate,
)
from admin.aaas.models import Tenant

router = Router()


@router.get("/check-slug")
def check_slug_availability(request, slug: str) -> dict:
    """Check if a tenant slug is available.

    Per SRS-AAAS-TENANT-CREATION.md Section 5.1:
    Real-time validation with suggestions for taken slugs.
    """
    # Normalize slug
    slug = slug.lower().strip()

    # Check if exists
    exists = Tenant.objects.filter(slug=slug).exists()

    if exists:
        # Generate suggestions
        suggestions = []
        for suffix in ["-inc", "-global", "-ai", "-1"]:
            new_slug = f"{slug}{suffix}"
            if not Tenant.objects.filter(slug=new_slug).exists():
                suggestions.append(new_slug)
                if len(suggestions) >= 3:
                    break

        return {
            "available": False,
            "slug": slug,
            "suggestions": suggestions,
        }

    return {"available": True, "slug": slug}


def _tenant_to_out(tenant: Tenant) -> TenantOut:
    """Convert Tenant model to output schema."""
    return TenantOut(
        id=str(tenant.id),
        name=tenant.name,
        slug=tenant.slug,
        status=tenant.status,
        tier=tenant.tier.slug if tenant.tier else "free",
        created_at=tenant.created_at,
        agents=tenant.agents.count(),
        users=tenant.users.count(),
        mrr=(tenant.tier.price_cents / 100.0) if tenant.tier else 0.0,
    )


@router.get("", response=TenantListResponse)
def list_tenants(
    request,
    status: Optional[str] = None,
    tier: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """List all tenants with filtering and pagination."""
    qs = Tenant.objects.select_related("tier").prefetch_related("agents", "users")

    if status:
        qs = qs.filter(status=status)
    if tier:
        qs = qs.filter(tier__slug=tier)
    if search:
        qs = qs.filter(name__icontains=search)

    total = qs.count()
    offset = (page - 1) * per_page
    tenants = qs.order_by("-created_at")[offset : offset + per_page]

    return TenantListResponse(
        items=[_tenant_to_out(t) for t in tenants],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{tenant_id}", response=TenantOut)
def get_tenant(request, tenant_id: str):
    """Get single tenant details."""
    tenant = Tenant.objects.select_related("tier").get(id=tenant_id)
    return _tenant_to_out(tenant)


@router.post("", response=TenantOut)
@transaction.atomic
def create_tenant(request, payload: TenantCreate):
    """
    Provision a new tenant.
    Creates tenant in database and optionally syncs to Lago.
    """
    from admin.aaas.models import SubscriptionTier

    # Get the requested tier or default to starter
    tier = SubscriptionTier.objects.filter(slug=payload.tier).first()
    if not tier:
        tier = SubscriptionTier.objects.filter(slug="starter").first()

    tenant = Tenant.objects.create(
        id=uuid4(),
        name=payload.name,
        slug=slugify(payload.name),
        tier=tier,
        status="active",
        lago_customer_id=None,  # Will be set when synced to Lago
        keycloak_realm_id=None,  # Will be set when provisioned in Keycloak
    )

    return _tenant_to_out(tenant)


@router.patch("/{tenant_id}", response=TenantOut)
@transaction.atomic
def update_tenant(request, tenant_id: str, payload: TenantUpdate):
    """Update tenant details."""
    tenant = Tenant.objects.select_related("tier").get(id=tenant_id)

    if payload.name is not None:
        tenant.name = payload.name
        tenant.slug = slugify(payload.name)
    if payload.status is not None:
        tenant.status = payload.status
    if payload.tier is not None:
        from admin.aaas.models import SubscriptionTier

        tier = SubscriptionTier.objects.filter(slug=payload.tier).first()
        if tier:
            tenant.tier = tier

    tenant.save()
    return _tenant_to_out(tenant)


@router.delete("/{tenant_id}", response=MessageResponse)
@transaction.atomic
def delete_tenant(request, tenant_id: str):
    """Soft-delete a tenant by setting status to churned."""
    tenant = Tenant.objects.get(id=tenant_id)
    tenant.status = "churned"
    tenant.save()
    return MessageResponse(message=f"Tenant {tenant.name} marked as churned")


@router.post("/{tenant_id}/suspend", response=MessageResponse)
@transaction.atomic
def suspend_tenant(request, tenant_id: str):
    """Suspend a tenant - per SRS Section 5.1."""
    tenant = Tenant.objects.get(id=tenant_id)
    tenant.status = "suspended"
    tenant.save()

    # Deactivate all agents
    tenant.agents.update(status="paused")

    return MessageResponse(message=f"Tenant {tenant.name} suspended")


@router.post("/{tenant_id}/activate", response=MessageResponse)
@transaction.atomic
def activate_tenant(request, tenant_id: str):
    """Reactivate a suspended tenant - per SRS Section 5.1."""
    tenant = Tenant.objects.get(id=tenant_id)
    tenant.status = "active"
    tenant.save()

    # Reactivate agents that were paused
    tenant.agents.filter(status="paused").update(status="active")

    return MessageResponse(message=f"Tenant {tenant.name} activated")
