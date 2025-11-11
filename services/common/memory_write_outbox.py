"""Postgres-backed outbox for SomaBrain memory writes.

When `remember()` fails (e.g., SomaBrain unavailable), enqueue the memory
payload here for later retry by the memory_sync worker. On success, the worker
also publishes `memory.wal` so the replica stays consistent.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import asyncpg

from services.common import runtime_config as cfg


@dataclass(slots=True)
class MemoryWriteItem:
    id: int
    payload: dict[str, Any]
    status: str
    retry_count: int
    next_attempt_at: datetime
    tenant: Optional[str]
    session_id: Optional[str]
    persona_id: Optional[str]
    idempotency_key: Optional[str]
    last_error: Optional[str]
    created_at: datetime
    updated_at: datetime


class MemoryWriteOutbox:
    def __init__(self, dsn: Optional[str] = None) -> None:
        raw_dsn = (
            dsn
            or cfg.db_dsn("postgresql://soma:soma@localhost:5432/somaagent01")
            or "postgresql://soma:soma@localhost:5432/somaagent01"
        )
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

    # Writer API
    async def enqueue(
        self,
        *,
        payload: dict[str, Any],
        tenant: Optional[str] = None,
        session_id: Optional[str] = None,
        persona_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        dedupe_key: Optional[str] = None,
    ) -> Optional[int]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO memory_write_outbox (
                    payload, status, retry_count, next_attempt_at,
                    tenant, session_id, persona_id, idempotency_key, dedupe_key
                ) VALUES (
                    $1::jsonb, 'pending', 0, NOW(),
                    $2, $3, $4, $5, $6
                )
                ON CONFLICT (dedupe_key) WHERE dedupe_key IS NOT NULL DO NOTHING
                RETURNING id
                """,
                json.dumps(payload, ensure_ascii=False),
                tenant,
                session_id,
                persona_id,
                idempotency_key,
                dedupe_key,
            )
        if not row:
            return None
        return int(row["id"])

    # Worker API
    async def claim_batch(self, *, limit: int = 100) -> list[MemoryWriteItem]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                rows = await conn.fetch(
                    """
                    SELECT id, payload, status, retry_count, next_attempt_at,
                           tenant, session_id, persona_id, idempotency_key,
                           last_error, created_at, updated_at
                    FROM memory_write_outbox
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
                        UPDATE memory_write_outbox
                        SET status = 'sending', updated_at = NOW()
                        WHERE id = ANY($1::bigint[])
                        """,
                        ids,
                    )
        items: list[MemoryWriteItem] = []
        for r in rows:
            items.append(
                MemoryWriteItem(
                    id=r["id"],
                    payload=r["payload"],
                    status="sending",
                    retry_count=r["retry_count"],
                    next_attempt_at=r["next_attempt_at"],
                    tenant=r["tenant"],
                    session_id=r["session_id"],
                    persona_id=r["persona_id"],
                    idempotency_key=r["idempotency_key"],
                    last_error=r["last_error"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
            )
        return items

    async def mark_sent(self, item_id: int) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE memory_write_outbox
                SET status = 'sent', updated_at = NOW(), last_error = NULL, last_error_at = NULL
                WHERE id = $1
                """,
                item_id,
            )

    async def mark_retry(self, item_id: int, *, backoff_seconds: float, error: str) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE memory_write_outbox
                SET status = 'pending',
                    retry_count = retry_count + 1,
                    next_attempt_at = NOW() + make_interval(secs => $2::double precision),
                    last_error = $3,
                    last_error_at = NOW(),
                    updated_at = NOW()
                WHERE id = $1
                """,
                item_id,
                backoff_seconds,
                error[:8000],
            )

    async def mark_failed(self, item_id: int, *, error: str) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE memory_write_outbox
                SET status = 'failed', last_error = $2, last_error_at = NOW(), updated_at = NOW()
                WHERE id = $1
                """,
                item_id,
                error[:8000],
            )

    async def count_pending(self) -> int:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT COUNT(*) AS c FROM memory_write_outbox WHERE status='pending'"
            )
            return int(row["c"])  # type: ignore[index]

    async def get_health_metrics(self) -> dict[str, Any]:
        """Get health metrics for memory monitoring."""
        try:
            pool = await self._ensure_pool()
            async with pool.acquire() as conn:
                # Get pending count
                pending = await conn.fetchrow(
                    "SELECT COUNT(*) as count FROM memory_write_outbox WHERE status='pending'"
                )

                # Get failed count
                failed = await conn.fetchrow(
                    "SELECT COUNT(*) as count FROM memory_write_outbox WHERE status='failed'"
                )

                # Get oldest pending
                oldest = await conn.fetchrow(
                    "SELECT MIN(created_at) as oldest FROM memory_write_outbox WHERE status='pending'"
                )

                # Get retry statistics
                retry_stats = await conn.fetchrow(
                    """
                    SELECT
                        AVG(retry_count) as avg_retries,
                        MAX(retry_count) as max_retries
                    FROM memory_write_outbox
                    WHERE status='pending' OR status='failed'
                    """
                )

                return {
                    "pending_count": int(pending["count"]),
                    "failed_count": int(failed["count"]),
                    "oldest_pending": str(oldest["oldest"]) if oldest["oldest"] else None,
                    "avg_retries": float(retry_stats["avg_retries"] or 0),
                    "max_retries": int(retry_stats["max_retries"] or 0),
                    "healthy": int(pending["count"]) < 100,  # Alert if >100 pending
                }
        except Exception as e:
            return {"error": str(e), "healthy": False}

    async def get_lag_metrics(self) -> dict[str, Any]:
        """Calculate WAL lag metrics for memory monitoring."""
        try:
            pool = await self._ensure_pool()
            async with pool.acquire() as conn:
                # Get latest processed WAL timestamp
                latest_processed = await conn.fetchrow(
                    "SELECT MAX(updated_at) as latest FROM memory_write_outbox WHERE status='sent'"
                )

                # Calculate lag if we have processed items
                if latest_processed and latest_processed["latest"]:
                    lag_seconds = (datetime.now() - latest_processed["latest"]).total_seconds()
                    return {
                        "wal_lag_seconds": max(0, lag_seconds),
                        "latest_processed": str(latest_processed["latest"]),
                    }
                else:
                    return {
                        "wal_lag_seconds": 0,
                        "latest_processed": None,
                        "note": "No processed items found",
                    }
        except Exception as e:
            return {"error": str(e), "wal_lag_seconds": -1}

    async def get_sla_metrics(self) -> dict[str, Any]:
        """Get SLA compliance metrics for memory operations."""
        try:
            pool = await self._ensure_pool()
            async with pool.acquire() as conn:
                # Get SLA compliance data
                sla_data = await conn.fetchrow(
                    """
                    SELECT 
                        COUNT(CASE WHEN status = 'sent' AND 
                                  updated_at - created_at <= INTERVAL '5 seconds' 
                                  THEN 1 END) as sla_compliant,
                        COUNT(CASE WHEN status = 'sent' THEN 1 END) as total_sent,
                        AVG(CASE WHEN status = 'sent' 
                                 THEN EXTRACT(EPOCH FROM (updated_at - created_at)) END) as avg_latency,
                        MAX(EXTRACT(EPOCH FROM (updated_at - created_at))) as max_latency
                    FROM memory_write_outbox 
                    WHERE created_at >= NOW() - INTERVAL '1 hour'
                    """
                )

                compliance_rate = 0.0
                if sla_data["total_sent"] and sla_data["total_sent"] > 0:
                    compliance_rate = float(sla_data["sla_compliant"] or 0) / float(
                        sla_data["total_sent"]
                    )

                return {
                    "sla_compliance_rate": compliance_rate,
                    "avg_latency_seconds": float(sla_data["avg_latency"] or 0),
                    "max_latency_seconds": float(sla_data["max_latency"] or 0),
                    "total_processed": int(sla_data["total_sent"] or 0),
                }
        except Exception as e:
            return {"error": str(e), "sla_compliance_rate": 0.0}

    async def cleanup_stale_retries(self, max_age_hours: int = 24) -> int:
        """Clean up stale retry attempts to prevent infinite loops."""
        try:
            pool = await self._ensure_pool()
            async with pool.acquire() as conn:
                result = await conn.fetch(
                    """
                    DELETE FROM memory_write_outbox 
                    WHERE status = 'failed' 
                    AND retry_count >= 10
                    AND updated_at < NOW() - INTERVAL '%s hours'
                    RETURNING 1
                    """
                    % max_age_hours
                )
                return len(result)
        except Exception as e:
            print(f"Cleanup failed: {e}")
            return 0

    async def get_tenant_metrics(self, tenant: str) -> dict[str, Any]:
        """Get per-tenant memory metrics for monitoring."""
        try:
            pool = await self._ensure_pool()
            async with pool.acquire() as conn:
                tenant_data = await conn.fetchrow(
                    """
                    SELECT 
                        COUNT(*) as total_messages,
                        COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
                        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
                        COUNT(CASE WHEN status = 'sent' THEN 1 END) as sent,
                        AVG(retry_count) as avg_retries,
                        MAX(created_at) as latest_message
                    FROM memory_write_outbox 
                    WHERE tenant = $1
                    """,
                    tenant,
                )

                return {
                    "tenant": tenant,
                    "total_messages": int(tenant_data["total_messages"] or 0),
                    "pending": int(tenant_data["pending"] or 0),
                    "failed": int(tenant_data["failed"] or 0),
                    "sent": int(tenant_data["sent"] or 0),
                    "avg_retries": float(tenant_data["avg_retries"] or 0),
                    "latest_message": str(tenant_data["latest_message"] or ""),
                }
        except Exception as e:
            return {"tenant": tenant, "error": str(e)}

    def _validate_payload(self, payload: dict[str, Any]) -> None:
        """Validate payload structure and required fields."""
        required_fields = ["type", "role", "content"]
        for field in required_fields:
            if field not in payload:
                raise ValueError(f"Missing required field: {field}")

        # Validate tenant/session consistency
        tenant = payload.get("tenant") or (payload.get("metadata") or {}).get("tenant")
        session_id = payload.get("session_id") or (payload.get("metadata") or {}).get("session_id")

        if not tenant:
            raise ValueError("Tenant is required for memory operations")

        if not session_id:
            raise ValueError("Session ID is required for memory operations")

    async def safe_enqueue(
        self,
        *,
        payload: dict[str, Any],
        tenant: str,
        session_id: str,
        persona_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> int | None:
        """Enqueue with full validation and safety checks."""
        try:
            # Validate payload
            self._validate_payload(payload)

            # Ensure idempotency key if missing
            if not idempotency_key:
                from services.common.idempotency import generate_for_memory_payload

                idempotency_key = generate_for_memory_payload(payload)

            # Rate limit check
            if await self._check_rate_limit(tenant, session_id):
                raise RuntimeError(f"Rate limit exceeded for tenant {tenant}")

            return await self.enqueue(
                payload=payload,
                tenant=tenant,
                session_id=session_id,
                persona_id=persona_id,
                idempotency_key=idempotency_key,
            )
        except Exception as e:
            # Log error and return None
            import logging

            logging.error(f"Failed to enqueue memory write: {e}")
            return None

    async def _check_rate_limit(self, tenant: str, session_id: str) -> bool:
        """Check if rate limit is exceeded for tenant."""
        try:
            pool = await self._ensure_pool()
            async with pool.acquire() as conn:
                recent_count = await conn.fetchval(
                    """
                    SELECT COUNT(*) FROM memory_write_outbox 
                    WHERE tenant = $1 AND session_id = $2
                    AND created_at > NOW() - INTERVAL '1 minute'
                    """,
                    tenant,
                    session_id,
                )
                return int(recent_count or 0) >= 100  # 100 messages per minute per session
        except Exception:
            return False


MIGRATION_SQL = """
CREATE TABLE IF NOT EXISTS memory_write_outbox (
    id BIGSERIAL PRIMARY KEY,
    payload JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    retry_count INT NOT NULL DEFAULT 0,
    next_attempt_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    tenant TEXT,
    session_id TEXT,
    persona_id TEXT,
    idempotency_key TEXT,
    dedupe_key TEXT,
    last_error TEXT,
    last_error_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS memory_write_outbox_dedupe_uniq
ON memory_write_outbox(dedupe_key) WHERE dedupe_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS memory_write_outbox_pending_idx
ON memory_write_outbox(status, next_attempt_at);

CREATE OR REPLACE FUNCTION memory_write_outbox_touch_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS memory_write_outbox_set_updated_at ON memory_write_outbox;
CREATE TRIGGER memory_write_outbox_set_updated_at
BEFORE UPDATE ON memory_write_outbox
FOR EACH ROW
EXECUTE FUNCTION memory_write_outbox_touch_updated_at();
"""


async def ensure_schema(store: MemoryWriteOutbox) -> None:
    pool = await store._ensure_pool()
    async with pool.acquire() as conn:
        await conn.execute(MIGRATION_SQL)
