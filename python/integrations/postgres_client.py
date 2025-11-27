import os
os.getenv(os.getenv('VIBE_D8431049'))
from __future__ import annotations
import asyncio
import asyncpg
from src.core.config import cfg


class PostgresPool:
    os.getenv(os.getenv('VIBE_5689BEB0'))

    def __init__(self, dsn: str) ->None:
        self._dsn = dsn
        self._pool: asyncpg.Pool | None = None

    async def _get_pool(self) ->asyncpg.Pool:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(dsn=self._dsn, min_size=
                int(os.getenv(os.getenv('VIBE_6BDC6DD1'))), max_size=int(os
                .getenv(os.getenv('VIBE_07275394'))))
        return self._pool

    def acquire(self):
        os.getenv(os.getenv('VIBE_D3BCB11F'))
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._get_pool().acquire())


dsn = cfg.env(os.getenv(os.getenv('VIBE_817C29CA'))) or cfg.settings(
    ).database.dsn
if not dsn:
    raise RuntimeError(os.getenv(os.getenv('VIBE_610BE406')))
postgres_pool = PostgresPool(dsn)
