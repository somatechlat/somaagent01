import os
from typing import Dict

import pytest
from fastapi.testclient import TestClient

from services.common import runtime_config as cfg
from services.common.tenant_flags import set_flag_fetcher


@pytest.mark.asyncio
async def test_feature_flags_match_cfg(monkeypatch):
    monkeypatch.setenv("SA01_FEATURE_PROFILE", "standard")
    monkeypatch.setenv("SA01_AUTH_REQUIRED", "false")
    tenant = "tenantA"

    def _fake_fetcher(t: str, flag: str) -> bool:
        return flag in {"sequence", "sse_enabled"}

    set_flag_fetcher(_fake_fetcher)

    from services.gateway.main import app  # noqa: WPS433

    client = TestClient(app)
    headers = {"X-Tenant-Id": tenant}
    resp = client.get("/v1/feature-flags", headers=headers)
    assert resp.status_code == 200
    payload: Dict[str, Dict[str, str]] = resp.json()
    flags = payload["flags"]

    for key, meta in flags.items():
        expected = cfg.flag(key, tenant)
        assert meta["effective"] == expected, f"{key} mismatch"
*** End of File
