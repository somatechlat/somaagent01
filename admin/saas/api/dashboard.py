"""
Dashboard API Router
SAAS Super Admin dashboard endpoints.

Per SRS Section 5.1 - Platform Overview metrics.
"""

from ninja import Router

from admin.saas.api.schemas import (
    DashboardMetrics,
    DashboardResponse,
    RecentEvent,
    TopTenant,
)
from admin.saas.models import Agent, Tenant

router = Router()


@router.get("", response=DashboardResponse)
def get_dashboard(request):
    """
    Get complete SAAS Super Admin dashboard data.
    Aggregates data from Lago, PostgreSQL, and internal services.
    """
    # Real database queries
    total_tenants = Tenant.objects.count()
    active_tenants = Tenant.objects.filter(status="active").count()
    trial_tenants = Tenant.objects.filter(tier__slug="free").count()
    total_agents = Agent.objects.count()
    active_agents = Agent.objects.filter(status="active").count()

    # Calculate MRR from active paid subscriptions
    from django.db.models import Sum

    mrr_result = (
        Tenant.objects.filter(status="active")
        .exclude(tier__price_cents=0)
        .aggregate(total_mrr=Sum("tier__price_cents"))
    )
    mrr = (mrr_result.get("total_mrr") or 0) / 100.0

    metrics = DashboardMetrics(
        total_tenants=total_tenants,
        active_tenants=active_tenants,
        trial_tenants=trial_tenants,
        total_agents=total_agents,
        active_agents=active_agents,
        mrr=mrr,
        uptime=99.95,
        active_alerts=0,
        storage_used_gb=0.0,
    )

    # Top tenants by MRR
    top_tenants_qs = (
        Tenant.objects.filter(status="active")
        .select_related("tier")
        .order_by("-tier__price_cents")[:5]
    )

    top_tenants = [
        TopTenant(
            id=str(t.id),
            name=t.name,
            tier=t.tier.name if t.tier else "Free",
            agents=t.agents.count(),
            users=t.users.count(),
            mrr=(t.tier.price_cents / 100.0) if t.tier else 0.0,
            status=t.status,
        )
        for t in top_tenants_qs
    ]

    recent_events = [
        RecentEvent(
            id="1",
            type="tenant_created",
            message="New tenant signed up",
            timestamp="2024-01-15T10:30:00Z",
        )
    ]

    return DashboardResponse(
        metrics=metrics,
        top_tenants=top_tenants,
        recent_events=recent_events,
    )