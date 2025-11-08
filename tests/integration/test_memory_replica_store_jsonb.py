import os
import time
import uuid

import pytest

from services.common.memory_replica_store import ensure_schema, MemoryReplicaStore

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_memory_replica_payload_is_dict():
    """
    Ensure MemoryReplicaStore decodes JSONB to Python dict via asyncpg codecs.
    Skips gracefully if Postgres is unreachable in this environment.
    """
    # Use DSN resolution from store by default
    store = MemoryReplicaStore(dsn=os.getenv("POSTGRES_DSN"))

    # Try to connect; skip if cannot
    try:
        await ensure_schema(store)
    except Exception as exc:
        pytest.skip(f"Postgres not reachable for integration test: {exc}")

    # Insert a unique WAL event and read it back
    event_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    wal = {
        "type": "memory.write",
        "role": "tool",
        "session_id": session_id,
        "tenant": os.getenv("SOMA_TENANT_ID", "public"),
        "payload": {
            "id": event_id,
            "type": "unit_test_payload",
            "content": {"hello": "world", "n": 42},
        },
        "result": {"coord": None, "trace_id": None, "request_id": None},
        "timestamp": time.time(),
    }

    _ = await store.insert_from_wal(wal)

    row = await store.get_by_event_id(event_id)
    assert row is not None, "inserted replica row not found"
    assert isinstance(row.payload, dict), f"payload must be dict, got {type(row.payload)}"
    assert row.payload.get("type") == "unit_test_payload"

    # Verify list_memories also yields dict payload
    rows = await store.list_memories(limit=5, session_id=session_id)
    assert any(
        isinstance(r.payload, dict) for r in rows
    ), "list_memories returned non-dict payloads"
