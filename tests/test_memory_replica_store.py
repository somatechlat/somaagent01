import time

import pytest

from services.common.memory_replica_store import ensure_schema, MemoryReplicaStore


@pytest.mark.asyncio
@pytest.mark.integration
async def test_insert_from_wal_and_latest_timestamp():
    store = MemoryReplicaStore()
    await ensure_schema(store)

    now = time.time()
    wal = {
        "type": "memory.write",
        "role": "user",
        "session_id": "s-test",
        "persona_id": None,
        "tenant": "default",
        "payload": {"id": "evt-1", "type": "user_message", "content": "hello", "metadata": {}},
        "result": {"coord": "c1", "trace_id": "t1", "request_id": "r1"},
        "timestamp": now,
    }

    row_id = await store.insert_from_wal(wal)
    assert isinstance(row_id, int) and row_id > 0

    latest = await store.latest_wal_timestamp()
    assert latest is not None
    # Allow slight drift between recording and reading
    assert abs(latest - now) < 10.0
