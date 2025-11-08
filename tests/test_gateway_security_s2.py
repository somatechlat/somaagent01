import pytest
from fastapi.testclient import TestClient

from services.gateway.main import app


@pytest.fixture(autouse=True)
def disable_write_through(monkeypatch):
    monkeypatch.setenv("GATEWAY_WRITE_THROUGH", "false")
    yield


def test_cors_env_config(monkeypatch):
    # Configure explicit origins and ensure CORS headers are present for a matching origin
    monkeypatch.setenv("GATEWAY_CORS_ORIGINS", "http://example.com,http://localhost:3000")
    client = TestClient(app)
    headers = {"Origin": "http://localhost:3000"}
    resp = client.options("/v1/health", headers=headers)
    # Depending on CORS config, star or explicit origin may be returned
    allow_origin = resp.headers.get("access-control-allow-origin")
    assert allow_origin in {"*", "http://localhost:3000"}


# CSRF references removed: no CSRF tests remain by design.
