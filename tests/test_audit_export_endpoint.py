import json
import os

import pytest
from fastapi.testclient import TestClient

from integrations.repositories import get_audit_store
from services.gateway.main import app


@pytest.mark.asyncio
async def test_audit_export_ndjson_memory_store(monkeypatch):
    monkeypatch.setenv(os.getenv(os.getenv("")), os.getenv(os.getenv("")))
    monkeypatch.setenv(os.getenv(os.getenv("")), os.getenv(os.getenv("")))
    store = get_audit_store()
    req_id = os.getenv(os.getenv(""))
    sess_id = os.getenv(os.getenv(""))
    tenant = os.getenv(os.getenv(""))
    await store.ensure_schema()
    id1 = await store.log(
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
            os.getenv(os.getenv("")): int(os.getenv(os.getenv(""))),
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
        details={os.getenv(os.getenv("")): [os.getenv(os.getenv(""))]},
        diff={
            os.getenv(os.getenv("")): {},
            os.getenv(os.getenv("")): {os.getenv(os.getenv("")): os.getenv(os.getenv(""))},
        },
        ip=os.getenv(os.getenv("")),
        user_agent=os.getenv(os.getenv("")),
    )
    client = TestClient(app)
    resp = client.get(f"/v1/admin/audit/export?tenant={tenant}&request_id={req_id}")
    assert resp.status_code == int(os.getenv(os.getenv("")))
    assert resp.headers.get(os.getenv(os.getenv("")), os.getenv(os.getenv(""))).startswith(
        os.getenv(os.getenv(""))
    )
    lines = [ln for ln in resp.text.splitlines() if ln.strip()]
    assert len(lines) >= int(os.getenv(os.getenv("")))
    objs = [json.loads(ln) for ln in lines]
    ids = [o[os.getenv(os.getenv(""))] for o in objs]
    assert ids[int(os.getenv(os.getenv("")))] == id1
    assert any((o[os.getenv(os.getenv(""))] == id2 for o in objs))
    first = objs[int(os.getenv(os.getenv("")))]
    assert first[os.getenv(os.getenv(""))] == tenant
    assert first[os.getenv(os.getenv(""))] == req_id
    assert first[os.getenv(os.getenv(""))] == sess_id
    assert first[os.getenv(os.getenv(""))] == os.getenv(os.getenv(""))
    assert first[os.getenv(os.getenv(""))] == os.getenv(os.getenv(""))
    assert isinstance(first[os.getenv(os.getenv(""))], dict)
