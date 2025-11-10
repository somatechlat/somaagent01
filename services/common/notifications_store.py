"""Postgres-backed notifications store.

Schema fields:
    id UUID PRIMARY KEY
    tenant_id TEXT NOT NULL
    user_id TEXT NULL
    type TEXT NOT NULL
    title TEXT NOT NULL
    body TEXT NOT NULL
    severity TEXT NOT NULL CHECK (severity IN ('info','success','warning','error'))
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    read_at TIMESTAMPTZ NULL
    ttl_at TIMESTAMPTZ NULL
    meta JSONB NOT NULL DEFAULT '{}'::jsonb

Indexes:
    idx_notifications_tenant_created (tenant_id, created_at DESC)
    idx_notifications_tenant_read (tenant_id, read_at)
    idx_notifications_ttl (ttl_at)

The store provides CRUD helpers used by REST endpoints and janitor task.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import asyncpg

SEVERITIES = {"info", "success", "warning", "error"}


class NotificationsStore:
    def __init__(self, dsn: Optional[str] = None) -> None:
        from services.common import runtime_config as cfg
        raw_dsn = dsn or cfg.env(
            "POSTGRES_DSN", "postgresql://soma:soma@localhost:5432/somaagent01"
        )
        self.dsn = os.path.expandvars(raw_dsn)
        self._pool: Optional[asyncpg.Pool] = None

    async def _pool_ensure(self) -> asyncpg.Pool:
        if self._pool is None:
            min_size = int(cfg.env("PG_POOL_MIN_SIZE", "1"))
            max_size = int(cfg.env("PG_POOL_MAX_SIZE", "2"))
            self._pool = await asyncpg.create_pool(
                self.dsn, min_size=max(0, min_size), max_size=max(1, max_size)
            )
        return self._pool

    async def ensure_schema(self) -> None:
        pool = await self._pool_ensure()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ui_notifications (
                    id UUID PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    user_id TEXT NULL,
                    type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    body TEXT NOT NULL,
                    severity TEXT NOT NULL CHECK (severity IN ('info','success','warning','error')),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    read_at TIMESTAMPTZ NULL,
                    ttl_at TIMESTAMPTZ NULL,
                    meta JSONB NOT NULL DEFAULT '{}'::jsonb
                );
                CREATE INDEX IF NOT EXISTS idx_notifications_tenant_created ON ui_notifications (tenant_id, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_notifications_tenant_read ON ui_notifications (tenant_id, read_at);
                CREATE INDEX IF NOT EXISTS idx_notifications_ttl ON ui_notifications (ttl_at);
                """
            )

    async def create(
        self,
        *,
        tenant_id: str,
        user_id: Optional[str],
        ntype: str,
        title: str,
        body: str,
        severity: str,
        ttl_seconds: Optional[int],
        meta: Dict[str, Any],
    ) -> Dict[str, Any]:
        if severity not in SEVERITIES:
            raise ValueError("invalid severity")
        nid = uuid.uuid4()
        ttl_at = None
        if ttl_seconds and ttl_seconds > 0:
            ttl_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        pool = await self._pool_ensure()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO ui_notifications (id, tenant_id, user_id, type, title, body, severity, ttl_at, meta)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9::jsonb)
                RETURNING id, tenant_id, user_id, type, title, body, severity, created_at, read_at, ttl_at, meta
                """,
                nid,
                tenant_id,
                user_id,
                ntype,
                title,
                body,
                severity,
                ttl_at,
                json.dumps(meta or {}, ensure_ascii=False),
            )
        return self._format(row)

    async def list(
        self,
        *,
        tenant_id: str,
        user_id: Optional[str],
        limit: int = 50,
        severity: Optional[str] = None,
        unread_only: bool = False,
        cursor_created_at: Optional[datetime] = None,
        cursor_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        pool = await self._pool_ensure()
        base_sql = [
            "SELECT id, tenant_id, user_id, type, title, body, severity, created_at, read_at, ttl_at, meta FROM ui_notifications WHERE tenant_id = $1"
        ]
        params: List[Any] = [tenant_id]
        idx = 2
        if user_id:
            base_sql.append(f"AND (user_id IS NULL OR user_id = ${idx})")
            params.append(user_id)
            idx += 1
        if severity:
            base_sql.append(f"AND severity = ${idx}")
            params.append(severity)
            idx += 1
        if unread_only:
            base_sql.append("AND read_at IS NULL")
        if cursor_created_at and cursor_id:
            base_sql.append(f"AND (created_at, id) < (${idx}, ${idx+1})")
            params.append(cursor_created_at)
            params.append(uuid.UUID(cursor_id))
            idx += 2
        base_sql.append("ORDER BY created_at DESC, id DESC")
        base_sql.append(f"LIMIT {max(1,min(limit,200))}")
        sql = "\n".join(base_sql)
        async with pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
        return [self._format(r) for r in rows]

    async def mark_read(self, *, tenant_id: str, notif_id: str, user_id: Optional[str]) -> bool:
        pool = await self._pool_ensure()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE ui_notifications SET read_at = NOW()
                WHERE id = $1 AND tenant_id = $2 AND (user_id IS NULL OR user_id = $3) AND read_at IS NULL
                RETURNING id
                """,
                uuid.UUID(notif_id),
                tenant_id,
                user_id,
            )
        return bool(row)

    async def clear(self, *, tenant_id: str, user_id: Optional[str]) -> int:
        pool = await self._pool_ensure()
        async with pool.acquire() as conn:
            result = await conn.execute(
                """
                DELETE FROM ui_notifications
                WHERE tenant_id = $1 AND (user_id IS NULL OR user_id = $2)
                """,
                tenant_id,
                user_id,
            )
        # asyncpg returns e.g. 'DELETE 5'
        try:
            return int(result.split()[-1])
        except Exception:
            return 0

    async def delete_expired(self) -> int:
        pool = await self._pool_ensure()
        async with pool.acquire() as conn:
            result = await conn.execute(
                """
                DELETE FROM ui_notifications WHERE ttl_at IS NOT NULL AND ttl_at < NOW()
                """
            )
        try:
            return int(result.split()[-1])
        except Exception:
            return 0

    def _format(self, row: Any) -> Dict[str, Any]:
        meta = row["meta"]
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except Exception:
                meta = {}
        return {
            "id": str(row["id"]),
            "tenant_id": row["tenant_id"],
            "user_id": row["user_id"],
            "type": row["type"],
            "title": row["title"],
            "body": row["body"],
            "severity": row["severity"],
            "created_at": (
                row["created_at"].isoformat()
                if getattr(row["created_at"], "isoformat", None)
                else None
            ),
            "read_at": row["read_at"].isoformat() if row["read_at"] else None,
            "ttl_at": row["ttl_at"].isoformat() if row["ttl_at"] else None,
            "meta": meta if isinstance(meta, dict) else {},
        }
