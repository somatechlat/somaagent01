"""A shared Redis client must outlive one event loop.

``get_async_redis_pool`` caches one ``redis.asyncio`` client per URL for the
life of the process. That client is bound to the event loop it first ran on.
When the loop is replaced — an ASGI worker recycling its loop, a test run, any
caller that creates and closes a loop — every command on the cached client
raises ``Event loop is closed``.

The rate limiter's fail-closed policy then converts that into ``allowed=False``,
and ``check_rate_limit`` turns it into a 429. Login is bricked for every caller
while the process still looks healthy. Fail-closed is the right answer to a
Redis that is down; it is the wrong answer to a client that is merely stale.

The pool must therefore notice that it is being asked to run on a different
loop than the one it was built for, and re-acquire. Not "reset everything
optimistically", and not "catch the error and allow" — both of those are
fallbacks wearing a coat.

Run:
    pytest tests/unit/test_redis_pool_loop_restart.py -v

Requires a reachable Redis. Real Redis, real client — no stub of either.
"""

from __future__ import annotations

import asyncio

from services.common.redis_pool import get_async_redis_pool, reset_pools


def _redis_url() -> str:
    import os

    return os.getenv("SA01_REDIS_URL") or os.getenv(
        "REDIS_URL", "redis://localhost:6379/0"
    )


async def _check_on_fresh_loop(url: str) -> bool:
    """Run one round-trip on a loop this call creates and closes itself."""
    client = get_async_redis_pool(url)
    await client.ping()
    return True


def test_a_pool_client_survives_the_loop_that_created_it():
    """The baseline: on one loop, the pooled client works."""
    url = _redis_url()
    reset_pools()

    async def _run() -> bool:
        return await _check_on_fresh_loop(url)

    assert asyncio.run(_run()) is True


def test_a_pool_client_is_reacquired_when_the_loop_changes():
    """The defect. Two sequential loops, same process, same URL.

    The second loop must still be able to talk to Redis. Today the cached
    client belongs to the first, closed loop and every command raises, which
    the rate limiter reads as "deny everyone".
    """
    url = _redis_url()
    reset_pools()

    async def _first() -> bool:
        return await _check_on_fresh_loop(url)

    async def _second() -> bool:
        return await _check_on_fresh_loop(url)

    assert asyncio.run(_first()) is True
    assert asyncio.run(_second()) is True


def test_the_rate_limiter_still_denies_when_redis_is_genuinely_unreachable():
    """The gate must not be softened to make the above pass.

    A pool that cannot reach Redis is a real outage and must fail closed.
    Only a stale client on a replaced loop is the bug; "Redis is down" is
    still a denial.
    """
    from services.common.rate_limiter import RedisRateLimiter

    limiter = RedisRateLimiter(
        redis_url="redis://127.0.0.1:1/0",  # nothing listens here
        default_limit=10,
        default_window_seconds=60,
    )

    async def _run():
        return await limiter.check(tenant_id="t", endpoint="/x", limit=5, window_seconds=60)

    result = asyncio.run(_run())
    assert result.allowed is False
    assert result.remaining == 0
