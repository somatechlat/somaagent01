"""Session events and context endpoints (extracted, minimal functional)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

# Legacy admin settings removed – use central cfg singleton.
from src.core.config import cfg
from services.common.session_repository import (
    ensure_schema as ensure_session_schema,
    PostgresSessionStore,
)

router = APIRouter(prefix="/v1/sessions", tags=["sessions"])


async def _store() -> PostgresSessionStore:
    store = PostgresSessionStore(cfg.settings().database.dsn)
    await ensure_session_schema(store)
    return store


@router.get("/{session_id}/events")
async def session_events(session_id: str, limit: int = Query(200, ge=1, le=500)) -> dict[str, Any]:
    store = await _store()
    events = await store.list_events(session_id=session_id, limit=limit)
    if events is None:
        raise HTTPException(status_code=404, detail="session_not_found")
    return {"session_id": session_id, "events": events}


@router.get("/{session_id}/context-window")
async def session_context_window(
    session_id: str, window: int = Query(20, ge=1, le=200)
) -> dict[str, Any]:
    store = await _store()
    events = await store.list_events(session_id=session_id, limit=window)
    if events is None:
        raise HTTPException(status_code=404, detail="session_not_found")
    # Simple context window: last N events
    return {"session_id": session_id, "context": list(reversed(events))[:window]}
