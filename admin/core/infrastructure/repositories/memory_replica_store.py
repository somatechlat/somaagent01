"""Memory replica store repository implementation.

Re-exports the production store from services.memory_replicator.store
and adds repository-layer helpers expected by the infrastructure package.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from services.memory_replicator.store import MemoryReplicaStore as _MemoryReplicaStore


@dataclass
class MemoryReplicaRow:
    """Row representation of a memory replica record."""

    id: int
    event_id: str
    tenant: Optional[str]
    namespace: Optional[str]
    payload: Dict[str, Any]
    wal_timestamp: Optional[str]
    created_at: Optional[str]


MIGRATION_SQL = """
CREATE TABLE IF NOT EXISTS memory_replicas (
    id SERIAL PRIMARY KEY,
    event_id TEXT UNIQUE NOT NULL,
    tenant TEXT,
    namespace TEXT,
    payload JSONB NOT NULL,
    wal_timestamp TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_memory_replicas_event_id ON memory_replicas(event_id);
CREATE INDEX IF NOT EXISTS idx_memory_replicas_tenant ON memory_replicas(tenant);
"""


class MemoryReplicaStore(_MemoryReplicaStore):
    """Repository adapter over the production memory replica store."""

    pass


async def ensure_schema(store: MemoryReplicaStore) -> None:
    """Ensure the memory replica schema exists."""
    await store.ensure_schema()
