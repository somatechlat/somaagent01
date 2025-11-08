import json
import os

import pytest
from fastapi.testclient import TestClient

from services.common.export_job_store import (
    ensure_schema as ensure_export_jobs_schema,
    ExportJobStore,
)
from services.common.memory_replica_store import (
    ensure_schema as ensure_replica_schema,
    MemoryReplicaStore,
)
from services.gateway.main import app


@pytest.mark.asyncio
@pytest.mark.integration
async def test_export_job_end_to_end(monkeypatch, tmp_path):
    dsn = os.getenv("TEST_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TEST_POSTGRES_DSN not set; skipping integration test")

    monkeypatch.setenv("POSTGRES_DSN", dsn)
    monkeypatch.setenv("EXPORT_JOBS_DIR", str(tmp_path))

    # Ensure schemas
    replica = MemoryReplicaStore(dsn=dsn)
    await ensure_replica_schema(replica)
    export_store = ExportJobStore(dsn=dsn)
    await ensure_export_jobs_schema(export_store)

    # Seed replica with two rows
    import time

    for idx in (1, 2):
        wal = {
            "type": "memory.write",
            "role": "assistant",
            "session_id": "s-exp",
            "tenant": "t-exp",
            "payload": {
                "id": f"exp-{idx}",
                "content": f"line {idx}",
                "metadata": {"universe_id": "u-exp", "namespace": "wm"},
            },
            "result": {"coord": f"c-{idx}", "trace_id": f"tr-{idx}", "request_id": f"rq-{idx}"},
            "timestamp": time.time(),
        }
        await replica.insert_from_wal(wal)

    client = TestClient(app)

    # Create export job (tenant-scoped)
    resp = client.post("/v1/memory/export/jobs", json={"tenant": "t-exp", "namespace": "wm"})
    assert resp.status_code == 200
    job_id = resp.json()["job_id"]

    # Process immediately by invoking the internal processor (avoids waiting for background loop)
    import services.gateway.main as gw

    await gw._process_export_job(job_id)  # type: ignore

    # Check job status
    st = client.get(f"/v1/memory/export/jobs/{job_id}")
    assert st.status_code == 200
    body = st.json()
    assert body["status"] == "completed"
    assert body["row_count"] >= 2
    assert body["download_url"]

    # Download and validate NDJSON lines
    dl = client.get(body["download_url"])
    assert dl.status_code == 200
    lines = [ln for ln in dl.text.splitlines() if ln.strip()]
    assert len(lines) >= 2
    first = json.loads(lines[0])
    assert first.get("tenant") == "t-exp"
