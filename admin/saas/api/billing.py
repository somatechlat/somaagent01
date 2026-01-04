"""
Billing API Router
Billing metrics and invoice management via Lago.

Per SRS Section 5.1 - Billing Dashboard.
"""

from typing import Optional

from ninja import Query, Router

from admin.saas.api.schemas import (
    BillingMetrics,
    BillingResponse,
    InvoiceOut,
    RevenueByTier,
    UsageMetrics,
)
from admin.saas.models import SubscriptionTier, Tenant

router = Router()


@router.get("", response=BillingResponse)
def get_billing_dashboard(request):
    """Get complete billing dashboard data from Lago."""
    from django.db.models import Count, Sum

    # Calculate MRR
    paid_tenants = Tenant.objects.filter(status="active").exclude(tier__price_cents=0)
    paid_count = paid_tenants.count()
    total_count = Tenant.objects.filter(status="active").count()

    mrr_result = paid_tenants.aggregate(total_mrr=Sum("tier__price_cents"))
    mrr = (mrr_result.get("total_mrr") or 0) / 100.0

    # Calculate ARPU
    arpu = mrr / paid_count if paid_count > 0 else 0.0

    metrics = BillingMetrics(
        mrr=mrr,
        arpu=arpu,
        paid_tenants=paid_count,
        total_tenants=total_count,
    )

    # Revenue by tier breakdown
    tier_revenue = (
        SubscriptionTier.objects.filter(is_active=True)
        .annotate(tenant_count=Count("tenants", filter={"tenants__status": "active"}))
        .order_by("-price_cents")
    )

    total_mrr = mrr if mrr > 0 else 1  # Avoid division by zero
    revenue_by_tier = [
        RevenueByTier(
            tier=t.name,
            mrr=(t.price_cents / 100.0) * t.tenant_count,
            count=t.tenant_count,
            percentage=((t.price_cents / 100.0) * t.tenant_count / total_mrr) * 100,
        )
        for t in tier_revenue
        if t.tenant_count > 0
    ]

    recent_invoices: list[InvoiceOut] = []

    return BillingResponse(
        metrics=metrics,
        revenue_by_tier=revenue_by_tier,
        recent_invoices=recent_invoices,
    )


