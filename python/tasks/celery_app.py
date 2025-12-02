"""
Celery app configuration for SomaAgent01.
REAL IMPLEMENTATION - Production-ready Celery configuration.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable

from celery import Celery
from celery import signals

from python.tasks.config import get_celery_settings, celery_conf_overrides
from python.tasks.config import create_redis_client
from services.common.task_registry import TaskRegistry

LOGGER = logging.getLogger(__name__)

# REAL IMPLEMENTATION - Celery app configuration
_settings = get_celery_settings()
app = Celery(
    "somaagent01",
    broker=_settings.broker_url,
    backend=_settings.result_backend,
    include=[
        "python.tasks.a2a_chat_task",
        "python.tasks.core_tasks",
    ],
)

# REAL IMPLEMENTATION - Celery configuration (shared helper guarantees parity)
app.conf.update(celery_conf_overrides())

# Beat schedule (DB scheduler compatible)
app.conf.beat_schedule = {
    "publish-metrics-every-minute": {
        "task": "python.tasks.core_tasks.publish_metrics",
        "schedule": 60.0,
    },
    "cleanup-expired-sessions-hourly": {
        "task": "python.tasks.core_tasks.cleanup_sessions",
        "schedule": 3600.0,
    },
}

# ---------------------------------------------------------------------------
# Dynamic task registry integration
# ---------------------------------------------------------------------------
_registry = TaskRegistry()
_redis_client = create_redis_client()


def _dedupe_once(key: str, ttl: int = 3600) -> bool:
    try:
        if _redis_client.setnx(key, 1):
            _redis_client.expire(key, ttl)
            return True
        return False
    except Exception:
        return True


def _wrap_entry(entry, fn: Callable) -> Callable:
    """Create a Celery task wrapper that enforces policy, schema, and dedupe."""

    @app.task(
        bind=True,
        name=entry.name,
        queue=entry.queue,
        rate_limit=entry.rate_limit,
        max_retries=entry.max_retries or 3,
        soft_time_limit=entry.soft_time_limit or 300,
        time_limit=entry.time_limit or 360,
        autoretry_for=(Exception,),
        retry_backoff=True,
        retry_jitter=True,
    )
    def _task(self, *args, **kwargs):
        tenant = kwargs.get("tenant_id") or kwargs.get("tenant")
        persona = kwargs.get("persona_id") or kwargs.get("persona")
        if tenant:
            allowed = asyncio.run(_registry.allowed_for(entry, tenant, persona, action="task.run"))
            if not allowed:
                raise PermissionError("task.run denied by policy")
        _registry.validate_args(entry, kwargs)
        req_id = kwargs.get("request_id") or kwargs.get("id")
        if req_id:
            if not _dedupe_once(f"dyn:{entry.name}:{req_id}"):
                return {"status": "duplicate", "request_id": req_id}
        return fn(*args, **kwargs)

    return _task


def register_dynamic_tasks(*, force_refresh: bool = False) -> int:
    """Load registry entries and register Celery tasks at runtime."""
    try:
        entries = asyncio.run(_registry.load_all(force_refresh=force_refresh))
    except Exception as exc:  # pragma: no cover - startup diagnostics only
        LOGGER.error("Failed to load task registry", exc_info=exc)
        return 0

    registered = 0
    for entry in entries:
        try:
            _registry.verify_artifact(entry)
            fn = _registry.import_callable(entry)
            task = _wrap_entry(entry, fn)
            app.tasks.register(task)
            registered += 1
        except Exception as exc:  # pragma: no cover - defensive logging
            LOGGER.error("Failed to register dynamic task", extra={"task": entry.name, "error": str(exc)})
    return registered


@signals.after_setup_task_logger.connect
def _load_registry_on_start(**kwargs: Any):
    register_dynamic_tasks(force_refresh=True)


@app.control.command(name="task_registry.reload")
def reload_registry(**kwargs):
    """Remote control command to force reload on a worker."""
    return {"reloaded": register_dynamic_tasks(force_refresh=True)}

if __name__ == "__main__":
    app.start()
