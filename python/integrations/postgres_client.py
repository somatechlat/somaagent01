"""Lightweight Postgres client shim for tests.

Provides a ``postgres_pool`` symbol that can be imported during pytest collection.
The implementation intentionally avoids real database connections. Any runtime
use will raise a clear error to prevent accidental reliance in unit tests that
aren't selected.
"""

from __future__ import annotations


class _DummyConn:
    async def execute(self, *args, **kwargs):  # pragma: no cover
        raise RuntimeError("postgres_client stub: no database in test mode")

    async def fetchval(self, *args, **kwargs):  # pragma: no cover
        return 1


class _Acquire:
    async def __aenter__(self):  # pragma: no cover
        return _DummyConn()

    async def __aexit__(self, exc_type, exc, tb):  # pragma: no cover
        return False


class _DummyPool:
    def acquire(self) -> _Acquire:  # pragma: no cover
        return _Acquire()


postgres_pool = _DummyPool()

__all__ = ["postgres_pool"]
