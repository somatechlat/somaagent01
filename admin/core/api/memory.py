"""Memory admin API endpoints.

Migrated from: services/gateway/routers/admin_memory.py
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Optional

from django.http import HttpRequest
from ninja import Query, Router
from pydantic import BaseModel

from admin.common.auth import RoleRequired
from admin.common.exceptions import NotFoundError

router = Router(tags=["admin-memory"])
logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS
# =============================================================================


class AdminMemoryItem(BaseModel):
    """Memory item for admin viewing."""

    id: int
    event_id: str
    session_id: Optional[str] = None
    persona_id: Optional[str] = None
    tenant: Optional[str] = None
    role: Optional[str] = None
    coord: Any = None
    request_id: Optional[str] = None
    trace_id: Optional[str] = None
    payload: dict[str, Any]
    wal_timestamp: Optional[float] = None
    created_at: datetime


class AdminMemoryListResponse(BaseModel):
    """Paginated memory list response."""

    items: list[AdminMemoryItem]
    next_cursor: Optional[int] = None


class MemoryMetricsResponse(BaseModel):
    """Memory metrics response."""

    kafka: dict[str, Any]


# =============================================================================
# HELPERS
# =============================================================================


def _parse_payload(payload: Any) -> dict:
    """Parse payload to dict."""
    if isinstance(payload, str):
        try:
            return json.loads(payload)
        except Exception:
            return {}
    elif isinstance(payload, dict):
        return payload
    return {}


def _row_to_item(row: Any) -> AdminMemoryItem:
    """Convert database row to AdminMemoryItem."""
    return AdminMemoryItem(
        id=row.id,
        event_id=row.event_id,
        session_id=row.session_id,
        persona_id=row.persona_id,
        tenant=row.tenant,
        role=row.role,
        coord=row.coord,
        request_id=row.request_id,
        trace_id=row.trace_id,
        payload=_parse_payload(row.payload),
        wal_timestamp=row.wal_timestamp,
        created_at=row.created_at,
    )


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get(
    "/memory",
    response=AdminMemoryListResponse,
    summary="List memory replica rows",
    auth=RoleRequired("admin", "saas_admin"),
)
async def list_admin_memory(
    request: HttpRequest,
    tenant: Optional[str] = Query(None, description="Filter by tenant"),
    persona_id: Optional[str] = Query(None, description="Filter by persona id"),
    role: Optional[str] = Query(None, description="Filter by role (user|assistant|tool)"),
    session_id: Optional[str] = Query(None, description="Filter by session id"),
    universe: Optional[str] = Query(None, description="Filter by universe_id"),
    namespace: Optional[str] = Query(None, description="Filter by memory namespace"),
    q: Optional[str] = Query(None, description="Case-insensitive search in payload"),
    min_ts: Optional[float] = Query(None, description="Minimum wal_timestamp"),
    max_ts: Optional[float] = Query(None, description="Maximum wal_timestamp"),
    after: Optional[int] = Query(None, ge=0, description="Cursor for pagination"),
    limit: int = Query(50, ge=1, le=200, description="Items per page"),
) -> AdminMemoryListResponse:
    """List memory replica rows with filtering and pagination."""
    from src.core.infrastructure.repositories import MemoryReplicaStore

    store = MemoryReplicaStore()
    rows = await store.list_memories(
        limit=limit,
        after_id=after,
        tenant=tenant,
        persona_id=persona_id,
        role=role,
        session_id=session_id,
        universe=universe,
        namespace=namespace,
        min_ts=min_ts,
        max_ts=max_ts,
        q=q,
    )

    items = [_row_to_item(r) for r in rows]
    next_cursor = items[-1].id if items else None

    return AdminMemoryListResponse(items=items, next_cursor=next_cursor)


@router.get(
    "/memory/{event_id}",
    response=AdminMemoryItem,
    summary="Get memory by event_id",
    auth=RoleRequired("admin", "saas_admin"),
)
async def get_admin_memory_item(
    request: HttpRequest,
    event_id: str,
) -> AdminMemoryItem:
    """Get a specific memory item by event_id."""
    from src.core.infrastructure.repositories import MemoryReplicaStore

    store = MemoryReplicaStore()
    row = await store.get_by_event_id(event_id)

    if not row:
        raise NotFoundError("memory event", event_id)

    return _row_to_item(row)


@router.get(
    "/memory/metrics",
    response=MemoryMetricsResponse,
    summary="Get memory and Kafka metrics",
    auth=RoleRequired("admin", "saas_admin"),
)
async def admin_memory_metrics(
    request: HttpRequest,
    tenant: str = Query(..., description="Tenant identifier"),
    namespace: str = Query(..., description="Memory namespace"),
) -> MemoryMetricsResponse:
    """Get Kafka health metrics for memory subsystem."""
    from services.common.event_bus import KafkaEventBus, KafkaSettings

    client = KafkaEventBus(KafkaSettings.from_env())
    result = await client.healthcheck()
    await client.close()

    return MemoryMetricsResponse(kafka=result)
