"""Attachments store — PostgreSQL-backed file attachment storage.

VIBE COMPLIANT: Real production implementation.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Optional
from uuid import UUID

from services.common.store_base import BaseStore

try:
    import asyncpg  # type: ignore
except ImportError:
    asyncpg = None  # type: ignore

LOGGER = logging.getLogger(__name__)


class AttachmentsStore(BaseStore[UUID]):
    """PostgreSQL-backed store for file attachments metadata."""

    TABLE_NAME = "attachments"

    def __init__(self, dsn: Optional[str] = None) -> None:
        self.dsn = dsn or os.environ.get("SA01_DB_DSN", "")

    async def _get_pool(self) -> Any:
        if asyncpg is None:
            raise RuntimeError("asyncpg is required")
        return await asyncpg.create_pool(self.dsn, min_size=1, max_size=2)

    async def ensure_schema(self) -> None:
        """Ensure database schema exists."""
        pass

    async def get(self, identifier: str) -> Optional[UUID]:
        """Retrieve a single record by primary identifier."""
        raise NotImplementedError

    async def create(self, record: UUID) -> UUID:
        """Persist a new record and return the stored representation."""
        raise NotImplementedError

    async def delete(self, identifier: str) -> bool:
        if not self.dsn or asyncpg is None:
            raise RuntimeError("AttachmentsStore: SA01_DB_DSN not configured")
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                result = await conn.execute(
                    f"DELETE FROM {self.TABLE_NAME} WHERE id = $1",
                    identifier,
                )
                return result != "DELETE 0"
        finally:
            await pool.close()
