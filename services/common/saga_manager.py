"""
Simple Saga manager with Postgres-backed state table.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import asyncpg
import os

from src.core.config import cfg


@dataclass(slots=True)
class SagaState:
    saga_id: str
    name: str
    status: str
    step: str
    data: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class SagaManager:
    def __init__(self, dsn: Optional[str] = None) -> None:
        default_dsn = cfg.settings().database.dsn
        raw_dsn = dsn or cfg.env("POSTGRES_DSN", default_dsn) or default_dsn
        self.dsn = os.path.expandvars(raw_dsn)
        self._pool: Optional[asyncpg.Pool] = None

    async def _pool_conn(self) -> asyncpg.Pool:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(self.dsn, min_size=1, max_size=4)
        return self._pool

    async def ensure_schema(self) -> None:
        pool = await self._pool_conn()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS saga_instances (
                    saga_id UUID PRIMARY KEY,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    step TEXT NOT NULL,
                    data JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS saga_instances_name_idx ON saga_instances(name);
                CREATE INDEX IF NOT EXISTS saga_instances_status_idx ON saga_instances(status);

                CREATE OR REPLACE FUNCTION saga_touch_updated_at()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = NOW();
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;

                DROP TRIGGER IF EXISTS saga_set_updated_at ON saga_instances;
                CREATE TRIGGER saga_set_updated_at
                BEFORE UPDATE ON saga_instances
                FOR EACH ROW EXECUTE FUNCTION saga_touch_updated_at();
                """
            )

    async def start(self, name: str, step: str, data: dict[str, Any]) -> str:
        saga_id = str(uuid.uuid4())
        pool = await self._pool_conn()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO saga_instances (saga_id, name, status, step, data)
                VALUES ($1, $2, 'running', $3, $4)
                """,
                saga_id,
                name,
                step,
                data,
            )
        return saga_id

    async def list_recent(self, limit: int = 50) -> list[SagaState]:
        pool = await self._pool_conn()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT saga_id, name, status, step, data, created_at, updated_at
                FROM saga_instances
                ORDER BY updated_at DESC
                LIMIT $1
                """,
                limit,
            )
        return [
            SagaState(
                saga_id=str(r["saga_id"]),
                name=r["name"],
                status=r["status"],
                step=r["step"],
                data=r["data"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )
            for r in rows
        ]

    async def update(self, saga_id: str, step: str, status: str, data: dict[str, Any]) -> None:
        pool = await self._pool_conn()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE saga_instances
                SET step = $2, status = $3, data = $4
                WHERE saga_id = $1
                """,
                saga_id,
                step,
                status,
                data,
            )

    async def get(self, saga_id: str) -> Optional[SagaState]:
        pool = await self._pool_conn()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT saga_id, name, status, step, data, created_at, updated_at
                FROM saga_instances WHERE saga_id = $1
                """,
                saga_id,
            )
        if not row:
            return None
        return SagaState(
            saga_id=str(row["saga_id"]),
            name=row["name"],
            status=row["status"],
            step=row["step"],
            data=row["data"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def complete(self, saga_id: str) -> None:
        await self.update(saga_id, step="completed", status="completed", data={})

    async def fail(self, saga_id: str, reason: str) -> None:
        await self.update(saga_id, step="failed", status=f"failed:{reason}", data={})


# Optional in-memory compensation registry (process local)
_compensations: dict[str, Any] = {}


def register_compensation(name: str, fn) -> None:
    """Register a compensation callable keyed by saga name."""
    _compensations[name] = fn


async def run_compensation(name: str, saga_id: str, context: dict[str, Any]) -> None:
    fn = _compensations.get(name)
    if not fn:
        return
    maybe_coro = fn(saga_id, context)
    if hasattr(maybe_coro, "__await__"):
        await maybe_coro
