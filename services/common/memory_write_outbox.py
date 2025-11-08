"""Postgres-backed outbox for SomaBrain memory writes.

When `remember()` fails (e.g., SomaBrain unavailable), enqueue the memory
payload here for later retry by the memory_sync worker. On success, the worker
also publishes `memory.wal` so the replica stays consistent.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import asyncpg


@dataclass(slots=True)
class MemoryWriteItem:
    id: int
    payload: dict[str, Any]
    status: str
    retry_count: int
    next_attempt_at: datetime
    tenant: Optional[str]
    session_id: Optional[str]
    persona_id: Optional[str]
    idempotency_key: Optional[str]
    last_error: Optional[str]
    created_at: datetime
    updated_at: datetime


class MemoryWriteOutbox:
    def __init__(self, dsn: Optional[str] = None) -> None:
        raw_dsn = dsn or os.getenv(
            "POSTGRES_DSN", "postgresql://soma:soma@localhost:5432/somaagent01"
        )
        self.dsn = os.path.expandvars(raw_dsn)
        self._pool: Optional[asyncpg.Pool] = None

    async def _ensure_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            min_size = int(os.getenv("PG_POOL_MIN_SIZE", "1"))
            max_size = int(os.getenv("PG_POOL_MAX_SIZE", "2"))
            self._pool = await asyncpg.create_pool(
                self.dsn, min_size=max(0, min_size), max_size=max(1, max_size)
            )
        return self._pool

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    # Writer API
    async def enqueue(
        self,
        *,
        payload: dict[str, Any],
        tenant: Optional[str] = None,
        session_id: Optional[str] = None,
        persona_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        dedupe_key: Optional[str] = None,
    ) -> Optional[int]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO memory_write_outbox (
                    payload, status, retry_count, next_attempt_at,
                    tenant, session_id, persona_id, idempotency_key, dedupe_key
                ) VALUES (
                    $1::jsonb, 'pending', 0, NOW(),
                    $2, $3, $4, $5, $6
                )
                ON CONFLICT (dedupe_key) WHERE dedupe_key IS NOT NULL DO NOTHING
                RETURNING id
                """,
                json.dumps(payload, ensure_ascii=False),
                tenant,
                session_id,
                persona_id,
                idempotency_key,
                dedupe_key,
            )
        if not row:
            return None
        return int(row["id"])

    # Worker API
    async def claim_batch(self, *, limit: int = 100) -> list[MemoryWriteItem]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                rows = await conn.fetch(
                    """
                    SELECT id, payload, status, retry_count, next_attempt_at,
                           tenant, session_id, persona_id, idempotency_key,
                           last_error, created_at, updated_at
                    FROM memory_write_outbox
                    WHERE status = 'pending' AND next_attempt_at <= NOW()
                    ORDER BY id
                    FOR UPDATE SKIP LOCKED
                    LIMIT $1
                    """,
                    limit,
                )
                ids = [r["id"] for r in rows]
                if ids:
                    await conn.execute(
                        """
                        UPDATE memory_write_outbox
                        SET status = 'sending', updated_at = NOW()
                        WHERE id = ANY($1::bigint[])
                        """,
                        ids,
                    )
        items: list[MemoryWriteItem] = []
        for r in rows:
            items.append(
                MemoryWriteItem(
                    id=r["id"],
                    payload=r["payload"],
                    status="sending",
                    retry_count=r["retry_count"],
                    next_attempt_at=r["next_attempt_at"],
                    tenant=r["tenant"],
                    session_id=r["session_id"],
                    persona_id=r["persona_id"],
                    idempotency_key=r["idempotency_key"],
                    last_error=r["last_error"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
            )
        return items

    async def mark_sent(self, item_id: int) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE memory_write_outbox
                SET status = 'sent', updated_at = NOW(), last_error = NULL, last_error_at = NULL
                WHERE id = $1
                """,
                item_id,
            )

    async def mark_retry(self, item_id: int, *, backoff_seconds: float, error: str) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE memory_write_outbox
                SET status = 'pending',
                    retry_count = retry_count + 1,
                    next_attempt_at = NOW() + make_interval(secs => $2::double precision),
                    last_error = $3,
                    last_error_at = NOW(),
                    updated_at = NOW()
                WHERE id = $1
                """,
                item_id,
                backoff_seconds,
                error[:8000],
            )

    async def mark_failed(self, item_id: int, *, error: str) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE memory_write_outbox
                SET status = 'failed', last_error = $2, last_error_at = NOW(), updated_at = NOW()
                WHERE id = $1
                """,
                item_id,
                error[:8000],
            )

    async def count_pending(self) -> int:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT COUNT(*) AS c FROM memory_write_outbox WHERE status='pending'"
            )
            return int(row["c"])  # type: ignore[index]


MIGRATION_SQL = """
CREATE TABLE IF NOT EXISTS memory_write_outbox (
    id BIGSERIAL PRIMARY KEY,
    payload JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    retry_count INT NOT NULL DEFAULT 0,
    next_attempt_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    tenant TEXT,
    session_id TEXT,
    persona_id TEXT,
    idempotency_key TEXT,
    dedupe_key TEXT,
    last_error TEXT,
    last_error_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS memory_write_outbox_dedupe_uniq
ON memory_write_outbox(dedupe_key) WHERE dedupe_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS memory_write_outbox_pending_idx
ON memory_write_outbox(status, next_attempt_at);

CREATE OR REPLACE FUNCTION memory_write_outbox_touch_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS memory_write_outbox_set_updated_at ON memory_write_outbox;
CREATE TRIGGER memory_write_outbox_set_updated_at
BEFORE UPDATE ON memory_write_outbox
FOR EACH ROW
EXECUTE FUNCTION memory_write_outbox_touch_updated_at();
"""


async def ensure_schema(store: MemoryWriteOutbox) -> None:
    pool = await store._ensure_pool()
    async with pool.acquire() as conn:
        await conn.execute(MIGRATION_SQL)
