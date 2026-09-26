"""Unit tests for rate limiter fail-closed behavior.

Tests that the rate limiter DENIES requests when Redis is unavailable,
rather than allowing them through (fail-open).
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestRateLimiterFailClosed:
    """Test rate limiter fail-closed on Redis errors."""

    @pytest.mark.asyncio
    async def test_fail_closed_on_redis_error(self):
        """Rate limiter returns allowed=False when Redis raises an error."""
        from services.common.rate_limiter import RedisRateLimiter

        limiter = RedisRateLimiter()
        limiter._connected = True

        # Mock Redis to raise an error
        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(side_effect=ConnectionError("Redis down"))
        mock_redis.ping = AsyncMock(side_effect=ConnectionError("Redis down"))
        limiter._redis = mock_redis

        result = await limiter.check(tenant_id="test-tenant")

        assert result.allowed is False
        assert result.remaining == 0
        assert result.retry_after is not None
        assert result.retry_after > 0

    @pytest.mark.asyncio
    async def test_allows_when_redis_healthy(self):
        """Rate limiter allows requests when Redis is healthy."""
        from services.common.rate_limiter import RedisRateLimiter

        limiter = RedisRateLimiter()
        limiter._connected = True

        # Mock Redis to return allowed
        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(return_value=[1, 99, 1000.0])
        limiter._redis = mock_redis

        result = await limiter.check(tenant_id="test-tenant")

        assert result.allowed is True
        assert result.remaining == 99

    @pytest.mark.asyncio
    async def test_denies_when_over_limit(self):
        """Rate limiter denies when over limit."""
        from services.common.rate_limiter import RedisRateLimiter

        limiter = RedisRateLimiter()
        limiter._connected = True

        # Mock Redis to return denied
        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(return_value=[0, 0, 1000.0])
        limiter._redis = mock_redis

        result = await limiter.check(tenant_id="test-tenant")

        assert result.allowed is False
        assert result.remaining == 0

    def test_redis_url_priority(self, monkeypatch):
        """SA01_REDIS_URL takes priority over REDIS_URL."""
        monkeypatch.setenv("SA01_REDIS_URL", "redis://sa01-redis:6379/0")
        monkeypatch.setenv("REDIS_URL", "redis://legacy-redis:6379/0")

        from services.common.rate_limiter import RedisRateLimiter
        limiter = RedisRateLimiter()

        assert "sa01-redis" in limiter.redis_url
