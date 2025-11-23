"""Postgres-backed attachments store (no local filesystem).

Stores attachment bytes inline in BYTEA with metadata. Provides schema ensure,
insert, fetch, and TTL purge helpers.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import asyncpg

from src.core.config import cfg
from src.core.config import cfg


@dataclass(slots=True)
class Attachment:
    id: uuid.UUID
    tenant: Optional[str]
    session_id: Optional[str]
    persona_id: Optional[str]
    filename: str
    mime: str
    size: int
    sha256: str
    status: str  # 'clean' | 'quarantined'
    quarantine_reason: Optional[str]
    created_at: datetime


class AttachmentsStore:
    def __init__(self, dsn: Optional[str] = None) -> None:
        # Use centralized admin settings for Postgres DSN when not explicitly provided.
        default_dsn = cfg.settings().database.dsn
        raw_dsn = dsn or default_dsn
        self.dsn = raw_dsn
        self._pool: Optional[asyncpg.Pool] = None

    async def _ensure_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            min_size = int(cfg.env("PG_POOL_MIN_SIZE", "1") or "1")
            max_size = int(cfg.env("PG_POOL_MAX_SIZE", "2") or "2")
            self._pool = await asyncpg.create_pool(self.dsn, min_size=max(0, min_size), max_size=max(1, max_size))
        return self._pool

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def ensure_schema(self) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS attachments (
                    id UUID PRIMARY KEY,
                    tenant TEXT,
                    session_id TEXT,
                    persona_id TEXT,
                    filename TEXT NOT NULL,
                    mime TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    sha256 TEXT NOT NULL,
                    status TEXT NOT NULL CHECK (status IN ('clean','quarantined')),
                    quarantine_reason TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    content BYTEA
                );
                CREATE INDEX IF NOT EXISTS attachments_session_idx ON attachments(session_id, created_at DESC);
                CREATE INDEX IF NOT EXISTS attachments_tenant_idx ON attachments(tenant, created_at DESC);
                CREATE INDEX IF NOT EXISTS attachments_sha_idx ON attachments(tenant, sha256);
                """
            )

    async def insert(
        self,
        *,
        tenant: Optional[str],
        session_id: Optional[str],
        persona_id: Optional[str],
        filename: str,
        mime: str,
        size: int,
        sha256: str,
        status: str,
        quarantine_reason: Optional[str],
        content: Optional[bytes],
    ) -> uuid.UUID:
        att_id = uuid.uuid4()
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO attachments (
                    id, tenant, session_id, persona_id, filename, mime, size, sha256,
                    status, quarantine_reason, content
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8,
                    $9, $10, $11
                )
                """,
                att_id,
                tenant,
                session_id,
                persona_id,
                filename,
                mime,
                size,
                sha256,
                status,
                quarantine_reason,
                content,
            )
        return att_id

    async def get_metadata(self, att_id: uuid.UUID) -> Optional[Attachment]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, tenant, session_id, persona_id, filename, mime, size, sha256,
                       status, quarantine_reason, created_at
                FROM attachments WHERE id = $1
                """,
                att_id,
            )
        if not row:
            return None
        return Attachment(
            id=row["id"],
            tenant=row["tenant"],
            session_id=row["session_id"],
            persona_id=row["persona_id"],
            filename=row["filename"],
            mime=row["mime"],
            size=row["size"],
            sha256=row["sha256"],
            status=row["status"],
            quarantine_reason=row["quarantine_reason"],
            created_at=row["created_at"],
        )

    async def get_content(self, att_id: uuid.UUID) -> Optional[bytes]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT content FROM attachments WHERE id = $1", att_id)
        if not row:
            return None
        return row["content"]

    async def delete_older_than(self, days: float) -> int:
        cutoff = datetime.utcnow() - timedelta(days=days)
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            result = await conn.execute("DELETE FROM attachments WHERE created_at < $1", cutoff)
        # result like 'DELETE <count>'
        try:
            return int(result.split()[-1])
        except Exception:
            return 0
