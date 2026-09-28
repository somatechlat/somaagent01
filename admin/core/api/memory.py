"""Memory admin API endpoints.

Migrated from: services/gateway/routers/admin_memory.py
"""

from __future__ import annotations

from typing import Any

from django.http import HttpRequest
from ninja import Router
from pydantic import BaseModel

from admin.common.auth import RoleRequired

router = Router(tags=["admin-memory"])


# =============================================================================
# SCHEMAS
# =============================================================================


class MemoryMetricsResponse(BaseModel):
    """Memory metrics response."""

    kafka: dict[str, Any]


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get(
    "/memory/metrics",
    response=MemoryMetricsResponse,
    summary="Get memory and Kafka metrics",
    auth=RoleRequired("admin", "aaas_admin"),
)
async def admin_memory_metrics(
    request: HttpRequest,
) -> MemoryMetricsResponse:
    """Get Kafka health metrics for memory subsystem."""
    from services.common.event_bus import KafkaEventBus, KafkaSettings

    client = KafkaEventBus(KafkaSettings.from_env())
    result = await client.healthcheck()
    await client.close()

    return MemoryMetricsResponse(kafka=result or {})
