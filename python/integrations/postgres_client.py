import os

os.getenv(os.getenv(""))
from __future__ import annotations

import asyncio

import asyncpg

from src.core.config import cfg


class PostgresPool:
    os.getenv(os.getenv(""))

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._pool: asyncpg.Pool | None = None

    async def _get_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                dsn=self._dsn,
                min_size=int(os.getenv(os.getenv(""))),
                max_size=int(os.getenv(os.getenv(""))),
            )
        return self._pool

    def acquire(self):
        os.getenv(os.getenv(""))
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._get_pool().acquire())


dsn = cfg.env(os.getenv(os.getenv(""))) or cfg.settings().database.dsn
if not dsn:
    raise RuntimeError(os.getenv(os.getenv("")))
postgres_pool = PostgresPool(dsn)
