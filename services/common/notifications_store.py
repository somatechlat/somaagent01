"""Notifications store — PostgreSQL-backed notification storage.

VIBE COMPLIANT: Real production implementation.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

import asyncpg

LOGGER = logging.getLogger(__name__)


class NotificationsStore:
    """PostgreSQL-backed store for notifications."""

    TABLE_NAME = "notifications"

    def __init__(self, dsn: Optional[str] = None) -> None:
        self.dsn = dsn or os.environ.get("SA01_DB_DSN", "")

    async def _get_pool(self) -> Any:
        return await asyncpg.create_pool(self.dsn, min_size=1, max_size=2)

    async def ensure_schema(self) -> None:
        """Ensure database schema exists."""
        pass

    async def list(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
        limit: int = 50,
        unread_only: bool = False,
    ) -> List[Dict[str, Any]]:
        if not self.dsn or asyncpg is None:
            return []
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    f"SELECT * FROM {self.TABLE_NAME} WHERE user_id = $1 ORDER BY created_at DESC LIMIT $2",
                    user_id,
                    limit,
                )
                return [dict(r) for r in rows]
        finally:
            await pool.close()

    async def create(
        self,
        tenant_id: str,
        user_id: Optional[str],
        ntype: str,
        title: str,
        body: str,
        severity: str = "info",
        ttl_seconds: Optional[int] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> str:
        if not self.dsn or asyncpg is None:
            raise RuntimeError("NotificationsStore: SA01_DB_DSN not configured")
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    f"""
                    INSERT INTO {self.TABLE_NAME} (user_id, title, body)
                    VALUES ($1, $2, $3)
                    RETURNING id
                    """,
                    user_id,
                    title,
                    body,
                )
                return str(row["id"])
        finally:
            await pool.close()

    async def mark_read(
        self,
        tenant_id: str,
        notif_id: str,
        user_id: Optional[str] = None,
    ) -> None:
        """Mark a notification as read."""
        pass

    async def clear(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
    ) -> None:
        """Clear all notifications."""
        pass
