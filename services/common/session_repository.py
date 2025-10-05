"""Session repository abstractions for SomaAgent 01."""
from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Optional

import asyncpg
import redis.asyncio as redis

LOGGER = logging.getLogger(__name__)


class SessionCache(ABC):
    @abstractmethod
    async def get(self, key: str) -> Optional[dict[str, Any]]: ...

    @abstractmethod
    async def set(self, key: str, value: dict[str, Any], ttl: int = 0) -> None: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...

    async def ping(self) -> None:
        """Optional health check hook."""
        return None


class RedisSessionCache(SessionCache):
    def __init__(self, url: Optional[str] = None) -> None:
        self.url = url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._client: redis.Redis = redis.from_url(self.url, decode_responses=True)

    async def get(self, key: str) -> Optional[dict[str, Any]]:
        raw = await self._client.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def set(self, key: str, value: dict[str, Any], ttl: int = 0) -> None:
        data = json.dumps(value, ensure_ascii=False)
        if ttl > 0:
            await self._client.setex(key, ttl, data)
        else:
            await self._client.set(key, data)

    async def delete(self, key: str) -> None:
        await self._client.delete(key)

    async def ping(self) -> None:
        await self._client.ping()


class SessionStore(ABC):
    @abstractmethod
    async def append_event(self, session_id: str, event: dict[str, Any]) -> None: ...

    @abstractmethod
    async def list_events(self, session_id: str, limit: int = 100) -> list[dict[str, Any]]: ...


class PostgresSessionStore(SessionStore):
    def __init__(self, dsn: Optional[str] = None) -> None:
        self.dsn = dsn or os.getenv(
            "POSTGRES_DSN", "postgresql://soma:soma@localhost:5432/somaagent01"
        )
        self._pool: Optional[asyncpg.Pool] = None

    async def _ensure_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(self.dsn, min_size=1, max_size=5)
        return self._pool

    async def ping(self) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute("SELECT 1")

    async def append_event(self, session_id: str, event: dict[str, Any]) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO session_events (session_id, payload)
                VALUES ($1, $2)
                """,
                session_id,
                json.dumps(event, ensure_ascii=False),
            )

    async def list_events(self, session_id: str, limit: int = 100) -> list[dict[str, Any]]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT payload
                FROM session_events
                WHERE session_id = $1
                ORDER BY id DESC
                LIMIT $2
                """,
                session_id,
                limit,
            )
        return [json.loads(r["payload"]) for r in rows]


MIGRATION_SQL = """
CREATE TABLE IF NOT EXISTS session_events (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload JSONB NOT NULL
);
"""


async def ensure_schema(store: PostgresSessionStore) -> None:
    pool = await store._ensure_pool()
    async with pool.acquire() as conn:
        await conn.execute(MIGRATION_SQL)
        LOGGER.info("Ensured session_events table exists")
