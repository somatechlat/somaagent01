"""Memory replica store — PostgreSQL-backed WAL replication storage.

Separated from service.py to avoid Django/ninja import dependencies.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Optional

try:
    import asyncpg  # type: ignore
except ImportError:  # pragma: no cover
    asyncpg = None  # type: ignore

LOGGER = logging.getLogger(__name__)


class MemoryReplicaStore:
    """PostgreSQL-backed store for memory WAL replicas."""

    TABLE_NAME = "memory_replicas"

    def __init__(self, dsn: Optional[str] = None) -> None:
        self.dsn = dsn or os.environ.get("SA01_DB_DSN", "")

    async def _get_pool(self) -> Any:
        if asyncpg is None:
            raise RuntimeError("asyncpg is required for MemoryReplicaStore")
        return await asyncpg.create_pool(self.dsn, min_size=1, max_size=2)

    async def ensure_schema(self) -> None:
        if not self.dsn:
            raise RuntimeError("MemoryReplicaStore: SA01_DB_DSN not configured")
        if asyncpg is None:
            raise RuntimeError("MemoryReplicaStore: asyncpg is required")
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                        id SERIAL PRIMARY KEY,
                        event_id TEXT UNIQUE NOT NULL,
                        tenant TEXT,
                        namespace TEXT,
                        payload JSONB NOT NULL,
                        wal_timestamp TIMESTAMPTZ,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    )
                    """
                )
            await pool.close()
        except Exception as exc:
            LOGGER.warning("MemoryReplicaStore.ensure_schema failed: %s", exc)

    async def close(self) -> None:
        """Close any open connections (no-op for stateless store)."""
        pass

    async def insert_from_wal(self, wal: Dict[str, Any]) -> int:
        """Insert a memory record from a WAL event.

        Returns:
            ID of the inserted row.
        """
        if not self.dsn:
            raise RuntimeError("MemoryReplicaStore: SA01_DB_DSN not configured")
        if asyncpg is None:
            raise RuntimeError("MemoryReplicaStore: asyncpg is required")
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    f"""
                    INSERT INTO {self.TABLE_NAME}
                        (event_id, tenant, namespace, payload, wal_timestamp)
                    VALUES ($1, $2, $3, $4, to_timestamp($5))
                    ON CONFLICT (event_id)
                    DO UPDATE SET payload = EXCLUDED.payload, wal_timestamp = EXCLUDED.wal_timestamp
                    RETURNING id
                    """,
                    wal.get("event_id", ""),
                    wal.get("tenant"),
                    wal.get("namespace"),
                    json.dumps(wal.get("payload", {})),
                    float(wal.get("timestamp") or 0.0),
                )
                return row["id"] if row else 0
        finally:
            await pool.close()

    async def latest_wal_timestamp(self) -> Optional[float]:
        if not self.dsn:
            raise RuntimeError("MemoryReplicaStore: SA01_DB_DSN not configured")
        if asyncpg is None:
            raise RuntimeError("MemoryReplicaStore: asyncpg is required")
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    f"SELECT EXTRACT(EPOCH FROM MAX(wal_timestamp)) as ts FROM {self.TABLE_NAME}"
                )
                return row["ts"] if row and row["ts"] else None
        finally:
            await pool.close()


async def ensure_schema(store: MemoryReplicaStore) -> None:
    """Compatibility helper for memory replicator."""
    await store.ensure_schema()
