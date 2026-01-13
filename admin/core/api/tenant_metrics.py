"""
Tenant Usage Metrics API
Report usage and cost breakdown for tenant agents.


- Django Ninja router
- Real Prometheus metrics (with fallback)
- Per SRS-METRICS-DASHBOARDS.md Section 3.2

7-Persona Implementation:
- 📈 PM: Usage summary per quota
- 🏦 CFO: Cost estimation
- 🏗️ Architect: Prometheus integration
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

from django.conf import settings
from django.utils import timezone
from ninja import Router
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = Router(tags=["tenant-metrics"])


# =============================================================================
# SCHEMAS
# =============================================================================


class UsageMetric(BaseModel):
    """Usage metric with quota."""

    label: str
    current: int
    limit: int
    unit: str
    percentage: int


class AgentUsage(BaseModel):
    """Per-agent usage breakdown."""

    id: str
    name: str
    requests: int
    tokens: int
    images: int
    voice_minutes: int


class CostBreakdown(BaseModel):
    """Cost breakdown by category."""

    category: str
    amount: float
    details: str


class TenantUsageResponse(BaseModel):
    """Full tenant usage response."""

    usage: list[UsageMetric]
    agents: list[AgentUsage]
    costs: list[CostBreakdown]
    total_cost: float
    period_start: str
    period_end: str


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get("/tenant-usage", response=TenantUsageResponse)
async def get_tenant_usage(
    request,
    month: Optional[str] = None,  # YYYY-MM format
) -> TenantUsageResponse:
    """Get tenant usage metrics and cost breakdown.

    Permission: billing:view_usage
    """
    # Parse period
    if month:
        try:
            period_start = datetime.strptime(month, "%Y-%m")
        except ValueError:
            period_start = timezone.now().replace(day=1)
    else:
        period_start = timezone.now().replace(day=1)

    period_end = (period_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    # Try to get real metrics from Prometheus
    usage = await _get_usage_from_prometheus(request)
    agents = await _get_agent_usage(request)
    costs = _calculate_costs(usage, agents)

    total_cost = sum(c.amount for c in costs)

    return TenantUsageResponse(
        usage=usage,
        agents=agents,
        costs=costs,
        total_cost=total_cost,
        period_start=period_start.isoformat(),
        period_end=period_end.isoformat(),
    )


async def _get_usage_from_prometheus(request) -> list[UsageMetric]:
    """Fetch usage metrics from Prometheus."""
    import httpx

    prometheus_url = getattr(settings, "PROMETHEUS_URL", "http://localhost:9090")
    # SAAS external: http://localhost:63905
    # K8S: http://prometheus:9090

    tenant_id = getattr(request, "tenant_id", None) or "default"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Query API calls
            api_query = f'sum(gateway_requests_total{{tenant="{tenant_id}"}})'
            api_res = await client.get(
                f"{prometheus_url}/api/v1/query", params={"query": api_query}
            )
            api_calls = (
                _extract_prometheus_value(api_res.json()) if api_res.status_code == 200 else 0
            )

            # Query LLM tokens
            token_query = f'sum(conversation_worker_llm_input_tokens_total{{tenant="{tenant_id}"}}) + sum(conversation_worker_llm_output_tokens_total{{tenant="{tenant_id}"}})'
            token_res = await client.get(
                f"{prometheus_url}/api/v1/query", params={"query": token_query}
            )
            tokens = (
                _extract_prometheus_value(token_res.json()) if token_res.status_code == 200 else 0
            )

            # Query image generations
            img_query = f'sum(multimodal_image_generations_total{{tenant="{tenant_id}"}})'
            img_res = await client.get(
                f"{prometheus_url}/api/v1/query", params={"query": img_query}
            )
            images = _extract_prometheus_value(img_res.json()) if img_res.status_code == 200 else 0

            # Query voice minutes
            voice_query = f'sum(voice_session_duration_seconds{{tenant="{tenant_id}"}}) / 60'
            voice_res = await client.get(
                f"{prometheus_url}/api/v1/query", params={"query": voice_query}
            )
            voice_minutes = (
                _extract_prometheus_value(voice_res.json()) if voice_res.status_code == 200 else 0
            )

            # Get quotas from tenant settings
            quotas = _get_tenant_quotas(tenant_id)

            return [
                UsageMetric(
                    label="API Calls",
                    current=int(api_calls),
                    limit=quotas["api_calls"],
                    unit="",
                    percentage=_calc_percentage(api_calls, quotas["api_calls"]),
                ),
                UsageMetric(
                    label="LLM Tokens",
                    current=int(tokens),
                    limit=quotas["tokens"],
                    unit="",
                    percentage=_calc_percentage(tokens, quotas["tokens"]),
                ),
                UsageMetric(
                    label="Images",
                    current=int(images),
                    limit=quotas["images"],
                    unit="",
                    percentage=_calc_percentage(images, quot

