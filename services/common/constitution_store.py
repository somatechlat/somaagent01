"""Constitution store — persistent constitution/rule storage.

VIBE COMPLIANT: Uses Django ORM exclusively.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from services.common.store_base import BaseStore

LOGGER = logging.getLogger(__name__)


class ConstitutionStore(BaseStore[dict[str, Any]]):
    """Django ORM-backed store for agent constitutions."""

    async def ensure_schema(self) -> None:
        """Schema managed by Django migrations."""
        pass

    async def get(self, tenant_id: str) -> Optional[dict[str, Any]]:
        """Retrieve the active constitution."""
        from admin.core.models import Constitution

        constitution = await Constitution.objects.filter(is_active=True).afirst()
        if not constitution:
            return None
        return {
            "tenant_id": tenant_id,
            "rules": constitution.content,
            "updated_at": constitution.created_at.isoformat() if constitution.created_at else None,
        }

    async def create(self, record: dict[str, Any]) -> dict[str, Any]:
        """Persist a new constitution."""
        from admin.core.models import Constitution

        obj = await Constitution.objects.acreate(
            content=record.get("rules", {}),
            version="1.0.0",
            content_hash="",
            signature="",
        )
        return {
            "tenant_id": record.get("tenant_id", "default"),
            "rules": obj.content,
            "updated_at": obj.created_at.isoformat() if obj.created_at else None,
        }

    async def update(self, identifier: str, changes: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Apply partial updates."""
        from admin.core.models import Constitution

        constitution = await Constitution.objects.filter(is_active=True).afirst()
        if not constitution:
            return None
        rules = changes.get("rules")
        if rules is not None:
            constitution.content = rules
        await constitution.asave()
        return {
            "tenant_id": identifier,
            "rules": constitution.content,
            "updated_at": constitution.created_at.isoformat() if constitution.created_at else None,
        }

    async def delete(self, identifier: str) -> bool:
        """Remove a constitution."""
        from admin.core.models import Constitution

        deleted, _ = await Constitution.objects.filter(is_active=True).adelete()
        return deleted > 0
