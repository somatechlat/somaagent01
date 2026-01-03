"""Sessions API Router with SSE Streaming.

Migrated from: services/gateway/routers/sessions.py
Pure Django ORM implementation - NO session_repository.

VIBE COMPLIANT - Django ORM, no legacy stores.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import AsyncGenerator, Optional

from asgiref.sync import sync_to_async
from django.conf import settings
from django.http import StreamingHttpResponse
from ninja import Query, Router
from pydantic import BaseModel

from admin.core.models import Session, SessionEvent

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


@sync_to_async
def _list_sessions(limit: int):
    """List sessions using Django ORM."""
    return list(Session.objects.all().order_by("-created_at")[:limit])


@sync_to_async
def _get_session(session_id: str):
    """Get session by ID."""
    return Session.objects.filter(session_id=session_id).first()


@sync_to_async
def _get_session_events(session_id: str, limit: int):
    """Get session events."""
    session = Session.objects.filter(session_id=session_id).first()
    if not session:
        return None
    return list(session.events.all().order_by("-created_at")[:limit])


@sync_to_async
def _get_events_after(session_id: str, after_id: Optional[int], limit: int):
    """Get events after a given ID."""
    session = Session.objects.filter(session_id=session_id).first()
    if not session:
        return []
    qs = session.events.all()
    if after_id:
        qs = qs.filter(id__gt=after_id)
    return list(qs.order_by("id")[:limit])


@sync_to_async
def _create_or_update_session(session_id: str, persona_id: Optional[str], tenant: Optional[str]):
    """Create or get session."""
    session, _ = Session.objects.get_or_create(
        session_id=session_id, defaults={"persona_id": persona_id, "tenant": tenant}
    )
    return session


@sync_to_async
def _append_event(session_id: str, event_data: dict):
    """Append event to session."""
    session = Session.objects.filter(session_id=session_id).first()
    if not session:
        session = Session.objects.create(
            session_id=session_id,
            persona_id=event_data.get("persona_id"),
            tenant=event_data.get("metadata", {}).get("tenant"),
        )
    SessionEvent.objects.create(
        session=session,
        event_type="message",
        payload=event_data,
        role=event_data.get("role", "user"),
    )


async def _sse_event_generator(session_id: str) -> AsyncGenerator[str, None]:
    """Generate SSE events for a session by polling PostgreSQL."""
    last_event_id: Optional[int] = None
    last_keepalive = asyncio.get_event_loop().time()

    # Send initial keepalive
    yield f"data: {json.dumps({'type': 'system.keepalive', 'session_id': session_id})}\n\n"

    while True:
        try:
            events = await _get_events_after(session_id, last_event_id, 50)

            for event in events:
                event_id = event.id
                if event_id is not None:
                    last_event_id = event_id
                payload = event.payload or {}
                payload["event_type"] = event.event_type
                payload["role"] = event.role
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
    rows = await _list_sessions(limit)
    return [
        {
            "session_id": str(r.session_id),
            "persona_id": r.persona_id,
            "tenant": r.tenant,
        }
        for r in rows
    ]


@router.get("/{session_id}", summary="Get session details")
async def get_session(session_id: str) -> dict:
    """Get session envelope."""
    session = await _get_session(session_id)
    if session:
        return {
            "session_id": str(session.session_id),
            "persona_id": session.persona_id,
            "tenant": session.tenant,
            "metadata": session.metadata,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "updated_at": session.updated_at.isoformat() if session.updated_at else None,
        }
    return {"session_id": session_id, "status": "not_found"}


@router.get("/{session_id}/history", summary="Get session history")
async def session_history(session_id: str, limit: int = Query(100, ge=1, le=500)) -> dict:
    """Return session history events."""
    from admin.common.exceptions import NotFoundError

    events = await _get_session_events(session_id, limit)
    if events is None:
        raise NotFoundError("session", session_id)
    return {
        "session_id": session_id,
        "events": [
            {
                "event_type": e.event_type,
                "payload": e.payload,
                "role": e.role,
                "created_at": e.created_at.isoformat(),
            }
            for e in events
        ],
    }


@router.get("/{session_id}/events", summary="Session events (SSE or JSON)")
async def session_events_sse(
    request,
    session_id: str,
    stream: bool = Query(False),
    limit: int = Query(100, ge=1, le=500),
):
    """Session events endpoint with optional SSE streaming."""
    if stream:
        return StreamingHttpResponse(
            _sse_event_generator(session_id),
            content_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    events = await _get_session_events(session_id, limit)
    return {
        "session_id": session_id,
        "events": [
            {"event_type": e.event_type, "payload": e.payload, "role": e.role}
            for e in (events or [])
        ],
    }


@router.post("/message", response=SessionMessageResponse, summary="Post user message")
async def post_session_message(payload: SessionMessageRequest) -> dict:
    """Enqueue a user message and persist a session event."""
    from admin.common.exceptions import ValidationError
    from services.conversation_worker.temporal_worker import ConversationWorkflow
    from services.gateway import providers

    if not payload.message.strip():
        raise ValidationError("message required")

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

    await _append_event(session_id, event)

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
