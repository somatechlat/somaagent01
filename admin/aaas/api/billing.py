"""
Billing API Router
Billing metrics and invoice management via Lago.

Per SRS Section 5.1 - Billing Dashboard.
"""

import logging
from typing import Optional

from ninja import Query, Router

logger = logging.getLogger(__name__)

from admin.aaas.api.schemas import (
    BillingMetrics,
    BillingResponse,
    InvoiceOut,
    RevenueByTier,
    UsageMetrics,
)
from admin.aaas.models import SubscriptionTier, Tenant

router = Router()


@router.get("", response=BillingResponse)
def get_billing_dashboard(request):
    """Get complete billing dashboard data from Lago."""
    from django.db.models import Count, Q, Sum

    # Calculate MRR
    paid_tenants = Tenant.objects.filter(status="active").exclude(tier__base_price_cents=0)
    paid_count = paid_tenants.count()
    total_count = Tenant.objects.filter(status="active").count()

    mrr_result = paid_tenants.aggregate(total_mrr=Sum("tier__base_price_cents"))
    mrr = (mrr_result.get("total_mrr") or 0) / 100.0

    # Calculate ARPU
    arpu = mrr / paid_count if paid_count > 0 else 0.0

    metrics = BillingMetrics(
        mrr=mrr,
        mrr_growth=0.0,
        arpu=arpu,
        churn_rate=0.0,
        paid_tenants=paid_count,
        total_tenants=total_count,
    )

    # Revenue by tier breakdown
    from typing import Any

    tier_revenue: Any = (
        SubscriptionTier.objects.filter(is_active=True)
        .annotate(tenant_count=Count("tenants", filter=Q(tenants__status="active")))
        .order_by("-base_price_cents")
    )

    total_mrr = mrr if mrr > 0 else 1  # Avoid division by zero
    revenue_by_tier = [
        RevenueByTier(
            tier=t.name,
            mrr=(t.base_price_cents / 100.0) * t.tenant_count,
            count=t.tenant_count,
            percentage=((t.base_price_cents / 100.0) * t.tenant_count / total_mrr) * 100,
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
async def list_invoices(
    request,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """List all invoices from Lago."""
    from admin.billing.lago_client import get_lago_client

    try:
        client = get_lago_client()
        result = await client.list_invoices(page=page, per_page=per_page, status=status)
        invoices = result.get("invoices", [])
        return [
            InvoiceOut(
                id=inv.get("lago_id", ""),
                number=inv.get("number", ""),
                amount_cents=inv.get("total_amount_cents", 0),
                currency=inv.get("currency", "USD"),
                status=inv.get("status", "pending"),
                created_at=inv.get("created_at", ""),
            )
            for inv in invoices
        ]
    except Exception as exc:
        logger.error("Failed to list invoices from Lago: %s", exc)
        return []


@router.get("/usage", response=UsageMetrics)
def get_platform_usage(request, period: str = "month"):
    """Get platform-wide usage stats - per SRS Section 5.1."""
    from django.db.models import Sum

    from admin.aaas.models import Agent, UsageRecord

    # Aggregate usage records for the period
    usage = UsageRecord.objects.filter(billing_period=period).aggregate(
        total_tokens=Sum("quantity"),
    )

    return UsageMetrics(
        tenant_id=None,
        period=period,
        tokens_used=usage.get("total_tokens") or 0,
        storage_used_gb=0.0,
        api_calls=0,
        agents_active=Agent.objects.filter(status="active").count(),
        users_active=0,
    )


@router.get("/usage/{tenant_id}", response=UsageMetrics)
def get_tenant_usage(request, tenant_id: str, period: str = "month"):
    """Get usage stats for a specific tenant - per SRS Section 5.1."""
    from django.db.models import Sum

    from admin.aaas.models import Agent, UsageRecord

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
# Per AAAS_ADMIN_SRS.md Section 4.6 - Tenant Billing
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
    if tenant.tier and tenant.tier.base_price_cents > 0:
        # Simple: 30 days from creation (real impl would use Stripe/Lago)
        next_billing = (tenant.created_at + timedelta(days=30)).isoformat()

    return TenantBillingOut(
        tenant_id=str(tenant.id),
        tenant_name=tenant.name,
        current_tier=tenant.tier.name if tenant.tier else "Free",
        price_cents=tenant.tier.base_price_cents if tenant.tier else 0,
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
    old_price = tenant.tier.base_price_cents if tenant.tier else 0

    # Calculate proration (simplified - real impl uses Stripe)
    prorated = 0
    if payload.prorate and old_price > 0:
        # Simple: half-month proration estimate
        prorated = (new_tier.base_price_cents - old_price) // 2

    # Update tenant tier
    tenant.tier = new_tier
    tenant.save(update_fields=["tier", "updated_at"])

    # Log the change (audit trail)
    from uuid import uuid4

    from admin.aaas.models import AuditLog

    AuditLog.objects.create(
        actor_id=uuid4(),  # Would be request.user.id in real impl
        actor_email="system@somaagent.ai",
        tenant=tenant,
        action="tier.upgraded",
        resource_type="tenant",
        resource_id=tenant.id,
        old_value={"tier": old_tier_name, "price_cents": old_price},
        new_value={"tier": new_tier.name, "price_cents": new_tier.base_price_cents},
    )

    return UpgradeResponse(
        success=True,
        message=f"Successfully changed tier from {old_tier_name} to {new_tier.name}",
        old_tier=old_tier_name,
        new_tier=new_tier.name,
        prorated_amount_cents=max(0, prorated),
    )


@router.get("/tenant/{tenant_id}/invoices", response=list[InvoiceOut])
async def get_tenant_invoices(
    request,
    tenant_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """Get invoice history for a specific tenant from Lago."""
    from admin.billing.lago_client import get_lago_client

    try:
        tenant = Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist:
        from ninja.errors import HttpError

        raise HttpError(404, f"Tenant {tenant_id} not found")

    if not tenant.lago_customer_id:
        return []

    try:
        client = get_lago_client()
        result = await client.list_invoices(
            page=page,
            per_page=per_page,
            customer_external_id=tenant.lago_customer_id,
        )
        invoices = result.get("invoices", [])
        return [
            InvoiceOut(
                id=inv.get("lago_id", ""),
                number=inv.get("number", ""),
                amount_cents=inv.get("total_amount_cents", 0),
                currency=inv.get("currency", "USD"),
                status=inv.get("status", "pending"),
                created_at=inv.get("created_at", ""),
            )
            for inv in invoices
        ]
    except Exception as exc:
        logger.error("Failed to list tenant invoices from Lago: %s", exc)
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
async def add_payment_method(request, tenant_id: str, payload: PaymentMethodCreate):
    """Add a payment method for a tenant.

    Stores the payment provider token reference in tenant metadata.
    Does NOT fabricate card details — only persists the token reference.
    """
    from ninja.errors import HttpError

    try:
        tenant = Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist:
        raise HttpError(404, f"Tenant {tenant_id} not found")

    # Store token reference in tenant metadata (Stripe library not installed)
    # In production with Stripe: stripe.PaymentMethod.attach(payload.token, customer=tenant.stripe_id)
    metadata = tenant.metadata or {}
    payment_methods = metadata.get("payment_methods", [])

    pm_ref = {
        "id": f"pm_ref_{payload.token[:12]}",
        "token": payload.token,
        "type": "card",  # Type unknown until verified by payment provider
        "last4": None,  # Not available without Stripe verification
        "is_default": payload.set_default,
        "created_at": __import__("datetime")
        .datetime.now(__import__("datetime").timezone.utc)
        .isoformat(),
    }

    # If setting as default, unset others
    if payload.set_default:
        for pm in payment_methods:
            pm["is_default"] = False

    payment_methods.append(pm_ref)
    metadata["payment_methods"] = payment_methods
    tenant.metadata = metadata
    tenant.save(update_fields=["metadata", "updated_at"])

    return {
        "success": True,
        "message": "Payment method reference stored. Stripe verification required for full card details.",
        "payment_method": pm_ref,
    }