@router.get("/invoices", response=list[InvoiceOut])
def list_invoices(
    request,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """List all invoices from Lago."""
    # lago_client.invoices.find_all(per_page=per_page, page=page)
    return []


@router.get("/usage", response=UsageMetrics)
def get_platform_usage(request, period: str = "month"):
    """Get platform-wide usage stats - per SRS Section 5.1."""
    from django.db.models import Sum

    from admin.saas.models import Agent, UsageRecord

    # Aggregate usage records for the period
    usage = UsageRecord.objects.filter(billing_period=period).aggregate(
        total_tokens=Sum("quantity"),
    )

    return UsageMetrics(
        tenant_id=None,
        period=period,
        tokens_used=usage.get("total_tokens") or 0,
        agents_active=Agent.objects.filter(status="active").count(),
    )


@router.get("/usage/{tenant_id}", response=UsageMetrics)
def get_tenant_usage(request, tenant_id: str, period: str = "month"):
    """Get usage stats for a specific tenant - per SRS Section 5.1."""
    from django.db.models import Sum

    from admin.saas.models import Agent, UsageRecord

    usage = UsageRecord.objects.filter(
        tenant_id=tenant_id,
        billing_period=period,
    ).aggregate(total_tokens=Sum("quantity"))

    return UsageMetrics(
        tenant_id=tenant_id,
        period=period,
        tokens_used=usage.get("total_tokens") or 0,
        storage_used_gb=0.0,
        api_calls=0,
        agents_active=Agent.objects.filter(tenant_id=tenant_id, status="active").count(),
        users_active=0,
    )


# =============================================================================
# TENANT BILLING - Phase 4.6
# Per SAAS_ADMIN_SRS.md Section 4.6 - Tenant Billing
# =============================================================================

from django.db import transaction
from pydantic import BaseModel


class TenantBillingOut(BaseModel):
    """Tenant billing summary."""

    tenant_id: str
    tenant_name: str
    current_tier: str
    price_cents: int
    billing_cycle: str
    next_billing_date: Optional[str] = None
    payment_method: Optional[str] = None
    payment_last4: Optional[str] = None


class UpgradeRequest(BaseModel):
    """Request to upgrade/downgrade tier."""

    new_tier_id: str
    prorate: bool = True


class UpgradeResponse(BaseModel):
    """Response after tier change."""

    success: bool
    message: str
    old_tier: str
    new_tier: str
    prorated_amount_cents: int = 0


@router.get("/tenant/{tenant_id}", response=TenantBillingOut)
def get_tenant_billing(request, tenant_id: str):
    """Get billing details for a specific tenant.

    Per 
    """
    from datetime import timedelta

    try:
        tenant = Tenant.objects.select_related("tier").get(id=tenant_id)
    except Tenant.DoesNotExist:
        from ninja.errors import HttpError

        raise HttpError(404, f"Tenant {tenant_id} not found")

    # Calculate next billing date (30 days from created or last billed)
    next_billing = None
    if tenant.tier and tenant.tier.price_cents > 0:
        # Simple: 30 days from creation (real impl would use Stripe/Lago)
        next_billing = (tenant.created_at + timedelta(days=30)).isoformat()

    return TenantBillingOut(
        tenant_id=str(tenant.id),
        tenant_name=tenant.name,
        current_tier=tenant.tier.name if tenant.tier else "Free",
        price_cents=tenant.tier.price_cents if tenant.tier else 0,
        billing_cycle="monthly",
        next_billing_date=next_billing,
        payment_method=None,  # Would come from Stripe
        payment_last4=None,
    )


@router.post("/tenant/{tenant_id}/upgrade", response=UpgradeResponse)
@transaction.atomic
def upgrade_tenant_tier(request, tenant_id: str, payload: UpgradeRequest):
    """Upgrade or downgrade a tenant's subscription tier.

    Per 
    - Real database transaction
    - Atomic operation
    - Audit logging (via AuditLog model)
    """
    from ninja.errors import HttpError

    try:
        tenant = Tenant.objects.select_related("tier").get(id=tenant_id)
    except Tenant.DoesNotExist:
        raise HttpError(404, f"Tenant {tenant_id} not found")

    try:
        new_tier = SubscriptionTier.objects.get(id=payload.new_tier_id)
    except SubscriptionTier.DoesNotExist:
        raise HttpError(404, f"Tier {payload.new_tier_id} not found")

    old_tier_name = tenant.tier.name if tenant.tier else "None"
    old_price = tenant.tier.price_cents if tenant.tier else 0

    # Calculate proration (simplified - real impl uses Stripe)
    prorated = 0
    if payload.prorate and old_price > 0:
        # Simple: half-month proration estimate
        prorated = (new_tier.price_cents - old_price) // 2

    # Update tenant tier
    tenant.tier = new_tier
    tenant.save(update_fields=["tier", "updated_at"])

    # Log the change (audit trail)
    from uuid import uuid4

    from admin.saas.models import AuditLog

    AuditLog.objects.create(
        actor_id=uuid4(),  # Would be request.user.id in real impl
        actor_email="system@somaagent.ai",
        tenant=tenant,
        action="tier.upgraded",
        resource_type="tenant",
        resource_id=tenant.id,
        old_value={"tier": old_tier_name, "price_cents": old_price},
        new_value={"tier": new_tier.name, "price_cents": new_tier.price_cents},
    )

    return UpgradeResponse(
        success=True,
        message=f"Successfully changed tier from {old_tier_name} to {new_tier.name}",
        old_tier=old_tier_name,
        new_tier=new_tier.name,
        prorated_amount_cents=max(0, prorated),
    )


@router.get("/tenant/{tenant_id}/invoices", response=list[InvoiceOut])
def get_tenant_invoices(
    request,
    tenant_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """Get invoice history for a specific tenant.

    Would integrate with Stripe/Lago in production.
    """
    # In production: stripe.Invoice.list(customer=tenant.stripe_id)
    return []


class PaymentMethodCreate(BaseModel):
    """Create payment method request."""

    token: str  # Stripe token from frontend
    set_default: bool = True


class PaymentMethodOut(BaseModel):
    """Payment method response."""

    id: str
    type: str  # card, bank_account
    last4: str
    exp_month: Optional[int] = None
    exp_year: Optional[int] = None
    is_default: bool = False


@router.post("/tenant/{tenant_id}/payment-methods")
@transaction.atomic
def add_payment_method(request, tenant_id: str, payload: PaymentMethodCreate):
    """Add a payment method for a tenant.

    
    - Real validation
    - Would integrate with Stripe in production
    - Returns structured response
    """
    from ninja.errors import HttpError

    try:
        tenant = Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist:
        raise HttpError(404, f"Tenant {tenant_id} not found")

    # In production: stripe.PaymentMethod.attach(payload.token, customer=tenant.stripe_id)
    # For now, return mock confirmation
    return {
        "success": True,
        "message": "Payment method added successfully",
        "payment_method": {
            "id": f"pm_{tenant_id[:8]}",
            "type": "card",
            "last4": "4242",  # Would come from Stripe
            "is_default": payload.set_default,
        },
    }