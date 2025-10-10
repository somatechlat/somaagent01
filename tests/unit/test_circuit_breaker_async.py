import asyncio

import pytest

from python.helpers.circuit_breaker import circuit_breaker, CircuitOpenError


@pytest.mark.asyncio
async def test_async_circuit_breaker_opens_after_failures():
    attempts = {"count": 0}

    @circuit_breaker(failure_threshold=2, reset_timeout=0.05)
    async def flaky(_: dict[str, object]) -> dict[str, object]:
        attempts["count"] += 1
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        await flaky({})
    with pytest.raises(RuntimeError):
        await flaky({})
    with pytest.raises(CircuitOpenError):
        await flaky({})

    # After the reset timeout the circuit allows a trial call.
    await asyncio.sleep(0.06)
    with pytest.raises(RuntimeError):
        await flaky({})


@pytest.mark.asyncio
async def test_async_circuit_breaker_closes_after_successful_trial():
    attempts = {"count": 0}

    @circuit_breaker(failure_threshold=2, reset_timeout=0.05)
    async def recovering(_: dict[str, object]) -> dict[str, object]:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise RuntimeError("fail")
        return {"status": "ok"}

    with pytest.raises(RuntimeError):
        await recovering({})
    with pytest.raises(RuntimeError):
        await recovering({})
    with pytest.raises(CircuitOpenError):
        await recovering({})

    await asyncio.sleep(0.06)
    result = await recovering({})
    assert result == {"status": "ok"}
    # Subsequent calls should remain closed
    result = await recovering({})
    assert result == {"status": "ok"}
