"""Helper functions for persisting scheduler tasks in Redis.

The repository already uses Redis for session caching (see
``services.common.session_repository.RedisSessionCache``).  We reuse the same
client to store each task as a Redis hash under ``scheduler:task:{uuid}`` and keep a
set ``scheduler:tasks`` with all UUIDs.  This approach requires no database
migration and works out‑of‑the‑box with the existing Redis service defined in
``docker‑compose.yaml``.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List

from services.common.session_repository import RedisSessionCache

_cache = RedisSessionCache()
_TASK_SET = "scheduler:tasks"
_TASK_KEY_PREFIX = "scheduler:task:"


def _task_key(task_id: str) -> str:
    return f"{_TASK_KEY_PREFIX}{task_id}"


async def list_tasks() -> List[Dict[str, Any]]:
    """Return all stored tasks as Python dictionaries.

    The UI expects a list of objects with the fields defined in
    ``services.gateway.models.scheduler.TaskResponse``.  We load the raw hash from
    Redis, decode JSON fields (``schedule``, ``plan``, ``attachments``) and return
    a clean dict.
    """
    task_ids = await _cache._client.smembers(_TASK_SET)
    tasks: List[Dict[str, Any]] = []
    for raw_id in task_ids:
        task_id = raw_id.decode() if isinstance(raw_id, bytes) else raw_id
        data = await _cache._client.hgetall(_task_key(task_id))
        if not data:
            continue
        # Decode bytes -> appropriate Python types
        task: Dict[str, Any] = {k.decode(): v.decode() for k, v in data.items()}
        # JSON fields need to be parsed back to objects
        for json_field in ("schedule", "plan", "attachments"):
            if task.get(json_field):
                try:
                    task[json_field] = json.loads(task[json_field])
                except json.JSONDecodeError:
                    # Keep raw string if it is not valid JSON – defensive.
                    pass
        # Convert timestamps back to datetime objects (ISO strings are fine for UI)
        tasks.append(task)
    return tasks


async def save_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """Persist a new or updated task.

    If ``uuid`` is missing a new UUID is generated.  All values are stored as
    strings; complex objects are JSON‑encoded.
    """
    task_id = task.get("uuid") or str(uuid.uuid4())
    task["uuid"] = task_id
    now_iso = datetime.utcnow().isoformat() + "Z"
    task.setdefault("created_at", now_iso)
    task["updated_at"] = now_iso

    # Prepare a flat dict where each value is a string; JSON‑encode complex types.
    flat: Dict[str, str] = {}
    for k, v in task.items():
        if isinstance(v, (dict, list)):
            flat[k] = json.dumps(v)
        else:
            flat[k] = str(v)

    print(f"DEBUG: Saving task {task_id} to Redis at {_task_key(task_id)}")
    print(f"DEBUG: Redis client: {_cache._client}")
    await _cache._client.hmset(_task_key(task_id), flat)
    await _cache._client.sadd(_TASK_SET, task_id)
    print("DEBUG: Task saved.")
    return task


async def delete_task(task_id: str) -> None:
    """Remove a task from Redis.

    The function deletes the hash and removes the ID from the set.
    """
    await _cache._client.delete(_task_key(task_id))
    await _cache._client.srem(_TASK_SET, task_id)
