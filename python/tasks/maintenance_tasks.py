"""Maintenance and cleanup Celery tasks."""
from __future__ import annotations

import time
import uuid
from typing import Any

from celery import shared_task

from python.tasks.core_tasks import (
    _append_event_sync,
    _enforce_policy,
    _get_store,
    _run,
    build_headers,
    idempotency_key,
    publisher,
    SafeTask,
    task_invocations_total,
)
from python.tasks.schemas import CLEANUP_SESSIONS_ARGS_SCHEMA
from python.tasks.validation import validate_payload
from src.core.config import cfg


@shared_task(
    bind=True, base=SafeTask, name="python.tasks.maintenance_tasks.publish_metrics",
    max_retries=1, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True,
    soft_time_limit=15, time_limit=20,
)
def publish_metrics(self) -> dict[str, Any]:
    """Lightweight heartbeat to keep metrics series active."""
    _enforce_policy("publish_metrics", "system", "publish_metrics", {"name": "publish_metrics"})
    task_invocations_total.labels("publish_metrics", "tick").inc()
    return {"status": "ok", "timestamp": time.time()}


@shared_task(
    bind=True, base=SafeTask, name="python.tasks.maintenance_tasks.cleanup_sessions",
    max_retries=1, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True,
    soft_time_limit=90, time_limit=120,
)
def cleanup_sessions(self, max_age_hours: int = 24) -> dict[str, Any]:
    """Purge old session events/envelopes beyond age threshold."""
    validate_payload(CLEANUP_SESSIONS_ARGS_SCHEMA, {"max_age_hours": max_age_hours})
    _enforce_policy("cleanup_sessions", "system", "cleanup_sessions",
                   {"name": "cleanup_sessions", "max_age_hours": max_age_hours})
    store = _run(_get_store())
    cutoff_hours = max(max_age_hours, 1)
    sql_events = "DELETE FROM session_events WHERE occurred_at < (NOW() - ($1 || ' hours')::interval)"
    sql_envelopes = "DELETE FROM session_envelopes WHERE updated_at < (NOW() - ($1 || ' hours')::interval)"

    async def _purge():
        pool = await store._ensure_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                ev_res = await conn.execute(sql_events, cutoff_hours)
                env_res = await conn.execute(sql_envelopes, cutoff_hours)
                return ev_res, env_res

    ev_res, env_res = _run(_purge())
    return {"events": ev_res, "envelopes": env_res}


@shared_task(
    bind=True, base=SafeTask, name="python.tasks.maintenance_tasks.dead_letter",
    max_retries=0, rate_limit="120/m",
)
def dead_letter(self, task_name: str, args: Any, kwargs: dict[str, Any], error: str) -> dict[str, Any]:
    """Capture failed task payloads for inspection on DLQ."""
    event_id = str(uuid.uuid4())
    payload = {"type": "dead_letter", "event_id": event_id, "task_name": task_name,
               "args": args, "kwargs": kwargs, "error": error}
    session_id = kwargs.get("session_id") if isinstance(kwargs, dict) else None
    if session_id:
        _append_event_sync(session_id, payload)
    if publisher:
        headers = build_headers(event_type="dead_letter", event_id=event_id, session_id=session_id)
        _run(publisher.publish(cfg.env("DLQ_TOPIC", "dlq.events"),
            {**payload, "correlation_id": headers["correlation_id"]}, headers=headers,
            dedupe_key=idempotency_key(payload), session_id=session_id, tenant=None))
    return {"status": "captured", "event_id": event_id}
