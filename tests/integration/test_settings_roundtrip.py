import os

import pytest
from fastapi.testclient import TestClient

TEST_DSN = os.getenv("SA01_TEST_POSTGRES_DSN") or os.getenv("SA01_DB_DSN")
SOMA_BASE = os.getenv("SA01_SOMA_BASE_URL")

if not TEST_DSN:
    raise RuntimeError("SA01_TEST_POSTGRES_DSN or SA01_DB_DSN must be set.")
if not SOMA_BASE:
    raise RuntimeError("SA01_SOMA_BASE_URL must be set.")

os.environ["SA01_DB_DSN"] = TEST_DSN
os.environ["SA01_SOMA_BASE_URL"] = SOMA_BASE

from services.gateway.main import app  # noqa: E402


@pytest.mark.integration
def test_settings_roundtrip():
    with TestClient(app) as client:
        resp = client.get("/v1/settings/sections")
        assert resp.status_code == 200
        data = resp.json()
        sections = data.get("sections") or []
        payload = {"sections": sections}
        put = client.put("/v1/settings/sections", json={"data": payload})
        assert put.status_code == 200
        resp2 = client.get("/v1/settings/sections")
        assert resp2.status_code == 200
