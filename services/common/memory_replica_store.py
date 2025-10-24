"""Replica/audit store for memory writes consumed from WAL.

This persists a normalized copy of memory write events for auditing,
analytics, or serving backup reads if needed. It tracks basic metadata
and supports simple lag/health checks.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import asyncpg

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class MemoryReplicaRow:
    id: int
    event_id: str | None
    session_id: str | None
    persona_id: str | None
    tenant: str | None
    role: str | None
    coord: str | None
    request_id: str | None
    trace_id: str | None
    payload: dict[str, Any]
    wal_timestamp: float | None
    created_at: datetime


class MemoryReplicaStore:
    def __init__(self, dsn: Optional[str] = None) -> None:
        self.dsn = dsn or os.getenv(
            "POSTGRES_DSN", "postgresql://soma:soma@localhost:5432/somaagent01"
        )
        self._pool: Optional[asyncpg.Pool] = None

    async def _ensure_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(self.dsn, min_size=1, max_size=5)
        return self._pool

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def insert_from_wal(self, wal: dict[str, Any]) -> int:
        """Insert a replica record using a memory WAL event shape.

        Expected minimal shape:
        {
          "type": "memory.write",
          "role": "user|assistant|tool",
          "session_id": str,
          "persona_id": str|None,
          "tenant": str|None,
          "payload": { ... memory payload ... },
          "result": { "coord": str|None, "trace_id": str|None, "request_id": str|None },
          "timestamp": float
        }
        """
        payload = wal.get("payload") or {}
        result = wal.get("result") or {}
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO memory_replica (
                    event_id, session_id, persona_id, tenant, role,
                    coord, request_id, trace_id, payload, wal_timestamp
                ) VALUES (
                    $1, $2, $3, $4, $5,
                    $6, $7, $8, $9::jsonb, $10
                )
                ON CONFLICT (event_id) DO NOTHING
                RETURNING id
                """,
                (payload or {}).get("id"),
                wal.get("session_id"),
                wal.get("persona_id"),
                wal.get("tenant"),
                wal.get("role"),
                (result or {}).get("coord"),
                (result or {}).get("request_id"),
                (result or {}).get("trace_id"),
                json.dumps(payload, ensure_ascii=False),
                wal.get("timestamp"),
            )
            if row:
                return int(row["id"])  # type: ignore[index]
            # If the row already exists, return its id if available, else 0
            existing = await conn.fetchrow(
                "SELECT id FROM memory_replica WHERE event_id = $1 ORDER BY id DESC LIMIT 1",
                (payload or {}).get("id"),
            )
            return int(existing["id"]) if existing else 0

    async def latest_wal_timestamp(self) -> float | None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT wal_timestamp FROM memory_replica ORDER BY id DESC LIMIT 1"
            )
            if not row:
                return None
            return float(row["wal_timestamp"]) if row["wal_timestamp"] is not None else None


MIGRATION_SQL = """
CREATE TABLE IF NOT EXISTS memory_replica (
    id BIGSERIAL PRIMARY KEY,
    event_id TEXT,
    session_id TEXT,
    persona_id TEXT,
    tenant TEXT,
    role TEXT,
    coord TEXT,
    request_id TEXT,
    trace_id TEXT,
    payload JSONB NOT NULL,
    wal_timestamp DOUBLE PRECISION,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS memory_replica_session_idx
ON memory_replica(session_id, id DESC);

-- Ensure idempotency on event_id when provided
CREATE UNIQUE INDEX IF NOT EXISTS memory_replica_event_id_uniq
ON memory_replica(event_id)
WHERE event_id IS NOT NULL;
"""


async def ensure_schema(store: MemoryReplicaStore) -> None:
    pool = await store._ensure_pool()
    async with pool.acquire() as conn:
        await conn.execute(MIGRATION_SQL)
        LOGGER.info("Ensured memory_replica table exists")
