"""Audit Store — persistent audit event storage.

VIBE COMPLIANT: Uses Django ORM exclusively.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from services.common.store_base import BaseStore

LOGGER = logging.getLogger(__name__)


class AuditStore(BaseStore[Dict[str, Any]]):
    """Django ORM-backed store for audit events."""

    async def ensure_schema(self) -> None:
        """Schema managed by Django migrations."""
        pass

    async def record(
        self,
        event_type: str,
        actor: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Persist an audit event."""
        from admin.aaas.models import AuditLog

        await AuditLog.objects.acreate(
            action=event_type,
            actor_id=actor or None,
            resource_type=resource or "",
            resource_id=resource or None,
            new_value=payload or {},
        )

    async def get(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single audit event by ID."""
        from admin.aaas.models import AuditLog

        event = await AuditLog.objects.filter(id=identifier).afirst()
        if not event:
            return None
        return {
            "id": str(event.id),
            "event_type": event.action,
            "actor": str(event.actor_id) if event.actor_id else None,
            "resource": event.resource_type,
            "action": event.action,
            "payload": event.new_value,
            "created_at": event.created_at.isoformat() if event.created_at else None,
        }

    async def list(
        self,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List audit events."""
        from admin.aaas.models import AuditLog

        qs = AuditLog.objects.all().order_by("-created_at")
        if event_type:
            qs = qs.filter(action=event_type)
        qs = qs[:limit]

        results = []
        async for event in qs:
            results.append(
                {
                    "id": str(event.id),
                    "event_type": event.action,
                    "actor": str(event.actor_id) if event.actor_id else None,
                    "resource": event.resource_type,
                    "action": event.action,
                    "payload": event.new_value,
                    "created_at": event.created_at.isoformat() if event.created_at else None,
                }
            )
        return results

    async def create(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Persist a new audit event."""
        await self.record(
            event_type=record.get("event_type", "unknown"),
            actor=record.get("actor"),
            resource=record.get("resource"),
            action=record.get("action"),
            payload=record.get("payload"),
        )
        return record

    async def update(self, identifier: str, changes: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Audit events are immutable."""
        raise RuntimeError("Audit events are immutable")

    async def delete(self, identifier: str) -> bool:
        """Remove an audit event."""
        from admin.aaas.models import AuditLog

        deleted, _ = await AuditLog.objects.filter(id=identifier).adelete()
        return deleted > 0


def from_env() -> AuditStore:
    """Create an AuditStore from environment variables."""
    return AuditStore()
