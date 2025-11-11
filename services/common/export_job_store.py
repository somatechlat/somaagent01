"""Postgres-backed store for asynchronous memory export jobs.

Keeps track of job parameters, status, output file path and simple metrics.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import asyncpg


@dataclass(slots=True)
class ExportJob:
    id: int
    status: str
    params: dict[str, Any]
    tenant: Optional[str]
    file_path: Optional[str]
    row_count: Optional[int]
    byte_size: Optional[int]
    error: Optional[str]
    created_at: datetime
    updated_at: datetime


class ExportJobStore:
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

    async def create(self, *, params: dict[str, Any], tenant: Optional[str]) -> int:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO export_jobs (status, params, tenant)
                VALUES ('queued', $1::jsonb, $2)
                RETURNING id
                """,
                json.dumps(params, ensure_ascii=False),
                tenant,
            )
            return int(row["id"])  # type: ignore[index]

    async def get(self, job_id: int) -> Optional[ExportJob]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, status, params, tenant, file_path, row_count, byte_size, error, created_at, updated_at
                FROM export_jobs WHERE id = $1
                """,
                job_id,
            )
            if not row:
                return None
            return ExportJob(
                id=row["id"],
                status=row["status"],
                params=row["params"],
                tenant=row["tenant"],
                file_path=row["file_path"],
                row_count=row["row_count"],
                byte_size=row["byte_size"],
                error=row["error"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    async def claim_next(self) -> Optional[int]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    """
                    SELECT id FROM export_jobs
                    WHERE status = 'queued'
                    ORDER BY id
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                    """
                )
                if not row:
                    return None
                job_id = int(row["id"])
                await conn.execute(
                    "UPDATE export_jobs SET status = 'running', updated_at = NOW() WHERE id = $1",
                    job_id,
                )
                return job_id

    async def mark_running(self, job_id: int) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE export_jobs SET status = 'running', updated_at = NOW() WHERE id = $1",
                job_id,
            )

    async def mark_complete(
        self, job_id: int, *, file_path: str, rows: int, byte_size: int
    ) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE export_jobs
                SET status = 'completed', file_path = $2, row_count = $3, byte_size = $4, updated_at = NOW()
                WHERE id = $1
                """,
                job_id,
                file_path,
                rows,
                byte_size,
            )

    async def mark_failed(self, job_id: int, *, error: str) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE export_jobs SET status = 'failed', error = $2, updated_at = NOW() WHERE id = $1",
                job_id,
                error[:8000],
            )


MIGRATION_SQL = """
CREATE TABLE IF NOT EXISTS export_jobs (
    id BIGSERIAL PRIMARY KEY,
    status TEXT NOT NULL,
    params JSONB NOT NULL,
    tenant TEXT,
    file_path TEXT,
    row_count BIGINT,
    byte_size BIGINT,
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS export_jobs_status_idx ON export_jobs(status, id);
"""


async def ensure_schema(store: ExportJobStore) -> None:
    pool = await store._ensure_pool()
    async with pool.acquire() as conn:
        await conn.execute(MIGRATION_SQL)
