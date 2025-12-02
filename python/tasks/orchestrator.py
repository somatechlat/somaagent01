"""
Task orchestration helpers for FastA2A chat flows.
Centralises queueing, status inspection, and health reporting.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from python.observability.event_publisher import publish_event
from python.observability.metrics import (
    fast_a2a_errors_total,
    fast_a2a_requests_total,
    increment_counter,
    set_health_status,
)
from python.tasks.a2a_chat_task import (
    a2a_chat_task,
    check_celery_health,
    get_conversation_history,
    get_task_result,
)


@dataclass(frozen=True)
class QueueResult:
    """Response metadata after enqueueing a chat task."""

    task_id: str
    session_id: str


class ChatQueueError(RuntimeError):
    """Raised when queueing a chat request fails."""


async def enqueue_chat_request(
    *,
    agent_url: str,
    message: str,
    attachments: Optional[List[str]],
    reset: bool,
    session_id: Optional[str],
    metadata: Optional[Dict[str, Any]],
) -> QueueResult:
    """
    Queue a FastA2A chat task with full metrics + event emission.

    Returns:
        QueueResult containing task + session identifiers.
    """
    resolved_session_id = session_id or str(uuid.uuid4())
    try:
        task = a2a_chat_task.apply_async(
            kwargs={
                "agent_url": agent_url,
                "message": message,
                "attachments": attachments,
                "reset": reset,
                "session_id": resolved_session_id,
                "metadata": metadata,
            }
        )

        increment_counter(
            fast_a2a_requests_total,
            {
                "agent_url": agent_url,
                "method": "chat_endpoint",
                "status": "queued",
            },
        )

        await publish_event(
            event_type="fast_a2a_chat_queued",
            data={
                "task_id": task.id,
                "agent_url": agent_url,
                "session_id": resolved_session_id,
                "message_length": len(message),
                "has_attachments": bool(attachments),
                "reset": reset,
            },
            metadata=metadata,
        )

        set_health_status("fastapi", "chat_endpoint", True)
        return QueueResult(task_id=task.id, session_id=resolved_session_id)
    except Exception as exc:
        increment_counter(
            fast_a2a_errors_total,
            {
                "agent_url": agent_url,
                "error_type": type(exc).__name__,
                "method": "chat_endpoint",
            },
        )
        set_health_status("fastapi", "chat_endpoint", False)
        raise ChatQueueError(str(exc)) from exc


def fetch_task_status(task_id: str) -> Dict[str, Any]:
    """Return stored Celery task metadata."""
    return get_task_result(task_id)


def fetch_conversation_history(session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Return recent conversation history for a session."""
    return get_conversation_history(session_id, limit=limit)


def celery_health_status() -> Dict[str, Any]:
    """Expose Celery worker health snapshot."""
    return check_celery_health()
