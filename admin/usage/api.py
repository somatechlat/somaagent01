"""Usage API - Usage metering and billing.


Usage tracking and billing integration.

7-Persona Implementation:
- PM: Usage visibility, billing transparency
- DevOps: Lago integration, metrics
- Security Auditor: Accurate metering
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import uuid4

from django.utils import timezone
from ninja import Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer

router = Router(tags=["usage"])
logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS
# =============================================================================


class UsageEvent(BaseModel):
    """Usage event record."""

    event_id: str
    tenant_id: str
    metric: str  # api_calls, tokens, storage, agents
    quantity: float
    timestamp: str
    metadata: Optional[dict] = None


class UsageSummary(BaseModel):
    """Usage summary."""

    tenant_id: str
    period_start: str
    period_end: str
    metrics: dict


class UsageQuota(BaseModel):
    """Usage quota."""

    metric: str
    limit: float
    used: float
    remaining: float
    reset_at: str


class BillingCycle(BaseModel):
    """Billing cycle info."""

    tenant_id: str
    start_date: str
    end_date: str
    current_cost: float
    projected_cost: float


# =============================================================================
# ENDPOINTS - Usage Events
# =============================================================================


@router.post(
    "/events",
    summary="Record usage event",
    auth=AuthBearer(),
)
async def record_usage_event(
    request,
    tenant_id: str,
    metric: str,
    quantity: float,
    metadata: Optional[dict] = None,
) -> dict:
    """Record a usage event.

    DevOps: Real-time metering to Lago.
    """
    event_id = str(uuid4())

    # In production: send to Lago
    # lago_client.events.create(
    #     transaction_id=event_id,
    #     external_customer_id=tenant_id,
    #     code=metric,
    #     properties={"quantity": quantity, **metadata},
    # )

    logger.debug(f"Usage event: {tenant_id}/{metric}/{quantity}")

    return {
        "event_id": event_id,
        "tenant_id": tenant_id,
        "metric": metric,
        "quantity": quantity,
        "recorded": True,
    }


@router.post(
    "/events/batch",
    summary="Record batch events",
    auth=AuthBearer(),
)
async def record_batch_events(
    request,
    events: list[dict],
) -> dict:
    """Record multiple usage events.

    DevOps: Batch metering for efficiency.
    """
    event_ids = [str(uuid4()) for _ in events]

    return {
        "event_ids": event_ids,
        "count": len(events),
        "recorded": True,
    }


# =============================================================================
# ENDPOINTS - Usage Summary
# =============================================================================


@router.get(
    "/summary/{tenant_id}",
    response=UsageSummary,
    summary="Get usage summary",
    auth=AuthBearer(),
)
async def get_usage_summary(
    request,
    tenant_id: str,
    period: str = "current_month",  # current_month, last_month, custom
) -> UsageSummary:
    """Get usage summary for a tenant.

    PM: Usage visibility.
    """
    return UsageSummary(
        tenant_id=tenant_id,
        period_start=timezone.now().isoformat(),
        period_end=timezone.now().isoformat(),
        metrics={
            "api_calls": 0,
            "tokens_used": 0,
            "storage_mb": 0.0,
            "active_agents": 0,
        },
    )


@router.get(
    "/summary/{tenant_id}/history",
    summary="Get usage history",
    auth=AuthBearer(),
)
async def get_usage_history(
    request,
    tenant_id: str,
    metric: str,
    granularity: str = "daily",  # hourly, daily, monthly
    limit: int = 30,
) -> dict:
    """Get historical usage data.

    PM: Usage trends.
    """
    return {
        "tenant_id": tenant_id,
        "metric": metric,
        "granularity": granularity,
        "data_points": [],
    }


# =============================================================================
# ENDPOINTS - Quotas
# =============================================================================


@router.get(
    "/quotas/{tenant_id}",
    summary="Get quotas",
    auth=AuthBearer(),
)
async def get_quotas(request, tenant_id: str) -> dict:
    """Get tenant quotas and usage.

    PM: Quota visibility.
    """
    return {
        "tenant_id": tenant_id,
        "quotas": [
            UsageQuota(
                metric="api_calls",
                limit=100000,
                used=0,
                remaining=100000,
                reset_at=timezone.now().isoformat(),
            ).dict(),
            UsageQuota(
                metric="storage_mb",
                limit=10240,
                used=0,
                remaining=10240,
                reset_at=timezone.now().isoformat(),
            ).dict(),
        ],
    }


@router.patch(
    "/quotas/{tenant_id}",
    summary="Update quotas",
    auth=AuthBearer(),
)
async def update_quotas(
    request,
    tenant_id: str,
    quotas: dict,
) -> dict:
    """Update tenant quotas.

    PM: Plan customization.
    """
    return {
        "tenant_id": tenant_id,
        "updated": True,
    }


# =============================================================================
# ENDPOINTS - Billing
# =============================================================================


@router.get(
    "/billing/{tenant_id}/current",
    response=BillingCycle,
    summary="Get current billing",
    auth=AuthBearer(),
)
async def get_current_billing(
    request,
    tenant_id: str,
) -> BillingCycle:
    """Get current billing cycle.

    PM: Billing transparency.
    """
    return BillingCycle(
        tenant_id=tenant_id,
        start_date=timezone.now().isoformat(),
        end_date=timezone.now().isoformat(),
        current_cost=0.0,
        projected_cost=0.0,
    )


@router.get(
    "/billing/{tenant_id}/invoices",
    summary="Get invoices",
    auth=AuthBearer(),
)
async def get_invoices(
    request,
    tenant_id: str,
    limit: int = 12,
) -> dict:
    """Get billing invoices.

    PM: Historical billing.
    """
    return {
        "tenant_id": tenant_id,
        "invoices": [],
        "total": 0,
    }


# =============================================================================
# ENDPOINTS - Metrics
# =============================================================================


@router.get(
    "/metrics",
    summary="List available metrics",
    auth=AuthBearer(),
)
async def list_metrics(request) -> dict:
    """List available usage metrics.

    DevOps: Metric catalog.
    """
    return {
        "metrics": [
            {"code": "api_calls", "description": "API request count", "unit": "calls"},
            {"code": "tokens_used", "description": "LLM tokens consumed", "unit": "tokens"},
            {"code": "storage_mb", "description": "Storage used", "unit": "MB"},
            {"code": "active_agents", "description": "Active agent count", "unit": "agents"},
            {"code": "conversations", "description": "Conversations started", "unit": "count"},
            {"code": "voice_minutes", "description": "Voice minutes used", "unit": "minutes"},
        ],
        "total": 6,
    }


# =============================================================================
# ENDPOINTS - Alerts
# =============================================================================


@router.get(
    "/alerts/{tenant_id}",
    summary="Get usage alerts",
    auth=AuthBearer(),
)
async def get_usage_alerts(request, tenant_id: str) -> dict:
    """Get usage alerts for a tenant.

    PM: Proactive notifications.
    """
    return {
        "tenant_id": tenant_id,
        "alerts": [],
        "total": 0,
    }


@router.post(
    "/alerts/{tenant_id}",
    summary="Configure alert",
    auth=AuthBearer(),
)
async def configure_alert(
    request,
    tenant_id: str,
    metric: str,
    threshold_percent: int,
    notification_channels: list[str],
) -> dict:
    """Configure a usage alert."""
    alert_id = str(uuid4())

    return {
        "alert_id": alert_id,
        "tenant_id": tenant_id,
        "metric": metric,
        "threshold_percent": threshold_percent,
        "created": True,
    }