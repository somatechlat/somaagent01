"""Repository for persisting cognitive state (NeuroState)."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

import asyncpg

LOGGER = logging.getLogger(__name__)


async def ensure_schema(conn: asyncpg.Connection) -> None:
    """Ensure the cognitive_states table exists."""
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS cognitive_states (
            session_id TEXT PRIMARY KEY,
            state_data JSONB NOT NULL DEFAULT '{}'::jsonb,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """
    )


class CognitiveStateStore:
    """Persists cognitive state (NeuroState) to PostgreSQL."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    async def save_state(self, session_id: str, state: Dict[str, Any]) -> None:
        """Save the cognitive state for a session."""
        query = """
            INSERT INTO cognitive_states (session_id, state_data, updated_at)
            VALUES ($1, $2, NOW())
            ON CONFLICT (session_id)
            DO UPDATE SET state_data = $2, updated_at = NOW();
        """
        try:
            conn: asyncpg.Connection
            async with asyncpg.create_pool(self._dsn, min_size=1, max_size=1) as pool:
                async with pool.acquire() as conn:
                    await ensure_schema(conn)  # Ensure schema on write (lazy)
                    await conn.execute(query, session_id, json.dumps(state))
            LOGGER.debug("Cognitive state saved", extra={"session_id": session_id})
        except Exception:
            LOGGER.error(
                "Failed to save cognitive state", exc_info=True, extra={"session_id": session_id}
            )

    async def load_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load the cognitive state for a session."""
        query = "SELECT state_data FROM cognitive_states WHERE session_id = $1"
        try:
            conn: asyncpg.Connection
            async with asyncpg.create_pool(self._dsn, min_size=1, max_size=1) as pool:
                async with pool.acquire() as conn:
                    # We don't ensure schema on read to avoid overhead, assuming write happens first or schema exists
                    # But for safety in dev, we can catch UndefinedTableError if needed.
                    # For now, let's just run it.
                    try:
                        row = await conn.fetchrow(query, session_id)
                    except asyncpg.UndefinedTableError:
                        return None

            if row:
                data = row["state_data"]
                if isinstance(data, str):
                    return json.loads(data)
                return data
            return None
        except Exception:
            LOGGER.error(
                "Failed to load cognitive state", exc_info=True, extra={"session_id": session_id}
            )
            return None
