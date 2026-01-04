"""
Redis Rate Limiter for API Endpoints
Per CANONICAL_REQUIREMENTS.md REQ-SEC-006


- Real Redis backend
- Sliding window algorithm
- Per-tenant rate limiting
- Prometheus metrics
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass
from typing import Optional, Tuple

import redis.asyncio as redis
from prometheus_client import Counter, Gauge

LOGGER = logging.getLogger(__name__)

# Prometheus metrics
RATE_LIMIT_REQUESTS = Counter(
    "rate_limit_requests_total",
    "Total rate limit check requests",
    labelnames=("tenant_id", "result"),
)
RATE_LIMIT_REMAINING = Gauge(
    "rate_limit_remaining",
    "Remaining request quota",
    labelnames=("tenant_id", "window"),
)


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""

    allowed: bool
    remaining: int
    reset_at: float
    retry_after: Optional[int] = None


class RedisRateLimiter:
    """
    Redis-backed sliding window rate limiter.

    Uses a sorted set to implement sliding window rate limiting.
    Supports per-tenant and per-endpoint limits.
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        default_limit: int = 100,
        default_window_seconds: int = 60,
        key_prefix: str = "rate_limit:",
    ):
        """Initialize the instance."""

        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.default_limit = default_limit
        self.default_window_seconds = default_window_seconds
        self.key_prefix = key_prefix

        self._redis: Optional[redis.Redis] = None
        self._connected = False

    async def connect(self) -> None:
        """Connect to Redis."""
        if not self._connected:
            self._redis = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            # Test connection
            await self._redis.ping()
            self._connected = True
            LOGGER.info(f"Redis rate limiter connected: {self.redis_url}")

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._connected = False

    async def check(
        self,
        tenant_id: str,
        endpoint: Optional[str] = None,
        limit: Optional[int] = None,
        window_seconds: Optional[int] = None,
    ) -> RateLimitResult:
        """
        Check if request should be allowed.

        Uses sliding window algorithm:
        1. Remove expired entries from sorted set
        2. Count entries in current window
        3. If under limit, add new entry and allow
        4. If over limit, deny with retry-after

        Args:
            tenant_id: Tenant identifier
            endpoint: Optional endpoint for per-endpoint limits
            limit: Max requests in window (default: 100)
            window_seconds: Window size in seconds (default: 60)

        Returns:
            RateLimitResult with allowed status and remaining quota
        """
        if not self._connected:
            await self.connect()

        # Build key
        key_parts = [self.key_prefix, tenant_id]
        if endpoint:
            key_parts.append(endpoint.replace("/", "_"))
        key = ":".join(key_parts)

        limit = limit or self.default_limit
        window = window_seconds or self.default_window_seconds

        now = time.time()
        window_start = now - window

        # Lua script for atomic sliding window rate limit
        lua_script = """
        local key = KEYS[1]
        local now = tonumber(ARGV[1])
        local window_start = tonumber(ARGV[2])
        local limit = tonumber(ARGV[3])
        local window = tonumber(ARGV[4])
        
        -- Remove expired entries
        redis.call('ZREMRANGEBYSCORE', key, '-inf', window_start)
        
        -- Count current entries
        local count = redis.call('ZCARD', key)
        
        if count < limit then
            -- Add new entry
            redis.call('ZADD', key, now, now .. ':' .. math.random())
            redis.call('EXPIRE', key, window + 1)
            return {1, limit - count - 1, now + window}
        else
            -- Get oldest entry for retry-after
            local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
            local reset_at = oldest[2] and (tonumber(oldest[2]) + window) or (now + window)
            return {0, 0, reset_at}
        end
        """

        try:
            result = await self._redis.eval(
                lua_script,
                1,  # Number of keys
                key,
                str(now),
                str(window_start),
                str(limit),
                str(window),
            )

            allowed = bool(result[0])
            remaining = int(result[1])
            reset_at = float(result[2])
            retry_after = None if allowed else max(1, int(reset_at - now))

            status = "allowed" if allowed else "denied"
            RATE_LIMIT_REQUESTS.labels(tenant_id, status).inc()
            RATE_LIMIT_REMAINING.labels(tenant_id, str(window)).set(remaining)

            return RateLimitResult(
                allowed=allowed,
                remaining=remaining,
                reset_at=reset_at,
                retry_after=retry_after,
            )

        except Exception as e:
            LOGGER.error(f"Rate limit check failed: {e}")
            # Fail open for rate limiting to avoid blocking on Redis issues
            RATE_LIMIT_REQUESTS.labels(tenant_id, "error").inc()
            return RateLimitResult(
                allowed=True,
                remaining=limit,
                reset_at=now + window,
            )

    async def reset(self, tenant_id: str, endpoint: Optional[str] = None) -> None:
        """Reset rate limit for a tenant/endpoint."""
        if not self._connected:
            await self.connect()

        key_parts = [self.key_prefix, tenant_id]
        if endpoint:
            key_parts.append(endpoint.replace("/", "_"))
        key = ":".join(key_parts)

        await self._redis.delete(key)
        LOGGER.info(f"Rate limit reset for {key}")


# Preconfigured limits per CANONICAL_REQUIREMENTS.md
RATE_LIMITS = {
    # Upload endpoints - more restrictive
    "/v1/uploads": {"limit": 10, "window": 60},
    "/v1/files/upload": {"limit": 10, "window": 60},
    "/api/v2/uploads": {"limit": 10, "window": 60},
    # Memory endpoints - moderate
    "/v1/memory": {"limit": 50, "window": 60},
    "/api/v2/memory": {"limit": 50, "window": 60},
    # General API - permissive
    "default": {"limit": 100, "window": 60},
}


def get_limit_for_endpoint(endpoint: str) -> Tuple[int, int]:
    """Get rate limit configuration for an endpoint."""
    for pattern, config in RATE_LIMITS.items():
        if pattern in endpoint:
            return config["limit"], config["window"]
    default = RATE_LIMITS["default"]
    return default["limit"], default["window"]


# Singleton instance
_limiter_instance: Optional[RedisRateLimiter] = None


async def get_rate_limiter() -> RedisRateLimiter:
    """Get or create the singleton rate limiter."""
    global _limiter_instance
    if _limiter_instance is None:
        _limiter_instance = RedisRateLimiter()
        await _limiter_instance.connect()
    return _limiter_instance


__all__ = [
    "RedisRateLimiter",
    "RateLimitResult",
    "get_rate_limiter",
    "get_limit_for_endpoint",
    "RATE_LIMITS",
]