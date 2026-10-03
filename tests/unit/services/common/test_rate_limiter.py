"""Unit tests for the Redis-backed rate limiter.

Two things are on trial here, and neither of them is a mock:

* **Where the limiter finds Redis.** There is one resolver
  (``redis_pool.get_redis_url``) and the limiter must not keep a private
  second opinion about it. These claims are pure: constructing the limiter
  does not open a socket, so no fake is needed to observe the URL it chose.

* **That the singleton is a real connected limiter.** That claim is made
  against a real Redis. A ``connect`` stub would let this suite pass with no
  server present and prove nothing about the thing that matters — whether
  the limiter can actually count.

Run:
    pytest tests/unit/services/common/test_rate_limiter.py -v

Requires a reachable Redis for the singleton test. Nothing is stubbed.
"""

from __future__ import annotations

import os

import pytest

from services.common.rate_limiter import get_rate_limiter, RedisRateLimiter


@pytest.fixture
def clean_limiter_singleton():
    """Reset the module-level singleton so each test gets a fresh instance.

    Clearing a cache is not a mock: the object under test is still the real
    limiter and the code that builds it is still the real code.
    """
    import services.common.rate_limiter as rl_module

    rl_module._limiter_instance = None
    yield
    rl_module._limiter_instance = None


def _live_redis_url() -> str:
    return os.getenv("SA01_REDIS_URL") or os.getenv(
        "REDIS_URL", "redis://localhost:6379/0"
    )


def test_redis_rate_limiter_uses_sa01_redis_url(monkeypatch):
    """RedisRateLimiter must respect SA01_REDIS_URL, not a private default."""
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


def test_the_limiter_does_not_keep_a_second_opinion_about_the_redis_url():
    """The single-resolver rule.

    ``RedisRateLimiter`` used to rebuild the environment chain itself and
    default to ``redis://localhost:6379/0``. Two resolvers had already
    disagreed in practice: one module reached the configured Redis while the
    limiter dialled a hardcoded host that nothing was listening on. The limiter
    must ask the one place that owns the answer.
    """
    from services.common.redis_pool import get_redis_url

    assert RedisRateLimiter().redis_url == get_redis_url()


@pytest.mark.asyncio
async def test_get_rate_limiter_returns_a_real_connected_limiter(
    clean_limiter_singleton,
):
    """The factory hands back a limiter that has actually talked to Redis.

    No ``connect`` stub. If this passes, the connection is real; if Redis is
    absent, it fails — which is the honest outcome for a test of a
    Redis-backed limiter.
    """
    limiter = await get_rate_limiter()

    assert limiter.redis_url == _live_redis_url()
    assert limiter._connected is True

    # A round-trip proves the connection works, not merely that it was opened.
    result = await limiter.check(
        tenant_id="unit-test-rate-limiter-probe",
        endpoint="/probe",
        limit=5,
        window_seconds=60,
    )
    assert result.allowed is True
    assert result.remaining >= 0
