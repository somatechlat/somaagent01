"""Memory replica store — Django ORM-backed WAL replication storage.

Separated from service.py to avoid Django/ninja import dependencies.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

LOGGER = logging.getLogger(__name__)


class MemoryReplicaStore:
    """Django ORM-backed store for memory WAL replicas."""

    def __init__(self) -> None:
        pass

    async def ensure_schema(self) -> None:
        """Schema managed by Django migrations."""
        pass

    async def insert_from_wal(self, event: Dict[str, Any]) -> None:
        """Persist a memory WAL event."""
        from admin.core.models import MemoryReplica

        await MemoryReplica.objects.acreate(
            event_id=event.get("id", ""),
            session_id=event.get("session_id", ""),
            persona_id=event.get("persona_id", ""),
            tenant=event.get("tenant", ""),
            role=event.get("role", ""),
            coord=event.get("namespace", ""),
            request_id=event.get("request_id", ""),
            trace_id=event.get("trace_id", ""),
            payload=event.get("payload", {}),
            wal_timestamp=event.get("timestamp"),
        )

    async def get_latest(self, tenant: str, namespace: str) -> Optional[Dict[str, Any]]:
        """Get the latest replica for tenant/namespace."""
        from admin.core.models import MemoryReplica

        replica = (
            await MemoryReplica.objects.filter(tenant=tenant, coord=namespace)
            .order_by("-created_at")
            .afirst()
        )
        if not replica:
            return None
        return {
            "event_id": replica.event_id,
            "tenant": replica.tenant,
            "namespace": replica.coord,
            "payload": replica.payload,
            "created_at": replica.created_at.isoformat() if replica.created_at else None,
        }

    async def list(
        self,
        tenant: str,
        namespace: Optional[str] = None,
        limit: int = 100,
    ) -> list[Dict[str, Any]]:
        """List replicas for tenant/namespace."""
        from admin.core.models import MemoryReplica

        qs = MemoryReplica.objects.filter(tenant=tenant)
        if namespace:
            qs = qs.filter(coord=namespace)
        qs = qs.order_by("-created_at")[:limit]

        results = []
        async for replica in qs:
            results.append(
                {
                    "event_id": replica.event_id,
                    "tenant": replica.tenant,
                    "namespace": replica.coord,
                    "payload": replica.payload,
                    "created_at": replica.created_at.isoformat() if replica.created_at else None,
                }
            )
        return results
