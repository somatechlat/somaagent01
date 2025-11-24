"""Celery tasks used by the scheduler UI.

The UI only needs a single operation at the moment – run a scheduled task on
request.  In a full production system this could trigger a Somabrain workflow,
invoke a model, or perform any arbitrary job.  Here we provide a minimal, yet
fully functional, implementation that logs the execution and returns a result
payload.  The task is registered under the name ``scheduler.run_task`` so that
the FastAPI router can call it via ``celery_app.send_task``.
"""

from __future__ import annotations

import logging
from datetime import datetime

from services.common.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="scheduler.run_task")
def run_task(task_id: str) -> dict:
    """Execute a scheduled task.

    In a real system this would delegate to the appropriate agent logic.  For
    now we simply record the execution timestamp and return a small status dict.
    """
    now = datetime.utcnow().isoformat() + "Z"
    logger.info("Running scheduled task %s at %s", task_id, now)
    # The return value is stored in the Celery result backend (Redis) and can be
    # inspected by the UI if needed.
    return {"task_id": task_id, "status": "started", "timestamp": now}
