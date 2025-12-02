"""Sessions router with SSE streaming support.

Provides real-time session event streaming using Server-Sent Events.
Uses PostgresSessionStore for event persistence and polling.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncGenerator, Optional

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from services.common.session_repository import PostgresSessionStore, ensure_schema
from services.common.admin_settings import ADMIN_SETTINGS

router = APIRouter(prefix="/v1/session", tags=["sessions"])

# SSE polling interval in seconds
SSE_POLL_INTERVAL = 2.0
SSE_KEEPALIVE_INTERVAL = 10.0


async def _get_store() -> PostgresSessionStore:
    """Get initialized session store."""
    store = PostgresSessionStore(ADMIN_SETTINGS.postgres_dsn)
    await ensure_schema(store)
    return store


async def _sse_event_generator(
    session_id: str,
    store: PostgresSessionStore,
) -> AsyncGenerator[str, None]:
    """Generate SSE events for a session by polling PostgreSQL."""
    last_event_id: Optional[int] = None
    last_keepalive = asyncio.get_event_loop().time()

    # Send initial keepalive
    yield f"data: {json.dumps({'type': 'system.keepalive', 'session_id': session_id})}\n\n"

    while True:
        try:
            # Poll for new events
            events = await store.list_events_after(
                session_id,
                after_id=last_event_id,
                limit=50,
            )

            # Send new events
            for event in events:
                event_id = event.get("id")
                if event_id is not None:
                    last_event_id = event_id
                payload = event.get("payload", event)
                yield f"data: {json.dumps(payload)}\n\n"

            # Send keepalive if no events and interval passed
            now = asyncio.get_event_loop().time()
            if now - last_keepalive >= SSE_KEEPALIVE_INTERVAL:
                yield f"data: {json.dumps({'type': 'system.keepalive', 'session_id': session_id})}\n\n"
                last_keepalive = now

            # Wait before next poll
            await asyncio.sleep(SSE_POLL_INTERVAL)

        except asyncio.CancelledError:
            break
        except Exception:
            # On error, send keepalive and continue
            yield f"data: {json.dumps({'type': 'system.keepalive', 'session_id': session_id})}\n\n"
            await asyncio.sleep(SSE_POLL_INTERVAL)


@router.get("/{session_id}/events")
async def session_events_sse(
    session_id: str,
    stream: bool = Query(False),
    limit: int = Query(100, ge=1, le=500),
) -> Any:
    """Session events endpoint with optional SSE streaming.

    Args:
        session_id: The session identifier
        stream: If true, return SSE stream; otherwise return JSON
        limit: Maximum events to return (JSON mode only)
    """
    store = await _get_store()

    if stream:
        return StreamingResponse(
            _sse_event_generator(session_id, store),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # Non-streaming: return events as JSON
    events = await store.list_events(session_id=session_id, limit=limit)
    return {"session_id": session_id, "events": events or []}


@router.get("/{session_id}")
async def get_session(session_id: str) -> dict[str, Any]:
    """Get session envelope."""
    store = await _get_store()
    envelope = await store.get_envelope(session_id)
    if envelope:
        return {
            "session_id": str(envelope.session_id),
            "persona_id": envelope.persona_id,
            "tenant": envelope.tenant,
            "metadata": envelope.metadata,
            "created_at": envelope.created_at.isoformat() if envelope.created_at else None,
            "updated_at": envelope.updated_at.isoformat() if envelope.updated_at else None,
        }
    return {"session_id": session_id, "status": "not_found"}
