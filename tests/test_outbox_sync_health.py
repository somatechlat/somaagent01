import pytest

from services.outbox_sync.main import OutboxSyncWorker


class DummyStore:
    def __init__(self):
        self.claimed_calls = []

    async def close(self):
        return None

    async def ensure(self):
        return None

    async def claim_batch(self, limit: int):
        self.claimed_calls.append(limit)
        return []


class DummyBus:
    async def close(self):
        return None


@pytest.mark.asyncio
async def test_effective_limits_change(monkeypatch):
    store = DummyStore()
    worker = OutboxSyncWorker(store=store, bus=DummyBus())
    # Force states and assert limits
    worker._health_state = "normal"
    bs, it = worker._compute_effective_limits()
    assert bs == worker.batch_size and it == worker.interval

    worker._health_state = "degraded"
    bs, it = worker._compute_effective_limits()
    assert bs <= 25 and it >= 1.0

    worker._health_state = "down"
    bs, it = worker._compute_effective_limits()
    assert bs == 1 and it >= max(worker.interval * 2.0, 3.0)
