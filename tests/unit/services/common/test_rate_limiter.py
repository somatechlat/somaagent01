"""Unit tests for the Redis-backed rate limiter."""

from __future__ import annotations

import pytest

from services.common.rate_limiter import get_rate_limiter, RedisRateLimiter


@pytest.fixture
def clean_limiter_singleton(monkeypatch):
    """Reset the module-level singleton so each test gets a fresh instance."""
    import services.common.rate_limiter as rl_module

    monkeypatch.setattr(rl_module, "_limiter_instance", None)
    yield
    monkeypatch.setattr(rl_module, "_limiter_instance", None)


def test_redis_rate_limiter_uses_sa01_redis_url(monkeypatch):
    """RedisRateLimiter must respect SA01_REDIS_URL, not hard-coded localhost."""
    expected_url = "redis://custom-redis.example:6379/3"
    monkeypatch.setenv("SA01_REDIS_URL", expected_url)
    # Ensure the legacy env var does not take precedence
    monkeypatch.delenv("REDIS_URL", raising=False)

    limiter = RedisRateLimiter()

    assert limiter.redis_url == expected_url


def test_redis_rate_limiter_uses_explicit_url_over_env(monkeypatch):
    """An explicit redis_url parameter must override environment variables."""
    monkeypatch.setenv("SA01_REDIS_URL", "redis://env-redis:6379/0")
    explicit_url = "redis://explicit-redis:6379/1"

    limiter = RedisRateLimiter(redis_url=explicit_url)

    assert limiter.redis_url == explicit_url


@pytest.mark.asyncio
async def test_get_rate_limiter_uses_sa01_redis_url(monkeypatch, clean_limiter_singleton):
    """The singleton factory must resolve Redis URL from project env vars."""
    expected_url = "redis://factory-redis.example:6379/2"
    monkeypatch.setenv("SA01_REDIS_URL", expected_url)
    monkeypatch.delenv("REDIS_URL", raising=False)

    # Avoid opening a real Redis connection in a unit test.
    async def _noop_connect(self) -> None:
        return None

    monkeypatch.setattr(RedisRateLimiter, "connect", _noop_connect)

    limiter = await get_rate_limiter()

    assert limiter.redis_url == expected_url
