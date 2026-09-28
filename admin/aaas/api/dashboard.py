"""
Dashboard API Router
AAAS Super Admin dashboard endpoints.

Per SRS Section 5.1 - Platform Overview metrics.
"""

from ninja import Router

from admin.aaas.api.schemas import (
    DashboardMetrics,
    DashboardResponse,
    RecentEvent,
    TopTenant,
)
from admin.aaas.models import Agent, Tenant

router = Router()


# Mapping of AuditLog action prefixes to dashboard event types and messages.
_AUDIT_EVENT_TYPES = {
    "tenant.": ("tenant_event", "Tenant activity"),
    "agent.": ("agent_event", "Agent activity"),
    "user.": ("user_event", "User activity"),
    "impersonation.": ("security_event", "Security activity"),
    "tier.": ("billing_event", "Billing activity"),
}


@router.get("", response=DashboardResponse)
def get_dashboard(request):
    """
    Get complete AAAS Super Admin dashboard data.
    Aggregates data from PostgreSQL and internal services.

    Sync on purpose: every step is ORM work and nothing is awaited, so a
    plain ``def`` runs on django-ninja's threadpool. Declaring this
    ``async def`` put the sync ORM under a live event loop and Django's
    ``async_unsafe`` guard turned every request into a 500.
    """
    # Real database queries
    total_tenants = Tenant.objects.count()
    active_tenants = Tenant.objects.filter(status="active").count()
    trial_tenants = Tenant.objects.filter(tier__slug="free").count()
    total_agents = Agent.objects.count()
    active_agents = Agent.objects.filter(status="active").count()

    # MRR is owned by admin.aaas.services.billing so the metric cannot
    # fork across handlers again (it did — this file used a field name
    # SubscriptionTier never had).
    from admin.aaas.services.billing import compute_mrr_and_arpu

    revenue = compute_mrr_and_arpu()
    mrr = revenue.mrr

    metrics = DashboardMetrics(
        total_tenants=total_tenants,
        active_tenants=active_tenants,
        trial_tenants=trial_tenants,
        total_agents=total_agents,
        active_agents=active_agents,
        total_users=0,
        mrr=mrr,
        mrr_growth=0.0,
        uptime=99.95,
        active_alerts=0,
        tokens_this_month=0,
        storage_used_gb=0.0,
    )

    # Top tenants by MRR
    top_tenants_qs = (
        Tenant.objects.filter(status="active")
        .select_related("tier")
        .order_by("-tier__base_price_cents")[:5]
    )

    top_tenants = [
        TopTenant(
            id=str(t.id),
            name=t.name,
            tier=t.tier.name if t.tier else "Free",
            agents=t.agents.count(),
            users=t.users.count(),
            mrr=(t.tier.base_price_cents / 100.0) if t.tier else 0.0,
            status=t.status,
        )
        for t in top_tenants_qs
    ]

    from admin.aaas.models import AuditLog

    recent_events = []
    for audit in AuditLog.objects.order_by("-created_at")[:10]:
        event_type = "platform_event"
        message = audit.action
        for prefix, (evt_type, evt_msg) in _AUDIT_EVENT_TYPES.items():
            if audit.action and audit.action.startswith(prefix):
                event_type = evt_type
                message = f"{evt_msg}: {audit.action}"
                break
        recent_events.append(
            RecentEvent(
                id=str(audit.id),
                type=event_type,
                message=message,
                timestamp=audit.created_at.isoformat() if audit.created_at else "",
            )
        )

    return DashboardResponse(
        metrics=metrics,
        top_tenants=top_tenants,
        recent_events=recent_events,
    )
