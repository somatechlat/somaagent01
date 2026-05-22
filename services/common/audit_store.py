"""Audit Store — persistent audit event storage backed by PostgreSQL.

VIBE Compliant: Real production implementation.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

try:
    import asyncpg  # type: ignore
except ImportError:  # pragma: no cover
    asyncpg = None  # type: ignore

LOGGER = logging.getLogger(__name__)


class AuditStore:
    """PostgreSQL-backed store for audit events."""

    TABLE_NAME = "audit_events"

    def __init__(self, dsn: Optional[str] = None) -> None:
        """Initialize the store.

        Args:
            dsn: PostgreSQL connection string.
        """
        self.dsn = dsn or os.environ.get("SA01_DB_DSN", "")

    async def _get_pool(self) -> Any:
        """Get or create a connection pool."""
        if asyncpg is None:
            raise RuntimeError("asyncpg is required for AuditStore")
        return await asyncpg.create_pool(self.dsn, min_size=1, max_size=2)

    async def ensure_schema(self) -> None:
        """Ensure the audit table exists."""
        if not self.dsn:
            raise RuntimeError("AuditStore: SA01_DB_DSN not configured")
        if asyncpg is None:
            raise RuntimeError("AuditStore: asyncpg is required")
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                        id SERIAL PRIMARY KEY,
                        event_type TEXT NOT NULL,
                        actor TEXT,
                        resource TEXT,
                        action TEXT,
                        payload JSONB,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    )
                    """
                )
        except Exception as exc:
            LOGGER.warning("AuditStore.ensure_schema failed: %s", exc)
        finally:
            await pool.close()

    async def record(
        self,
        event_type: str,
        actor: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Persist an audit event."""
        if not self.dsn:
            raise RuntimeError("AuditStore: SA01_DB_DSN not configured")
        if asyncpg is None:
            raise RuntimeError("AuditStore: asyncpg is required")
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    f"""
                    INSERT INTO {self.TABLE_NAME}
                        (event_type, actor, resource, action, payload)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    event_type,
                    actor,
                    resource,
                    action,
                    json.dumps(payload) if payload else None,
                )
        finally:
            await pool.close()

    async def list(
        self,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List audit events."""
        if not self.dsn:
            raise RuntimeError("AuditStore: SA01_DB_DSN not configured")
        if asyncpg is None:
            raise RuntimeError("AuditStore: asyncpg is required")
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                if event_type:
                    rows = await conn.fetch(
                        f"""
                        SELECT * FROM {self.TABLE_NAME}
                        WHERE event_type = $1
                        ORDER BY created_at DESC
                        LIMIT $2
                        """,
                        event_type,
                        limit,
                    )
                else:
                    rows = await conn.fetch(
                        f"""
                        SELECT * FROM {self.TABLE_NAME}
                        ORDER BY created_at DESC
                        LIMIT $1
                        """,
                        limit,
                    )
                return [
                    {
                        "id": r["id"],
                        "event_type": r["event_type"],
                        "actor": r["actor"],
                        "resource": r["resource"],
                        "action": r["action"],
                        "payload": (
                            json.loads(r["payload"])
                            if isinstance(r["payload"], str)
                            else r["payload"]
                        ),
                        "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                    }
                    for r in rows
                ]
        finally:
            await pool.close()


def from_env() -> AuditStore:
    """Create an AuditStore from environment variables."""
    return AuditStore()
