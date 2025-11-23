"""Session events and context endpoints (extracted, minimal functional)."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

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
async def session_events(
    session_id: str,
    request: Request,
    limit: int = Query(200, ge=1, le=500),
    stream: bool = Query(False),
    poll_interval: float = Query(0.75, ge=0.2, le=5.0),
) -> Any:
    store = await _store()

    if not stream:
        events = await store.list_events(session_id=session_id, limit=limit)
        if events is None:
            raise HTTPException(status_code=404, detail="session_not_found")
        return {"session_id": session_id, "events": events}

    # SSE stream mode: poll Postgres for new events and emit them incrementally.
    async def event_generator():
        last_event_id = None
        while True:
            if await request.is_disconnected():
                break
            events = await store.list_events(session_id=session_id, limit=limit)
            if events is None:
                yield "data: {}\n\n"
                break
            # Filter new events using event_id ordering.
            new_events = []
            for ev in events:
                ev_id = ev.get("event_id") or ev.get("id")
                if last_event_id is None or ev_id != last_event_id:
                    new_events.append(ev)
            if new_events:
                last_event_id = new_events[-1].get("event_id") or last_event_id
                payload = {"session_id": session_id, "events": new_events}
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
            await asyncio.sleep(poll_interval)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/{session_id}/context-window")
async def session_context_window(session_id: str, window: int = Query(20, ge=1, le=200)) -> dict[str, Any]:
    store = await _store()
    events = await store.list_events(session_id=session_id, limit=window)
    if events is None:
        raise HTTPException(status_code=404, detail="session_not_found")
    # Simple context window: last N events
    return {"session_id": session_id, "context": list(reversed(events))[:window]}
