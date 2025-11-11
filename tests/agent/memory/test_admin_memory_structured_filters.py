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
async def test_admin_memory_structured_filters(monkeypatch):
    dsn = os.getenv("TEST_SA01_DB_DSN")
    if not dsn:
        pytest.skip("TEST_SA01_DB_DSN not set; skipping integration test")

    monkeypatch.setenv("SA01_DB_DSN", dsn)
    store = MemoryReplicaStore(dsn=dsn)
    await ensure_replica_schema(store)

    # Insert rows via insert_from_wal with different universe/namespace encodings
    wal1 = {
        "type": "memory.write",
        "role": "user",
        "session_id": "s-1",
        "tenant": "t-1",
        "payload": {
            "id": "m-1",
            "content": "u1-ns-wm",
            "metadata": {"universe_id": "u-1", "namespace": "wm"},
        },
        "result": {},
        "timestamp": time.time(),
    }
    wal2 = {
        "type": "memory.write",
        "role": "user",
        "session_id": "s-2",
        "tenant": "t-1",
        "payload": {
            "id": "m-2",
            "content": "u1-ns-ltm",
            "namespace": "ltm",
            "metadata": {"universe_id": "u-1"},
        },
        "result": {},
        "timestamp": time.time(),
    }
    wal3 = {
        "type": "memory.write",
        "role": "user",
        "session_id": "s-3",
        "tenant": "t-1",
        "payload": {"id": "m-3", "content": "u2", "metadata": {"universe_id": "u-2"}},
        "result": {},
        "timestamp": time.time(),
    }
    await store.insert_from_wal(wal1)
    await store.insert_from_wal(wal2)
    await store.insert_from_wal(wal3)

    client = TestClient(app)

    # Filter by universe u-1
    resp = client.get("/v1/admin/memory", params={"tenant": "t-1", "universe": "u-1"})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any("u1-ns-wm" in (it.get("payload", {}).get("content", "")) for it in items)
    assert any("u1-ns-ltm" in (it.get("payload", {}).get("content", "")) for it in items)
    assert all(
        ((it.get("payload") or {}).get("metadata", {}).get("universe_id") == "u-1") for it in items
    )

    # Filter by namespace wm
    resp2 = client.get("/v1/admin/memory", params={"tenant": "t-1", "namespace": "wm"})
    assert resp2.status_code == 200
    items2 = resp2.json()["items"]
    assert any("u1-ns-wm" in (it.get("payload", {}).get("content", "")) for it in items2)
    assert all(
        (
            (it.get("payload") or {}).get("namespace") == "wm"
            or (it.get("payload") or {}).get("metadata", {}).get("namespace") == "wm"
        )
        for it in items2
    )
