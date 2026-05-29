"""DLQ Store — persistent dead-letter queue storage.

VIBE COMPLIANT: Uses Django ORM exclusively.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from services.common.store_base import BaseStore

LOGGER = logging.getLogger(__name__)


class DLQStore(BaseStore[Dict[str, Any]]):
    """Django ORM-backed store for dead-letter events."""

    def __init__(self) -> None:
        pass

    async def ensure_schema(self) -> None:
        """Schema managed by Django migrations."""
        pass

    async def add(
        self,
        topic: str,
        event: Dict[str, Any],
        error: Optional[str] = None,
    ) -> None:
        """Persist a dead-letter event."""
        from admin.core.models import DeadLetterMessage

        await DeadLetterMessage.objects.acreate(
            original_topic=topic,
            payload=event,
            headers={},
            error_message=error or "",
            idempotency_key=event.get("id", ""),
        )

    async def get(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Retrieve a DLQ entry by ID."""
        from admin.core.models import DeadLetterMessage

        msg = await DeadLetterMessage.objects.filter(id=identifier).afirst()
        if not msg:
            return None
        return {
            "id": str(msg.id),
            "topic": msg.original_topic,
            "event": msg.payload,
            "error": msg.error_message,
            "created_at": msg.created_at.isoformat() if msg.created_at else None,
        }

    async def list(
        self,
        topic: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List dead-letter events."""
        from admin.core.models import DeadLetterMessage

        qs = DeadLetterMessage.objects.all().order_by("-created_at")
        if topic:
            qs = qs.filter(original_topic=topic)
        qs = qs[:limit]

        results = []
        async for msg in qs:
            results.append(
                {
                    "id": str(msg.id),
                    "topic": msg.original_topic,
                    "event": msg.payload,
                    "error": msg.error_message,
                    "created_at": msg.created_at.isoformat() if msg.created_at else None,
                }
            )
        return results

    async def create(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Persist a dead-letter event."""
        await self.add(
            topic=record.get("topic", "unknown"),
            event=record.get("event", {}),
            error=record.get("error"),
        )
        return record

    async def update(self, identifier: str, changes: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a DLQ entry (e.g., mark resolved)."""
        from admin.core.models import DeadLetterMessage

        msg = await DeadLetterMessage.objects.filter(id=identifier).afirst()
        if not msg:
            return None
        if "resolved" in changes:
            msg.resolved = changes["resolved"]
        if "error" in changes:
            msg.error_message = changes["error"]
        await msg.asave()
        return await self.get(identifier)

    async def delete(self, identifier: str) -> bool:
        """Remove a DLQ entry."""
        from admin.core.models import DeadLetterMessage

        deleted, _ = await DeadLetterMessage.objects.filter(id=identifier).adelete()
        return deleted > 0


async def ensure_schema(store: DLQStore) -> None:
    """No-op: schema managed by Django migrations."""
    pass
