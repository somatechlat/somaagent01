"""Smoke test ensuring orchestrator app responds healthy."""

from fastapi.testclient import TestClient

from orchestrator.main import create_app


def test_smoke_health():
    app = create_app()
    client = TestClient(app)
    resp = client.get("/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("healthy") is True
