"""Tool catalog storage for enabling/disabling tools at runtime.

Backed by Postgres (asyncpg), this store provides a minimal catalog with an
enabled flag and optional description/extra params. Absent entries default to
enabled=True to preserve current behavior until explicitly toggled.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Optional

import asyncpg


from src.core.config import cfg


@dataclass
class ToolCatalogEntry:
    name: str
    enabled: bool = True
    description: str | None = None
    params: dict[str, Any] | None = None


class ToolCatalogStore:
    def __init__(self, dsn: Optional[str] = None) -> None:
        # Prefer the central configuration DSN unless an explicit override is given.
        # ``cfg.settings().database.dsn`` provides the validated Postgres DSN.
        raw_dsn = dsn or cfg.settings().database.dsn
        self.dsn = os.path.expandvars(raw_dsn)
        self._pool: Optional[asyncpg.Pool] = None

    @classmethod
    def from_settings(cls, settings: object | None = None) -> "ToolCatalogStore":
        """Constructor that accepts optional settings object."""

        database = getattr(settings, "database", None) if settings is not None else None
        dsn = getattr(database, "dsn", None) or cfg.settings().database.dsn
        return cls(dsn=dsn)

    async def _ensure_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            min_size = int(cfg.env("PG_POOL_MIN_SIZE", "1") or "1")
            max_size = int(cfg.env("PG_POOL_MAX_SIZE", "2") or "2")
            self._pool = await asyncpg.create_pool(
                self.dsn, min_size=max(0, min_size), max_size=max(1, max_size)
            )
        return self._pool

    async def ensure_schema(self) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tool_catalog (
                  name TEXT PRIMARY KEY,
                  enabled BOOLEAN NOT NULL DEFAULT TRUE,
                  description TEXT,
                  params JSONB NOT NULL DEFAULT '{}'::jsonb,
                  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                """
            )

    async def upsert(self, entry: ToolCatalogEntry) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO tool_catalog (name, enabled, description, params, updated_at)
                VALUES ($1, $2, $3, $4, now())
                ON CONFLICT (name) DO UPDATE SET
                  enabled = EXCLUDED.enabled,
                  description = EXCLUDED.description,
                  params = EXCLUDED.params,
                  updated_at = now();
                """,
                entry.name,
                bool(entry.enabled),
                entry.description,
                json.dumps(entry.params or {}),
            )

    async def set_enabled(self, name: str, enabled: bool) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE tool_catalog SET enabled=$2, updated_at=now() WHERE name=$1",
                name,
                bool(enabled),
            )

    async def is_enabled(self, name: str) -> bool:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT enabled FROM tool_catalog WHERE name=$1", name)
        if row is None:
            # Default to enabled when not explicitly configured
            return True
        return bool(row["enabled"])  # type: ignore[index]

    async def list_all(self) -> list[ToolCatalogEntry]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT name, enabled, description, params FROM tool_catalog ORDER BY name ASC"
            )
        out: list[ToolCatalogEntry] = []
        for row in rows:
            params = row["params"]
            if isinstance(params, str):
                try:
                    import json as _json

                    params = _json.loads(params)
                except Exception:
                    params = {}
            out.append(
                ToolCatalogEntry(
                    name=row["name"],
                    enabled=bool(row["enabled"]),
                    description=row["description"],
                    params=params if isinstance(params, dict) else None,
                )
            )
        return out
