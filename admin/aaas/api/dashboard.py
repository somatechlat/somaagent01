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
from admin.aaas.models import Agent, Tenant, TenantUser

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

    total_users = TenantUser.objects.count()

    # Tokens and storage are summed from the tables that actually hold them.
    # A month boundary is applied to recorded_at; if nothing is metered the
    # true sum is zero, which is what is reported.
    from datetime import datetime, timezone as _tz

    from django.db.models import Sum

    from admin.aaas.models import UsageRecord
    from admin.core.models import Asset

    month_start = datetime.now(_tz.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    tokens_this_month = int(
        UsageRecord.objects.filter(
            metric_code="tokens", recorded_at__gte=month_start
        ).aggregate(n=Sum("quantity"))["n"]
        or 0
    )
    storage_used_gb = (
        Asset.objects.filter(status="active").aggregate(n=Sum("content_size_bytes"))["n"] or 0
    ) / (1024**3)

    from admin.observability.api import get_uptime_seconds

    metrics = DashboardMetrics(
        total_tenants=total_tenants,
        active_tenants=active_tenants,
        trial_tenants=trial_tenants,
        total_agents=total_agents,
        active_agents=active_agents,
        total_users=total_users,
        mrr=mrr,
        # No prior-period MRR is stored, so growth is unknown.
        mrr_growth=None,
        uptime_seconds=get_uptime_seconds(),
        # No alert store exists in this system.
        active_alerts=None,
        tokens_this_month=tokens_this_month,
        storage_used_gb=storage_used_gb,
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
