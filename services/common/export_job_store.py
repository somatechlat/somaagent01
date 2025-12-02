"""Postgres-backed store for asynchronous memory export jobs.

Keeps track of job parameters, status, output file path and simple metrics.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import asyncpg

from services.common.admin_settings import ADMIN_SETTINGS
from src.core.config import cfg


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

    # Compatibility alias used by older code expecting ``result_path``.
    @property
    def result_path(self) -> Optional[str]:
        return self.file_path


class ExportJobStatus(str, Enum):
    """Enum representing the lifecycle states of an export job.

    The original codebase referenced this enum for type‑checking and status
    comparisons.  It mirrors the string values stored in the ``status`` column
    of the ``export_jobs`` table.
    """

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ExportJobStore:
    def __init__(self, dsn: Optional[str] = None) -> None:
        # Prefer admin-wide Postgres DSN when not explicitly provided.
        # Use the admin-wide Postgres DSN; ADMIN_SETTINGS already resolves any environment overrides.
        raw_dsn = dsn or ADMIN_SETTINGS.postgres_dsn
        self.dsn = os.path.expandvars(raw_dsn)
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

    # ---------------------------------------------------------------------
    # Legacy helper methods expected by ``services.gateway.routers.memory_exports``
    # ---------------------------------------------------------------------
    async def create_job(
        self, tenant: Optional[str], namespace: Optional[str], limit: Optional[int]
    ) -> ExportJob:
        """Create a new export job and return the full ``ExportJob`` record.

        The original monolith exposed a ``create_job`` method that accepted the
        three parameters used by the router.  Internally we store them in the
        ``params`` JSON column.  After insertion we retrieve the complete record
        to provide ``id``, ``status`` and the ``result_path`` (alias for
        ``file_path``).
        """
        params = {"namespace": namespace, "limit": limit}
        job_id = await self.create(params=params, tenant=tenant)
        job = await self.get(job_id)
        return (
            job
            if job is not None
            else ExportJob(
                id=job_id,
                status="queued",
                params=params,
                tenant=tenant,
                file_path=None,
                row_count=None,
                byte_size=None,
                error=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )

    async def get_job(self, job_id: int) -> Optional[ExportJob]:
        """Legacy wrapper returning the same shape as the original ``ExportJob``.

        The router accesses ``job.id``, ``job.status`` and ``job.result_path``.
        ``ExportJob`` already provides these attributes (``result_path`` is a
        property defined above).
        """
        return await self.get(job_id)

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
