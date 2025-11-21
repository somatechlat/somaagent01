"""Celery application factory for SomaAgent01 (Celery-only architecture).

Uses Redis for broker and result backend, pulling configuration from the
centralized config (src.core.config). This module is imported by both workers
and API routers to enqueue tasks.
"""

from __future__ import annotations

from celery import Celery
from src.core.config import cfg


def create_celery_app() -> Celery:
    broker = cfg.env("CELERY_BROKER_URL", "redis://localhost:6379/0")
    backend = cfg.env("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
    app = Celery("somaagent01", broker=broker, backend=backend)
    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone=cfg.env("TZ", "UTC"),
        enable_utc=True,
        worker_prefetch_multiplier=int(cfg.env("CELERY_PREFETCH", 4)),
        task_acks_late=True,
        task_acks_on_failure_or_timeout=True,
        task_reject_on_worker_lost=True,
        task_default_queue="default",
        broker_transport_options={
            "visibility_timeout": int(cfg.env("CELERY_VISIBILITY_TIMEOUT", 7200))
        },
        result_expires=int(cfg.env("CELERY_RESULT_EXPIRES", 86400)),
    )

    # Task routing per queue (configurable via env overrides).
    app.conf.task_routes = {
        "services.celery_worker.tasks.delegate*": {"queue": cfg.env("CELERY_QUEUE_DELEGATION", "delegation")},
        "services.celery_worker.tasks.browser*": {"queue": cfg.env("CELERY_QUEUE_BROWSER", "browser")},
        "services.celery_worker.tasks.code*": {"queue": cfg.env("CELERY_QUEUE_CODE", "code")},
        "services.celery_worker.tasks.heavy*": {"queue": cfg.env("CELERY_QUEUE_HEAVY", "heavy")},
    }

    app.autodiscover_tasks(["services.celery_worker"])
    return app


celery_app = create_celery_app()


__all__ = ["celery_app", "create_celery_app"]
