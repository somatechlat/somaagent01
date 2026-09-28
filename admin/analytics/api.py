"""Analytics API - Dashboard metrics and reports.


Platform analytics for Eye of God dashboard.

- PM: Business metrics, KPIs
- PhD Dev: Statistical analysis
- DevOps: Infrastructure metrics
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Optional
from uuid import uuid4

from asgiref.sync import sync_to_async
from django.db.models import Count, Q
from django.utils import timezone
from ninja import Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer
from admin.common.exceptions import ServiceUnavailableError

router = Router(tags=["analytics"])
logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS
# =============================================================================


class TimeSeriesPoint(BaseModel):
    """Time series data point."""

    timestamp: str
    value: float


class MetricSummary(BaseModel):
    """Metric summary."""

    name: str
    current_value: float
    previous_value: float
    change_percent: float
    trend: str  # up, down, stable


class DashboardMetrics(BaseModel):
    """Platform dashboard metrics."""

    total_tenants: int
    active_tenants: int
    total_agents: int
    active_agents: int
    total_users: int
    active_users: int
    total_conversations: int
    total_messages: int
    api_requests_today: int
    avg_response_time_ms: float
    error_rate_percent: float


class UsageReport(BaseModel):
    """Usage report."""

    report_id: str
    period_start: str
    period_end: str
    total_api_calls: int
    total_tokens_used: int
    total_conversations: int
    total_agents_active: int
    cost_estimate: float


class TenantAnalytics(BaseModel):
    """Tenant-specific analytics."""

    tenant_id: str
    active_agents: int
    active_users: int
    conversations_24h: int
    messages_24h: int
    api_calls_24h: int
    avg_response_time_ms: float


# =============================================================================
# ENDPOINTS - Dashboard
# =============================================================================


@router.get(
    "/dashboard",
    response=DashboardMetrics,
    summary="Get dashboard metrics",
    auth=AuthBearer(),
)
async def get_dashboard_metrics(request) -> DashboardMetrics:
    """Get platform dashboard metrics.

    PM: High-level business KPIs for Eye of God.
    """
    from admin.aaas.models import Agent, Tenant, TenantUser
    from admin.chat.models import Conversation, Message

    @sync_to_async
    def _aggregate():
        return {
            "total_tenants": Tenant.objects.count(),
            "active_tenants": Tenant.objects.filter(status="active").count(),
            "total_agents": Agent.objects.count(),
            "active_agents": Agent.objects.filter(status="active").count(),
            "total_users": TenantUser.objects.count(),
            "active_users": TenantUser.objects.filter(is_active=True).count(),
            "total_conversations": Conversation.objects.count(),
            "total_messages": Message.objects.count(),
            "api_requests_today": 0,  # Requires metrics backend; not fabricated
            "avg_response_time_ms": 0.0,  # Requires metrics backend; not fabricated
            "error_rate_percent": 0.0,  # Requires metrics backend; not fabricated
        }

    data = await _aggregate()
    return DashboardMetrics(**data)


@router.get(
    "/dashboard/summary",
    summary="Get metric summaries",
    auth=AuthBearer(),
)
async def get_metric_summaries(request) -> dict:
    """Get metric summaries with trends.

    PM: Changes compared to previous period.
    """
    from admin.aaas.models import Agent, Tenant

    @sync_to_async
    def _summaries():
        now = timezone.now()
        prev = now - timedelta(days=7)
        current_tenants = Tenant.objects.filter(status="active", created_at__lte=now).count()
        previous_tenants = Tenant.objects.filter(status="active", created_at__lte=prev).count()
        current_agents = Agent.objects.filter(status="active", created_at__lte=now).count()
        previous_agents = Agent.objects.filter(status="active", created_at__lte=prev).count()

        def trend(current, previous):
            if previous == 0:
                return "up" if current > 0 else "stable"
            pct = ((current - previous) / previous) * 100
            if pct > 1:
                return "up"
            if pct < -1:
                return "down"
            return "stable"

        return [
            MetricSummary(
                name="active_tenants",
                current_value=float(current_tenants),
                previous_value=float(previous_tenants),
                change_percent=round(
                    ((current_tenants - previous_tenants) / max(previous_tenants, 1)) * 100, 2
                ),
                trend=trend(current_tenants, previous_tenants),
            ).dict(),
            MetricSummary(
                name="active_agents",
                current_value=float(current_agents),
                previous_value=float(previous_agents),
                change_percent=round(
                    ((current_agents - previous_agents) / max(previous_agents, 1)) * 100, 2
                ),
                trend=trend(current_agents, previous_agents),
            ).dict(),
        ]

    return {"summaries": await _summaries()}


# =============================================================================
# ENDPOINTS - Time Series
# =============================================================================


@router.get(
    "/timeseries/{metric}",
    summary="Get time series data",
    auth=AuthBearer(),
)
async def get_timeseries(
    request,
    metric: str,
    period: str = "24h",  # 1h, 24h, 7d, 30d
    granularity: str = "hour",  # minute, hour, day
) -> dict:
    """Get time series data for a metric.

    PhD Dev: Statistical time series for analysis.
    """
    # VIBE: Do not fabricate time-series samples. Real metrics backend required.
    logger.error(
        "Time-series metrics backend not implemented for metric=%s period=%s",
        metric,
        period,
    )
    raise ServiceUnavailableError(
        "metrics_backend",
        "Time-series metrics backend is not implemented. Configure a metrics store.",
    )


# =============================================================================
# ENDPOINTS - Usage Reports
# =============================================================================


@router.get(
    "/usage/current",
    response=UsageReport,
    summary="Get current period usage",
    auth=AuthBearer(),
)
async def get_current_usage(request) -> UsageReport:
    """Get usage for current billing period.

    PM: Billing-relevant usage data.
    """
    from admin.aaas.models import Agent
    from admin.aaas.models.usage import UsageRecord
    from admin.chat.models import Conversation, Message
    from django.db.models import Sum

    now = timezone.now()
    period_start = now.replace(day=1, hour=0, minute=0, second=0)

    @sync_to_async
    def _aggregate():
        tokens = (
            UsageRecord.objects.filter(period_start__gte=period_start)
            .aggregate(total=Sum("quantity"))
            .get("total")
            or 0
        )
        msg_tokens = (
            Message.objects.filter(created_at__gte=period_start)
            .aggregate(total=Sum("token_count"))
            .get("total")
            or 0
        )
        return {
            "report_id": str(uuid4()),
            "period_start": period_start.isoformat(),
            "period_end": now.isoformat(),
            "total_api_calls": 0,  # Requires API gateway metrics backend
            "total_tokens_used": int(tokens) + int(msg_tokens),
            "total_conversations": Conversation.objects.filter(
                created_at__gte=period_start
            ).count(),
            "total_agents_active": Agent.objects.filter(status="active").count(),
            "cost_estimate": 0.0,  # Requires billing integration
        }

    data = await _aggregate()
    return UsageReport(**data)


@router.get(
    "/usage/history",
    summary="Get usage history",
    auth=AuthBearer(),
)
async def get_usage_history(
    request,
    months: int = 12,
) -> dict:
    """Get historical usage reports.

    PM: Trend analysis for capacity planning.
    """
    from admin.aaas.models.usage import UsageRecord
    from django.db.models import Sum

    @sync_to_async
    def _history():
        # Aggregate usage records by billing period
        periods = (
            UsageRecord.objects.values("billing_period")
            .annotate(total_tokens=Sum("quantity"))
            .order_by("-billing_period")[:months]
        )
        return [
            {
                "period": p["billing_period"],
                "total_tokens_used": p["total_tokens"] or 0,
                "total_api_calls": 0,  # Requires metrics backend
                "cost_estimate": 0.0,  # Requires billing integration
            }
            for p in periods
        ]

    reports = await _history()
    return {"reports": reports, "total": len(reports)}


@router.get(
    "/usage/export",
    summary="Export usage report",
    auth=AuthBearer(),
)
async def export_usage(
    request,
    period_start: str,
    period_end: str,
    format: str = "csv",  # csv, json
) -> dict:
    """Export usage report for a period.

    PM: Downloadable reports for accounting.
    """
    logger.error(
        "Usage report export not implemented for period %s - %s",
        period_start,
        period_end,
    )
    raise ServiceUnavailableError(
        "analytics_export",
        "Usage report export is not implemented. Configure an export backend.",
    )


# =============================================================================
# ENDPOINTS - Tenant Analytics
# =============================================================================


@router.get(
    "/tenants/{tenant_id}",
    response=TenantAnalytics,
    summary="Get tenant analytics",
    auth=AuthBearer(),
)
async def get_tenant_analytics(
    request,
    tenant_id: str,
) -> TenantAnalytics:
    """Get analytics for a specific tenant.

    PM: Tenant-level performance metrics.
    """
    from admin.aaas.models import Agent, TenantUser
    from admin.chat.models import Conversation, Message

    @sync_to_async
    def _aggregate():
        since = timezone.now() - timedelta(hours=24)
        return {
            "tenant_id": tenant_id,
            "active_agents": Agent.objects.filter(tenant_id=tenant_id, status="active").count(),
            "active_users": TenantUser.objects.filter(
                tenant_id=tenant_id, is_active=True
            ).count(),
            "conversations_24h": Conversation.objects.filter(
                tenant_id=tenant_id, created_at__gte=since
            ).count(),
            "messages_24h": Message.objects.filter(
                conversation_id__in=Conversation.objects.filter(tenant_id=tenant_id)
                .values("id"),
                created_at__gte=since,
            ).count(),
            "api_calls_24h": 0,  # Requires metrics backend
            "avg_response_time_ms": 0.0,  # Requires metrics backend
        }

    data = await _aggregate()
    return TenantAnalytics(**data)


@router.get(
    "/tenants",
    summary="Get all tenants analytics",
    auth=AuthBearer(),
)
async def get_all_tenants_analytics(
    request,
    sort_by: str = "api_calls",
    limit: int = 100,
) -> dict:
    """Get analytics for all tenants.

    PM: Platform-wide tenant comparison.
    """
    from admin.aaas.models import Agent, Tenant, TenantUser
    from admin.chat.models import Conversation, Message

    @sync_to_async
    def _tenants():
        since = timezone.now() - timedelta(hours=24)
        tenants = Tenant.objects.filter(status="active").order_by("name")[:limit]
        result = []
        for tenant in tenants:
            result.append(
                {
                    "tenant_id": str(tenant.id),
                    "active_agents": Agent.objects.filter(
                        tenant_id=tenant.id, status="active"
                    ).count(),
                    "active_users": TenantUser.objects.filter(
                        tenant_id=tenant.id, is_active=True
                    ).count(),
                    "conversations_24h": Conversation.objects.filter(
                        tenant_id=tenant.id, created_at__gte=since
                    ).count(),
                    "messages_24h": Message.objects.filter(
                        conversation_id__in=Conversation.objects.filter(
                            tenant_id=tenant.id
                        ).values("id"),
                        created_at__gte=since,
                    ).count(),
                    "api_calls_24h": 0,  # Requires metrics backend
                }
            )
        return result

    tenants = await _tenants()
    return {"tenants": tenants, "total": len(tenants)}


# =============================================================================
# ENDPOINTS - Agent Analytics
# =============================================================================


@router.get(
    "/agents/{agent_id}",
    summary="Get agent analytics",
    auth=AuthBearer(),
)
async def get_agent_analytics(
    request,
    agent_id: str,
) -> dict:
    """Get analytics for a specific agent.

    PhD Dev: Agent performance metrics.
    """
    from admin.chat.models import Conversation, Message

    @sync_to_async
    def _aggregate():
        since = timezone.now() - timedelta(hours=24)
        conversations = Conversation.objects.filter(
            agent_id=agent_id, created_at__gte=since
        ).count()
        messages = Message.objects.filter(
            conversation_id__in=Conversation.objects.filter(agent_id=agent_id).values("id"),
            created_at__gte=since,
        ).count()
        return {
            "agent_id": agent_id,
            "conversations_24h": conversations,
            "messages_24h": messages,
            "avg_response_time_ms": 0.0,  # Requires metrics backend
            "user_satisfaction_score": None,  # Requires feedback aggregation
            "error_rate_percent": 0.0,  # Requires metrics backend
        }

    return await _aggregate()


@router.get(
    "/agents",
    summary="Get all agents analytics",
    auth=AuthBearer(),
)
async def get_all_agents_analytics(
    request,
    tenant_id: Optional[str] = None,
    limit: int = 100,
) -> dict:
    """Get analytics for all agents."""
    from admin.aaas.models import Agent
    from admin.chat.models import Conversation, Message

    @sync_to_async
    def _agents():
        since = timezone.now() - timedelta(hours=24)
        qs = Agent.objects.all()
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        qs = qs.order_by("name")[:limit]
        result = []
        for agent in qs:
            result.append(
                {
                    "agent_id": str(agent.id),
                    "conversations_24h": Conversation.objects.filter(
                        agent_id=agent.id, created_at__gte=since
                    ).count(),
                    "messages_24h": Message.objects.filter(
                        conversation_id__in=Conversation.objects.filter(
                            agent_id=agent.id
                        ).values("id"),
                        created_at__gte=since,
                    ).count(),
                    "avg_response_time_ms": 0.0,  # Requires metrics backend
                    "user_satisfaction_score": None,  # Requires feedback aggregation
                    "error_rate_percent": 0.0,  # Requires metrics backend
                }
            )
        return result

    agents = await _agents()
    return {"agents": agents, "total": len(agents)}


# =============================================================================
# ENDPOINTS - Infrastructure
# =============================================================================


@router.get(
    "/infrastructure",
    summary="Get infrastructure metrics",
    auth=AuthBearer(),
)
async def get_infrastructure_metrics(request) -> dict:
    """Get infrastructure metrics.

    DevOps: System health and performance.
    """
    import time

    import httpx
    from django.conf import settings
    from django.core.cache import cache
    from django.db import connection

    services: dict[str, dict] = {}

    # PostgreSQL
    start = time.time()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        services["postgres"] = {
            "status": "healthy",
            "latency_ms": round((time.time() - start) * 1000, 2),
        }
    except Exception as exc:
        services["postgres"] = {"status": "down", "latency_ms": None, "error": str(exc)}

    # Redis
    start = time.time()
    try:
        cache.set("analytics_health_check", "ok", timeout=5)
        result = cache.get("analytics_health_check")
        services["redis"] = {
            "status": "healthy" if result == "ok" else "degraded",
            "latency_ms": round((time.time() - start) * 1000, 2),
        }
    except Exception as exc:
        services["redis"] = {"status": "down", "latency_ms": None, "error": str(exc)}

    # SomaBrain
    somabrain_url = getattr(settings, "SOMABRAIN_URL", None)
    if somabrain_url:
        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{somabrain_url}/health")
            services["somabrain"] = {
                "status": "healthy" if response.status_code == 200 else "degraded",
                "latency_ms": round((time.time() - start) * 1000, 2),
            }
        except Exception as exc:
            services["somabrain"] = {"status": "down", "latency_ms": None, "error": str(exc)}
    else:
        services["somabrain"] = {"status": "unknown", "latency_ms": None, "error": "SOMABRAIN_URL not configured"}

    # Django itself is running because we are responding
    services["django"] = {"status": "healthy", "latency_ms": 0.0}

    return {
        "services": services,
        "system": {
            "cpu_percent": None,  # Requires host metrics collector
            "memory_percent": None,
            "disk_percent": None,
        },
    }
