"""Core Celery tasks - thin facade re-exporting domain-specific tasks.

Infrastructure, helpers, and base classes are defined here.
Domain tasks are in conversation_tasks, memory_tasks, maintenance_tasks.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any, Optional

import httpx
from celery import Task
from prometheus_client import Counter, Histogram
from redis import Redis

from python.tasks.config import create_redis_client
from services.common.event_bus import KafkaEventBus, KafkaSettings
from services.common.messaging_utils import build_headers, idempotency_key
from services.common.policy_client import PolicyClient, PolicyRequest
from services.common.publisher import DurablePublisher
from services.common.saga_manager import register_compensation, run_compensation, SagaManager
from services.common.session_repository import (
    ensure_schema as ensure_session_schema,
    PostgresSessionStore,
)
from src.core.config import cfg

LOGGER = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared resources
# ---------------------------------------------------------------------------
redis_client: Redis = create_redis_client()
_store: Optional[PostgresSessionStore] = None
_schema_ready = False
_schema_lock = asyncio.Lock()
policy_client = PolicyClient(base_url=cfg.settings().external.opa_url)

bus = KafkaEventBus(
    settings=KafkaSettings(
        bootstrap_servers=cfg.env(
            "KAFKA_BOOTSTRAP_SERVERS", cfg.settings().kafka.bootstrap_servers
        ),
        security_protocol=cfg.env("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
        sasl_mechanism=cfg.env("KAFKA_SASL_MECHANISM"),
        sasl_username=cfg.env("KAFKA_SASL_USERNAME"),
        sasl_password=cfg.env("KAFKA_SASL_PASSWORD"),
    )
)

_outbox = None
try:
    from services.common.outbox_repository import OutboxStore

    _outbox = OutboxStore(dsn=cfg.settings().database.dsn)
except Exception:
    pass

publisher = DurablePublisher(bus=bus, outbox=_outbox) if _outbox else None
saga_manager = SagaManager(dsn=cfg.settings().database.dsn)
_saga_schema_ready = False
_saga_lock = asyncio.Lock()

# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
task_invocations_total = Counter(
    "sa01_core_tasks_total", "Core tasks invocations", ["task", "result"]
)
task_latency_seconds = Histogram(
    "sa01_core_task_latency_seconds",
    "Latency of core tasks",
    ["task"],
    buckets=[0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10],
)
task_feedback_total = Counter(
    "sa01_task_feedback_total", "Task feedback delivery outcomes", ["status"]
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


async def _get_store() -> PostgresSessionStore:
    global _store, _schema_ready
    if _store is None:
        _store = PostgresSessionStore(dsn=cfg.settings().database.dsn)
    if not _schema_ready:
        async with _schema_lock:
            if not _schema_ready:
                await ensure_session_schema(_store)
                _schema_ready = True
    return _store


async def _ensure_saga_schema():
    global _saga_schema_ready
    if _saga_schema_ready:
        return
    async with _saga_lock:
        if not _saga_schema_ready:
            await saga_manager.ensure_schema()
            _saga_schema_ready = True


def _dedupe_once(key: str, ttl: int = 3600) -> bool:
    try:
        if redis_client.setnx(key, int(time.time())):
            redis_client.expire(key, ttl)
            return True
        return False
    except Exception:
        return True


def _append_event_sync(session_id: str, event: dict[str, Any]) -> None:
    store = _run(_get_store())
    _run(store.append_event(session_id, event))


def _enforce_policy(task_name: str, tenant_id: str, action: str, resource: dict[str, Any]) -> None:
    allowed = _run(
        policy_client.evaluate(
            PolicyRequest(
                tenant=tenant_id,
                persona_id=resource.get("persona_id"),
                action=action,
                resource=str(resource.get("name") or resource),
                context=resource,
            )
        )
    )
    if not allowed:
        raise PermissionError(f"{task_name} denied by policy for action {action}")


def _send_feedback_sync(
    *,
    task_name: str,
    tenant: Optional[str],
    persona: Optional[str],
    session_id: Optional[str],
    success: bool,
    latency_sec: float,
    error_type: Optional[str] = None,
    tags: Optional[list[str]] = None,
) -> None:
    base_url = cfg.get_somabrain_url()
    payload = {
        "task_name": task_name,
        "tenant_id": tenant,
        "persona_id": persona,
        "session_id": session_id,
        "success": success,
        "latency_ms": int(latency_sec * 1000),
        "error_type": error_type,
        "tags": tags or [],
    }
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(f"{base_url}/context/feedback", json=payload)
            resp.raise_for_status()
        task_feedback_total.labels("delivered").inc()
    except Exception as exc:
        if publisher:
            headers = build_headers(
                tenant=tenant,
                session_id=session_id,
                persona_id=persona,
                event_type="task_feedback",
                event_id=str(uuid.uuid4()),
            )
            try:
                _run(
                    publisher.publish(
                        cfg.env("TASK_FEEDBACK_TOPIC", "task.feedback.dlq"),
                        {"payload": payload, "error": str(exc)},
                        headers=headers,
                        dedupe_key=idempotency_key(payload, seed=task_name),
                        session_id=session_id,
                        tenant=tenant,
                    )
                )
                task_feedback_total.labels("queued_dlq").inc()
            except Exception:
                LOGGER.error("Failed to enqueue task_feedback to DLQ", exc_info=True)
                task_feedback_total.labels("failed").inc()
        else:
            LOGGER.error("task_feedback delivery failed", exc_info=True)
            task_feedback_total.labels("failed").inc()


class SafeTask(Task):
    """Base task providing metrics and robust error recording."""

    def __call__(self, *args, **kwargs):
        start = time.time()
        try:
            result = super().__call__(*args, **kwargs)
            latency = time.time() - start
            task_invocations_total.labels(self.name, "success").inc()
            task_latency_seconds.labels(self.name).observe(latency)
            _send_feedback_sync(
                task_name=self.name,
                tenant=kwargs.get("tenant_id") or kwargs.get("tenant"),
                persona=kwargs.get("persona_id") or kwargs.get("persona"),
                session_id=kwargs.get("session_id"),
                success=True,
                latency_sec=latency,
                tags=kwargs.get("soma_tags") or [],
            )
            return result
        except Exception as exc:
            latency = time.time() - start
            task_invocations_total.labels(self.name, "error").inc()
            task_latency_seconds.labels(self.name).observe(latency)
            _send_feedback_sync(
                task_name=self.name,
                tenant=kwargs.get("tenant_id") or kwargs.get("tenant"),
                persona=kwargs.get("persona_id") or kwargs.get("persona"),
                session_id=kwargs.get("session_id"),
                success=False,
                latency_sec=latency,
                error_type=exc.__class__.__name__,
                tags=kwargs.get("soma_tags") or [],
            )
            if self.name != "python.tasks.core_tasks.dead_letter":
                dead_letter.apply_async(
                    kwargs={
                        "task_name": self.name,
                        "args": args,
                        "kwargs": kwargs,
                        "error": str(args if not kwargs else kwargs),
                    },
                    queue="dlq",
                )
            raise


# ---------------------------------------------------------------------------
# Compensation registry
# ---------------------------------------------------------------------------
async def _delegate_compensation(saga_id: str, context: dict[str, Any]) -> None:
    saga = await saga_manager.get(saga_id)
    if not saga:
        return
    payload = saga.data.get("payload", {}) if isinstance(saga.data, dict) else {}
    session_id = payload.get("session_id") or saga.data.get("request_id")
    tenant = saga.data.get("tenant")
    event_id = str(uuid.uuid4())
    event = {
        "type": "delegate_compensation",
        "event_id": event_id,
        "session_id": session_id,
        "tenant": tenant,
        "reason": context.get("reason"),
        "metadata": {"source": "celery.delegate.compensation"},
        "saga_id": saga_id,
    }
    if session_id:
        _append_event_sync(session_id, event)
    if publisher:
        headers = build_headers(
            tenant=tenant,
            session_id=session_id,
            event_type="delegate_compensation",
            event_id=event_id,
        )
        _run(
            publisher.publish(
                cfg.env("AUDIT_TOPIC", "audit.events"),
                {**event, "correlation_id": headers["correlation_id"]},
                headers=headers,
                dedupe_key=idempotency_key(event),
                session_id=session_id,
                tenant=tenant,
            )
        )


register_compensation("delegate", _delegate_compensation)


# ---------------------------------------------------------------------------
# Re-export tasks from domain modules for backward compatibility
# ---------------------------------------------------------------------------
from python.tasks.conversation_tasks import (
    build_context,
    delegate,
    feedback_loop,
    store_interaction,
)
from python.tasks.maintenance_tasks import cleanup_sessions, dead_letter, publish_metrics
from python.tasks.memory_tasks import evaluate_policy, rebuild_index

__all__ = [
    "delegate",
    "build_context",
    "store_interaction",
    "feedback_loop",
    "rebuild_index",
    "evaluate_policy",
    "publish_metrics",
    "cleanup_sessions",
    "dead_letter",
    "SafeTask",
    "_run",
    "_get_store",
    "_dedupe_once",
    "_append_event_sync",
    "_enforce_policy",
    "_ensure_saga_schema",
    "policy_client",
    "publisher",
    "saga_manager",
    "run_compensation",
    "build_headers",
    "idempotency_key",
    "task_invocations_total",
]
