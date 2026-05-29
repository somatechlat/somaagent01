"""Attachments store — persistent file attachment metadata storage.

VIBE COMPLIANT: Uses Django ORM exclusively.
"""

from __future__ import annotations

import logging
from typing import Any, Optional
from uuid import UUID

from services.common.store_base import BaseStore

LOGGER = logging.getLogger(__name__)


class AttachmentsStore(BaseStore[UUID]):
    """Django ORM-backed store for file attachments metadata."""

    async def ensure_schema(self) -> None:
        """Schema managed by Django migrations."""
        pass

    async def get(self, identifier: str) -> Optional[UUID]:
        """Retrieve attachment by ID."""
        from admin.filesv2.models import File

        attachment = await File.objects.filter(id=identifier).afirst()
        if not attachment:
            return None
        return attachment.id

    async def create(self, record: UUID) -> UUID:
        """Persist attachment metadata."""
        raise RuntimeError(
            "Attachment creation requires multipart upload handling. Use the files API directly."
        )

    async def delete(self, identifier: str) -> bool:
        """Remove an attachment."""
        from admin.filesv2.models import File

        deleted, _ = await File.objects.filter(id=identifier).adelete()
        return deleted > 0
