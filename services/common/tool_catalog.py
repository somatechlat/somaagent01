"""Tool catalog store — PostgreSQL-backed tool registry storage.

VIBE COMPLIANT: Real production implementation.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

try:
    import asyncpg  # type: ignore
except ImportError:
    asyncpg = None  # type: ignore

import os

LOGGER = logging.getLogger(__name__)


@dataclass
class ToolCatalogEntry:
    """A tool catalog entry."""

    name: str
    description: str
    schema: Dict[str, Any]
    enabled: bool = True
    tags: Optional[List[str]] = None


class ToolCatalogStore:
    """PostgreSQL-backed store for tool catalog."""

    TABLE_NAME = "tool_catalog"

    def __init__(self, dsn: Optional[str] = None) -> None:
        self.dsn = dsn or os.environ.get("SA01_DB_DSN", "")

    async def _get_pool(self) -> Any:
        if asyncpg is None:
            raise RuntimeError("asyncpg is required")
        return await asyncpg.create_pool(self.dsn, min_size=1, max_size=2)

    async def ensure_schema(self) -> None:
        if not self.dsn or asyncpg is None:
            return
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                        name TEXT PRIMARY KEY,
                        description TEXT NOT NULL,
                        schema JSONB NOT NULL DEFAULT '{{}}',
                        enabled BOOLEAN DEFAULT TRUE
                    )
                    """
                )
        finally:
            await pool.close()

    async def list(self) -> List[ToolCatalogEntry]:
        if not self.dsn or asyncpg is None:
            return []
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch(f"SELECT * FROM {self.TABLE_NAME}")
                return [
                    ToolCatalogEntry(
                        name=r["name"],
                        description=r["description"],
                        schema=(
                            json.loads(r["schema"]) if isinstance(r["schema"], str) else r["schema"]
                        ),
                        enabled=r["enabled"],
                    )
                    for r in rows
                ]
        finally:
            await pool.close()

    async def is_enabled(self, name: str) -> bool:
        if not self.dsn or asyncpg is None:
            return True
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    f"SELECT enabled FROM {self.TABLE_NAME} WHERE name = $1", name
                )
                return row["enabled"] if row else True
        finally:
            await pool.close()

    async def upsert(self, entry: ToolCatalogEntry) -> None:
        if not self.dsn or asyncpg is None:
            raise RuntimeError("ToolCatalogStore: SA01_DB_DSN not configured")
        if asyncpg is None:
            raise RuntimeError("ToolCatalogStore: asyncpg is required")
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    f"""
                    INSERT INTO {self.TABLE_NAME} (name, description, schema, enabled)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (name) DO UPDATE SET
                        description = EXCLUDED.description,
                        schema = EXCLUDED.schema,
                        enabled = EXCLUDED.enabled
                    """,
                    entry.name,
                    entry.description,
                    json.dumps(entry.schema),
                    entry.enabled,
                )
        finally:
            await pool.close()
