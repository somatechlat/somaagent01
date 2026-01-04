"""Shared readiness probe helpers for SomaAgent services.

100% Django - 
Uses Django database connection instead of asyncpg.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict

from django.db import connection

# Public list of component names (order preserved for deterministic output)
COMPONENTS = ["postgres", "redis"]


def _timeout_seconds() -> float:
    import os

    try:
        return float(os.environ.get("READINESS_CHECK_TIMEOUT", "2.0"))
    except ValueError:
        return 2.0


async def _check_postgres() -> Dict[str, Any]:
    """Check Postgres health using Django database connection."""
    try:
        # Use Django's database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            val = cursor.fetchone()[0]
        ok = val == 1
        return {
            "status": "healthy" if ok else "unhealthy",
            "message": "Postgres SELECT 1 successful" if ok else "Unexpected result",
        }
    except Exception as exc:  # pragma: no cover (network / env dependent)
        return {"status": "unhealthy", "message": f"{type(exc).__name__}: {exc}"[:160]}


async def _check_redis() -> Dict[str, Any]:
    """Check Redis health using Django cache backend."""
    try:
        from django.core.cache import cache

        cache.set("health_check", "ok", timeout=5)
        val = cache.get("health_check")
        ok = val == "ok"
        return {
            "status": "healthy" if ok else "unhealthy",
            "message": "Redis cache ok" if ok else "Unexpected cache value",
        }
    except Exception as exc:  # pragma: no cover
        return {"status": "unhealthy", "message": f"{type(exc).__name__}: {exc}"[:160]}


_CHECK_MAP = {
    "postgres": _check_postgres,
    "redis": _check_redis,
}


async def readiness_summary() -> Dict[str, Any]:
    """Run all readiness checks concurrently and return a summary dict.

    Structure:
        {
          "status": "ready" | "unready",
          "timestamp": <iso8601>,
          "components": {
              "postgres": {"status": "healthy"|"unhealthy", "message": str},
              ...
          }
        }
    A component marked *unhealthy* causes overall status `unready`.
    """
    timeout = _timeout_seconds()
    tasks = [
        asyncio.create_task(asyncio.wait_for(_CHECK_MAP[name](), timeout=timeout))
        for name in COMPONENTS
    ]
    results: Dict[str, Dict[str, Any]] = {}
    for name, task in zip(COMPONENTS, tasks, strict=False):
        try:
            results[name] = await task
        except Exception as exc:  # timeout or unexpected
            results[name] = {"status": "unhealthy", "message": f"timeout_or_error: {exc}"[:160]}
    overall_ready = all(r.get("status") == "healthy" for r in results.values())
    return {
        "status": "ready" if overall_ready else "unready",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": results,
    }


__all__ = ["readiness_summary", "COMPONENTS"]
