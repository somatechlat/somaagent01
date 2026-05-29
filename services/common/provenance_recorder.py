"""Provenance recorder — tracks data lineage for multimodal operations.

VIBE COMPLIANT: Uses Django ORM exclusively.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from uuid import UUID

from services.common.store_base import BaseStore

LOGGER = logging.getLogger(__name__)


@dataclass
class ProvenanceRecord:
    """A provenance record."""

    asset_id: UUID = field(default_factory=UUID)
    tenant_id: str = ""
    generation_params: Dict[str, Any] = field(default_factory=dict)
    rework_count: int = 0


class ProvenanceRecorder(BaseStore[ProvenanceRecord]):
    """Django ORM-backed provenance recorder."""

    async def ensure_schema(self) -> None:
        """Schema managed by Django migrations."""
        pass

    async def get(self, asset_id: UUID) -> Optional[ProvenanceRecord]:
        """Get provenance record by asset ID."""
        from admin.core.models import Provenance

        record = await Provenance.objects.filter(asset_id=str(asset_id)).afirst()
        if not record:
            return None
        return ProvenanceRecord(
            asset_id=UUID(record.asset_id) if isinstance(record.asset_id, str) else record.asset_id,
            tenant_id=record.tenant_id or "",
            generation_params=record.generation_params or {},
            rework_count=record.rework_count or 0,
        )

    async def record(
        self,
        operation: Optional[str] = None,
        asset_id: Optional[str | UUID] = None,
        tenant_id: Optional[str] = None,
        generation_params: Optional[Dict[str, Any]] = None,
        rework_count: int = 0,
        **kwargs: Any,
    ) -> ProvenanceRecord:
        """Record provenance information."""
        from admin.core.models import Provenance

        params = generation_params or {}
        params.update(kwargs)
        obj = await Provenance.objects.acreate(
            asset_id=str(asset_id) if asset_id else "",
            tenant_id=tenant_id or "",
            operation=operation,
            generation_params=params,
            rework_count=rework_count,
        )
        return ProvenanceRecord(
            asset_id=UUID(obj.asset_id) if isinstance(obj.asset_id, str) else obj.asset_id,
            tenant_id=obj.tenant_id or "",
            generation_params=obj.generation_params or {},
            rework_count=obj.rework_count or 0,
        )

    async def create(self, record: ProvenanceRecord) -> ProvenanceRecord:
        """Persist a provenance record."""
        return await self.record(
            asset_id=record.asset_id,
            tenant_id=record.tenant_id,
            generation_params=record.generation_params,
            rework_count=record.rework_count,
        )

    async def update(
        self, identifier: str, changes: Dict[str, Any]
    ) -> Optional[ProvenanceRecord]:
        """Update a provenance record."""
        from admin.core.models import Provenance

        record = await Provenance.objects.filter(asset_id=identifier).afirst()
        if not record:
            return None
        if "generation_params" in changes:
            record.generation_params = changes["generation_params"]
        if "rework_count" in changes:
            record.rework_count = changes["rework_count"]
        await record.asave()
        return await self.get(UUID(identifier))

    async def delete(self, identifier: str) -> bool:
        """Remove a provenance record."""
        from admin.core.models import Provenance

        deleted, _ = await Provenance.objects.filter(asset_id=identifier).adelete()
        return deleted > 0
