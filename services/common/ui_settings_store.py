"""Simple Postgres-backed store for UI settings.

Stores a single JSONB document under a fixed key ("global"). This holds
operator-facing configuration that does not belong to secrets (Redis) or
model profiles (existing table).
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional

import asyncpg


class UiSettingsStore:
    def __init__(self, dsn: Optional[str] = None) -> None:
        raw_dsn = dsn or os.getenv("POSTGRES_DSN", "postgresql://soma:soma@localhost:5432/somaagent01")
        self.dsn = os.path.expandvars(raw_dsn)
        self._pool: Optional[asyncpg.Pool] = None

    async def _pool_ensure(self) -> asyncpg.Pool:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(self.dsn, min_size=1, max_size=4)
        return self._pool

    async def ensure_schema(self) -> None:
        pool = await self._pool_ensure()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ui_settings (
                    key TEXT PRIMARY KEY,
                    value JSONB NOT NULL DEFAULT '{}'::jsonb
                );
                """
            )

    async def get(self) -> dict[str, Any]:
        pool = await self._pool_ensure()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT value FROM ui_settings WHERE key = 'global'")
            if not row:
                return {}
            val = row["value"]
            return dict(val) if isinstance(val, dict) else {}

    async def set(self, value: dict[str, Any]) -> None:
        pool = await self._pool_ensure()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO ui_settings (key, value)
                VALUES ('global', $1::jsonb)
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;
                """,
                json.dumps(value, ensure_ascii=False),
            )

