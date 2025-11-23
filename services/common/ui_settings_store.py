"""Minimal UI settings store used by gateway UI routes.

Backed by the same Postgres table `ui_settings` used by the sections endpoint.
Non-secret fields live there; secrets remain in SecretManager.
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

import asyncpg

from services.common.admin_settings import ADMIN_SETTINGS


class UiSettingsStore:
    def __init__(self, dsn: Optional[str] = None) -> None:
        raw_dsn = dsn or ADMIN_SETTINGS.postgres_dsn
        self.dsn = os.path.expandvars(raw_dsn)
        self._pool_obj: Optional[asyncpg.Pool] = None

    async def _pool(self) -> asyncpg.Pool:
        if self._pool_obj is None:
            self._pool_obj = await asyncpg.create_pool(self.dsn, min_size=1, max_size=2)
        return self._pool_obj

    async def ensure_schema(self) -> None:
        pool = await self._pool()
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
        await self.ensure_schema()
        pool = await self._pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT value FROM ui_settings WHERE key = 'sections'")
            if not row:
                return {}
            val = row["value"]
            return val if isinstance(val, dict) else {"sections": val} if isinstance(val, list) else {}

    async def set(self, value: dict[str, Any]) -> None:
        await self.ensure_schema()
        pool = await self._pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO ui_settings (key, value)
                VALUES ('sections', $1::jsonb)
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;
                """,
                json.dumps(value, ensure_ascii=False),
            )

__all__ = ["UiSettingsStore"]
