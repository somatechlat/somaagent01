"""Asset store — persistent asset metadata storage.

VIBE COMPLIANT: Uses Django ORM exclusively.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional
from uuid import UUID

from services.common.store_base import BaseStore

LOGGER = logging.getLogger(__name__)


@dataclass
class AssetRecord:
    """An asset record."""

    id: str
    name: str
    status: str
    tenant: str
    asset_type: str = ""
    format: str = ""
    content_size_bytes: int = 0
    dimensions: Optional[Dict[str, int]] = None
    content: Optional[bytes] = None
    tenant_id: str = ""
    mime_type: Optional[str] = None
    original_filename: Optional[str] = None
    checksum_sha256: Optional[str] = None


class AssetType:
    """Asset type constants."""

    IMAGE = "image"
    DOCUMENT = "document"
    VIDEO = "video"
    SCREENSHOT = "screenshot"
    DIAGRAM = "diagram"


class AssetStore(BaseStore[AssetRecord]):
    """Django ORM-backed store for assets."""

    def __init__(self, dsn: Optional[str] = None) -> None:
        pass

    async def ensure_schema(self) -> None:
        """Schema managed by Django migrations."""
        pass

    async def get(self, asset_id: Optional[str | UUID]) -> Optional[AssetRecord]:
        """Get an asset by ID."""
        from admin.core.models import Asset

        asset = await Asset.objects.filter(id=str(asset_id)).afirst()
        if not asset:
            return None
        return AssetRecord(
            id=str(asset.id),
            name=asset.name,
            status=asset.status,
            tenant=asset.tenant_id,
            asset_type=asset.asset_type,
            format=asset.format,
            content_size_bytes=asset.content_size_bytes or 0,
            mime_type=asset.mime_type,
            original_filename=asset.original_filename,
            checksum_sha256=asset.checksum_sha256,
        )

    async def create(
        self,
        tenant_id: str,
        session_id: str,
        asset_type: str,
        format: str,
        content: Optional[bytes] = None,
        dimensions: Optional[Dict[str, int]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> AssetRecord:
        """Create a new asset."""
        from admin.core.models import Asset

        obj = await Asset.objects.acreate(
            tenant_id=tenant_id,
            session_id=session_id,
            asset_type=asset_type,
            format=format,
            content=content,
            content_size_bytes=len(content) if content else 0,
            dimensions=dimensions,
            metadata=metadata or {},
            **kwargs,
        )
        return AssetRecord(
            id=str(obj.id),
            name=obj.name,
            status=obj.status,
            tenant=tenant_id,
        )

    async def tombstone(self, asset_id: UUID, reason: str = "") -> bool:
        """Mark an asset as tombstoned."""
        from admin.core.models import Asset

        asset = await Asset.objects.filter(id=str(asset_id)).afirst()
        if not asset:
            return False
        asset.status = "tombstoned"
        asset.tombstone_reason = reason
        await asset.asave(update_fields=["status", "tombstone_reason", "updated_at"])
        return True

    async def delete(self, identifier: str) -> bool:
        """Remove an asset."""
        from admin.core.models import Asset

        deleted, _ = await Asset.objects.filter(id=identifier).adelete()
        return deleted > 0
