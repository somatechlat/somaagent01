"""Redis client utilities used by the degradation layer.

The project already depends on ``redis`` (see ``requirements.txt``).  This
module provides a thin async wrapper around ``redis.asyncio`` that is safe to
import from any service without pulling in heavy connection‑pool logic.  All
configuration is read from the central ``cfg`` helper so that the URL lives in a
single source of truth (VIBE rule: *single source of config*).

Only the minimal API required by the fail‑safe design is exposed:

* ``set_event(event_id: str, payload: dict)`` – store a JSON‑encoded event.
* ``get_all_events()`` – retrieve a ``dict[event_id, dict]`` of every buffered
  event.
* ``delete_event(event_id: str)`` – remove an event after it has been synced.

The functions are deliberately ``async`` because the surrounding code (gateway
and background syncer) already runs in an async event loop.
"""

from __future__ import annotations

import json
from typing import Dict, Optional, Any

import redis.asyncio as aioredis

from src.core.config import cfg

# ---------------------------------------------------------------------------
# Helper to obtain a singleton Redis connection.  ``aioredis.from_url`` lazily
# creates the connection pool on first use.  The URL is taken from the
# environment variable ``REDIS_URL`` with a sensible default for local dev.
# ---------------------------------------------------------------------------
# NOTE: We intentionally avoid long‑lived global connections because the test
# environment may change the ``SA01_REDIS_URL``/``REDIS_URL`` values between
# runs.  Creating a fresh client on each call guarantees the latest env vars
# are respected and prevents stale connections (e.g., a previous attempt to
# ``localhost:6379`` persisting after the URL was updated).

def _get_redis() -> aioredis.Redis:
    # Resolve the Redis URL with priority:
    #   1. ``SA01_REDIS_URL`` – the canonical variable used by services.
    #   2. ``REDIS_URL`` – legacy fallback.
    #   3. ``redis://localhost:20001/0`` – host‑side mapping when running tests
    #      outside Docker.
    # Directly read the environment to avoid the configuration façade, which
    # by default maps ``SA01_REDIS_URL`` to the internal Docker hostname.
    # For host‑side tests we rely on the plain ``REDIS_URL`` (or a default that
    # points at the host‑mapped port ``20001``).
    raw_url = cfg.env("SA01_REDIS_URL", cfg.settings().redis.url)
    if not raw_url:
        raw_url = cfg.env("REDIS_URL", "redis://localhost:20001/0")

    # When running inside a Docker container, connecting to the host-mapped
    # port (localhost:20001) will always fail. Prefer the service hostname in
    # that environment, regardless of any host-level overrides.
    try:
        import os
        if os.path.exists("/.dockerenv"):
            raw_url = cfg.env("SA01_REDIS_URL", "redis://redis:6379/0")
    except Exception:
        pass

    # When the URL points to the Docker‑internal hostname ``redis`` it is not
    # reachable from the host where the integration test runs. Detect this
    # pattern and rewrite it to use ``localhost`` with the host‑mapped port
    # (default 20001, overridable via ``REDIS_PORT``).
    # Only rewrite the redis hostname when explicitly requested (e.g. host-side tests).
    # In containers, rewriting breaks connectivity (localhost:20001 is host, not the redis service).
    if raw_url.startswith("redis://redis") and cfg.env("REDIS_REWRITE_TO_LOCALHOST", "").lower() == "true":
        from urllib.parse import urlparse, urlunparse

        parsed = urlparse(raw_url)
        host_port = cfg.env("REDIS_PORT", "20001")
        new_netloc = f"localhost:{host_port}"
        redis_url = urlunparse(
            (
                parsed.scheme,
                new_netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment,
            )
        )
    else:
        redis_url = raw_url

    # Debug log the final URL for troubleshooting.
    import logging

    logging.getLogger(__name__).debug("Resolved Redis URL: %s", redis_url)

    return aioredis.from_url(redis_url, decode_responses=True)


async def set_event(event_id: str, payload: dict) -> None:
    """Store *payload* under a namespaced key.

    The key format ``degraded:{event_id}`` guarantees uniqueness and makes it
    easy to enumerate all buffered events.
    """
    redis_conn = _get_redis()
    key = f"degraded:{event_id}"
    await redis_conn.set(key, json.dumps(payload))


async def get_all_events() -> Dict[str, dict]:
    """Return a mapping of ``event_id`` → decoded payload for every entry.

    The implementation scans keys with the ``degraded:*`` pattern.  For a
    production deployment the number of buffered events is expected to be low
    (the circuit‑breaker opens only when Somabrain is unavailable), so a simple
    ``SCAN`` loop is sufficient and avoids blocking the Redis server.
    """
    redis_conn = _get_redis()
    cursor = b"0"
    result: Dict[str, dict] = {}
    while cursor:
        cursor, keys = await redis_conn.scan(cursor=cursor, match="degraded:*", count=100)
        if keys:
            values = await redis_conn.mget(*keys)
            for k, v in zip(keys, values, strict=False):
                if v is None:
                    continue
                try:
                    payload = json.loads(v)
                except json.JSONDecodeError:
                    # Corrupted entry – skip it but keep the key for manual
                    # investigation.
                    continue
                event_id = k.split(":", 1)[1]
                result[event_id] = payload
        if cursor == b"0":
            break
    return result


async def delete_event(event_id: str) -> None:
    """Remove a buffered event after it has been synced to Postgres.
    """
    redis_conn = _get_redis()
    key = f"degraded:{event_id}"
    await redis_conn.delete(key)


class RedisCacheClient:
    """Generic Redis cache client implementing CacheClientProtocol."""

    async def get(self, key: str) -> Optional[dict]:
        """Retrieve a JSON dictionary from Redis."""
        redis_conn = _get_redis()
        try:
            data = await redis_conn.get(key)
            if data:
                return json.loads(data)
        except Exception:
            pass
        return None

    async def set(self, key: str, value: dict, ttl: int) -> None:
        """Store a JSON dictionary in Redis with TTL."""
        redis_conn = _get_redis()
        try:
            await redis_conn.set(key, json.dumps(value), ex=ttl)
        except Exception:
            pass

