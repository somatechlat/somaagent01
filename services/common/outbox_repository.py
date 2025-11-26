"""Postgres message outbox for resilient Kafka publishing.

Implements a lightweight transactional outbox with asyncpg and simple
status management. Use this from write paths to enqueue messages when
Kafka is unhealthy, and from the sync worker to publish pending rows.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import asyncpg
from prometheus_client import Counter, Histogram

from src.core.config import cfg

LOGGER = logging.getLogger(__name__)


# Metrics
OUTBOX_EVENTS = Counter(
    "outbox_events_total",
    "Outbox operations by action and result",
    labelnames=("action", "result"),
)

OUTBOX_PUBLISH_LATENCY = Histogram(
    "outbox_publish_seconds",
    "Time spent publishing outbox messages (worker-observed)",
)


@dataclass(slots=True)
class OutboxMessage:
    id: int
    topic: str
    payload: dict[str, Any]
    headers: dict[str, Any]
    partition_key: Optional[str]
    status: str
    retry_count: int
    next_attempt_at: datetime
    dedupe_key: Optional[str]
    session_id: Optional[str]
    tenant: Optional[str]
    created_at: datetime
    updated_at: datetime


class OutboxStore:
    def __init__(self, dsn: Optional[str] = None) -> None:
        raw_dsn = dsn or cfg.settings().database.dsn
        self.dsn = raw_dsn
        self._pool: Optional[asyncpg.Pool] = None

    async def _ensure_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            min_size = int(cfg.env("PG_POOL_MIN_SIZE", "1") or "1")
            max_size = int(cfg.env("PG_POOL_MAX_SIZE", "2") or "2")
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
        topic: str,
        payload: dict[str, Any],
        partition_key: Optional[str] = None,
        headers: Optional[dict[str, Any]] = None,
        dedupe_key: Optional[str] = None,
        session_id: Optional[str] = None,
        tenant: Optional[str] = None,
        eta: Optional[datetime] = None,
    ) -> Optional[int]:
        """Insert a message into the outbox.

        Returns the row ID, or None when dedupe_key conflicts and row existed.
        """
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            try:
                row = await conn.fetchrow(
                    """
                    INSERT INTO message_outbox (
                        topic, partition_key, payload, headers,
                        status, retry_count, next_attempt_at,
                        dedupe_key, session_id, tenant
                    ) VALUES (
                        $1, $2, $3::jsonb, $4::jsonb,
                        'pending', 0, COALESCE($5, NOW()),
                        $6, $7, $8
                    )
                    ON CONFLICT (dedupe_key) WHERE dedupe_key IS NOT NULL DO NOTHING
                    RETURNING id
                    """,
                    topic,
                    partition_key,
                    json.dumps(payload, ensure_ascii=False),
                    json.dumps(headers or {}, ensure_ascii=False),
                    eta,
                    dedupe_key,
                    session_id,
                    tenant,
                )
            except Exception:
                OUTBOX_EVENTS.labels("enqueue", "error").inc()
                raise
            else:
                if row and (msg_id := row["id"]):
                    OUTBOX_EVENTS.labels("enqueue", "inserted").inc()
                    return int(msg_id)
                OUTBOX_EVENTS.labels("enqueue", "deduped").inc()
                return None

    # Worker API
    async def claim_batch(self, *, limit: int = 100) -> list[OutboxMessage]:
        """Atomically claim a batch of pending messages for publishing.

        Uses SELECT FOR UPDATE SKIP LOCKED to avoid contention across workers.
        """
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                rows = await conn.fetch(
                    """
                    SELECT id, topic, payload, headers, partition_key,
                           status, retry_count, next_attempt_at,
                           dedupe_key, session_id, tenant,
                           created_at, updated_at
                    FROM message_outbox
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
                        UPDATE message_outbox
                        SET status = 'sending', updated_at = NOW()
                        WHERE id = ANY($1::bigint[])
                        """,
                        ids,
                    )

        messages: list[OutboxMessage] = []
        for r in rows:
            messages.append(
                OutboxMessage(
                    id=r["id"],
                    topic=r["topic"],
                    payload=r["payload"],
                    headers=r["headers"],
                    partition_key=r["partition_key"],
                    status="sending",
                    retry_count=r["retry_count"],
                    next_attempt_at=r["next_attempt_at"],
                    dedupe_key=r["dedupe_key"],
                    session_id=r["session_id"],
                    tenant=r["tenant"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
            )
        OUTBOX_EVENTS.labels("claim", "claimed" if messages else "empty").inc()
        return messages

    async def mark_sent(self, msg_id: int) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE message_outbox
                SET status = 'sent', updated_at = NOW(), last_error = NULL, last_error_at = NULL
                WHERE id = $1
                """,
                msg_id,
            )
        OUTBOX_EVENTS.labels("ack", "sent").inc()

    async def mark_retry(self, msg_id: int, *, backoff_seconds: float, error: str) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE message_outbox
                SET status = 'pending',
                    retry_count = retry_count + 1,
                    next_attempt_at = NOW() + make_interval(secs => $2::double precision),
                    last_error = $3,
                    last_error_at = NOW(),
                    updated_at = NOW()
                WHERE id = $1
                """,
                msg_id,
                backoff_seconds,
                error[:8000],
            )
        OUTBOX_EVENTS.labels("nack", "retry").inc()

    async def mark_failed(self, msg_id: int, *, error: str) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE message_outbox
                SET status = 'failed', last_error = $2, last_error_at = NOW(), updated_at = NOW()
                WHERE id = $1
                """,
                msg_id,
                error[:8000],
            )
        OUTBOX_EVENTS.labels("nack", "failed").inc()


MIGRATION_SQL = """
CREATE TABLE IF NOT EXISTS message_outbox (
    id BIGSERIAL PRIMARY KEY,
    topic TEXT NOT NULL,
    partition_key TEXT,
    payload JSONB NOT NULL,
    headers JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'pending',
    retry_count INT NOT NULL DEFAULT 0,
    next_attempt_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    dedupe_key TEXT,
    session_id TEXT,
    tenant TEXT,
    last_error TEXT,
    last_error_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS message_outbox_dedupe_key_uniq
ON message_outbox(dedupe_key) WHERE dedupe_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS message_outbox_pending_idx
ON message_outbox(status, next_attempt_at);

CREATE OR REPLACE FUNCTION message_outbox_touch_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS message_outbox_set_updated_at ON message_outbox;
CREATE TRIGGER message_outbox_set_updated_at
BEFORE UPDATE ON message_outbox
FOR EACH ROW
EXECUTE FUNCTION message_outbox_touch_updated_at();
"""


async def ensure_schema(store: OutboxStore) -> None:
    pool = await store._ensure_pool()
    async with pool.acquire() as conn:
        await conn.execute(MIGRATION_SQL)
        LOGGER.info("Ensured message_outbox table exists")
