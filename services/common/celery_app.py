"""Central Celery application used by the gateway and workers.

The repository already defines a Redis broker (see ``services/gateway`` and the
Docker compose file).  This module creates a single ``Celery`` instance that is
imported by the FastAPI router (to enqueue tasks) and by the Celery worker
process (started via ``docker compose``).  Keeping the app in ``services/common``
mirrors the existing pattern of shared utilities such as ``event_bus`` and
``outbox_repository``.
"""

from __future__ import annotations

from celery import Celery

from src.core.config import cfg

# Redis is the broker and result backend for the whole project (see
# ``docker-compose.yaml``).  ``cfg.settings().redis.url`` resolves to a fully
# qualified ``redis://`` URL.
_redis_url = cfg.settings().redis.url

celery_app = Celery(
    "soma",
    broker=_redis_url,
    backend=_redis_url,
    include=["services.gateway.tasks"],
)

# Minimal configuration – JSON is the default serializer for both tasks and
# results.  ``enable_utc`` and ``timezone`` follow the recommendations in the
# Celery docs (v5.5) and match the UI's expectation of UTC timestamps.
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

__all__ = ["celery_app"]
