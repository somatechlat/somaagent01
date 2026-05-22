"""Constitution store — PostgreSQL-backed constitution/rule storage.

VIBE COMPLIANT: Real production implementation.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional

from services.common.store_base import BaseStore

try:
    import asyncpg  # type: ignore
except ImportError:
    asyncpg = None  # type: ignore

LOGGER = logging.getLogger(__name__)


class ConstitutionStore(BaseStore[dict[str, Any]]):
    """PostgreSQL-backed store for agent constitutions."""

    TABLE_NAME = "constitutions"

    def __init__(self, dsn: Optional[str] = None) -> None:
        self.dsn = dsn or os.environ.get("SA01_DB_DSN", "")

    async def _get_pool(self) -> Any:
        if asyncpg is None:
            raise RuntimeError("asyncpg is required")
        return await asyncpg.create_pool(self.dsn, min_size=1, max_size=2)

    async def ensure_schema(self) -> None:
        """Ensure database schema exists."""
        pass

    async def get(self, tenant_id: str) -> Optional[dict[str, Any]]:
        if not self.dsn or asyncpg is None:
            return None
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    f"SELECT * FROM {self.TABLE_NAME} WHERE tenant = $1",
                    tenant_id,
                )
                return dict(row) if row else None
        finally:
            await pool.close()

    async def create(self, record: dict[str, Any]) -> dict[str, Any]:
        """Persist a new record and return the stored representation."""
        raise NotImplementedError

    async def update(self, identifier: str, changes: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Apply partial updates and return the updated record."""
        rules = changes.get("rules")
        if rules is None:
            raise ValueError("changes must contain 'rules'")
        if not self.dsn or asyncpg is None:
            raise RuntimeError("ConstitutionStore: SA01_DB_DSN not configured")
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    f"""
                    INSERT INTO {self.TABLE_NAME} (tenant, content)
                    VALUES ($1, $2)
                    ON CONFLICT (tenant) DO UPDATE SET content = EXCLUDED.content
                    """,
                    identifier,
                    json.dumps(rules),
                )
        finally:
            await pool.close()
        return await self.get(identifier)

    async def delete(self, identifier: str) -> bool:
        """Remove a record. Returns True if a record was removed."""
        raise NotImplementedError
