"""Session events and context endpoints (extracted, minimal functional)."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from services.common.session_repository import (
    ensure_schema as ensure_session_schema,
    PostgresSessionStore,
)
from src.core.config import cfg

router = APIRouter(prefix="/v1/sessions", tags=["sessions"])


async def _store() -> PostgresSessionStore:
    return PostgresSessionStore(cfg.settings().database.dsn)


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
        # 1. Determine start point (latest event ID) to avoid re-sending history
        # We fetch the latest event to know where to start.
        pool = await store._ensure_pool()  # noqa: SLF001
        async with pool.acquire() as conn:
            # Get the maximum ID currently in the table for this session
            max_id = await conn.fetchval(
                "SELECT MAX(id) FROM session_events WHERE session_id = $1",
                session_id
            )
        
        last_id = max_id or 0
        
        # Yield a comment to signal connection open
        yield ": connected\n\n"

        while True:
            if await request.is_disconnected():
                break
            
            # 2. Poll for NEW events after last_id
            # list_events_after returns events in ASC order (oldest -> newest)
            events = await store.list_events_after(session_id=session_id, after_id=last_id, limit=limit)
            
            if events:
                # Emit new events
                payload = {"session_id": session_id, "events": events}
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                # Update last_id to the max ID we just sent
                last_id = events[-1]["id"]
            else:
                # No new events, send keepalive to prevent timeout
                yield f"data: {json.dumps({'type': 'system.keepalive', 'session_id': session_id})}\n\n"
            
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
