"""Memory and index-related Celery tasks."""
from __future__ import annotations

import uuid
from typing import Any

from celery import shared_task

from python.tasks.core_tasks import (
    _append_event_sync,
    _enforce_policy,
    _run,
    build_headers,
    idempotency_key,
    policy_client,
    publisher,
    run_compensation,
    SafeTask,
    saga_manager,
)
from python.tasks.schemas import EVALUATE_POLICY_ARGS_SCHEMA, REBUILD_INDEX_ARGS_SCHEMA
from python.tasks.validation import validate_payload
from services.common.policy_client import PolicyRequest
from src.core.config import cfg


@shared_task(
    bind=True, base=SafeTask, name="python.tasks.memory_tasks.rebuild_index",
    max_retries=1, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True,
    soft_time_limit=60, time_limit=90,
)
def rebuild_index(self, tenant_id: str) -> dict[str, Any]:
    """Log an index rebuild request for the tenant."""
    validate_payload(REBUILD_INDEX_ARGS_SCHEMA, {"tenant_id": tenant_id})
    _enforce_policy("rebuild_index", tenant_id, "rebuild_index", {"name": "rebuild_index", "tenant": tenant_id})
    event_id = str(uuid.uuid4())
    session_id = f"rebuild-{tenant_id}"
    payload = {"type": "rebuild_index", "event_id": event_id, "session_id": session_id,
               "tenant": tenant_id, "metadata": {"source": "celery.rebuild_index"}}
    _append_event_sync(session_id, payload)
    return {"queued": True, "event_id": event_id}


@shared_task(
    bind=True, base=SafeTask, name="python.tasks.memory_tasks.evaluate_policy",
    max_retries=2, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True,
    soft_time_limit=20, time_limit=30,
)
def evaluate_policy(self, tenant_id: str, action: str, resource: dict[str, Any]) -> dict[str, Any]:
    """Evaluate an OPA policy decision and record it."""
    validate_payload(EVALUATE_POLICY_ARGS_SCHEMA, {"tenant_id": tenant_id, "action": action, "resource": resource})
    decision = _run(policy_client.evaluate(PolicyRequest(
        tenant=tenant_id, persona_id=resource.get("persona_id"), action=action,
        resource=resource.get("name") or str(resource), context=resource)))
    
    event_id = str(uuid.uuid4())
    event = {"type": "policy_decision", "event_id": event_id,
             "session_id": resource.get("session_id") or resource.get("id") or event_id,
             "tenant": tenant_id, "decision": decision, "action": action, "resource": resource,
             "metadata": {"source": "celery.evaluate_policy"}}
    _append_event_sync(event["session_id"], event)
    
    saga_id = resource.get("saga_id")
    if saga_id:
        _run(saga_manager.update(saga_id, step="policy_decision",
             status="allowed" if decision else "denied", data={"action": action, "resource": resource}))
        if not decision:
            _run(run_compensation("delegate", saga_id, {"reason": "policy_denied"}))
    
    if publisher:
        headers = build_headers(tenant=tenant_id, session_id=event["session_id"],
                               persona_id=resource.get("persona_id"), event_type="policy_decision", event_id=event_id)
        _run(publisher.publish(cfg.env("AUDIT_TOPIC", "audit.events"),
            {**event, "correlation_id": headers["correlation_id"]}, headers=headers,
            dedupe_key=idempotency_key(event), session_id=event["session_id"], tenant=tenant_id))
    
    return {"allowed": decision, "event_id": event_id}
