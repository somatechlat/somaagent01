"""Shared readiness probe helpers for SomaAgent services.

Centralizes dependency health checks so individual services only need to
import a single helper to implement their `/ready` endpoint.  This avoids
duplicated ad‑hoc probe logic scattered across service entrypoints.

Checks implemented:
  - Postgres: lightweight `SELECT 1` via asyncpg connection pool
  - Kafka: producer metadata refresh via existing `KafkaEventBus` abstraction
  - Redis: `PING` via `RedisSessionCache`

The helpers are defensive: failures are caught and converted into an
`unhealthy` status with a short error message.  Timeouts prevent slow
dependencies from blocking readiness entirely.

Usage (FastAPI):
    from services.common.readiness import readiness_summary
    @app.get("/ready")
    async def ready():
        result = await readiness_summary()
        if result["status"] == "ready":
            return {"status": "ready", "timestamp": result["timestamp"]}
        raise HTTPException(status_code=503, detail=result)

Environment overrides:
  SA01_DB_DSN            – override default Postgres DSN
  READINESS_CHECK_TIMEOUT – per‑check timeout in seconds (float, default 2.0)

The module intentionally does NOT cache results; each call performs fresh
probes so Kubernetes can rely on current state.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict

import asyncpg

from services.common.event_bus import KafkaEventBus, KafkaSettings
from services.common.session_repository import RedisSessionCache

# Public list of component names (order preserved for deterministic output)
COMPONENTS = ["postgres", "kafka", "redis"]


def _timeout_seconds() -> float:
    from src.core.config import cfg

    try:
        return float(cfg.env("READINESS_CHECK_TIMEOUT", "2.0"))
    except ValueError:
        return 2.0


async def _check_postgres() -> Dict[str, Any]:
    from src.core.config import cfg

    dsn = cfg.db_dsn("postgresql://soma:soma@localhost:5432/somaagent01")
    try:
        pool = await asyncpg.create_pool(dsn, min_size=0, max_size=1)
        async with pool.acquire() as conn:
            val = await conn.fetchval("SELECT 1")
        await pool.close()
        ok = val == 1
        return {
            "status": "healthy" if ok else "unhealthy",
            "message": "Postgres SELECT 1 successful" if ok else "Unexpected result",
        }
    except Exception as exc:  # pragma: no cover (network / env dependent)
        return {"status": "unhealthy", "message": f"{type(exc).__name__}: {exc}"[:160]}


async def _check_kafka() -> Dict[str, Any]:
    # Allow tests to disable Kafka probe to avoid noisy resource warnings when broker absent
    from src.core.config import cfg

    if cfg.env("READINESS_DISABLE_KAFKA", "false").lower() in {"true", "1", "yes", "on"}:
        return {"status": "healthy", "message": "Kafka probe disabled"}
    bus = None
    try:
        bus = KafkaEventBus(KafkaSettings.from_env())
        await bus.healthcheck()
        return {"status": "healthy", "message": "Kafka metadata refreshed"}
    except Exception as exc:  # pragma: no cover
        return {"status": "unhealthy", "message": f"{type(exc).__name__}: {exc}"[:160]}
    finally:
        try:
            if bus is not None:
                await bus.close()
        except Exception:
            pass


async def _check_redis() -> Dict[str, Any]:
    try:
        from src.core.config import cfg

        cache = RedisSessionCache(url=cfg.settings().redis_url or "redis://localhost:6379/0")
        await cache.ping()
        return {"status": "healthy", "message": "Redis PING ok"}
    except Exception as exc:  # pragma: no cover
        return {"status": "unhealthy", "message": f"{type(exc).__name__}: {exc}"[:160]}


_CHECK_MAP = {
    "postgres": _check_postgres,
    "kafka": _check_kafka,
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

# ---------------------------------------------------------------------------
# Compatibility shim for legacy imports.
# ``services.gateway.admin_memory`` historically imported ``get_replica_store``
# from this module.  The function now lives in the canonical replica store
# implementation under ``src.core.domain.memory.replica_store``.  Providing a thin
# wrapper maintains backward compatibility without duplicating logic.
# ---------------------------------------------------------------------------
from src.core.domain.memory.replica_store import MemoryReplicaStore

def get_replica_store() -> MemoryReplicaStore:
    """Return a ``MemoryReplicaStore`` instance using the current config.

    The replica store reads its DSN from the central configuration façade, so
    callers do not need to pass any arguments.  This wrapper satisfies legacy
    imports and keeps a single source of truth for the store implementation.
    """
    return MemoryReplicaStore()

# Export the shim alongside the original symbols.
__all__.append("get_replica_store")
