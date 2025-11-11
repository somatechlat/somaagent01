from typing import Any, Dict, Optional

import pytest
from fastapi.testclient import TestClient

from services.gateway.main import app, get_publisher, get_session_cache
from integrations.repositories import get_session_store


class StubPublisher:
    def __init__(self) -> None:
        self.published: list[Dict[str, Any]] = []

    async def publish(
        self,
        topic: str,
        event: Dict[str, Any],
        dedupe_key: Optional[str] = None,
        session_id: Optional[str] = None,
        tenant: Optional[str] = None,
    ) -> Dict[str, Any]:
        self.published.append(
            {
                "topic": topic,
                "event": event,
                "dedupe_key": dedupe_key,
                "session_id": session_id,
                "tenant": tenant,
            }
        )
        # Pretend Kafka published OK
        return {"published": True}


class StubCache:
    async def write_context(
        self, session_id: str, persona_id: Optional[str], metadata: Dict[str, Any]
    ) -> None:
        return None

    async def ping(self) -> None:
        return None


class StubStore:
    def __init__(self) -> None:
        self.events: list[Dict[str, Any]] = []

    async def append_event(self, session_id: str, payload: Dict[str, Any]) -> None:
        self.events.append({"session_id": session_id, "payload": payload})

    async def ping(self) -> None:
        return None


class FakeSoma:
    def __init__(self) -> None:
        self.requests: list[Dict[str, Any]] = []

    @classmethod
    def get(cls):  # type: ignore
        return cls()

    async def remember(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.requests.append(payload)
        # Return minimal response metadata
        return {"request_id": "req-1", "trace_id": "tr-1", "coordinate": "c1"}


@pytest.fixture(autouse=True)
def write_through_env(monkeypatch):
    monkeypatch.setenv("SA01_GATEWAY_WRITE_THROUGH", "true")
    monkeypatch.setenv("SA01_AUTH_REQUIRED", "false")
    monkeypatch.setenv("SOMA_NAMESPACE", "test-universe")
    yield


@pytest.fixture()
def overrides(monkeypatch):
    # Override dependencies
    stub_pub = StubPublisher()
    app.dependency_overrides[get_publisher] = lambda: stub_pub
    app.dependency_overrides[get_session_cache] = lambda: StubCache()
    app.dependency_overrides[get_session_store] = lambda: StubStore()
    # Monkeypatch SomaBrain client symbol inside gateway module
    import services.gateway.main as gw

    monkeypatch.setattr(gw, "SomaBrainClient", FakeSoma)
    yield stub_pub
    app.dependency_overrides.clear()


def test_message_header_propagation_and_write_through(overrides):
    client = TestClient(app)
    # Send message with headers and attachments
    payload = {
        "message": "hello",
        "attachments": ["a.txt"],
        "metadata": {"tenant": "t1"},
    }
    headers = {
        "X-Agent-Profile": "agent-123",
        "X-Universe-Id": "uni-999",
        "X-Persona-Id": "persona-1",
        "Authorization": "Bearer dummy",
    }
    resp = client.post("/v1/session/message", json=payload, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "session_id" in body and "event_id" in body

    # Verify a WAL publish occurred with attachments and idempotency
    published = overrides.published
    wal = [p for p in published if p["topic"].endswith("memory.wal")]
    assert wal, "Expected a WAL publish"
    wal_event = wal[-1]["event"]
    assert wal_event.get("payload", {}).get("metadata", {}).get("agent_profile_id") == "agent-123"
    assert wal_event.get("payload", {}).get("metadata", {}).get("universe_id") in {
        "uni-999",
        "test-universe",
    }
    assert wal_event.get("payload", {}).get("attachments") == ["a.txt"]
    assert "idempotency_key" in wal_event.get("payload", {})


def test_quick_action_write_through(overrides):
    client = TestClient(app)
    payload = {"action": "summarize", "metadata": {"tenant": "t1"}}
    headers = {"Authorization": "Bearer dummy"}
    resp = client.post("/v1/session/action", json=payload, headers=headers)
    assert resp.status_code == 200
    wal = [p for p in overrides.published if p["topic"].endswith("memory.wal")]
    assert wal, "Expected a WAL publish for quick action"
    wal_event = wal[-1]["event"]
    assert wal_event.get("payload", {}).get("role") == "user"
    assert wal_event.get("payload", {}).get("metadata", {}).get("action") == "summarize"
    assert "idempotency_key" in wal_event.get("payload", {})
