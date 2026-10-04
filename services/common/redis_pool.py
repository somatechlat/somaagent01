"""Shared Redis connection pool factory.

Eliminates duplicate `redis.from_url()` calls across modules.
Provides async and sync connection pools with proper configuration.

VIBE COMPLIANT:
- Real production-grade connection pooling
- No reinvention per module
- Configurable via environment variables
"""

from __future__ import annotations

import asyncio
import logging
import os
import threading
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from redis import Redis as SyncRedis
    from redis.asyncio import Redis as AsyncRedis

import redis
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

# Module-level cache for pools. Each async entry remembers the event loop the
# client was bound to, because a redis.asyncio client is only good for one.
_async_pools: dict[str, tuple[Optional[asyncio.AbstractEventLoop], "AsyncRedis"]] = {}
_sync_pools: dict[str, SyncRedis] = {}  # type: ignore[valid-type]

# Locks protecting the check-then-set pattern for pool creation
_async_pool_lock = threading.Lock()
_sync_pool_lock = threading.Lock()


def _running_loop() -> Optional[asyncio.AbstractEventLoop]:
    """The loop the caller is on, or None if there is not one.

    ``asyncio.get_running_loop`` raises outside a coroutine; for a factory
    that is a legitimate state, not an error — a client built there simply
    has not been bound yet.
    """
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        return None


def _redact(url: str) -> str:
    """Strip any credentials before a URL reaches a log line."""
    return url.replace("://", "://***@") if "://" in url else url


def get_redis_url() -> str:
    """Resolve the Redis URL, or refuse.

    Order: the configured URL (``SA01_REDIS_URL``), then the deployment
    topology in ``SettingsRegistry``. There is no third reconstruction from
    ``REDIS_HOST``/``REDIS_PORT`` with a localhost default — that path
    invented a broker nobody chose (VIBE Rule 91).
    """
    url = (os.environ.get("SA01_REDIS_URL") or "").strip()
    if url:
        return url
    from config.settings_registry import SettingsRegistry

    settings = SettingsRegistry.get()
    url = (settings.redis_url or "").strip()
    if not url:
        raise RuntimeError(
            "Redis is not configured. Set SA01_REDIS_URL or the redis_* "
            "topology for this deployment mode (config/settings_registry.py). "
            "There is no default broker."
        )
    return url


def get_async_redis_pool(
    url: Optional[str] = None,
    *,
    decode_responses: bool = True,
    max_connections: int = 50,
) -> AsyncRedis:
    """Get or create an async Redis connection pool.

    Args:
        url: Redis connection string. Defaults to SA01_REDIS_URL env var.
        decode_responses: Whether to decode responses to strings.
        max_connections: Maximum connections in the pool.

    Returns:
        Async Redis client with connection pooling.

    Raises:
        RuntimeError: If redis.asyncio is not installed.
    """

    resolved_url = url or get_redis_url()
    cache_key = f"{resolved_url}:{decode_responses}:{max_connections}"
    running = _running_loop()

    with _async_pool_lock:
        cached = _async_pools.get(cache_key)
        if cached is not None:
            bound_loop, client = cached
            if bound_loop is running or bound_loop is None or running is None:
                # ``bound_loop is None`` means the client was built outside
                # any loop and has not been used yet. redis.asyncio binds
                # lazily on first command, so the loop it is first asked to
                # run on is the one it belongs to. Record that now.
                if bound_loop is None and running is not None:
                    _async_pools[cache_key] = (running, client)
                return client
            # The loop this client was built for is gone. Its transports died
            # with it, so every command raises "attached to a different loop"
            # — which the rate limiter reads as a denial and every other
            # caller reads as an outage. Re-acquire instead of handing back a
            # client that can never answer. This is not a fallback: the old
            # client is genuinely unusable, and the new one is built the same
            # way the first was.
            logger.info(
                "Reacquiring async Redis pool after event loop change",
                extra={"url": _redact(resolved_url)},
            )
            _async_pools.pop(cache_key, None)

        client = aioredis.from_url(
            resolved_url,
            decode_responses=decode_responses,
            max_connections=max_connections,
        )
        _async_pools[cache_key] = (running, client)
        logger.info(
            "Created async Redis pool",
            extra={"url": _redact(resolved_url)},
        )
        return client


def get_sync_redis_pool(
    url: Optional[str] = None,
    *,
    decode_responses: bool = True,
    max_connections: int = 50,
) -> SyncRedis:
    """Get or create a sync Redis connection pool.

    Args:
        url: Redis connection string. Defaults to SA01_REDIS_URL env var.
        decode_responses: Whether to decode responses to strings.
        max_connections: Maximum connections in the pool.

    Returns:
        Sync Redis client with connection pooling.

    Raises:
        RuntimeError: If redis is not installed.
    """

    resolved_url = url or get_redis_url()
    cache_key = f"{resolved_url}:{decode_responses}:{max_connections}"

    with _sync_pool_lock:
        if cache_key not in _sync_pools:
            _sync_pools[cache_key] = redis.from_url(
                resolved_url,
                decode_responses=decode_responses,
                max_connections=max_connections,
            )
            logger.info(
                "Created sync Redis pool",
                extra={
                    "url": (
                        resolved_url.replace("://", "://***@")
                        if "://" in resolved_url
                        else resolved_url
                    )
                },
            )

        return _sync_pools[cache_key]


def reset_pools() -> None:
    """Close and clear all cached pools. Used primarily in tests."""
    global _async_pools, _sync_pools

    with _async_pool_lock:
        for _loop, client in list(_async_pools.values()):
            _close_quietly(client)
        _async_pools = {}

    with _sync_pool_lock:
        for client in list(_sync_pools.values()):
            try:
                client.close()
            except Exception:
                pass
        _sync_pools = {}

    logger.info("All Redis pools reset")


def _close_quietly(client: "AsyncRedis") -> None:
    """Release an async client without leaking a never-awaited coroutine.

    ``redis.asyncio``'s ``close()`` is a coroutine (``aclose()`` in 5.x).
    Calling it from sync code and dropping the result does not close
    anything — it just raises a RuntimeWarning and leaves the connections
    open. If a loop is running we schedule the close; if not, there is no
    way to drive it from here and the client is being discarded anyway.
    """
    closer = getattr(client, "aclose", None) or getattr(client, "close", None)
    if closer is None:
        return
    try:
        result = closer()
    except Exception:
        return
    if not asyncio.iscoroutine(result):
        return
    loop = _running_loop()
    if loop is not None:
        loop.create_task(result)
    else:
        result.close()
