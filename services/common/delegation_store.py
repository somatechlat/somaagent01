"""Delegation Store — persistent task delegation storage backed by PostgreSQL.

VIBE Compliant: Real production implementation.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

import asyncpg

LOGGER = logging.getLogger(__name__)


class DelegationStore:
    """PostgreSQL-backed store for delegation tasks."""

    TABLE_NAME = "delegation_tasks"

    def __init__(self, dsn: Optional[str] = None) -> None:
        """Initialize the store.

        Args:
            dsn: PostgreSQL connection string.
        """
        self.dsn = dsn or os.environ.get("SA01_DB_DSN", "")

    async def _get_pool(self) -> Any:
        """Get or create a connection pool."""
        return await asyncpg.create_pool(self.dsn, min_size=1, max_size=2)

    async def ensure_schema(self) -> None:
        """Ensure the delegation tasks table exists."""
        if not self.dsn:
            raise RuntimeError("DelegationStore: SA01_DB_DSN not configured")
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                        task_id TEXT PRIMARY KEY,
                        payload JSONB NOT NULL DEFAULT '{{}}',
                        status TEXT NOT NULL DEFAULT 'received',
                        callback_url TEXT,
                        metadata JSONB,
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        updated_at TIMESTAMPTZ DEFAULT NOW()
                    )
                    """
                )
        except Exception as exc:
            LOGGER.warning("DelegationStore.ensure_schema failed: %s", exc)
        finally:
            await pool.close()

    async def create_task(
        self,
        task_id: str,
        payload: Dict[str, Any],
        status: str = "received",
        callback_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Persist a delegation task."""
        if not self.dsn:
            raise RuntimeError("DelegationStore: SA01_DB_DSN not configured")
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    f"""
                    INSERT INTO {self.TABLE_NAME}
                        (task_id, payload, status, callback_url, metadata, updated_at)
                    VALUES ($1, $2, $3, $4, $5, NOW())
                    ON CONFLICT (task_id)
                    DO UPDATE SET
                        payload = EXCLUDED.payload,
                        status = EXCLUDED.status,
                        callback_url = EXCLUDED.callback_url,
                        metadata = EXCLUDED.metadata,
                        updated_at = NOW()
                    """,
                    task_id,
                    json.dumps(payload),
                    status,
                    callback_url,
                    json.dumps(metadata) if metadata else None,
                )
        finally:
            await pool.close()

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a task by ID."""
        if not self.dsn:
            raise RuntimeError("DelegationStore: SA01_DB_DSN not configured")
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    f"SELECT * FROM {self.TABLE_NAME} WHERE task_id = $1",
                    task_id,
                )
                if not row:
                    return None
                return {
                    "task_id": row["task_id"],
                    "payload": (
                        json.loads(row["payload"])
                        if isinstance(row["payload"], str)
                        else row["payload"]
                    ),
                    "status": row["status"],
                    "callback_url": row["callback_url"],
                    "metadata": (
                        json.loads(row["metadata"])
                        if isinstance(row["metadata"], str)
                        else row["metadata"]
                    ),
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                }
        finally:
            await pool.close()

    async def update_task(
        self,
        task_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update delegation task status and result."""
        if not self.dsn:
            raise RuntimeError("DelegationStore: SA01_DB_DSN not configured")
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    f"""
                    UPDATE {self.TABLE_NAME}
                    SET status = $1,
                        payload = COALESCE($2, payload),
                        updated_at = NOW()
                    WHERE task_id = $3
                    """,
                    status,
                    json.dumps(result) if result else None,
                    task_id,
                )
        finally:
            await pool.close()

    async def list_tasks(
        self,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List delegation tasks."""
        if not self.dsn:
            raise RuntimeError("DelegationStore: SA01_DB_DSN not configured")
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                if status:
                    rows = await conn.fetch(
                        f"""
                        SELECT * FROM {self.TABLE_NAME}
                        WHERE status = $1
                        ORDER BY created_at DESC
                        LIMIT $2
                        """,
                        status,
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
                        "task_id": r["task_id"],
                        "payload": (
                            json.loads(r["payload"])
                            if isinstance(r["payload"], str)
                            else r["payload"]
                        ),
                        "status": r["status"],
                        "callback_url": r["callback_url"],
                        "metadata": (
                            json.loads(r["metadata"])
                            if isinstance(r["metadata"], str)
                            else r["metadata"]
                        ),
                        "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                        "updated_at": r["updated_at"].isoformat() if r["updated_at"] else None,
                    }
                    for r in rows
                ]
        finally:
            await pool.close()
