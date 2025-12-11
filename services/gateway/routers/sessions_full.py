"""Session endpoints extracted from the gateway monolith (minimal functional subset)."""

from __future__ import annotations

from typing import Any, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from services.common.session_repository import (
    ensure_schema as ensure_session_schema,
    PostgresSessionStore,
)

# Legacy admin settings removed – use cfg singleton.
from src.core.config import cfg

router = APIRouter(prefix="/v1/sessions", tags=["sessions"])


class SessionSummary(BaseModel):
    session_id: str
    persona_id: str | None = None
    tenant: str | None = None


async def _session_store() -> PostgresSessionStore:
    store = PostgresSessionStore(cfg.settings().database.dsn)
    await ensure_session_schema(store)
    return store


@router.get("", response_model=List[SessionSummary])
async def list_sessions(limit: int = Query(50, ge=1, le=200)) -> List[SessionSummary]:
    store = await _session_store()
    rows = await store.list_sessions(limit=limit)
    return [
        SessionSummary(
            session_id=str(r.session_id),
            persona_id=getattr(r, "persona_id", None),
            tenant=getattr(r, "tenant", None),
        )
        for r in rows
    ]


@router.get("/{session_id}/history")
async def session_history(session_id: str, limit: int = Query(100, ge=1, le=500)) -> Any:
    store = await _session_store()
    events = await store.list_events(session_id=session_id, limit=limit)
    if events is None:
        raise HTTPException(status_code=404, detail="session_not_found")
    return {"session_id": session_id, "events": events}
