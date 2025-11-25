"""Lightweight stub for the ``asyncpg`` package used in development mode.

Only a tiny subset of the API is required for the code to import:

* ``Pool`` class with ``acquire`` (async context manager) and ``close``.
* ``create_pool`` coroutine returning a ``Pool`` instance.
* ``connect`` coroutine returning a connection object with ``fetchval``, ``execute``
  and ``close`` methods.

All methods raise ``NotImplementedError`` if called, because in ``DEV_MODE``
the code paths that require a real database are guarded to avoid execution. The
stub exists solely to satisfy imports.
"""

from __future__ import annotations

from typing import Any


class _DummyConnection:
    async def fetchval(self, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover
        raise NotImplementedError("asyncpg stub: fetchval called in DEV_MODE")

    async def fetch(self, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover
        raise NotImplementedError("asyncpg stub: fetch called in DEV_MODE")

    async def execute(self, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover
        raise NotImplementedError("asyncpg stub: execute called in DEV_MODE")

    async def close(self) -> None:  # pragma: no cover
        return None


class Pool:
    """Simple stub mimicking ``asyncpg.Pool``.

    The ``acquire`` method returns a ``_DummyConnection`` instance. It can be
    used as an async context manager (``async with pool.acquire() as conn``).
    """

    def __init__(self, *_, **__) -> None:
        self._conn = _DummyConnection()

    async def acquire(self) -> _DummyConnection:  # pragma: no cover
        return self._conn

    async def close(self) -> None:  # pragma: no cover
        return None


async def create_pool(*args: Any, **kwargs: Any) -> Pool:  # pragma: no cover
    """Return a stub ``Pool`` instance."""
    return Pool()


async def connect(*args: Any, **kwargs: Any) -> _DummyConnection:  # pragma: no cover
    """Return a stub connection object."""
    return _DummyConnection()


__all__ = ["Pool", "create_pool", "connect"]
