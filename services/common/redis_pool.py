"""Shared Redis connection pool factory.

Eliminates duplicate `redis.from_url()` calls across modules.
Provides async and sync connection pools with proper configuration.

VIBE COMPLIANT:
- Real production-grade connection pooling
- No reinvention per module
- Configurable via environment variables
"""

from __future__ import annotations

import logging
import os
import threading
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from redis import Redis as SyncRedis
    from redis.asyncio import Redis as AsyncRedis

try:
    import redis.asyncio as aioredis
except ImportError:  # pragma: no cover
    aioredis = None  # type: ignore

try:
    import redis
except ImportError:  # pragma: no cover
    redis = None  # type: ignore

logger = logging.getLogger(__name__)

# Module-level cache for pools
_async_pools: dict[str, AsyncRedis] = {}  # type: ignore[valid-type]
_sync_pools: dict[str, SyncRedis] = {}  # type: ignore[valid-type]

# Locks protecting the check-then-set pattern for pool creation
_async_pool_lock = threading.Lock()
_sync_pool_lock = threading.Lock()


def get_redis_url() -> str:
    """Get Redis URL from environment with sensible default."""
    url = os.environ.get("SA01_REDIS_URL", "")
    if not url:
        # Prefer centralized SettingsRegistry when available
        try:
            from config.settings_registry import SettingsRegistry

            settings = SettingsRegistry.get()
            return settings.redis_url
        except Exception:
            # Fallback for bootstrap contexts where SettingsRegistry isn't loaded
            host = os.environ.get("REDIS_HOST", "localhost")
            port = os.environ.get("REDIS_PORT", "6379")
            db = os.environ.get("REDIS_DB", "0")
            url = f"redis://{host}:{port}/{db}"
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
    if aioredis is None:
        raise RuntimeError("redis.asyncio is required. Install: pip install redis")

    resolved_url = url or get_redis_url()
    cache_key = f"{resolved_url}:{decode_responses}:{max_connections}"

    with _async_pool_lock:
        if cache_key not in _async_pools:
            _async_pools[cache_key] = aioredis.from_url(
                resolved_url,
                decode_responses=decode_responses,
                max_connections=max_connections,
            )
            logger.info(
                "Created async Redis pool",
                extra={
                    "url": (
                        resolved_url.replace("://", "://***@")
                        if "://" in resolved_url
                        else resolved_url
                    )
                },
            )

        return _async_pools[cache_key]


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
    if redis is None:
        raise RuntimeError("redis is required. Install: pip install redis")

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
        for client in list(_async_pools.values()):
            try:
                client.close()  # type: ignore
            except Exception:
                pass
        _async_pools = {}

    with _sync_pool_lock:
        for client in list(_sync_pools.values()):
            try:
                client.close()
            except Exception:
                pass
        _sync_pools = {}

    logger.info("All Redis pools reset")
