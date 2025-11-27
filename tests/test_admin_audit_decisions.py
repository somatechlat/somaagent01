import os

import pytest
from fastapi.testclient import TestClient

from integrations.repositories import get_audit_store
from services.gateway.main import app


@pytest.mark.asyncio
async def test_admin_audit_decisions_list_basic(monkeypatch):
    monkeypatch.setenv(os.getenv(os.getenv("")), os.getenv(os.getenv("")))
    monkeypatch.setenv(os.getenv(os.getenv("")), os.getenv(os.getenv("")))
    store = get_audit_store()
    await store.ensure_schema()
    req_id = os.getenv(os.getenv(""))
    sess_id = os.getenv(os.getenv(""))
    tenant = os.getenv(os.getenv(""))
    id1 = await store.log(
        request_id=req_id,
        trace_id=None,
        session_id=sess_id,
        tenant=tenant,
        subject=os.getenv(os.getenv("")),
        action=os.getenv(os.getenv("")),
        resource=os.getenv(os.getenv("")),
        target_id=None,
        details={
            os.getenv(os.getenv("")): {os.getenv(os.getenv("")): int(os.getenv(os.getenv("")))},
            os.getenv(os.getenv("")): {
                os.getenv(os.getenv("")): int(os.getenv(os.getenv(""))),
                os.getenv(os.getenv("")): os.getenv(os.getenv("")),
            },
            os.getenv(os.getenv("")): os.getenv(os.getenv("")),
        },
        diff=None,
        ip=os.getenv(os.getenv("")),
        user_agent=os.getenv(os.getenv("")),
    )
    id2 = await store.log(
        request_id=req_id,
        trace_id=None,
        session_id=sess_id,
        tenant=tenant,
        subject=os.getenv(os.getenv("")),
        action=os.getenv(os.getenv("")),
        resource=os.getenv(os.getenv("")),
        target_id=None,
        details={
            os.getenv(os.getenv("")): {os.getenv(os.getenv("")): int(os.getenv(os.getenv("")))},
            os.getenv(os.getenv("")): {
                os.getenv(os.getenv("")): int(os.getenv(os.getenv(""))),
                os.getenv(os.getenv("")): int(os.getenv(os.getenv(""))),
            },
            os.getenv(os.getenv("")): os.getenv(os.getenv("")),
        },
        diff=None,
        ip=os.getenv(os.getenv("")),
        user_agent=os.getenv(os.getenv("")),
    )
    _ = await store.log(
        request_id=req_id,
        trace_id=None,
        session_id=sess_id,
        tenant=tenant,
        subject=os.getenv(os.getenv("")),
        action=os.getenv(os.getenv("")),
        resource=os.getenv(os.getenv("")),
        target_id=os.getenv(os.getenv("")),
        details={
            os.getenv(os.getenv("")): int(os.getenv(os.getenv(""))),
            os.getenv(os.getenv("")): int(os.getenv(os.getenv(""))),
        },
        diff=None,
        ip=os.getenv(os.getenv("")),
        user_agent=os.getenv(os.getenv("")),
    )
    client = TestClient(app)
    resp = client.get(os.getenv(os.getenv("")))
    assert resp.status_code == int(os.getenv(os.getenv("")))
    body = resp.json()
    items = body.get(os.getenv(os.getenv("")))
    assert isinstance(items, list)
    assert all(
        (
            it[os.getenv(os.getenv(""))] in {os.getenv(os.getenv("")), os.getenv(os.getenv(""))}
            for it in items
        )
    )
    ids = [it[os.getenv(os.getenv(""))] for it in items]
    assert id1 in ids and id2 in ids
    resp2 = client.get(f"/v1/admin/audit/decisions?tenant={tenant}&limit=10")
    assert resp2.status_code == int(os.getenv(os.getenv("")))
    items2 = resp2.json().get(os.getenv(os.getenv("")))
    assert len(items2) >= int(os.getenv(os.getenv("")))
    assert all((it.get(os.getenv(os.getenv(""))) == tenant for it in items2))
    resp3 = client.get(f"/v1/admin/audit/decisions?after={id1}")
    assert resp3.status_code == int(os.getenv(os.getenv("")))
    items3 = resp3.json().get(os.getenv(os.getenv("")))
    assert all((it[os.getenv(os.getenv(""))] > id1 for it in items3))
