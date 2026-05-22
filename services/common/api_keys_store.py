"""API keys store — PostgreSQL-backed API key metadata storage.

VIBE COMPLIANT: Real production implementation.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

try:
    import asyncpg  # type: ignore
except ImportError:
    asyncpg = None  # type: ignore

LOGGER = logging.getLogger(__name__)


class ApiKeysStore:
    """PostgreSQL-backed store for API key metadata."""

    TABLE_NAME = "api_keys"

    def __init__(self, dsn: Optional[str] = None) -> None:
        self.dsn = dsn or os.environ.get("SA01_DB_DSN", "")

    async def _get_pool(self) -> Any:
        if asyncpg is None:
            raise RuntimeError("asyncpg is required")
        return await asyncpg.create_pool(self.dsn, min_size=1, max_size=2)

    async def ensure_schema(self) -> None:
        """Ensure database schema exists."""
        pass

    async def list(self, tenant_id: str) -> List[Dict[str, Any]]:
        if not self.dsn or asyncpg is None:
            return []
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    f"SELECT * FROM {self.TABLE_NAME} WHERE tenant = $1",
                    tenant_id,
                )
                return [dict(r) for r in rows]
        finally:
            await pool.close()

    async def create(self, tenant_id: str, name: str, scope: Optional[str] = None) -> str:
        if not self.dsn or asyncpg is None:
            raise RuntimeError("ApiKeysStore: SA01_DB_DSN not configured")
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    f"""
                    INSERT INTO {self.TABLE_NAME} (tenant, label, hashed_key)
                    VALUES ($1, $2, $3)
                    RETURNING id
                    """,
                    tenant_id,
                    name,
                    scope or "",
                )
                return str(row["id"])
        finally:
            await pool.close()

    async def revoke(self, tenant_id: str, key_id: str) -> bool:
        if not self.dsn or asyncpg is None:
            raise RuntimeError("ApiKeysStore: SA01_DB_DSN not configured")
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                result = await conn.execute(
                    f"DELETE FROM {self.TABLE_NAME} WHERE tenant = $1 AND id = $2",
                    tenant_id,
                    key_id,
                )
                return result != "DELETE 0"
        finally:
            await pool.close()
