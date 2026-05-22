"""DLQ Store — persistent dead-letter queue backed by PostgreSQL.

VIBE Compliant: Real production implementation.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

import asyncpg

LOGGER = logging.getLogger(__name__)


class DLQStore:
    """PostgreSQL-backed store for dead-letter events."""

    TABLE_NAME = "dlq_events"

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
        """Ensure the DLQ table exists."""
        if not self.dsn:
            raise RuntimeError("DLQStore: SA01_DB_DSN not configured")
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                        id SERIAL PRIMARY KEY,
                        topic TEXT NOT NULL,
                        event JSONB NOT NULL,
                        error TEXT,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    )
                    """
                )
        except Exception as exc:
            LOGGER.warning("DLQStore.ensure_schema failed: %s", exc)
        finally:
            await pool.close()

    async def add(
        self,
        topic: str,
        event: Dict[str, Any],
        error: Optional[str] = None,
    ) -> None:
        """Persist a dead-letter event.

        Args:
            topic: Original Kafka topic.
            event: The failed event payload.
            error: Error message / stack trace.
        """
        if not self.dsn:
            raise RuntimeError("DLQStore: SA01_DB_DSN not configured")
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    f"""
                    INSERT INTO {self.TABLE_NAME} (topic, event, error)
                    VALUES ($1, $2, $3)
                    """,
                    topic,
                    json.dumps(event),
                    error,
                )
        finally:
            await pool.close()

    async def list(
        self,
        topic: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List dead-letter events.

        Args:
            topic: Filter by topic (optional).
            limit: Maximum rows to return.

        Returns:
            List of DLQ rows as dicts.
        """
        if not self.dsn:
            raise RuntimeError("DLQStore: SA01_DB_DSN not configured")
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                if topic:
                    rows = await conn.fetch(
                        f"""
                        SELECT id, topic, event, error, created_at
                        FROM {self.TABLE_NAME}
                        WHERE topic = $1
                        ORDER BY created_at DESC
                        LIMIT $2
                        """,
                        topic,
                        limit,
                    )
                else:
                    rows = await conn.fetch(
                        f"""
                        SELECT id, topic, event, error, created_at
                        FROM {self.TABLE_NAME}
                        ORDER BY created_at DESC
                        LIMIT $1
                        """,
                        limit,
                    )
                return [
                    {
                        "id": r["id"],
                        "topic": r["topic"],
                        "event": (
                            json.loads(r["event"]) if isinstance(r["event"], str) else r["event"]
                        ),
                        "error": r["error"],
                        "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                    }
                    for r in rows
                ]
        finally:
            await pool.close()


async def ensure_schema(store: DLQStore) -> None:
    """Compatibility helper for memory replicator."""
    await store.ensure_schema()
