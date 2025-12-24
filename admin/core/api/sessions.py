"""Sessions API Router with SSE Streaming.

Migrated from: services/gateway/routers/sessions.py
Pure Django Ninja implementation with async SSE support.

VIBE COMPLIANT - Django patterns, centralized config, no hardcoded values.
"""

from __future__ import annotations

import asyncio
import json
import uuid
import logging
from typing import Any, AsyncGenerator, Optional

from django.conf import settings
from django.http import StreamingHttpResponse, JsonResponse
from ninja import Router, Query
from pydantic import BaseModel

router = Router(tags=["sessions"])
logger = logging.getLogger(__name__)

# SSE configuration - centralized
SSE_POLL_INTERVAL = float(getattr(settings, "SSE_POLL_INTERVAL", 2.0))
SSE_KEEPALIVE_INTERVAL = float(getattr(settings, "SSE_KEEPALIVE_INTERVAL", 10.0))


class SessionSummary(BaseModel):
    """Session summary schema."""
    
    session_id: str
    persona_id: Optional[str] = None
    tenant: Optional[str] = None


class SessionMessageRequest(BaseModel):
    """Request schema for posting a message."""
    
    message: str
    session_id: Optional[str] = None
    persona_id: Optional[str] = None
    tenant: Optional[str] = None


class SessionMessageResponse(BaseModel):
    """Response schema for posted message."""
    
    session_id: str
    event_id: str
    workflow_id: str


async def _get_store():
    """Get initialized session store."""
    from services.common.session_repository import ensure_schema, PostgresSessionStore
    from django.conf import settings
    
    store = PostgresSessionStore(settings.DATABASE_DSN)
    await ensure_schema(store)
    return store


def _get_session_cache():
    """Get session cache from providers."""
    from services.gateway import providers
    return providers.get_session_cache()


async def _sse_event_generator(
    session_id: str,
    store,
) -> AsyncGenerator[str, None]:
    """Generate SSE events for a session by polling PostgreSQL."""
    last_event_id: Optional[int] = None
    last_keepalive = asyncio.get_event_loop().time()

    # Send initial keepalive
    yield f"data: {json.dumps({'type': 'system.keepalive', 'session_id': session_id})}\n\n"

    while True:
        try:
            events = await store.list_events_after(
                session_id,
                after_id=last_event_id,
                limit=50,
            )

            for event in events:
                event_id = event.get("id")
                if event_id is not None:
                    last_event_id = event_id
                payload = event.get("payload", event)
                yield f"data: {json.dumps(payload)}\n\n"

            now = asyncio.get_event_loop().time()
            if now - last_keepalive >= SSE_KEEPALIVE_INTERVAL:
                yield f"data: {json.dumps({'type': 'system.keepalive', 'session_id': session_id})}\n\n"
                last_keepalive = now

            await asyncio.sleep(SSE_POLL_INTERVAL)

        except asyncio.CancelledError:
            break
        except Exception:
            yield f"data: {json.dumps({'type': 'system.keepalive', 'session_id': session_id})}\n\n"
            await asyncio.sleep(SSE_POLL_INTERVAL)


@router.get("", response=list[SessionSummary], summary="List recent sessions")
async def list_sessions(limit: int = Query(50, ge=1, le=200)) -> list[dict]:
    """List recent sessions."""
    store = await _get_store()
    rows = await store.list_sessions(limit=limit)
    return [
        {
            "session_id": str(r.session_id),
            "persona_id": getattr(r, "persona_id", None),
            "tenant": getattr(r, "tenant", None),
        }
        for r in rows
    ]


@router.get("/{session_id}", summary="Get session details")
async def get_session(session_id: str) -> dict:
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


@router.get("/{session_id}/history", summary="Get session history")
async def session_history(session_id: str, limit: int = Query(100, ge=1, le=500)) -> dict:
    """Return session history events."""
    from admin.common.exceptions import NotFoundError
    
    store = await _get_store()
    events = await store.list_events(session_id=session_id, limit=limit)
    if events is None:
        raise NotFoundError("session", session_id)
    return {"session_id": session_id, "events": events}


@router.get("/{session_id}/events", summary="Session events (SSE or JSON)")
async def session_events_sse(
    request,
    session_id: str,
    stream: bool = Query(False),
    limit: int = Query(100, ge=1, le=500),
):
    """Session events endpoint with optional SSE streaming.

    Args:
        session_id: The session identifier
        stream: If true, return SSE stream; otherwise return JSON
        limit: Maximum events to return (JSON mode only)
    """
    store = await _get_store()

    if stream:
        return StreamingHttpResponse(
            _sse_event_generator(session_id, store),
            content_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    events = await store.list_events(session_id=session_id, limit=limit)
    return {"session_id": session_id, "events": events or []}


@router.post("/message", response=SessionMessageResponse, summary="Post user message")
async def post_session_message(payload: SessionMessageRequest) -> dict:
    """Enqueue a user message and persist a session event.

    Returns session_id, event_id, and workflow_id for the enqueued message.
    """
    from admin.common.exceptions import ValidationError
    from services.gateway import providers
    from services.conversation_worker.temporal_worker import ConversationWorkflow
    from django.conf import settings
    
    if not payload.message.strip():
        raise ValidationError("message required")

    store = await _get_store()
    cache = _get_session_cache()

    session_id = payload.session_id or str(uuid.uuid4())
    event_id = str(uuid.uuid4())

    event = {
        "session_id": session_id,
        "persona_id": payload.persona_id,
        "metadata": {"tenant": payload.tenant, "source": "gateway"},
        "message": payload.message,
        "role": "user",
        "event_id": event_id,
    }

    await store.append_event(session_id, event)

    # Start Temporal workflow
    client = await providers.get_temporal_client()
    task_queue = settings.TEMPORAL_CONVERSATION_QUEUE
    workflow_id = f"conversation-{session_id}-{event_id}"
    event["workflow_id"] = workflow_id
    
    await client.start_workflow(
        ConversationWorkflow.run,
        event,
        id=workflow_id,
        task_queue=task_queue,
    )

    try:
        await cache.write_context(session_id, payload.persona_id, {"tenant": payload.tenant})
    except Exception:
        pass

    return {"session_id": session_id, "event_id": event_id, "workflow_id": workflow_id}


@router.post("/terminate/{workflow_id}", summary="Terminate conversation workflow")
async def terminate_conversation(workflow_id: str) -> dict:
    """Cancel a running conversation workflow."""
    from services.gateway import providers
    
    client = await providers.get_temporal_client()
    try:
        handle = client.get_workflow_handle(workflow_id=workflow_id)
        await handle.cancel()
        return {"status": "canceled", "workflow_id": workflow_id}
    except Exception as exc:
        return {"status": "error", "workflow_id": workflow_id, "error": str(exc)}
