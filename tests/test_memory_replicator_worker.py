import os
import time

import pytest

from services.common.dlq_store import DLQStore, ensure_schema as ensure_dlq_schema
from services.common.memory_replica_store import (
    ensure_schema as ensure_replica_schema,
    MemoryReplicaStore,
)
from services.memory_replicator.main import MemoryReplicator


@pytest.mark.asyncio
@pytest.mark.integration
async def test_replicator_handle_wal_persists_row(monkeypatch):
    # Use a temporary Postgres provided by TEST_POSTGRES_DSN if set; otherwise skip
    dsn = os.getenv("TEST_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TEST_POSTGRES_DSN not set; skipping integration test")

    replica = MemoryReplicaStore(dsn=dsn)
    dlq_store = DLQStore(dsn=dsn)
    await ensure_replica_schema(replica)
    await ensure_dlq_schema(dlq_store)

    rep = MemoryReplicator()
    # Inject stores to point at our test database and disable Kafka DLQ publish
    rep.replica = replica
    rep.dlq_store = dlq_store

    class _NoKafkaDLQ:
        async def send_to_dlq(self, event, error, *, retry_count: int = 0):
            return None

    rep.dlq = _NoKafkaDLQ()

    event = {
        "type": "memory.write",
        "role": "user",
        "session_id": "s-test",
        "persona_id": "p-1",
        "tenant": "t1",
        "payload": {"id": "mem-1", "content": "hello"},
        "result": {"coord": "c1", "trace_id": "tr1", "request_id": "rq1"},
        "timestamp": time.time(),
    }

    await rep._handle_wal(event)

    # Verify replica row exists by checking latest wal timestamp
    ts = await replica.latest_wal_timestamp()
    assert ts is not None and ts > 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_replicator_error_goes_to_dlq_store(monkeypatch):
    dsn = os.getenv("TEST_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TEST_POSTGRES_DSN not set; skipping integration test")

    replica = MemoryReplicaStore(dsn=dsn)
    dlq_store = DLQStore(dsn=dsn)
    await ensure_replica_schema(replica)
    await ensure_dlq_schema(dlq_store)

    rep = MemoryReplicator()
    rep.replica = replica
    rep.dlq_store = dlq_store

    class _NoKafkaDLQ:
        async def send_to_dlq(self, event, error, *, retry_count: int = 0):
            return None

    rep.dlq = _NoKafkaDLQ()

    # Monkeypatch insert to raise
    async def _boom(_event):
        raise RuntimeError("replica down")

    rep.replica.insert_from_wal = _boom  # type: ignore[assignment]

    event = {
        "type": "memory.write",
        "role": "user",
        "session_id": "s-test",
        "persona_id": "p-1",
        "tenant": "t1",
        "payload": {"id": "mem-2", "content": "will fail"},
        "result": {"coord": None, "trace_id": "trX", "request_id": "rqX"},
        "timestamp": time.time(),
    }

    await rep._handle_wal(event)

    # Verify DLQ row persisted
    count = await dlq_store.count(topic=f"{rep.wal_topic}.dlq")
    assert count >= 1
