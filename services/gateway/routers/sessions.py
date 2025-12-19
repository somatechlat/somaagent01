"""Sessions router with SSE streaming support.

Provides real-time session event streaming using Server-Sent Events.
Uses PostgresSessionStore for event persistence and polling.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncGenerator, Optional, List

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from services.common.session_repository import ensure_schema, PostgresSessionStore
from services.gateway import providers

# Legacy admin settings replaced – use central cfg singleton.
from src.core.config import cfg

router = APIRouter(prefix="/v1/sessions", tags=["sessions"])

# SSE polling interval in seconds
SSE_POLL_INTERVAL = 2.0
SSE_KEEPALIVE_INTERVAL = 10.0


class SessionSummary(BaseModel):
    session_id: str
    persona_id: str | None = None
    tenant: str | None = None


async def _get_store() -> PostgresSessionStore:
    """Get initialized session store."""
    store = PostgresSessionStore(cfg.settings().database.dsn)
    await ensure_schema(store)
    return store


def _get_event_bus():
    return providers.get_event_bus()


def _get_session_cache():
    return providers.get_session_cache()


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


@router.get("", response_model=List[SessionSummary])
async def list_sessions(limit: int = Query(50, ge=1, le=200)) -> List[SessionSummary]:
    """List recent sessions."""
    store = await _get_store()
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
    """Return session history events."""
    store = await _get_store()
    events = await store.list_events(session_id=session_id, limit=limit)
    if events is None:
        raise HTTPException(status_code=404, detail="session_not_found")
    return {"session_id": session_id, "events": events}


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


@router.post("/message")
async def post_session_message(
    payload: dict[str, Any],
    bus=Depends(_get_event_bus),
    store: PostgresSessionStore = Depends(_get_store),
    cache=Depends(_get_session_cache),
):
    """Enqueue a user message and persist a session event.

    Returns ``session_id`` and ``event_id`` for the enqueued message.
    """
    message = payload.get("message", "")
    if not isinstance(message, str) or not message.strip():
        raise HTTPException(status_code=400, detail="message required")

    import uuid

    session_id = payload.get("session_id") or str(uuid.uuid4())
    event = {
        "session_id": session_id,
        "persona_id": payload.get("persona_id"),
        "metadata": {"tenant": payload.get("tenant"), "source": "gateway"},
        "message": message,
        "role": "user",
    }

    # Persist event
    await store.append_event(session_id, event)

    # Fetch last event id for response
    events = await store.list_events_after(session_id, limit=1)
    event_id = events[-1]["id"] if events else None

    # Publish to event bus for downstream workers
    try:
        await bus.publish("conversation.inbound", {"session_id": session_id, "message": message})
    except Exception:
        # Metrics/logging would capture; do not fail user path
        pass

    # Cache persona/metadata for quick access
    try:
        await cache.write_context(session_id, payload.get("persona_id"), {"tenant": payload.get("tenant")})
    except Exception:
        pass

    return {"session_id": session_id, "event_id": event_id}


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
