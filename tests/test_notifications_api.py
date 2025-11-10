import os

import pytest
from fastapi import status
import httpx

from services.gateway.main import app, get_notifications_store


@pytest.mark.asyncio
async def test_notifications_crud(monkeypatch):
    # Configure in-memory / ephemeral Postgres DSN for test if not set
    dsn = os.getenv("POSTGRES_DSN")
    if not dsn:
        pytest.skip("POSTGRES_DSN not set for integration test")

    # Ensure schema
    store = get_notifications_store()
    await store.ensure_schema()

    # Monkeypatch authorize_request to bypass auth with fixed tenant
    async def fake_auth(request, payload):  # noqa: ANN001
        return {"tenant": "test-tenant", "subject": "tester"}

    monkeypatch.setattr("services.gateway.main.authorize_request", fake_auth)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Create
        resp = await client.post(
            "/v1/ui/notifications",
            json={
                "type": "system.update",
                "title": "Update",
                "body": "Body text",
                "severity": "info",
                "ttl_seconds": 5,
                "meta": {"k": "v"},
            },
        )
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        nid = data["notification"]["id"]
        assert data["notification"]["severity"] == "info"

        # List
        resp2 = await client.get("/v1/ui/notifications")
        assert resp2.status_code == 200
        listed = resp2.json()["notifications"]
        assert any(n["id"] == nid for n in listed)

        # Mark read
        resp3 = await client.post(f"/v1/ui/notifications/{nid}/read")
        assert resp3.status_code == 200

        # Clear
        resp4 = await client.delete("/v1/ui/notifications/clear")
        assert resp4.status_code == 200
        cleared = resp4.json()["deleted"]
        assert cleared >= 1


@pytest.mark.asyncio
async def test_notifications_invalid_severity(monkeypatch):
    dsn = os.getenv("POSTGRES_DSN")
    if not dsn:
        pytest.skip("POSTGRES_DSN not set")
    store = get_notifications_store()
    await store.ensure_schema()

    async def fake_auth(request, payload):  # noqa: ANN001
        return {"tenant": "x"}

    monkeypatch.setattr("services.gateway.main.authorize_request", fake_auth)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        r = await client.post(
            "/v1/ui/notifications",
            json={"type": "x", "title": "t", "body": "b", "severity": "bad", "meta": {}},
        )
        assert r.status_code == 400
