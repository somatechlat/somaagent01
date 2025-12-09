"""Conversation-related Celery tasks."""
from __future__ import annotations

import uuid
from typing import Any

from celery import shared_task

from python.tasks.core_tasks import (
    _append_event_sync,
    _dedupe_once,
    _enforce_policy,
    _ensure_saga_schema,
    _run,
    build_headers,
    idempotency_key,
    policy_client,
    publisher,
    run_compensation,
    SafeTask,
    saga_manager,
)
from python.tasks.schemas import (
    DELEGATE_PAYLOAD_SCHEMA,
    FEEDBACK_LOOP_PAYLOAD_SCHEMA,
    STORE_INTERACTION_PAYLOAD_SCHEMA,
)
from python.tasks.validation import validate_payload
from services.common.policy_client import PolicyRequest
from src.core.config import cfg


@shared_task(
    bind=True, base=SafeTask, name="python.tasks.conversation_tasks.delegate",
    max_retries=3, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True,
    soft_time_limit=45, time_limit=60, rate_limit="60/m",
)
def delegate(self, payload: dict[str, Any], tenant_id: str, request_id: str) -> dict[str, Any]:
    """Authorize and record a delegation request."""
    validate_payload(DELEGATE_PAYLOAD_SCHEMA, payload)
    _run(_ensure_saga_schema())
    saga_id = _run(saga_manager.start("delegate", step="authorize",
        data={"request_id": request_id, "tenant": tenant_id, "payload": payload}))
    
    allowed = _run(policy_client.evaluate(PolicyRequest(
        tenant=tenant_id, persona_id=payload.get("persona_id"), action="delegate.task",
        resource=str(payload.get("target") or payload.get("task") or "delegate"),
        context={"request_id": request_id})))
    
    if not allowed:
        _run(saga_manager.fail(saga_id, "policy_denied"))
        _run(run_compensation("delegate", saga_id, {"reason": "policy_denied"}))
        raise PermissionError("delegate.task denied by policy")

    if not _dedupe_once(f"delegate:{request_id}", ttl=3600):
        _run(saga_manager.update(saga_id, step="dedupe", status="duplicate", data={"request_id": request_id}))
        _run(run_compensation("delegate", saga_id, {"reason": "duplicate"}))
        return {"status": "duplicate", "request_id": request_id, "saga_id": saga_id}

    session_id = payload.get("session_id") or request_id
    event_id = str(uuid.uuid4())
    event = {"type": "delegate_request", "event_id": event_id, "session_id": session_id,
             "tenant": tenant_id, "persona_id": payload.get("persona_id"), "payload": payload,
             "metadata": {"source": "celery.delegate"}, "saga_id": saga_id}
    _append_event_sync(session_id, event)
    
    if publisher:
        headers = build_headers(tenant=tenant_id, session_id=session_id, persona_id=payload.get("persona_id"),
                               event_type="delegate_request", event_id=event_id, correlation=request_id)
        _run(publisher.publish(cfg.env("AUDIT_TOPIC", "audit.events"),
            {**event, "correlation_id": headers["correlation_id"]}, headers=headers,
            dedupe_key=idempotency_key(event, seed=request_id), session_id=session_id, tenant=tenant_id))
    
    _run(saga_manager.update(saga_id, step="recorded", status="accepted", data={"event_id": event_id}))
    return {"status": "accepted", "event_id": event_id, "saga_id": saga_id}


@shared_task(
    bind=True, base=SafeTask, name="python.tasks.conversation_tasks.build_context",
    max_retries=2, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True,
    soft_time_limit=30, time_limit=45,
)
def build_context(self, tenant_id: str, session_id: str) -> dict[str, Any]:
    """Record a context build trigger for the session."""
    event_id = str(uuid.uuid4())
    event = {"type": "context_build_requested", "event_id": event_id, "session_id": session_id,
             "tenant": tenant_id, "metadata": {"source": "celery.build_context"}}
    _append_event_sync(session_id, event)
    return {"status": "queued", "event_id": event_id}


@shared_task(
    bind=True, base=SafeTask, name="python.tasks.conversation_tasks.store_interaction",
    max_retries=2, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True,
    soft_time_limit=30, time_limit=45,
)
def store_interaction(self, session_id: str, interaction: dict[str, Any]) -> dict[str, Any]:
    """Persist a conversation interaction into the session timeline."""
    validate_payload(STORE_INTERACTION_PAYLOAD_SCHEMA, {"session_id": session_id, "interaction": interaction})
    _enforce_policy("store_interaction", interaction.get("tenant_id", "unknown"), "store_interaction",
                   {"name": "store_interaction", "session_id": session_id, "tenant": interaction.get("tenant_id")})
    event_id = str(uuid.uuid4())
    interaction = dict(interaction or {})
    interaction.setdefault("event_id", event_id)
    interaction.setdefault("session_id", session_id)
    interaction.setdefault("type", "interaction")
    _append_event_sync(session_id, interaction)
    return {"stored": True, "event_id": event_id}


@shared_task(
    bind=True, base=SafeTask, name="python.tasks.conversation_tasks.feedback_loop",
    max_retries=2, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True,
    soft_time_limit=30, time_limit=45,
)
def feedback_loop(self, session_id: str, feedback: dict[str, Any]) -> dict[str, Any]:
    """Persist feedback for later analysis and model learning."""
    validate_payload(FEEDBACK_LOOP_PAYLOAD_SCHEMA, {"session_id": session_id, "feedback": feedback})
    _enforce_policy("feedback_loop", feedback.get("tenant_id", "unknown"), "feedback_loop",
                   {"name": "feedback_loop", "session_id": session_id, "tenant": feedback.get("tenant_id")})
    event_id = str(uuid.uuid4())
    payload = {"type": "feedback", "event_id": event_id, "session_id": session_id,
               "payload": feedback, "metadata": {"source": "celery.feedback"}}
    _append_event_sync(session_id, payload)
    return {"stored": True, "event_id": event_id}
