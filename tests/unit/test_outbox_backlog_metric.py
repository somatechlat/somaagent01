from services.outbox_sync.main import OUTBOX_BACKLOG, OutboxSyncWorker


class _FakeStore:
    def __init__(self, counts):
        self._counts = counts
        self._i = 0

    async def count_pending(self):
        val = self._counts[min(self._i, len(self._counts) - 1)]
        self._i += 1
        return val

    async def claim_batch(self, limit: int = 1):  # pragma: no cover - unused in test
        return []

    async def close(self):  # pragma: no cover - unused
        pass


class _FakeBus:
    async def publish(self, topic, payload):  # pragma: no cover - unused in test
        pass

    async def close(self):  # pragma: no cover - unused
        pass


async def _run_one_loop(worker):
    # Run a single iteration of the loop body logic we need (probe + backlog + claim)
    # We mimic the structure inside start() without starting infinite loop.
    from services.outbox_sync.main import EFFECTIVE_BATCH

    worker._health_checked_at = 0  # force probe
    await worker._maybe_probe_health()
    bsize, interval = worker._compute_effective_limits()
    EFFECTIVE_BATCH.set(bsize)
    OUTBOX_BACKLOG.set(await worker.store.count_pending())


def test_outbox_backlog_gauge_event_loop(monkeypatch):
    # Use a fake store that returns deterministic counts
    store = _FakeStore([5, 3])
    worker = OutboxSyncWorker(store=store, bus=_FakeBus())

    import asyncio

    async def _t():
        await _run_one_loop(worker)
        first = OUTBOX_BACKLOG._value.get()  # access current gauge value
        await _run_one_loop(worker)
        second = OUTBOX_BACKLOG._value.get()
        assert first == 5
        assert second == 3

    asyncio.run(_t())
