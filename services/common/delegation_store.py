"""Delegation Store — persistent task delegation storage.

VIBE COMPLIANT: Uses Django ORM exclusively.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from services.common.store_base import BaseStore

LOGGER = logging.getLogger(__name__)


class DelegationStore(BaseStore[Dict[str, Any]]):
    """Django ORM-backed store for delegation tasks."""

    async def ensure_schema(self) -> None:
        """Schema managed by Django migrations."""
        pass

    async def get(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a task by ID."""
        from admin.core.models import DelegationTask

        task = await DelegationTask.objects.filter(task_id=task_id).afirst()
        if not task:
            return None
        return {
            "task_id": task.task_id,
            "payload": task.payload,
            "status": task.status,
            "callback_url": task.callback_url,
            "metadata": task.metadata,
            "result": task.result,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        }

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Alias for get()."""
        return await self.get(task_id)

    async def create(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Persist a delegation task."""
        from admin.core.models import DelegationTask

        obj = await DelegationTask.objects.acreate(
            task_id=record["task_id"],
            payload=record.get("payload", {}),
            status=record.get("status", "received"),
            callback_url=record.get("callback_url"),
            metadata=record.get("metadata"),
            result=record.get("result"),
        )
        return {
            "task_id": obj.task_id,
            "payload": obj.payload,
            "status": obj.status,
            "callback_url": obj.callback_url,
            "metadata": obj.metadata,
            "result": obj.result,
            "created_at": obj.created_at.isoformat() if obj.created_at else None,
            "updated_at": obj.updated_at.isoformat() if obj.updated_at else None,
        }

    async def create_task(
        self,
        task_id: str,
        payload: Dict[str, Any],
        status: str = "received",
        callback_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a delegation task (API-facing alias)."""
        return await self.create(
            {
                "task_id": task_id,
                "payload": payload,
                "status": status,
                "callback_url": callback_url,
                "metadata": metadata,
            }
        )

    async def update(self, task_id: str, changes: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update task status and result."""
        from admin.core.models import DelegationTask

        task = await DelegationTask.objects.filter(task_id=task_id).afirst()
        if not task:
            return None
        if "status" in changes:
            task.status = changes["status"]
        if "result" in changes:
            task.result = changes["result"]
        if "payload" in changes:
            task.payload = changes["payload"]
        if "callback_url" in changes:
            task.callback_url = changes["callback_url"]
        if "metadata" in changes:
            task.metadata = changes["metadata"]
        await task.asave()
        return await self.get(task_id)

    async def update_task(
        self,
        task_id: str,
        status: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Optional[Dict[str, Any]]:
        """Alias for update()."""
        changes: Dict[str, Any] = dict(kwargs)
        if status is not None:
            changes["status"] = status
        if result is not None:
            changes["result"] = result
        return await self.update(task_id, changes)

    async def delete(self, task_id: str) -> bool:
        """Remove a task."""
        from admin.core.models import DelegationTask

        deleted, _ = await DelegationTask.objects.filter(task_id=task_id).adelete()
        return deleted > 0

    async def list(
        self,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List delegation tasks."""
        from admin.core.models import DelegationTask

        qs = DelegationTask.objects.all()
        if status:
            qs = qs.filter(status=status)
        qs = qs.order_by("-created_at")[:limit]

        results = []
        async for task in qs:
            results.append(
                {
                    "task_id": task.task_id,
                    "payload": task.payload,
                    "status": task.status,
                    "callback_url": task.callback_url,
                    "metadata": task.metadata,
                    "result": task.result,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "updated_at": task.updated_at.isoformat() if task.updated_at else None,
                }
            )
        return results
