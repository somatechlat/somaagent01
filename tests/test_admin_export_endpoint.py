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
async def test_admin_memory_export_stream(monkeypatch):
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
        "role": "assistant",
        "session_id": "s-export",
        "persona_id": "p-export",
        "tenant": "t-export",
        "payload": {"id": "ev-exp-1", "content": "hello export", "metadata": {"k": "v"}},
        "result": {"coord": "c-exp", "request_id": "rq-exp", "trace_id": "tr-exp"},
        "timestamp": time.time(),
    }
    await store.insert_from_wal(wal)

    client = TestClient(app)
    resp = client.get("/v1/memory/export", params={"tenant": "t-export", "limit_total": 10})
    assert resp.status_code == 200
    body = resp.text.strip()
    assert body, "export body should not be empty"
    # NDJSON first line contains our event id
    first_line = body.splitlines()[0]
    assert "ev-exp-1" in first_line
