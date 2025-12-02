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

# ---------------------------------------------------------------
# Worker metrics endpoint (Prometheus)
# ---------------------------------------------------------------
# Expose a /metrics HTTP endpoint on each Celery worker for observability.
# The port can be overridden via the SA01_WORKER_METRICS_PORT env variable.
from prometheus_client import start_http_server
from src.core.config import cfg


def _start_worker_metrics() -> None:
    """Start a Prometheus metrics HTTP server for the worker process.

    This function is invoked via the Celery ``worker_process_init`` signal so
    that each forked worker process runs its own server without interfering
    with the main process.  The default port ``8000`` is safe for local dev;
    production deployments should set ``SA01_WORKER_METRICS_PORT`` to avoid
    collisions.
    """
    port = int(cfg.env("SA01_WORKER_METRICS_PORT", "8000"))
    # ``start_http_server`` is idempotent – calling it multiple times on the
    # same port raises a ``OSError``; we guard against that by catching the
    # exception and logging.
    try:
        start_http_server(port)
        LOGGER.info("Prometheus worker metrics server started on port %s", port)
    except OSError as exc:
        LOGGER.warning(
            "Prometheus worker metrics server could not start on port %s: %s",
            port,
            exc,
        )


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

# ---------------------------------------------------------------------------
# VIBE‑COMPLIANT EXTENSIONS
# ---------------------------------------------------------------------------
# 1. Visibility timeout – ensures tasks are re‑queued if a worker dies.
# 2. Reject on worker lost – forces re‑queue on worker failure.
# 3. Task routes – explicit routing to dedicated queues per architecture guide.
# These settings are added on top of the existing configuration.

app.conf.update(
    broker_transport_options={
        "visibility_timeout": 7200,  # 2 hours as required by VIBE spec
    },
    task_reject_on_worker_lost=True,
    task_routes={
        "python.tasks.core_tasks.delegate": {"queue": "delegation"},
        "python.tasks.core_tasks.build_context": {"queue": "fast_a2a"},
        "python.tasks.core_tasks.evaluate_policy": {"queue": "fast_a2a"},
        "python.tasks.core_tasks.store_interaction": {"queue": "fast_a2a"},
        "python.tasks.core_tasks.feedback_loop": {"queue": "fast_a2a"},
        "python.tasks.core_tasks.rebuild_index": {"queue": "heavy"},
        "python.tasks.core_tasks.publish_metrics": {"queue": "default"},
        "python.tasks.core_tasks.cleanup_sessions": {"queue": "default"},
        "a2a_chat": {"queue": "fast_a2a"},
    },
)

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
            LOGGER.error(
                "Failed to register dynamic task", extra={"task": entry.name, "error": str(exc)}
            )
    return registered


@signals.after_setup_task_logger.connect
def _load_registry_on_start(**kwargs: Any):
    register_dynamic_tasks(force_refresh=True)


# ---------------------------------------------------------------
# Start Prometheus metrics server in each Celery worker process.
# ---------------------------------------------------------------
@signals.worker_process_init.connect
def _init_worker_metrics(**kwargs: Any):
    _start_worker_metrics()


@app.control.command(name="task_registry.reload")
def reload_registry(**kwargs):
    """Remote control command to force reload on a worker."""
    return {"reloaded": register_dynamic_tasks(force_refresh=True)}


if __name__ == "__main__":
    app.start()
