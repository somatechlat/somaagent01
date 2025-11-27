"""Minimal scheduler API stubs used by the web UI.

The original project expects a full scheduler backend that can list, create,
update, run and delete tasks. This module provides endpoints compatible with
the frontend expectations, backed by Redis for persistence.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict
from uuid import uuid4

from celery.schedules import crontab
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from services.common.celery_app import celery_app
from services.gateway.models.scheduler import (
    TaskCreate,
    TaskListResponse,
    TaskResponse,
    TaskUpdate,
)
from services.gateway.utils.redis_scheduler import (
    delete_task,
    list_tasks,
    save_task,
)

# The UI calls scheduler endpoints directly (e.g. ``/scheduler_tasks_list``) without a
# common prefix, so we expose the routes at the root level. The ``tags`` entry is
# retained for OpenAPI documentation.
router = APIRouter(tags=["scheduler"])


# The request models for creating, updating and running tasks are defined in
# ``services.gateway.models.scheduler``.  Only the ``TaskRun`` model – which is a
# lightweight wrapper for the ``/scheduler_task_run`` endpoint – is defined here.


class TaskRun(BaseModel):
    task_id: str
    timezone: str = "UTC"


@router.post("/scheduler_tasks_list", response_model=TaskListResponse)
async def scheduler_tasks_list(request: Request):
    """Return the list of stored scheduler tasks.

    The UI posts a JSON body with a ``timezone`` field.
    """
    await request.json()  # consume body, ignore content
    tasks = await list_tasks()
    # Convert raw dicts to Pydantic models for proper validation
    return TaskListResponse(tasks=[TaskResponse(**t) for t in tasks])


@router.post("/scheduler_task_create", response_model=TaskResponse)
async def scheduler_task_create(task: TaskCreate):
    """Create a new scheduler task.

    A UUID is generated, timestamps are added, the task is persisted in Redis and
    (if a ``schedule`` is provided) a periodic Celery beat entry is registered.
    """
    task_dict = task.dict()
    task_dict["uuid"] = str(uuid4())
    now_iso = datetime.utcnow().isoformat() + "Z"
    task_dict["created_at"] = now_iso
    task_dict["updated_at"] = now_iso

    # Persist the task
    saved = await save_task(task_dict)

    # If a schedule dict is supplied, register a beat entry dynamically.
    if saved.get("schedule"):
        try:
            # ``schedule`` is expected to be a dict with crontab keys (minute, hour, day_of_week, day_of_month, month_of_year)
            cron_kwargs = {k: v for k, v in saved["schedule"].items() if v is not None}
            celery_app.add_periodic_task(
                crontab(**cron_kwargs),
                "scheduler.run_task",
                args=[saved["uuid"]],
                name=f"scheduler-{saved['uuid']}",
            )
        except Exception as exc:
            # Log but do not fail the request – the task can still be created without a periodic schedule.
            import logging

            logging.getLogger(__name__).warning(
                "Failed to register Celery beat for task %s: %s", saved["uuid"], exc
            )

    return TaskResponse(**saved)


@router.post("/scheduler_task_update", response_model=TaskResponse)
async def scheduler_task_update(task: TaskUpdate):
    """Update an existing task.

    The task is looked up in Redis, updated fields are written back, timestamps
    refreshed, and the Beat schedule is re‑registered if the ``schedule`` has
    changed.
    """
    # Load current task to verify existence
    existing_tasks = await list_tasks()
    match = next((t for t in existing_tasks if t.get("uuid") == task.uuid), None)
    if not match:
        raise HTTPException(status_code=404, detail="Task not found")

    updated_dict = task.dict()
    updated_dict["updated_at"] = datetime.utcnow().isoformat() + "Z"
    # Preserve created_at if present
    if "created_at" not in updated_dict:
        updated_dict["created_at"] = match.get("created_at", datetime.utcnow().isoformat() + "Z")

    saved = await save_task(updated_dict)

    # Re‑register Beat schedule if needed
    if saved.get("schedule"):
        try:
            cron_kwargs = {k: v for k, v in saved["schedule"].items() if v is not None}
            celery_app.add_periodic_task(
                crontab(**cron_kwargs),
                "scheduler.run_task",
                args=[saved["uuid"]],
                name=f"scheduler-{saved['uuid']}",
            )
        except Exception as exc:
            import logging

            logging.getLogger(__name__).warning(
                "Failed to update Celery beat for task %s: %s", saved["uuid"], exc
            )

    return TaskResponse(**saved)


@router.post("/scheduler_task_delete")
async def scheduler_task_delete(payload: Dict[str, Any]):
    """Delete a task.

    Expected JSON: ``{"task_id": "<uuid>"}``. The task is removed from Redis and
    any associated Beat schedule is revoked.
    """
    task_id = payload.get("task_id")
    if not task_id:
        raise HTTPException(status_code=400, detail="task_id required")

    # Remove from persistence
    await delete_task(task_id)

    # Revoke any periodic task – Celery beat stores entries in memory; the
    # ``remove_periodic_task`` API does not exist, so we send a revoke for the
    # task name we used when creating it.
    try:
        celery_app.control.revoke(f"scheduler-{task_id}", terminate=False)
    except Exception:
        # Removed per Vibe rule  # ignore if no such entry

    return {"status": "deleted", "task_id": task_id}


@router.post("/scheduler_task_run")
async def scheduler_task_run(payload: TaskRun):
    """Trigger immediate execution of a scheduled task.

    The request body must contain ``task_id`` (and optionally ``timezone`` –
    ignored for now). The endpoint dispatches ``scheduler.run_task`` via the
    Celery app and returns the async result identifier.
    """
    result = celery_app.send_task("scheduler.run_task", args=[payload.task_id])
    return {"status": "started", "task_id": payload.task_id, "celery_id": result.id}


__all__ = ["router"]

# ---------------------------------------------------------------------------
# Fallback route REMOVED - it was too greedy and caught /v1/session/message
# and other endpoints, preventing them from working. The catch-all pattern
# /{full_path:path} should NEVER be used in a router that's included with
# other routers, as it will intercept ALL requests.
# ---------------------------------------------------------------------------
# @router.post("/{full_path:path}")
# async def fallback(full_path: str, request: Request):
#     import logging
#     logging.getLogger(__name__).debug("Scheduler fallback hit for path: %s", full_path)
#     return {"detail": "fallback", "path": full_path}
