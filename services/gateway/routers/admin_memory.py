"""Admin memory endpoints extracted from the gateway monolith."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from services.common.authorization import _require_admin_scope, authorize_request
from services.common.event_bus import KafkaEventBus, KafkaSettings
from src.core.infrastructure.repositories import MemoryReplicaStore

router = APIRouter(prefix="/v1/admin", tags=["admin"])


def _enforce_admin_rate_limit(request: Request) -> None:
    """Placeholder – defer to orchestrator-level rate limiting or add token bucket here."""
    return None


class AdminMemoryItem(BaseModel):
    id: int
    event_id: str
    session_id: str | None
    persona_id: str | None
    tenant: str | None
    role: str | None
    coord: Any | None
    request_id: str | None
    trace_id: str | None
    payload: dict[str, Any]
    wal_timestamp: float | None
    created_at: datetime


class AdminMemoryListResponse(BaseModel):
    items: list[AdminMemoryItem]
    next_cursor: int | None


@router.get("/memory", response_model=AdminMemoryListResponse, summary="List memory replica rows")
async def list_admin_memory(
    request: Request,
    tenant: str | None = Query(None, description="Filter by tenant"),
    persona_id: str | None = Query(None, description="Filter by persona id"),
    role: str | None = Query(None, description="Filter by role (user|assistant|tool)"),
    session_id: str | None = Query(None, description="Filter by session id"),
    universe: str | None = Query(None, description="Filter by universe_id (logical scope)"),
    namespace: str | None = Query(None, description="Filter by memory namespace (e.g., wm, ltm)"),
    q: str | None = Query(None, description="Case-insensitive search in payload JSON text"),
    min_ts: float | None = Query(None, description="Minimum wal_timestamp (epoch seconds)"),
    max_ts: float | None = Query(None, description="Maximum wal_timestamp (epoch seconds)"),
    after: int | None = Query(
        None, ge=0, description="Return items with database id less than this cursor (paging)"
    ),
    limit: int = Query(50, ge=1, le=200),
    store: Annotated[MemoryReplicaStore, Depends(lambda: MemoryReplicaStore())] = None,  # type: ignore[assignment]
) -> AdminMemoryListResponse:
    await _enforce_admin_rate_limit(request)
    auth = await authorize_request(
        request,
        {
            "tenant": tenant,
            "persona_id": persona_id,
            "role": role,
            "session_id": session_id,
        },
    )
    _require_admin_scope(auth)

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
    items = []
    for r in rows:
        payload_obj = r.payload
        if isinstance(payload_obj, str):
            try:
                payload_obj = json.loads(payload_obj)
            except Exception:
                payload_obj = {}
        elif not isinstance(payload_obj, dict):
            payload_obj = {}
        items.append(
            AdminMemoryItem(
                id=r.id,
                event_id=r.event_id,
                session_id=r.session_id,
                persona_id=r.persona_id,
                tenant=r.tenant,
                role=r.role,
                coord=r.coord,
                request_id=r.request_id,
                trace_id=r.trace_id,
                payload=payload_obj,  # type: ignore[arg-type]
                wal_timestamp=r.wal_timestamp,
                created_at=r.created_at,
            )
        )
    next_cursor = items[-1].id if items else None
    return AdminMemoryListResponse(items=items, next_cursor=next_cursor)


@router.get("/memory/{event_id}", response_model=AdminMemoryItem, summary="Get memory by event_id")
async def get_admin_memory_item(
    event_id: str,
    request: Request,
    store: Annotated[MemoryReplicaStore, Depends(lambda: MemoryReplicaStore())] = None,  # type: ignore[assignment]
) -> AdminMemoryItem:
    await _enforce_admin_rate_limit(request)
    auth = await authorize_request(request, {"event_id": event_id})
    _require_admin_scope(auth)
    row = await store.get_by_event_id(event_id)
    if not row:
        raise HTTPException(status_code=404, detail="memory event not found")
    payload_obj = row.payload
    if isinstance(payload_obj, str):
        try:
            payload_obj = json.loads(payload_obj)
        except Exception:
            payload_obj = {}
    elif not isinstance(payload_obj, dict):
        payload_obj = {}
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
        payload=payload_obj,  # type: ignore[arg-type]
        wal_timestamp=row.wal_timestamp,
        created_at=row.created_at,
    )


@router.get("/memory/metrics")
async def admin_memory_metrics(
    request: Request,
    tenant: str = Query(..., description="Tenant identifier"),
    namespace: str = Query(..., description="Memory namespace (e.g., wm, ltm)"),
) -> JSONResponse:
    await _enforce_admin_rate_limit(request)
    auth = await authorize_request(request, {"tenant": tenant, "namespace": namespace})
    _require_admin_scope(auth)
    client = KafkaEventBus(KafkaSettings.from_env())
    result = await client.healthcheck()
    await client.close()
    return JSONResponse({"kafka": result})
