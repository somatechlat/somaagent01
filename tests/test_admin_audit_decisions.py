import os
import pytest
from fastapi.testclient import TestClient
from integrations.repositories import get_audit_store
from services.gateway.main import app


@pytest.mark.asyncio
async def test_admin_audit_decisions_list_basic(monkeypatch):
    monkeypatch.setenv(os.getenv(os.getenv('VIBE_21EA12E0')), os.getenv(os.
        getenv('VIBE_D9D0CCAA')))
    monkeypatch.setenv(os.getenv(os.getenv('VIBE_2D46255D')), os.getenv(os.
        getenv('VIBE_596B607E')))
    store = get_audit_store()
    await store.ensure_schema()
    req_id = os.getenv(os.getenv('VIBE_DE0C4154'))
    sess_id = os.getenv(os.getenv('VIBE_7BE63DD1'))
    tenant = os.getenv(os.getenv('VIBE_AD759C6F'))
    id1 = await store.log(request_id=req_id, trace_id=None, session_id=
        sess_id, tenant=tenant, subject=os.getenv(os.getenv('VIBE_42FCB946'
        )), action=os.getenv(os.getenv('VIBE_FC924155')), resource=os.
        getenv(os.getenv('VIBE_2CD11467')), target_id=None, details={os.
        getenv(os.getenv('VIBE_BDDC4671')): {os.getenv(os.getenv(
        'VIBE_9F571882')): int(os.getenv(os.getenv('VIBE_44D4E135')))}, os.
        getenv(os.getenv('VIBE_3C30C861')): {os.getenv(os.getenv(
        'VIBE_3C2184E3')): int(os.getenv(os.getenv('VIBE_102934C7'))), os.
        getenv(os.getenv('VIBE_97C49211')): os.getenv(os.getenv(
        'VIBE_25CC5264'))}, os.getenv(os.getenv('VIBE_256C36B4')): os.
        getenv(os.getenv('VIBE_E12783BB'))}, diff=None, ip=os.getenv(os.
        getenv('VIBE_6071FC79')), user_agent=os.getenv(os.getenv(
        'VIBE_D05345F2')))
    id2 = await store.log(request_id=req_id, trace_id=None, session_id=
        sess_id, tenant=tenant, subject=os.getenv(os.getenv('VIBE_42FCB946'
        )), action=os.getenv(os.getenv('VIBE_FC924155')), resource=os.
        getenv(os.getenv('VIBE_283B5736')), target_id=None, details={os.
        getenv(os.getenv('VIBE_BDDC4671')): {os.getenv(os.getenv(
        'VIBE_9F571882')): int(os.getenv(os.getenv('VIBE_44D4E135')))}, os.
        getenv(os.getenv('VIBE_3C30C861')): {os.getenv(os.getenv(
        'VIBE_3C2184E3')): int(os.getenv(os.getenv('VIBE_44D4E135'))), os.
        getenv(os.getenv('VIBE_D3E14DB6')): int(os.getenv(os.getenv(
        'VIBE_44D4E135')))}, os.getenv(os.getenv('VIBE_256C36B4')): os.
        getenv(os.getenv('VIBE_E12783BB'))}, diff=None, ip=os.getenv(os.
        getenv('VIBE_6071FC79')), user_agent=os.getenv(os.getenv(
        'VIBE_D05345F2')))
    _ = await store.log(request_id=req_id, trace_id=None, session_id=
        sess_id, tenant=tenant, subject=os.getenv(os.getenv('VIBE_42FCB946'
        )), action=os.getenv(os.getenv('VIBE_5F7E4BF4')), resource=os.
        getenv(os.getenv('VIBE_8AF4D689')), target_id=os.getenv(os.getenv(
        'VIBE_CEF02D2D')), details={os.getenv(os.getenv('VIBE_605C1949')):
        int(os.getenv(os.getenv('VIBE_44D4E135'))), os.getenv(os.getenv(
        'VIBE_E8123F04')): int(os.getenv(os.getenv('VIBE_44D4E135')))},
        diff=None, ip=os.getenv(os.getenv('VIBE_6071FC79')), user_agent=os.
        getenv(os.getenv('VIBE_D05345F2')))
    client = TestClient(app)
    resp = client.get(os.getenv(os.getenv('VIBE_5E8EAA4C')))
    assert resp.status_code == int(os.getenv(os.getenv('VIBE_025C065F')))
    body = resp.json()
    items = body.get(os.getenv(os.getenv('VIBE_38E6AE3B')))
    assert isinstance(items, list)
    assert all(it[os.getenv(os.getenv('VIBE_467BEE5A'))] in {os.getenv(os.
        getenv('VIBE_2CD11467')), os.getenv(os.getenv('VIBE_283B5736'))} for
        it in items)
    ids = [it[os.getenv(os.getenv('VIBE_7C27C505'))] for it in items]
    assert id1 in ids and id2 in ids
    resp2 = client.get(f'/v1/admin/audit/decisions?tenant={tenant}&limit=10')
    assert resp2.status_code == int(os.getenv(os.getenv('VIBE_025C065F')))
    items2 = resp2.json().get(os.getenv(os.getenv('VIBE_38E6AE3B')))
    assert len(items2) >= int(os.getenv(os.getenv('VIBE_BE0EBF67')))
    assert all(it.get(os.getenv(os.getenv('VIBE_0C8E5485'))) == tenant for
        it in items2)
    resp3 = client.get(f'/v1/admin/audit/decisions?after={id1}')
    assert resp3.status_code == int(os.getenv(os.getenv('VIBE_025C065F')))
    items3 = resp3.json().get(os.getenv(os.getenv('VIBE_38E6AE3B')))
    assert all(it[os.getenv(os.getenv('VIBE_7C27C505'))] > id1 for it in items3
        )
