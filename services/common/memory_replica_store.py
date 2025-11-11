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

from services.common import runtime_config as cfg

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
        raw_dsn = (
            dsn
            or cfg.db_dsn("postgresql://soma:soma@localhost:5432/somaagent01")
            or "postgresql://soma:soma@localhost:5432/somaagent01"
        )
        self.dsn = os.path.expandvars(raw_dsn)
        self._pool: Optional[asyncpg.Pool] = None

    async def _ensure_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            min_size = int(cfg.env("PG_POOL_MIN_SIZE", "1") or "1")
            max_size = int(cfg.env("PG_POOL_MAX_SIZE", "2") or "2")

            async def _init_conn(conn: asyncpg.Connection) -> None:  # type: ignore[name-defined]
                """Ensure JSON/JSONB are decoded to Python objects.

                Using text format keeps compatibility across asyncpg versions.
                """
                try:
                    await conn.set_type_codec(
                        "json",
                        schema="pg_catalog",
                        encoder=json.dumps,
                        decoder=json.loads,
                        format="text",
                    )
                except Exception:
                    LOGGER.debug("Failed to set json codec", exc_info=True)
                try:
                    await conn.set_type_codec(
                        "jsonb",
                        schema="pg_catalog",
                        encoder=json.dumps,
                        decoder=json.loads,
                        format="text",
                    )
                except Exception:
                    LOGGER.debug("Failed to set jsonb codec", exc_info=True)

            self._pool = await asyncpg.create_pool(
                self.dsn,
                min_size=max(0, min_size),
                max_size=max(1, max_size),
                init=_init_conn,
            )
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

    async def get_by_event_id(self, event_id: str) -> Optional[MemoryReplicaRow]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, event_id, session_id, persona_id, tenant, role,
                       coord, request_id, trace_id, payload, wal_timestamp, created_at
                FROM memory_replica
                WHERE event_id = $1
                ORDER BY id DESC
                LIMIT 1
                """,
                event_id,
            )
        if not row:
            return None
        return MemoryReplicaRow(
            id=row["id"],
            event_id=row["event_id"],
            session_id=row["session_id"],
            persona_id=row["persona_id"],
            tenant=row["tenant"],
            role=row["role"],
            coord=row["coord"],
            request_id=row["request_id"],
            trace_id=row["trace_id"],
            payload=row["payload"],
            wal_timestamp=row["wal_timestamp"],
            created_at=row["created_at"],
        )

    async def list_memories(
        self,
        *,
        limit: int = 50,
        after_id: Optional[int] = None,
        tenant: Optional[str] = None,
        persona_id: Optional[str] = None,
        role: Optional[str] = None,
        session_id: Optional[str] = None,
        universe: Optional[str] = None,
        namespace: Optional[str] = None,
        min_ts: Optional[float] = None,
        max_ts: Optional[float] = None,
        q: Optional[str] = None,
    ) -> list[MemoryReplicaRow]:
        """List replica rows with common filters.

        Pagination uses id DESC with `after_id` acting as a cursor (exclusive upper bound).
        """
        pool = await self._ensure_pool()
        conditions: list[str] = []
        params: list[Any] = []

        if after_id is not None:
            params.append(after_id)
            conditions.append(f"id < ${len(params)}")
        if tenant:
            params.append(tenant)
            conditions.append(f"tenant = ${len(params)}")
        if persona_id:
            params.append(persona_id)
            conditions.append(f"persona_id = ${len(params)}")
        if role:
            params.append(role)
            conditions.append(f"role = ${len(params)}")
        if session_id:
            params.append(session_id)
            conditions.append(f"session_id = ${len(params)}")
        if universe:
            params.append(universe)
            conditions.append(f"(payload->'metadata'->>'universe_id') = ${len(params)}")
        if namespace:
            params.append(namespace)
            conditions.append(
                f"COALESCE(payload->>'namespace', payload->'metadata'->>'namespace') = ${len(params)}"
            )
        if min_ts is not None:
            params.append(min_ts)
            conditions.append(f"wal_timestamp >= ${len(params)}")
        if max_ts is not None:
            params.append(max_ts)
            conditions.append(f"wal_timestamp <= ${len(params)}")
        if q:
            # Simple text search in JSON for now; consider GIN index for scale
            params.append(f"%{q}%")
            conditions.append(f"payload::text ILIKE ${len(params)}")

        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        params.append(limit)
        sql = f"""
            SELECT id, event_id, session_id, persona_id, tenant, role,
                   coord, request_id, trace_id, payload, wal_timestamp, created_at
            FROM memory_replica
            {where}
            ORDER BY id DESC
            LIMIT ${len(params)}
        """
        async with pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)

        items: list[MemoryReplicaRow] = []
        for r in rows:
            items.append(
                MemoryReplicaRow(
                    id=r["id"],
                    event_id=r["event_id"],
                    session_id=r["session_id"],
                    persona_id=r["persona_id"],
                    tenant=r["tenant"],
                    role=r["role"],
                    coord=r["coord"],
                    request_id=r["request_id"],
                    trace_id=r["trace_id"],
                    payload=r["payload"],
                    wal_timestamp=r["wal_timestamp"],
                    created_at=r["created_at"],
                )
            )
        return items


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
-- For ON CONFLICT (event_id) to work without specifying a predicate,
-- an unqualified UNIQUE index (or constraint) must exist on (event_id).
-- We keep the historical partial index if present, but add a full unique
-- index to satisfy Postgres' conflict target inference.
CREATE UNIQUE INDEX IF NOT EXISTS memory_replica_event_id_uniq_full
ON memory_replica(event_id);

-- Helpful indexes for common filters
CREATE INDEX IF NOT EXISTS memory_replica_tenant_idx ON memory_replica(tenant, id DESC);
CREATE INDEX IF NOT EXISTS memory_replica_persona_idx ON memory_replica(persona_id, id DESC);
CREATE INDEX IF NOT EXISTS memory_replica_created_idx ON memory_replica(created_at DESC);
CREATE INDEX IF NOT EXISTS memory_replica_wal_ts_idx ON memory_replica(wal_timestamp DESC);
-- JSONB GIN index for payload text filters (optional but useful)
CREATE INDEX IF NOT EXISTS memory_replica_payload_gin ON memory_replica USING gin (payload);
-- Expression indexes for structured filters (universe / namespace)
CREATE INDEX IF NOT EXISTS memory_replica_universe_expr_idx
ON memory_replica ((payload->'metadata'->>'universe_id'));
CREATE INDEX IF NOT EXISTS memory_replica_namespace_expr_idx
ON memory_replica ((COALESCE(payload->>'namespace', payload->'metadata'->>'namespace')));
"""


async def ensure_schema(store: MemoryReplicaStore) -> None:
    pool = await store._ensure_pool()
    async with pool.acquire() as conn:
        await conn.execute(MIGRATION_SQL)
        LOGGER.info("Ensured memory_replica table exists")
