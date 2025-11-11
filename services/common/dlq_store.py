"""Postgres-backed Dead Letter Queue store for admin inspection.

Stores DLQ messages in a simple table for listing and purging via admin
endpoints. This complements the Kafka-based DLQ topic by providing a
queryable store inside Postgres.
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
class DLQMessage:
    id: int
    topic: str
    event: dict[str, Any]
    error: str | None
    created_at: datetime


class DLQStore:
    def __init__(self, dsn: Optional[str] = None) -> None:
        from services.common import runtime_config as cfg

        raw_dsn = dsn or cfg.db_dsn("postgresql://soma:soma@localhost:5432/somaagent01")
        self.dsn = os.path.expandvars(raw_dsn)
        self._pool: Optional[asyncpg.Pool] = None

    async def _ensure_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            min_size = int(cfg.env("PG_POOL_MIN_SIZE", "1"))
            max_size = int(cfg.env("PG_POOL_MAX_SIZE", "2"))
            self._pool = await asyncpg.create_pool(
                self.dsn, min_size=max(0, min_size), max_size=max(1, max_size)
            )
        return self._pool

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def add(self, *, topic: str, event: dict[str, Any], error: str | None = None) -> int:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO dlq_messages (topic, event, error)
                VALUES ($1, $2::jsonb, $3)
                RETURNING id
                """,
                topic,
                json.dumps(event, ensure_ascii=False),
                (error or "")[:8000],
            )
            return int(row["id"])  # type: ignore[index]

    async def list_recent(self, *, topic: str, limit: int = 100) -> list[DLQMessage]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, topic, event, error, created_at
                FROM dlq_messages
                WHERE topic = $1
                ORDER BY id DESC
                LIMIT $2
                """,
                topic,
                limit,
            )
        return [
            DLQMessage(
                id=r["id"],
                topic=r["topic"],
                event=r["event"],
                error=r["error"],
                created_at=r["created_at"],
            )
            for r in rows
        ]

    async def get_by_id(self, *, id: int) -> DLQMessage | None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, topic, event, error, created_at
                FROM dlq_messages
                WHERE id = $1
                """,
                id,
            )
        if not row:
            return None
        return DLQMessage(
            id=row["id"],
            topic=row["topic"],
            event=row["event"],
            error=row["error"],
            created_at=row["created_at"],
        )

    async def purge(self, *, topic: str) -> int:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                """
                DELETE FROM dlq_messages
                WHERE topic = $1
                """,
                topic,
            )
        try:
            # result looks like "DELETE <count>"
            return int(str(result).split(" ")[-1])
        except Exception:
            return 0

    async def count(self, *, topic: str) -> int:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT COUNT(*) AS c FROM dlq_messages WHERE topic = $1",
                topic,
            )
        return int(row["c"])  # type: ignore[index]

    async def delete_by_id(self, *, id: int) -> int:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM dlq_messages WHERE id = $1",
                id,
            )
        try:
            return int(str(result).split(" ")[-1])
        except Exception:
            return 0


MIGRATION_SQL = """
CREATE TABLE IF NOT EXISTS dlq_messages (
    id BIGSERIAL PRIMARY KEY,
    topic TEXT NOT NULL,
    event JSONB NOT NULL,
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS dlq_messages_topic_idx
ON dlq_messages(topic, id DESC);
"""


async def ensure_schema(store: DLQStore) -> None:
    pool = await store._ensure_pool()
    async with pool.acquire() as conn:
        await conn.execute(MIGRATION_SQL)
        LOGGER.info("Ensured dlq_messages table exists")
