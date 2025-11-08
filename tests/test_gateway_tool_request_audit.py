import json

import pytest
from fastapi.testclient import TestClient

from services.gateway.main import app, get_publisher


class _FakePublisher:
    async def publish(self, *args, **kwargs):
        # Emulate successful enqueue
        return {"published": True}


@pytest.mark.asyncio
async def test_tool_request_enqueue_audit(monkeypatch):
    # Use in-memory audit store and disable auth for simplicity
    monkeypatch.setenv("AUDIT_STORE_MODE", "memory")
    monkeypatch.setenv("GATEWAY_REQUIRE_AUTH", "false")

    # Override publisher to avoid Kafka dependency
    app.dependency_overrides[get_publisher] = lambda: _FakePublisher()

    client = TestClient(app)

    session_id = "sess-audit-1"
    payload = {
        "session_id": session_id,
        "tool_name": "echo",
        "args": {"text": "hello"},
        "metadata": {"tenant": "public"},
    }

    r = client.post("/v1/tool/request", json=payload)
    assert r.status_code == 200
    event_id = r.json().get("event_id")
    assert event_id

    # Export audit events filtered by session_id and action
    exp = client.get(f"/v1/admin/audit/export?action=tool.request.enqueue&session_id={session_id}")
    assert exp.status_code == 200

    lines = [ln for ln in exp.text.splitlines() if ln.strip()]
    assert lines, "no audit events returned"
    entries = [json.loads(ln) for ln in lines]
    # Find our event
    match = [
        e
        for e in entries
        if (e.get("target_id") == event_id and e.get("resource") == "tool.request")
    ]
    assert match, f"expected audit entry for event_id={event_id}"

    ent = match[0]
    assert ent["action"] == "tool.request.enqueue"
    assert ent["session_id"] == session_id
    assert set(ent.get("details", {}).get("args_keys", [])) == {"text"}

    # Clean overrides
    app.dependency_overrides.pop(get_publisher, None)
