import os
from typing import Any, Dict, Optional

import pytest
from fastapi.testclient import TestClient

from services.gateway.main import app, get_publisher, get_session_cache, get_session_store


class StubPublisher:
    async def publish(
        self,
        topic: str,
        event: Dict[str, Any],
        dedupe_key: Optional[str] = None,
        session_id: Optional[str] = None,
        tenant: Optional[str] = None,
    ) -> Dict[str, Any]:
        return {"published": True}


class StubCache:
    async def write_context(self, session_id: str, persona_id: Optional[str], metadata: Dict[str, Any]) -> None:
        return None

    async def ping(self) -> None:
        return None


class StubStore:
    async def append_event(self, session_id: str, payload: Dict[str, Any]) -> None:
        return None

    async def ping(self) -> None:
        return None


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


def test_csrf_protection_blocks_without_token(monkeypatch):
    # Enable CSRF and use cookie-based check; POST should fail without matching header
    monkeypatch.setenv("GATEWAY_CSRF_ENABLED", "true")
    monkeypatch.setenv("GATEWAY_CSRF_COOKIE_NAME", "csrf_token")

    # Override dependencies to avoid Kafka/Postgres requirements
    app.dependency_overrides[get_publisher] = lambda: StubPublisher()
    app.dependency_overrides[get_session_cache] = lambda: StubCache()
    app.dependency_overrides[get_session_store] = lambda: StubStore()

    client = TestClient(app)
    payload = {"message": "hello", "metadata": {"tenant": "t1"}}
    # No CSRF header; cookie present but header missing
    cookies = {"csrf_token": "abc"}
    resp = client.post("/v1/session/message", json=payload, cookies=cookies)
    assert resp.status_code == 403


def test_csrf_protection_allows_with_matching_token(monkeypatch):
    monkeypatch.setenv("GATEWAY_CSRF_ENABLED", "true")
    monkeypatch.setenv("GATEWAY_CSRF_COOKIE_NAME", "csrf_token")

    # Override dependencies
    app.dependency_overrides[get_publisher] = lambda: StubPublisher()
    app.dependency_overrides[get_session_cache] = lambda: StubCache()
    app.dependency_overrides[get_session_store] = lambda: StubStore()

    client = TestClient(app)
    payload = {"message": "hello", "metadata": {"tenant": "t1"}}
    cookies = {"csrf_token": "abc"}
    headers = {"X-CSRF-Token": "abc"}
    resp = client.post("/v1/session/message", json=payload, cookies=cookies, headers=headers)
    assert resp.status_code in {200, 201}

