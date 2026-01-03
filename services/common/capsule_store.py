"""Redis-backed CapsuleStore.

Provides persistence for Capsule definitions using Redis json.
Implements the interface expected by capsules.py and agentiq_governor.py.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from typing import List, Optional

import redis.asyncio as redis

from services.common.capsule_enforcer import CapsuleRecord, CapsuleStatus

logger = logging.getLogger(__name__)


class CapsuleStore:
    def __init__(self, redis_url: Optional[str] = None):
        default_url = os.environ.get("SA01_REDIS_URL", "")
        self.url = (
            redis_url or os.environ.get("REDIS_URL", default_url) or "redis://localhost:6379/0"
        )
        self.client = redis.from_url(self.url, decode_responses=True)
        self.prefix = "capsule:v1"

    async def ensure_schema(self) -> None:
        """No-op for Redis."""
        pass

    async def get(self, capsule_id: str) -> Optional[CapsuleRecord]:
        """Get capsule by ID."""
        key = f"{self.prefix}:{capsule_id}"
        data = await self.client.get(key)
        if not data:
            return None
        return self._deserialize(json.loads(data))

    async def get_by_name_version(
        self, tenant_id: str, name: str, version: str
    ) -> Optional[CapsuleRecord]:
        """Get capsule by name/version (scan)."""
        # Inefficient scan for Redis, but acceptable for config data
        async for key in self.client.scan_iter(f"{self.prefix}:*"):
            data = await self.client.get(key)
            if data:
                rec = self._deserialize(json.loads(data))
                if rec.tenant_id == tenant_id and rec.name == name and rec.version == version:
                    return rec
        return None

    async def list(self, tenant_id: Optional[str] = None) -> List[CapsuleRecord]:
        """List all capsules, optionally filtered by tenant."""
        results = []
        async for key in self.client.scan_iter(f"{self.prefix}:*"):
            data = await self.client.get(key)
            if data:
                rec = self._deserialize(json.loads(data))
                if not tenant_id or rec.tenant_id == tenant_id:
                    results.append(rec)
        return results

    async def create(self, record: CapsuleRecord) -> None:
        """Create new capsule record."""
        key = f"{self.prefix}:{record.capsule_id}"
        await self.client.set(key, json.dumps(self._serialize(record)))

    async def install(self, capsule_id: str) -> bool:
        """Set installed=True."""
        return await self._update_field(capsule_id, "installed", True)

    async def publish(self, capsule_id: str) -> bool:
        """Set status=PUBLISHED."""
        return await self._update_field(capsule_id, "status", CapsuleStatus.PUBLISHED.value)

    async def deprecate(self, capsule_id: str) -> bool:
        """Set status=DEPRECATED."""
        return await self._update_field(capsule_id, "status", CapsuleStatus.DEPRECATED.value)

    async def _update_field(self, capsule_id: str, field: str, value: Any) -> bool:
        rec = await self.get(capsule_id)
        if not rec:
            return False

        # Update attribute
        setattr(rec, field, value)

        # Save back
        await self.create(rec)
        return True

    def _serialize(self, record: CapsuleRecord) -> dict:
        d = record.__dict__.copy()
        # Handle enums
        if "status" in d and hasattr(d["status"], "value"):
            d["status"] = d["status"].value
        return d

    def _deserialize(self, data: dict) -> CapsuleRecord:
        # Convert status string back to Enum if needed, or just keep as consistent type
        if "status" in data:
            try:
                data["status"] = CapsuleStatus(data["status"])
            except ValueError:
                pass
        return CapsuleRecord(**data)
