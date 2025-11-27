import os
import json
import pytest
from fastapi.testclient import TestClient
from integrations.repositories import get_audit_store
from services.gateway.main import app


@pytest.mark.asyncio
async def test_audit_export_ndjson_memory_store(monkeypatch):
    monkeypatch.setenv(os.getenv(os.getenv('VIBE_E7AB7D4A')), os.getenv(os.
        getenv('VIBE_6F3412C5')))
    monkeypatch.setenv(os.getenv(os.getenv('VIBE_555C4B29')), os.getenv(os.
        getenv('VIBE_C03EF574')))
    store = get_audit_store()
    req_id = os.getenv(os.getenv('VIBE_CE03A30A'))
    sess_id = os.getenv(os.getenv('VIBE_5066AE71'))
    tenant = os.getenv(os.getenv('VIBE_1D2646F4'))
    await store.ensure_schema()
    id1 = await store.log(request_id=req_id, trace_id=None, session_id=
        sess_id, tenant=tenant, subject=os.getenv(os.getenv('VIBE_4B91B3C6'
        )), action=os.getenv(os.getenv('VIBE_3720F7D0')), resource=os.
        getenv(os.getenv('VIBE_D7DBF159')), target_id=os.getenv(os.getenv(
        'VIBE_04A070F8')), details={os.getenv(os.getenv('VIBE_F0FDAA90')):
        int(os.getenv(os.getenv('VIBE_98A33F42'))), os.getenv(os.getenv(
        'VIBE_DD881878')): int(os.getenv(os.getenv('VIBE_CF6EC91D'))), os.
        getenv(os.getenv('VIBE_0F323828')): int(os.getenv(os.getenv(
        'VIBE_CF6EC91D')))}, diff=None, ip=os.getenv(os.getenv(
        'VIBE_F0B5A7B8')), user_agent=os.getenv(os.getenv('VIBE_B4838D19')))
    id2 = await store.log(request_id=req_id, trace_id=None, session_id=
        sess_id, tenant=tenant, subject=os.getenv(os.getenv('VIBE_4B91B3C6'
        )), action=os.getenv(os.getenv('VIBE_DDD3EBF6')), resource=os.
        getenv(os.getenv('VIBE_989492A9')), target_id=None, details={os.
        getenv(os.getenv('VIBE_2E337B6C')): [os.getenv(os.getenv(
        'VIBE_7BA36846'))]}, diff={os.getenv(os.getenv('VIBE_4708CAAA')): {
        }, os.getenv(os.getenv('VIBE_E2D9958A')): {os.getenv(os.getenv(
        'VIBE_83E229A8')): os.getenv(os.getenv('VIBE_562D084D'))}}, ip=os.
        getenv(os.getenv('VIBE_F0B5A7B8')), user_agent=os.getenv(os.getenv(
        'VIBE_B4838D19')))
    client = TestClient(app)
    resp = client.get(
        f'/v1/admin/audit/export?tenant={tenant}&request_id={req_id}')
    assert resp.status_code == int(os.getenv(os.getenv('VIBE_A14F3915')))
    assert resp.headers.get(os.getenv(os.getenv('VIBE_E1BD92F0')), os.
        getenv(os.getenv('VIBE_E2E8A0EE'))).startswith(os.getenv(os.getenv(
        'VIBE_AC12B5F1')))
    lines = [ln for ln in resp.text.splitlines() if ln.strip()]
    assert len(lines) >= int(os.getenv(os.getenv('VIBE_DE1EFB4F')))
    objs = [json.loads(ln) for ln in lines]
    ids = [o[os.getenv(os.getenv('VIBE_E0A19FAE'))] for o in objs]
    assert ids[int(os.getenv(os.getenv('VIBE_98A33F42')))] == id1
    assert any(o[os.getenv(os.getenv('VIBE_E0A19FAE'))] == id2 for o in objs)
    first = objs[int(os.getenv(os.getenv('VIBE_98A33F42')))]
    assert first[os.getenv(os.getenv('VIBE_4F610130'))] == tenant
    assert first[os.getenv(os.getenv('VIBE_F30A57BA'))] == req_id
    assert first[os.getenv(os.getenv('VIBE_7C693B78'))] == sess_id
    assert first[os.getenv(os.getenv('VIBE_925C08C3'))] == os.getenv(os.
        getenv('VIBE_3720F7D0'))
    assert first[os.getenv(os.getenv('VIBE_1848BF33'))] == os.getenv(os.
        getenv('VIBE_D7DBF159'))
    assert isinstance(first[os.getenv(os.getenv('VIBE_06942A95'))], dict)
