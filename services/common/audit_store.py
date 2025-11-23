"""Audit event store.

Provides an append-only audit log in Postgres with simple filters and
export helpers. A lightweight in-memory implementation is available
for tests via AUDIT_STORE_MODE=memory.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import asyncpg

from src.core.config import cfg

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class AuditEvent:
    id: int
    ts: datetime
    request_id: str | None
    trace_id: str | None
    session_id: str | None
    tenant: str | None
    subject: str | None
    action: str
    resource: str
    target_id: str | None
    details: dict[str, Any] | None
    diff: dict[str, Any] | None
    ip: str | None
    user_agent: str | None


MIGRATION_SQL = """
CREATE TABLE IF NOT EXISTS audit_event (
    id BIGSERIAL PRIMARY KEY,
    ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    request_id TEXT,
    trace_id TEXT,
    session_id TEXT,
    tenant TEXT,
    subject TEXT,
    action TEXT NOT NULL,
    resource TEXT NOT NULL,
    target_id TEXT,
    details JSONB,
    diff JSONB,
    ip INET,
    user_agent TEXT
);

CREATE INDEX IF NOT EXISTS audit_event_ts_idx ON audit_event(ts DESC);
CREATE INDEX IF NOT EXISTS audit_event_request_idx ON audit_event(request_id);
CREATE INDEX IF NOT EXISTS audit_event_session_idx ON audit_event(session_id);
CREATE INDEX IF NOT EXISTS audit_event_tenant_idx ON audit_event(tenant);
CREATE INDEX IF NOT EXISTS audit_event_action_idx ON audit_event(action);
"""


class AuditStore:
    async def ensure_schema(self) -> None: ...
    async def log(self, **kwargs: Any) -> int: ...
    async def list(
        self,
        *,
        request_id: str | None = None,
        session_id: str | None = None,
        tenant: str | None = None,
        action: str | None = None,
        limit: int = 1000,
        after_id: int | None = None,
    ) -> list[AuditEvent]: ...


class PostgresAuditStore(AuditStore):
    def __init__(self, dsn: Optional[str] = None) -> None:
        # Prefer admin-wide Postgres DSN when not explicitly provided.
        # Use the admin-wide Postgres DSN singleton; it already handles env fallback.
        raw_dsn = dsn or cfg.settings().database.dsn
        self.dsn = os.path.expandvars(raw_dsn)
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
            await conn.execute(MIGRATION_SQL)
            LOGGER.info("Ensured audit_event table exists")

    async def log(self, **kwargs: Any) -> int:
        pool = await self._ensure_pool()
        fields = (
            "request_id",
            "trace_id",
            "session_id",
            "tenant",
            "subject",
            "action",
            "resource",
            "target_id",
            "details",
            "diff",
            "ip",
            "user_agent",
        )
        values = [kwargs.get(k) for k in fields]
        # Ensure JSON serialization for dict-like fields
        if isinstance(values[8], (dict, list)):
            values[8] = json.dumps(values[8], ensure_ascii=False)
        if isinstance(values[9], (dict, list)):
            values[9] = json.dumps(values[9], ensure_ascii=False)
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO audit_event (
                    request_id, trace_id, session_id, tenant, subject,
                    action, resource, target_id, details, diff, ip, user_agent
                ) VALUES (
                    $1, $2, $3, $4, $5,
                    $6, $7, $8, $9::jsonb, $10::jsonb, $11, $12
                ) RETURNING id
                """,
                *values,
            )
            return int(row["id"])  # type: ignore[index]

    async def list(
        self,
        *,
        request_id: str | None = None,
        session_id: str | None = None,
        tenant: str | None = None,
        action: str | None = None,
        limit: int = 1000,
        after_id: int | None = None,
    ) -> list[AuditEvent]:
        conditions: list[str] = []
        params: list[Any] = []
        if after_id is not None:
            params.append(after_id)
            conditions.append(f"id > ${len(params)}")
        if request_id:
            params.append(request_id)
            conditions.append(f"request_id = ${len(params)}")
        if session_id:
            params.append(session_id)
            conditions.append(f"session_id = ${len(params)}")
        if tenant:
            params.append(tenant)
            conditions.append(f"tenant = ${len(params)}")
        if action:
            params.append(action)
            conditions.append(f"action = ${len(params)}")
        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        params.append(limit)
        sql = f"""
            SELECT id, ts, request_id, trace_id, session_id, tenant, subject,
                   action, resource, target_id, details, diff, ip, user_agent
            FROM audit_event
            {where}
            ORDER BY id ASC
            LIMIT ${len(params)}
        """
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
        out: list[AuditEvent] = []
        for r in rows:
            out.append(
                AuditEvent(
                    id=r["id"],
                    ts=r["ts"],
                    request_id=r["request_id"],
                    trace_id=r["trace_id"],
                    session_id=r["session_id"],
                    tenant=r["tenant"],
                    subject=r["subject"],
                    action=r["action"],
                    resource=r["resource"],
                    target_id=r["target_id"],
                    details=r["details"],
                    diff=r["diff"],
                    ip=(str(r["ip"]) if r["ip"] is not None else None),
                    user_agent=r["user_agent"],
                )
            )
        return out


class InMemoryAuditStore(AuditStore):
    def __init__(self) -> None:
        self._rows: list[AuditEvent] = []
        self._next_id = 1

    async def ensure_schema(self) -> None:  # no-op
        return None

    async def log(self, **kwargs: Any) -> int:
        evt = AuditEvent(
            id=self._next_id,
            ts=datetime.utcnow(),
            request_id=kwargs.get("request_id"),
            trace_id=kwargs.get("trace_id"),
            session_id=kwargs.get("session_id"),
            tenant=kwargs.get("tenant"),
            subject=kwargs.get("subject"),
            action=kwargs.get("action") or "",
            resource=kwargs.get("resource") or "",
            target_id=kwargs.get("target_id"),
            details=kwargs.get("details"),
            diff=kwargs.get("diff"),
            ip=kwargs.get("ip"),
            user_agent=kwargs.get("user_agent"),
        )
        self._rows.append(evt)
        self._next_id += 1
        return evt.id

    async def list(
        self,
        *,
        request_id: str | None = None,
        session_id: str | None = None,
        tenant: str | None = None,
        action: str | None = None,
        limit: int = 1000,
        after_id: int | None = None,
    ) -> list[AuditEvent]:
        rows = [r for r in self._rows if (
            (request_id is None or r.request_id == request_id) and
            (session_id is None or r.session_id == session_id) and
            (tenant is None or r.tenant == tenant) and
            (action is None or r.action == action) and
            (after_id is None or r.id > after_id)
        )]
        return rows[:limit]


def from_env() -> AuditStore:
    mode = cfg.env("AUDIT_STORE_MODE", "postgres").lower()
    if mode == "memory":
        return InMemoryAuditStore()
    # Use admin-wide Postgres DSN when not explicitly provided.
    return PostgresAuditStore(dsn=cfg.settings().database.dsn)
