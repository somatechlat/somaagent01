"""
Celery app configuration for SomaAgent01.
REAL IMPLEMENTATION - Production-ready Celery configuration.
"""

from __future__ import annotations

from celery import Celery

from python.tasks.config import celery_conf_overrides, get_celery_settings

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

if __name__ == "__main__":
    app.start()
