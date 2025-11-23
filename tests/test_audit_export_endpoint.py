import json

import pytest
from fastapi.testclient import TestClient

from integrations.repositories import get_audit_store
from services.gateway.main import app


@pytest.mark.asyncio
async def test_audit_export_ndjson_memory_store(monkeypatch):
    # Force in-memory audit store to avoid Postgres dependency
    monkeypatch.setenv("AUDIT_STORE_MODE", "memory")
    # Ensure auth is not required for admin endpoints in this test
    monkeypatch.setenv("SA01_AUTH_REQUIRED", "false")

    # Seed a couple of audit events
    store = get_audit_store()
    req_id = "req-123"
    sess_id = "sess-abc"
    tenant = "t-001"

    await store.ensure_schema()
    id1 = await store.log(
        request_id=req_id,
        trace_id=None,
        session_id=sess_id,
        tenant=tenant,
        subject="user-1",
        action="message.enqueue",
        resource="conversation.message",
        target_id="evt-1",
        details={"attachments": 0, "published": True, "enqueued": True},
        diff=None,
        ip="127.0.0.1",
        user_agent="pytest",
    )
    id2 = await store.log(
        request_id=req_id,
        trace_id=None,
        session_id=sess_id,
        tenant=tenant,
        subject="user-1",
        action="settings.update",
        resource="ui.settings",
        target_id=None,
        details={"providers_updated": ["openai"]},
        diff={"before": {}, "after": {"agent_profile": "default"}},
        ip="127.0.0.1",
        user_agent="pytest",
    )

    # Call the export endpoint with a filter to this tenant/request
    client = TestClient(app)
    resp = client.get(f"/v1/admin/audit/export?tenant={tenant}&request_id={req_id}")

    assert resp.status_code == 200
    assert resp.headers.get("Content-Type", "").startswith("application/x-ndjson")

    # Parse NDJSON
    lines = [ln for ln in resp.text.splitlines() if ln.strip()]
    assert len(lines) >= 2

    objs = [json.loads(ln) for ln in lines]
    # ids should be ascending and include our two entries
    ids = [o["id"] for o in objs]
    assert ids[0] == id1
    assert any(o["id"] == id2 for o in objs)

    # Spot-check fields
    first = objs[0]
    assert first["tenant"] == tenant
    assert first["request_id"] == req_id
    assert first["session_id"] == sess_id
    assert first["action"] == "message.enqueue"
    assert first["resource"] == "conversation.message"
    assert isinstance(first["details"], dict)
