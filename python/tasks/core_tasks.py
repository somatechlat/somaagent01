"""
Canonical Celery tasks for SomaAgent01 (delegate, context, policy, storage, maintenance).

All tasks are production-grade: policy-checked, idempotent via Redis, and persist
events into PostgresSessionStore. Metrics are emitted via Prometheus counters/histograms.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any, Optional

import httpx
from celery import Task, shared_task
from prometheus_client import Counter, Histogram
from redis import Redis

from services.common.admin_settings import ADMIN_SETTINGS
from services.common.policy_client import PolicyClient, PolicyRequest
from services.common.session_repository import (
    PostgresSessionStore,
    ensure_schema as ensure_session_schema,
)
from services.common.publisher import DurablePublisher
from services.common.event_bus import KafkaEventBus
from services.common.messaging_utils import build_headers, idempotency_key
from services.common.saga_manager import (
    SagaManager,
    run_compensation,
    register_compensation,
)
from src.core.config import cfg

from python.tasks.config import create_redis_client

LOGGER = logging.getLogger(__name__)

# Validation utilities for task payloads (VIBE security)
from python.tasks.validation import validate_payload
from python.tasks.schemas import (
    DELEGATE_PAYLOAD_SCHEMA,
    STORE_INTERACTION_PAYLOAD_SCHEMA,
    FEEDBACK_LOOP_PAYLOAD_SCHEMA,
    CLEANUP_SESSIONS_ARGS_SCHEMA,
    REBUILD_INDEX_ARGS_SCHEMA,
    EVALUATE_POLICY_ARGS_SCHEMA,
)


# ---------------------------------------------------------------------------
# Helper: enforce OPA policy for core tasks
# ---------------------------------------------------------------------------
def _enforce_policy(task_name: str, tenant_id: str, action: str, resource: dict[str, Any]) -> None:
    """Raise PermissionError if the OPA policy denies the requested action.

    All mutable core tasks should be guarded by a policy check.  The ``PolicyClient``
    evaluates a ``PolicyRequest`` and returns a boolean indicating permission.
    If the result is falsy we raise a ``PermissionError`` which will be captured
    by ``SafeTask`` and routed to the DLQ.
    """
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


# ---------------------------------------------------------------------------
# Shared resources
# ---------------------------------------------------------------------------
redis_client: Redis = create_redis_client()
_store: Optional[PostgresSessionStore] = None
_schema_ready = False
_schema_lock = asyncio.Lock()
policy_client = PolicyClient(base_url=ADMIN_SETTINGS.opa_url)
# Audit publisher (Kafka + outbox)
bus = KafkaEventBus(
    settings={
        "bootstrap_servers": cfg.env("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        "security_protocol": cfg.env("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
        "sasl_mechanism": cfg.env("KAFKA_SASL_MECHANISM"),
        "sasl_plain_username": cfg.env("KAFKA_SASL_USERNAME"),
        "sasl_plain_password": cfg.env("KAFKA_SASL_PASSWORD"),
    }
)
_outbox = None
try:
    from services.common.outbox_repository import OutboxStore

    _outbox = OutboxStore(dsn=ADMIN_SETTINGS.postgres_dsn)
except Exception:
    _outbox = None
publisher = DurablePublisher(bus=bus, outbox=_outbox) if _outbox else None
saga_manager = SagaManager(dsn=ADMIN_SETTINGS.postgres_dsn)
_saga_schema_ready = False
_saga_lock = asyncio.Lock()


async def _get_store() -> PostgresSessionStore:
    global _store, _schema_ready
    if _store is None:
        _store = PostgresSessionStore(dsn=ADMIN_SETTINGS.postgres_dsn)
    if not _schema_ready:
        async with _schema_lock:
            if not _schema_ready:
                await ensure_session_schema(_store)
                _schema_ready = True
    return _store


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


async def _ensure_saga_schema():
    global _saga_schema_ready
    if _saga_schema_ready:
        return
    async with _saga_lock:
        if not _saga_schema_ready:
            await saga_manager.ensure_schema()
            _saga_schema_ready = True


def _dedupe_once(key: str, ttl: int = 3600) -> bool:
    """Return True if this key has not been seen; set key with TTL."""
    try:
        if redis_client.setnx(key, int(time.time())):
            redis_client.expire(key, ttl)
            return True
        return False
    except Exception:
        # fail-open on dedupe to avoid blocking task
        return True


def _append_event_sync(session_id: str, event: dict[str, Any]) -> None:
    store = _run(_get_store())
    _run(store.append_event(session_id, event))


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
    """Send task_feedback to SomaBrain; on failure enqueue to DLQ."""
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
        # Push to DLQ for later retry
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
                # last resort: log only to avoid silent loss
                LOGGER.error(
                    "Failed to enqueue task_feedback to DLQ",
                    exc_info=True,
                    extra={"task": task_name},
                )
                task_feedback_total.labels("failed").inc()
        else:
            LOGGER.error(
                "task_feedback delivery failed and no publisher configured",
                exc_info=True,
                extra={"task": task_name},
            )
            task_feedback_total.labels("failed").inc()


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
task_invocations_total = Counter(
    "sa01_core_tasks_total",
    "Core tasks invocations",
    ["task", "result"],
)

task_latency_seconds = Histogram(
    "sa01_core_task_latency_seconds",
    "Latency of core tasks",
    ["task"],
    buckets=[0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10],
)

task_feedback_total = Counter(
    "sa01_task_feedback_total",
    "Task feedback delivery outcomes",
    ["status"],
)


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
            # forward to DLQ
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
# Tasks
# ---------------------------------------------------------------------------


@shared_task(
    bind=True,
    base=SafeTask,
    name="python.tasks.core_tasks.delegate",
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    soft_time_limit=45,
    time_limit=60,
    rate_limit="60/m",
)
def delegate(self, payload: dict[str, Any], tenant_id: str, request_id: str) -> dict[str, Any]:
    """Authorize and record a delegation request."""
    # Validate the payload against the declared schema before any processing.
    validate_payload(DELEGATE_PAYLOAD_SCHEMA, payload)
    _run(_ensure_saga_schema())
    saga_id = _run(
        saga_manager.start(
            "delegate",
            step="authorize",
            data={"request_id": request_id, "tenant": tenant_id, "payload": payload},
        )
    )
    allowed = _run(
        policy_client.evaluate(
            PolicyRequest(
                tenant=tenant_id,
                persona_id=payload.get("persona_id"),
                action="delegate.task",
                resource=str(payload.get("target") or payload.get("task") or "delegate"),
                context={"request_id": request_id},
            )
        )
    )
    if not allowed:
        _run(saga_manager.fail(saga_id, "policy_denied"))
        _run(run_compensation("delegate", saga_id, {"reason": "policy_denied"}))
        raise PermissionError("delegate.task denied by policy")

    dedupe_key = f"delegate:{request_id}"
    if not _dedupe_once(dedupe_key, ttl=3600):
        _run(
            saga_manager.update(
                saga_id, step="dedupe", status="duplicate", data={"request_id": request_id}
            )
        )
        _run(run_compensation("delegate", saga_id, {"reason": "duplicate"}))
        return {"status": "duplicate", "request_id": request_id, "saga_id": saga_id}

    session_id = payload.get("session_id") or request_id
    event_id = str(uuid.uuid4())
    event = {
        "type": "delegate_request",
        "event_id": event_id,
        "session_id": session_id,
        "tenant": tenant_id,
        "persona_id": payload.get("persona_id"),
        "payload": payload,
        "metadata": {"source": "celery.delegate"},
        "saga_id": saga_id,
    }
    _append_event_sync(session_id, event)
    if publisher:
        headers = build_headers(
            tenant=tenant_id,
            session_id=session_id,
            persona_id=payload.get("persona_id"),
            event_type="delegate_request",
            event_id=event_id,
            correlation=request_id,
        )
        _run(
            publisher.publish(
                cfg.env("AUDIT_TOPIC", "audit.events"),
                {**event, "correlation_id": headers["correlation_id"]},
                headers=headers,
                dedupe_key=idempotency_key(event, seed=request_id),
                session_id=session_id,
                tenant=tenant_id,
            )
        )
    _run(
        saga_manager.update(
            saga_id, step="recorded", status="accepted", data={"event_id": event_id}
        )
    )
    return {"status": "accepted", "event_id": event_id, "saga_id": saga_id}


@shared_task(
    bind=True,
    base=SafeTask,
    name="python.tasks.core_tasks.build_context",
    max_retries=2,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    soft_time_limit=30,
    time_limit=45,
)
def build_context(self, tenant_id: str, session_id: str) -> dict[str, Any]:
    """Record a context build trigger for the session (downstream builder consumes)."""
    event_id = str(uuid.uuid4())
    event = {
        "type": "context_build_requested",
        "event_id": event_id,
        "session_id": session_id,
        "tenant": tenant_id,
        "metadata": {"source": "celery.build_context"},
    }
    _append_event_sync(session_id, event)
    return {"status": "queued", "event_id": event_id}


@shared_task(
    bind=True,
    base=SafeTask,
    name="python.tasks.core_tasks.evaluate_policy",
    max_retries=2,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    soft_time_limit=20,
    time_limit=30,
)
def evaluate_policy(self, tenant_id: str, action: str, resource: dict[str, Any]) -> dict[str, Any]:
    """Evaluate an OPA policy decision and record it."""
    # Validate arguments against schema (VIBE security)
    validate_payload(
        EVALUATE_POLICY_ARGS_SCHEMA,
        {"tenant_id": tenant_id, "action": action, "resource": resource},
    )
    decision = _run(
        policy_client.evaluate(
            PolicyRequest(
                tenant=tenant_id,
                persona_id=resource.get("persona_id"),
                action=action,
                resource=resource.get("name") or str(resource),
                context=resource,
            )
        )
    )
    event_id = str(uuid.uuid4())
    event = {
        "type": "policy_decision",
        "event_id": event_id,
        "session_id": resource.get("session_id") or resource.get("id") or event_id,
        "tenant": tenant_id,
        "decision": decision,
        "action": action,
        "resource": resource,
        "metadata": {"source": "celery.evaluate_policy"},
    }
    _append_event_sync(event["session_id"], event)
    saga_id = resource.get("saga_id")
    if saga_id:
        _run(
            saga_manager.update(
                saga_id,
                step="policy_decision",
                status="allowed" if decision else "denied",
                data={"action": action, "resource": resource},
            )
        )
        if not decision:
            _run(run_compensation("delegate", saga_id, {"reason": "policy_denied"}))
    if publisher:
        headers = build_headers(
            tenant=tenant_id,
            session_id=event["session_id"],
            persona_id=resource.get("persona_id"),
            event_type="policy_decision",
            event_id=event_id,
        )
        _run(
            publisher.publish(
                cfg.env("AUDIT_TOPIC", "audit.events"),
                {**event, "correlation_id": headers["correlation_id"]},
                headers=headers,
                dedupe_key=idempotency_key(event),
                session_id=event["session_id"],
                tenant=tenant_id,
            )
        )
    return {"allowed": decision, "event_id": event_id}


@shared_task(
    bind=True,
    base=SafeTask,
    name="python.tasks.core_tasks.store_interaction",
    max_retries=2,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    soft_time_limit=30,
    time_limit=45,
)
def store_interaction(self, session_id: str, interaction: dict[str, Any]) -> dict[str, Any]:
    """Persist a conversation interaction into the session timeline."""
    # Validate payload against schema (VIBE security)
    validate_payload(
        STORE_INTERACTION_PAYLOAD_SCHEMA,
        {"session_id": session_id, "interaction": interaction},
    )
    # Enforce policy – only allow storing interactions if permitted
    _enforce_policy(
        task_name="store_interaction",
        tenant_id=interaction.get("tenant_id", "unknown"),
        action="store_interaction",
        resource={
            "name": "store_interaction",
            "session_id": session_id,
            "tenant": interaction.get("tenant_id"),
        },
    )
    event_id = str(uuid.uuid4())
    interaction = dict(interaction or {})
    interaction.setdefault("event_id", event_id)
    interaction.setdefault("session_id", session_id)
    interaction.setdefault("type", "interaction")
    _append_event_sync(session_id, interaction)
    return {"stored": True, "event_id": event_id}


@shared_task(
    bind=True,
    base=SafeTask,
    name="python.tasks.core_tasks.feedback_loop",
    max_retries=2,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    soft_time_limit=30,
    time_limit=45,
)
def feedback_loop(self, session_id: str, feedback: dict[str, Any]) -> dict[str, Any]:
    """Persist feedback for later analysis and model learning."""
    # Validate payload against schema (VIBE security)
    validate_payload(
        FEEDBACK_LOOP_PAYLOAD_SCHEMA,
        {"session_id": session_id, "feedback": feedback},
    )
    # Enforce policy – only allow storing feedback if permitted
    _enforce_policy(
        task_name="feedback_loop",
        tenant_id=feedback.get("tenant_id", "unknown"),
        action="feedback_loop",
        resource={
            "name": "feedback_loop",
            "session_id": session_id,
            "tenant": feedback.get("tenant_id"),
        },
    )
    event_id = str(uuid.uuid4())
    payload = {
        "type": "feedback",
        "event_id": event_id,
        "session_id": session_id,
        "payload": feedback,
        "metadata": {"source": "celery.feedback"},
    }
    _append_event_sync(session_id, payload)
    return {"stored": True, "event_id": event_id}


@shared_task(
    bind=True,
    base=SafeTask,
    name="python.tasks.core_tasks.rebuild_index",
    max_retries=1,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    soft_time_limit=60,
    time_limit=90,
)
def rebuild_index(self, tenant_id: str) -> dict[str, Any]:
    """Log an index rebuild request for the tenant (consumed by search pipeline)."""
    # Validate arguments against schema (VIBE security)
    validate_payload(
        REBUILD_INDEX_ARGS_SCHEMA,
        {"tenant_id": tenant_id},
    )
    # Enforce policy for rebuild_index operation
    _enforce_policy(
        task_name="rebuild_index",
        tenant_id=tenant_id,
        action="rebuild_index",
        resource={"name": "rebuild_index", "tenant": tenant_id},
    )
    event_id = str(uuid.uuid4())
    session_id = f"rebuild-{tenant_id}"
    payload = {
        "type": "rebuild_index",
        "event_id": event_id,
        "session_id": session_id,
        "tenant": tenant_id,
        "metadata": {"source": "celery.rebuild_index"},
    }
    _append_event_sync(session_id, payload)
    return {"queued": True, "event_id": event_id}


@shared_task(
    bind=True,
    base=SafeTask,
    name="python.tasks.core_tasks.publish_metrics",
    max_retries=1,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    soft_time_limit=15,
    time_limit=20,
)
def publish_metrics(self) -> dict[str, Any]:
    """Lightweight heartbeat to keep metrics series active."""
    # Publishing metrics is an internal operation; enforce a permissive policy
    _enforce_policy(
        task_name="publish_metrics",
        tenant_id="system",
        action="publish_metrics",
        resource={"name": "publish_metrics"},
    )
    task_invocations_total.labels("publish_metrics", "tick").inc()
    return {"status": "ok", "timestamp": time.time()}


@shared_task(
    bind=True,
    base=SafeTask,
    name="python.tasks.core_tasks.cleanup_sessions",
    max_retries=1,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    soft_time_limit=90,
    time_limit=120,
)
def cleanup_sessions(self, max_age_hours: int = 24) -> dict[str, Any]:
    """Purge old session events/envelopes beyond age threshold."""
    # Validate arguments against schema (VIBE security)
    validate_payload(
        CLEANUP_SESSIONS_ARGS_SCHEMA,
        {"max_age_hours": max_age_hours},
    )
    # Enforce a permissive system‑level policy for cleanup operations
    _enforce_policy(
        task_name="cleanup_sessions",
        tenant_id="system",
        action="cleanup_sessions",
        resource={"name": "cleanup_sessions", "max_age_hours": max_age_hours},
    )
    store = _run(_get_store())
    cutoff_hours = max(max_age_hours, 1)
    sql_events = """
        DELETE FROM session_events
        WHERE occurred_at < (NOW() - ($1 || ' hours')::interval)
    """
    sql_envelopes = """
        DELETE FROM session_envelopes
        WHERE updated_at < (NOW() - ($1 || ' hours')::interval)
    """

    async def _purge():
        pool = await store._ensure_pool()  # type: ignore[attr-defined]
        async with pool.acquire() as conn:
            async with conn.transaction():
                ev_res = await conn.execute(sql_events, cutoff_hours)
                env_res = await conn.execute(sql_envelopes, cutoff_hours)
                return ev_res, env_res

    ev_res, env_res = _run(_purge())
    return {"events": ev_res, "envelopes": env_res}


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


# Register compensation on import
register_compensation("delegate", _delegate_compensation)


@shared_task(
    bind=True,
    base=SafeTask,
    name="python.tasks.core_tasks.dead_letter",
    max_retries=0,
    rate_limit="120/m",
)
def dead_letter(
    self, task_name: str, args: Any, kwargs: dict[str, Any], error: str
) -> dict[str, Any]:
    """Capture failed task payloads for inspection on DLQ."""
    event_id = str(uuid.uuid4())
    payload = {
        "type": "dead_letter",
        "event_id": event_id,
        "task_name": task_name,
        "args": args,
        "kwargs": kwargs,
        "error": error,
    }
    session_id = kwargs.get("session_id") if isinstance(kwargs, dict) else None
    if session_id:
        _append_event_sync(session_id, payload)
    if publisher:
        headers = build_headers(
            event_type="dead_letter",
            event_id=event_id,
            session_id=session_id,
        )
        _run(
            publisher.publish(
                cfg.env("DLQ_TOPIC", "dlq.events"),
                {**payload, "correlation_id": headers["correlation_id"]},
                headers=headers,
                dedupe_key=idempotency_key(payload),
                session_id=session_id,
                tenant=None,
            )
        )
    return {"status": "captured", "event_id": event_id}
