import pytest
from fastapi.testclient import TestClient

from integrations.repositories import get_audit_store
from services.gateway.main import app


@pytest.mark.asyncio
async def test_admin_audit_decisions_list_basic(monkeypatch):
    # Use in-memory audit store and disable auth for test simplicity
    monkeypatch.setenv("AUDIT_STORE_MODE", "memory")
    monkeypatch.setenv("SA01_AUTH_REQUIRED", "false")

    store = get_audit_store()
    await store.ensure_schema()

    # Seed some decision and non-decision events
    req_id = "req-xyz"
    sess_id = "sess-123"
    tenant = "t-decisions"

    # Two decision receipts
    id1 = await store.log(
        request_id=req_id,
        trace_id=None,
        session_id=sess_id,
        tenant=tenant,
        subject="user-7",
        action="auth.decision",
        resource="/v1/foo",
        target_id=None,
        details={
            "opa": {"allow": True},
            "openfga": {"enforced": False, "reason": "not_configured"},
            "scope": "admin",
        },
        diff=None,
        ip="127.0.0.1",
        user_agent="pytest",
    )
    id2 = await store.log(
        request_id=req_id,
        trace_id=None,
        session_id=sess_id,
        tenant=tenant,
        subject="user-7",
        action="auth.decision",
        resource="/v1/bar",
        target_id=None,
        details={
            "opa": {"allow": True},
            "openfga": {"enforced": True, "allowed": True},
            "scope": "admin",
        },
        diff=None,
        ip="127.0.0.1",
        user_agent="pytest",
    )

    # A different action that should be ignored by this endpoint
    _ = await store.log(
        request_id=req_id,
        trace_id=None,
        session_id=sess_id,
        tenant=tenant,
        subject="user-7",
        action="message.enqueue",
        resource="conversation.message",
        target_id="evt-1",
        details={"published": True, "enqueued": True},
        diff=None,
        ip="127.0.0.1",
        user_agent="pytest",
    )

    client = TestClient(app)

    # List without filters -> should return the two decisions in ascending id order
    resp = client.get("/v1/admin/audit/decisions?limit=10")
    assert resp.status_code == 200
    body = resp.json()
    items = body.get("items")
    assert isinstance(items, list)
    # Ensure only decision entries are present
    assert all(it["resource"] in {"/v1/foo", "/v1/bar"} for it in items)
    ids = [it["id"] for it in items]
    assert id1 in ids and id2 in ids

    # Filter by tenant
    resp2 = client.get(f"/v1/admin/audit/decisions?tenant={tenant}&limit=10")
    assert resp2.status_code == 200
    items2 = resp2.json().get("items")
    assert len(items2) >= 2
    assert all(it.get("tenant") == tenant for it in items2)

    # Pagination: use after=id1, expect id2 and beyond
    resp3 = client.get(f"/v1/admin/audit/decisions?after={id1}")
    assert resp3.status_code == 200
    items3 = resp3.json().get("items")
    assert all(it["id"] > id1 for it in items3)
