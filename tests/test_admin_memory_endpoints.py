import os
import time

import pytest
from fastapi.testclient import TestClient

from services.common.memory_replica_store import (
    ensure_schema as ensure_replica_schema,
    MemoryReplicaStore,
)
from services.gateway.main import app


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admin_memory_list_and_detail(monkeypatch):
    dsn = os.getenv("TEST_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TEST_POSTGRES_DSN not set; skipping integration test")

    # Point gateway and store at test DB and ensure schema
    monkeypatch.setenv("POSTGRES_DSN", dsn)
    store = MemoryReplicaStore(dsn=dsn)
    await ensure_replica_schema(store)

    # Insert a sample WAL-derived row via insert_from_wal
    wal = {
        "type": "memory.write",
        "role": "user",
        "session_id": "s-admin",
        "persona_id": "p-admin",
        "tenant": "t-admin",
        "payload": {"id": "ev-123", "content": "hello admin", "metadata": {"k": "v"}},
        "result": {"coord": "c-xyz", "request_id": "rq-xyz", "trace_id": "tr-xyz"},
        "timestamp": time.time(),
    }
    await store.insert_from_wal(wal)

    # Call API without requiring auth (default in tests) and verify response
    client = TestClient(app)
    resp = client.get("/v1/admin/memory", params={"tenant": "t-admin", "limit": 10})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data.get("items"), list)
    assert any(item.get("event_id") == "ev-123" for item in data.get("items", []))

    # Detail by event id
    resp2 = client.get("/v1/admin/memory/ev-123")
    assert resp2.status_code == 200
    detail = resp2.json()
    assert detail.get("event_id") == "ev-123"
