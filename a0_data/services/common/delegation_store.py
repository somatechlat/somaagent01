"""Delegation task persistence helpers."""
from __future__ import annotations

import json
import os
from typing import Any, Optional

import asyncpg


class DelegationStore:
    def __init__(self, dsn: Optional[str] = None) -> None:
        self.dsn = dsn or os.getenv(
            "POSTGRES_DSN", "postgresql://soma:soma@localhost:5432/somaagent01"
        )
        self._pool: Optional[asyncpg.Pool] = None

    async def _ensure_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(self.dsn, min_size=1, max_size=5)
            await self.ensure_schema()
        return self._pool

    async def ensure_schema(self) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS delegation_tasks (
                    id SERIAL PRIMARY KEY,
                    task_id TEXT UNIQUE NOT NULL,
                    status TEXT NOT NULL,
                    payload JSONB NOT NULL,
                    result JSONB,
                    callback_url TEXT,
                    metadata JSONB,
                    occurred_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                );
                """
            )

    async def create_task(
        self,
        *,
        task_id: str,
        payload: dict[str, Any],
        status: str = "queued",
        callback_url: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO delegation_tasks (task_id, status, payload, callback_url, metadata)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (task_id) DO UPDATE SET
                    status = excluded.status,
                    payload = excluded.payload,
                    callback_url = excluded.callback_url,
                    metadata = excluded.metadata,
                    updated_at = NOW()
                """,
                task_id,
                status,
                json.dumps(payload, ensure_ascii=False),
                callback_url,
                json.dumps(metadata or {}, ensure_ascii=False),
            )

    async def update_task(
        self,
        task_id: str,
        *,
        status: str,
        result: Optional[dict[str, Any]] = None,
    ) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE delegation_tasks
                SET status = $2,
                    result = $3,
                    updated_at = NOW()
                WHERE task_id = $1
                """,
                task_id,
                status,
                json.dumps(result or {}, ensure_ascii=False) if result is not None else None,
            )

    async def get_task(self, task_id: str) -> Optional[dict[str, Any]]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT task_id, status, payload, result, callback_url, metadata, occurred_at, updated_at
                FROM delegation_tasks
                WHERE task_id = $1
                """,
                task_id,
            )
        if row is None:
            return None
        return {
            "task_id": row["task_id"],
            "status": row["status"],
            "payload": row["payload"],
            "result": row["result"],
            "callback_url": row["callback_url"],
            "metadata": row["metadata"],
            "occurred_at": row["occurred_at"].isoformat() if row["occurred_at"] else None,
            "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
        }
