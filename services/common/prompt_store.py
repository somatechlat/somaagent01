"""Prompt store — persistent prompt template storage.

VIBE COMPLIANT: Uses Django ORM exclusively.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from services.common.store_base import BaseStore

LOGGER = logging.getLogger(__name__)


class PromptStore(BaseStore[Dict[str, Any]]):
    """Django ORM-backed store for prompt templates."""

    async def ensure_schema(self) -> None:
        """Schema managed by Django migrations."""
        pass

    async def get(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a prompt template by name."""
        from admin.core.models import Prompt

        prompt = await Prompt.objects.filter(name=name).afirst()
        if not prompt:
            return None
        return {
            "name": prompt.name,
            "content": prompt.template,
            "description": prompt.metadata.get("description", ""),
            "updated_at": prompt.updated_at.isoformat() if prompt.updated_at else None,
        }

    async def get_prompt(self, name: str) -> Optional[str]:
        """Get prompt template content by name."""
        record = await self.get(name)
        return record.get("content") if record else None

    async def list(self) -> List[Dict[str, Any]]:
        """List all prompt templates."""
        from admin.core.models import Prompt

        prompts = []
        async for prompt in Prompt.objects.all():
            prompts.append(
                {
                    "name": prompt.name,
                    "content": prompt.template,
                    "description": prompt.metadata.get("description", ""),
                    "updated_at": prompt.updated_at.isoformat() if prompt.updated_at else None,
                }
            )
        return prompts

    async def create(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Persist a new prompt template."""
        from admin.core.models import Prompt

        meta = record.get("metadata", {})
        if "description" in record:
            meta["description"] = record["description"]
        obj = await Prompt.objects.acreate(
            name=record["name"],
            template=record.get("content", ""),
            metadata=meta,
            tenant=record.get("tenant", "default"),
        )
        return {
            "name": obj.name,
            "content": obj.template,
            "description": obj.metadata.get("description", ""),
            "updated_at": obj.updated_at.isoformat() if obj.updated_at else None,
        }

    async def update(self, identifier: str, changes: dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Apply partial updates."""
        from admin.core.models import Prompt

        prompt = await Prompt.objects.filter(name=identifier).afirst()
        if not prompt:
            return None
        if "content" in changes:
            prompt.template = changes["content"]
        if "description" in changes:
            prompt.metadata["description"] = changes["description"]
        await prompt.asave()
        return {
            "name": prompt.name,
            "content": prompt.template,
            "description": prompt.metadata.get("description", ""),
            "updated_at": prompt.updated_at.isoformat() if prompt.updated_at else None,
        }

    async def delete(self, identifier: str) -> bool:
        """Remove a prompt template."""
        from admin.core.models import Prompt

        deleted, _ = await Prompt.objects.filter(name=identifier).adelete()
        return deleted > 0
