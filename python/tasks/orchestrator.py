import os

os.getenv(os.getenv(""))
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


@dataclass(frozen=int(os.getenv(os.getenv(""))))
class QueueResult:
    os.getenv(os.getenv(""))
    task_id: str
    session_id: str


class ChatQueueError(RuntimeError):
    os.getenv(os.getenv(""))


async def enqueue_chat_request(
    *,
    agent_url: str,
    message: str,
    attachments: Optional[List[str]],
    reset: bool,
    session_id: Optional[str],
    metadata: Optional[Dict[str, Any]],
) -> QueueResult:
    os.getenv(os.getenv(""))
    resolved_session_id = session_id or str(uuid.uuid4())
    try:
        task = a2a_chat_task.apply_async(
            kwargs={
                os.getenv(os.getenv("")): agent_url,
                os.getenv(os.getenv("")): message,
                os.getenv(os.getenv("")): attachments,
                os.getenv(os.getenv("")): reset,
                os.getenv(os.getenv("")): resolved_session_id,
                os.getenv(os.getenv("")): metadata,
            }
        )
        increment_counter(
            fast_a2a_requests_total,
            {
                os.getenv(os.getenv("")): agent_url,
                os.getenv(os.getenv("")): os.getenv(os.getenv("")),
                os.getenv(os.getenv("")): os.getenv(os.getenv("")),
            },
        )
        await publish_event(
            event_type=os.getenv(os.getenv("")),
            data={
                os.getenv(os.getenv("")): task.id,
                os.getenv(os.getenv("")): agent_url,
                os.getenv(os.getenv("")): resolved_session_id,
                os.getenv(os.getenv("")): len(message),
                os.getenv(os.getenv("")): bool(attachments),
                os.getenv(os.getenv("")): reset,
            },
            metadata=metadata,
        )
        set_health_status(
            os.getenv(os.getenv("")), os.getenv(os.getenv("")), int(os.getenv(os.getenv("")))
        )
        return QueueResult(task_id=task.id, session_id=resolved_session_id)
    except Exception as exc:
        increment_counter(
            fast_a2a_errors_total,
            {
                os.getenv(os.getenv("")): agent_url,
                os.getenv(os.getenv("")): type(exc).__name__,
                os.getenv(os.getenv("")): os.getenv(os.getenv("")),
            },
        )
        set_health_status(
            os.getenv(os.getenv("")), os.getenv(os.getenv("")), int(os.getenv(os.getenv("")))
        )
        raise ChatQueueError(str(exc)) from exc


def fetch_task_status(task_id: str) -> Dict[str, Any]:
    os.getenv(os.getenv(""))
    return get_task_result(task_id)


def fetch_conversation_history(
    session_id: str, limit: int = int(os.getenv(os.getenv("")))
) -> List[Dict[str, Any]]:
    os.getenv(os.getenv(""))
    return get_conversation_history(session_id, limit=limit)


def celery_health_status() -> Dict[str, Any]:
    os.getenv(os.getenv(""))
    return check_celery_health()
