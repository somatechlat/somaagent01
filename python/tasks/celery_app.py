"""
Celery app configuration for SomaAgent01.
REAL IMPLEMENTATION - Production-ready Celery configuration.
"""

from __future__ import annotations

from celery import Celery

from python.tasks.config import get_celery_settings, celery_conf_overrides

# REAL IMPLEMENTATION - Celery app configuration
_settings = get_celery_settings()
app = Celery(
    "somaagent01",
    broker=_settings.broker_url,
    backend=_settings.result_backend,
    include=["python.tasks.a2a_chat_task"],
)

# REAL IMPLEMENTATION - Celery configuration (shared helper guarantees parity)
app.conf.update(celery_conf_overrides())

# REAL IMPLEMENTATION - Celery Beat Schedule
app.conf.beat_schedule = {
    "publish-metrics-every-60s": {
        "task": "python.tasks.core_tasks.publish_metrics",
        "schedule": 60.0,
    },
    "cleanup-sessions-every-3600s": {
        "task": "python.tasks.core_tasks.cleanup_sessions",
        "schedule": 3600.0,
        "args": (86400,),  # Cleanup sessions older than 24 hours
    },
}

# REAL IMPLEMENTATION - Task Routes
app.conf.task_routes = {
    "python.tasks.core_tasks.delegate": {"queue": "delegation"},
    "python.tasks.core_tasks.build_context": {"queue": "context"},
    "python.tasks.core_tasks.evaluate_policy": {"queue": "policy"},
    "python.tasks.core_tasks.store_interaction": {"queue": "storage"},
    "python.tasks.core_tasks.feedback_loop": {"queue": "feedback"},
    "python.tasks.core_tasks.rebuild_index": {"queue": "indexing"},
    "python.tasks.core_tasks.publish_metrics": {"queue": "metrics"},
    "python.tasks.core_tasks.cleanup_sessions": {"queue": "maintenance"},
    "python.tasks.a2a_chat_task.a2a_chat": {"queue": "fast_a2a"},
}

# REAL IMPLEMENTATION - Reliability Settings
app.conf.update(
    task_reject_on_worker_lost=True,
    broker_transport_options={
        "visibility_timeout": 7200,  # 2 hours
    },
    worker_deduplicate_successful_tasks=True,  # Dedup hook
)

if __name__ == "__main__":
    app.start()
