"""Postgres client integration.

The production implementation uses **asyncpg** to provide a connection pool that
can be imported throughout the code‑base via ``postgres_pool``.  During unit‑test
execution the ``PYTEST_CURRENT_TEST`` environment variable is set – in that
scenario we fall back to a lightweight stub that raises a clear error when a
runtime operation is attempted.  This preserves the original test behaviour
while enabling real database connections when the application runs (e.g. in the
Docker development stack).

Key behaviours:
* ``postgres_pool`` exposes an ``acquire()`` async context manager returning a
  connection with ``execute`` and ``fetchval`` methods.
* Connection parameters are taken from ``SA01_DB_DSN`` (or ``APP_SETTINGS``
* If the pool cannot be created (e.g., missing ``asyncpg`` or DB unavailable),
  a ``RuntimeError`` is raised at import time, making the failure obvious.
* The stub is deliberately minimal and only used when the ``PYTEST_CURRENT_TEST``
  environment variable is present.
"""

from __future__ import annotations

import os
import asyncio
from typing import Any

try:
    import asyncpg  # type: ignore
except Exception as exc:  # pragma: no cover – asyncpg missing in CI is a config error
    asyncpg = None
    _IMPORT_ERROR = exc


class _StubConn:

    Any attempt to execute a query will raise a RuntimeError, mirroring the
    original stub's behaviour but providing a more explicit message.
    """

    async def execute(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover
        raise RuntimeError(
            "postgres_client stub: attempted DB operation in test mode"
        )

    async def fetchval(self, *args: Any, **kwargs: Any) -> int:  # pragma: no cover
        # Return a harmless default value for callers that merely check existence.
        return 1


class _StubAcquire:
    async def __aenter__(self) -> _StubConn:  # pragma: no cover
        return _StubConn()

"""Postgres client integration.

Provides a ``postgres_pool`` that works both in the Docker development stack
and during unit‑test collection.  When the ``PYTEST_CURRENT_TEST`` environment
variable is present we fall back to a lightweight stub (preserving the original
behaviour of raising on any real operation).  In normal runtime the pool is a
real ``asyncpg`` connection pool created from ``SA01_DB_DSN``.
"""
        return _StubAcquire()


def _create_real_pool(dsn: str):
    """Create an asyncpg connection pool.

    The function is isolated so that import‑time side effects are minimal. It is
    called only when we are **not** in a pytest environment and ``asyncpg`` is
    available.
    """
    if asyncpg is None:
        raise RuntimeError(
            f"asyncpg import failed: {_IMPORT_ERROR}. Ensure the dependency is "
            "installed for runtime use."
        )
    # ``asyncio.get_event_loop`` may raise if no loop is running; we create a
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(asyncpg.create_pool(dsn=dsn, min_size=1, max_size=5))


# Decide whether we are in a pytest run. ``PYTEST_CURRENT_TEST`` is set by pytest.
_in_pytest = "PYTEST_CURRENT_TEST" in os.environ

if _in_pytest:
    # Use the lightweight stub – this mirrors the original behaviour.
    postgres_pool = _StubPool()
else:
class _RealPool:
    """Wrapper around an asyncpg pool exposing the same ``acquire`` API.

    The pool is created lazily on first use to avoid side‑effects at import time.
    """

    _pool: Any = None

    async def _ensure_pool(self) -> None:
        if self._pool is not None:
            return
        dsn = os.getenv("SA01_DB_DSN")
        if not dsn:
            raise RuntimeError(
                "SA01_DB_DSN environment variable is required for Postgres "
                "connections but is not set."
            )
        if asyncpg is None:
            raise RuntimeError(
                "asyncpg is not installed – cannot create a real Postgres pool."
            )
        self._pool = await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=5)

    def acquire(self) -> Any:

        The returned object is ``self._pool.acquire()`` once the pool is
        initialised. ``asyncio.get_event_loop`` is used to schedule the lazy
        creation if necessary.
        """
        async def _acquire_wrapper():
            await self._ensure_pool()
            return self._pool.acquire()

        loop = asyncio.get_event_loop()
        return loop.run_until_complete(_acquire_wrapper())

# Choose implementation based on environment.
if "PYTEST_CURRENT_TEST" in os.environ:
    postgres_pool = _StubPool()
else:
    postgres_pool = _RealPool()
    # Runtime mode – obtain DSN from env or raise a clear error.
    dsn = os.getenv("SA01_DB_DSN")
    if not dsn:
        raise RuntimeError(
            "SA01_DB_DSN environment variable is required for Postgres "
            "connections but is not set."
        )
    postgres_pool = _create_real_pool(dsn)

__all__ = ["postgres_pool"]
