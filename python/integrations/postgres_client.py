"""Production Postgres client - NO TEST STUBS, NO FALLBACKS"""

from __future__ import annotations

import os
import asyncio
from typing import Any

import asyncpg


class PostgresPool:
    """Real asyncpg connection pool."""
    
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._pool: asyncpg.Pool | None = None

    async def _get_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                dsn=self._dsn,
                min_size=1,
                max_size=5
            )
        return self._pool

    def acquire(self):
        """Return real asyncpg connection."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._get_pool().acquire())


# PRODUCTION ONLY - Always use real postgres
dsn = os.getenv("SA01_DB_DSN")
if not dsn:
    raise RuntimeError("SA01_DB_DSN environment variable required")

postgres_pool = PostgresPool(dsn)
