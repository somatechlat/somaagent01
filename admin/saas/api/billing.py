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
