"""
Billing API Router
Billing metrics and invoice management.

Per SRS Section 5.1 - Billing Dashboard.
"""

import hashlib
import hmac
import logging
from datetime import datetime, timezone
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
from admin.common.auth import AuthBearer
from admin.common.messages import get_message, SuccessCode

router = Router()


@router.get("", response=BillingResponse)
def get_billing_dashboard(request):
    """Get complete billing dashboard data."""
    from django.db.models import Count, Q

    # MRR/ARPU are owned by admin.aaas.services.billing.
    from admin.aaas.services.billing import compute_mrr_and_arpu

    revenue = compute_mrr_and_arpu()
    mrr = revenue.mrr
    arpu = revenue.arpu
    paid_count = revenue.paid_count
    total_count = revenue.total_count

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
        # Simple: 30 days from creation
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


class PaymentMethodCreate(BaseModel):
    """Create payment method request.

    `token` is the single-use token minted by the client-side provider SDK.
    It is never stored: only a one-way fingerprint of it is kept.
    """

    token: str
    set_default: bool = True


class PaymentMethodOut(BaseModel):
    """Payment method record.

    Deliberately carries no card details. This system does not talk to a
    payment provider, so brand, last4 and expiry are unknown; asserting
    them would be fabrication.
    """

    id: str
    fingerprint: str
    verified: bool
    is_default: bool = False
    created_at: str


def _payment_token_fingerprint(token: str) -> str:
    """Return a non-reversible fingerprint of a payment token.

    Keyed with SECRET_KEY so the fingerprint cannot be brute-forced back to
    the token even if the metadata blob leaks. The token itself is never
    written anywhere — not to the database, not to a response, not to a log.
    """
    from django.conf import settings

    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:32]


@router.post(
    "/tenant/{tenant_id}/payment-methods",
    response=PaymentMethodOut,
    auth=AuthBearer(),
)
@transaction.atomic
def add_payment_method(request, tenant_id: str, payload: PaymentMethodCreate):
    """Record a payment method reference for a tenant.

    Stores only a one-way fingerprint of the provider token in tenant
    metadata. The raw token is discarded immediately: keeping it would put
    live payment credential material into a JSON metadata column.
    """
    from ninja.errors import HttpError

    try:
        tenant = Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist:
        raise HttpError(404, f"Tenant {tenant_id} not found")

    fingerprint = _payment_token_fingerprint(payload.token)
    metadata = tenant.metadata or {}
    payment_methods = metadata.get("payment_methods", [])

    pm_ref = {
        "id": f"pm_ref_{fingerprint[:16]}",
        "fingerprint": fingerprint,
        # No payment provider is integrated, so this reference has not been
        # verified against one. Say so rather than inventing card details.
        "verified": False,
        "is_default": payload.set_default,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    # If setting as default, unset others
    if payload.set_default:
        for pm in payment_methods:
            pm["is_default"] = False

    payment_methods.append(pm_ref)
    metadata["payment_methods"] = payment_methods
    tenant.metadata = metadata
    tenant.save(update_fields=["metadata", "updated_at"])

    return PaymentMethodOut(**pm_ref)
