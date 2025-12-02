from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient


@pytest.mark.asyncio
async def test_feature_flags_endpoint_basic(monkeypatch):
    # Ensure predictable profile and disable auth
    monkeypatch.setenv("SA01_FEATURE_PROFILE", "standard")
    monkeypatch.setenv("SA01_AUTH_REQUIRED", "false")
    monkeypatch.setenv("FEATURE_FLAGS_TTL_SECONDS", "2")  # short TTL for test

    # Stub remote flag fetch: pretend remote overrides enable one flag and disable another
    from python.integrations import somabrain_client as sc

    def _fake_get_tenant_flag(tenant_id: str, flag: str) -> bool:
        if flag == "sequence":
            return True  # ensure remote override path triggers
        if flag == "semantic_recall":
            return False  # explicit remote off
        raise RuntimeError("unexpected flag")

    monkeypatch.setattr(sc, "get_tenant_flag", _fake_get_tenant_flag)

    from services.gateway.main import app  # import after monkeypatch/env

    client = TestClient(app)
    headers = {"X-Tenant-Id": "tenantA"}
    resp = client.get("/v1/feature-flags", headers=headers)
    assert resp.status_code == 200
    data: Dict[str, Any] = resp.json()
    assert data["tenant"] == "tenantA"
    assert data["profile"] == "standard"
    assert "flags" in data
    flags = data["flags"]
    assert "sequence" in flags
    assert flags["sequence"]["source"] in {"remote", "local"}
    # remote override for sequence should force effective True
    assert flags["sequence"]["effective"] is True
    # semantic_recall remote override False should yield effective False regardless of profile
    assert flags["semantic_recall"]["effective"] is False

    # Second call should hit cache and produce identical payload
    resp2 = client.get("/v1/feature-flags", headers=headers)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["flags"] == flags
