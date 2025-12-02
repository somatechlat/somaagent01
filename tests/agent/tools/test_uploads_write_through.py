import io
import uuid
from typing import Any, Dict, Optional

import pytest
from fastapi.testclient import TestClient

from integrations.repositories import get_session_store
from services.gateway.main import app, get_publisher, get_session_cache


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
        return {"published": True}


class StubCache:
    async def write_context(
        self, session_id: str, persona_id: Optional[str], metadata: Dict[str, Any]
    ) -> None:
        return None

    async def ping(self) -> None:
        return None


class StubStore:
    async def append_event(self, session_id: str, payload: Dict[str, Any]) -> None:
        return None

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
        return {"request_id": "req-1", "trace_id": "tr-1", "coordinate": "c1"}


class FakeAttachmentsStore:
    async def ensure_schema(self) -> None:
        return None

    async def insert(
        self,
        *,
        tenant: Optional[str],
        session_id: Optional[str],
        persona_id: Optional[str],
        filename: str,
        mime: str,
        size: int,
        sha256: str,
        status: str,
        quarantine_reason: Optional[str],
        content: Optional[bytes],
    ) -> uuid.UUID:
        return uuid.uuid4()


@pytest.fixture(autouse=True)
def write_through_env(monkeypatch):
    monkeypatch.setenv("SA01_GATEWAY_WRITE_THROUGH", "true")
    monkeypatch.setenv("SA01_AUTH_REQUIRED", "false")
    monkeypatch.setenv("SA01_SOMA_NAMESPACE", "test-universe")
    yield


@pytest.fixture()
def overrides(monkeypatch):
    # Override dependencies
    stub_pub = StubPublisher()
    app.dependency_overrides[get_publisher] = lambda: stub_pub
    app.dependency_overrides[get_session_cache] = lambda: StubCache()
    app.dependency_overrides[get_session_store] = lambda: StubStore()
    # Monkeypatch SomaBrain client and attachments store inside gateway module
    import services.gateway.main as gw

    monkeypatch.setattr(gw, "SomaBrainClient", FakeSoma)
    monkeypatch.setattr(gw, "get_attachments_store", lambda: FakeAttachmentsStore())
    yield stub_pub
    app.dependency_overrides.clear()


def test_uploads_write_through_includes_universe_and_idempotency(overrides):
    client = TestClient(app)
    headers = {
        "Authorization": "Bearer dummy",
        "X-Universe-Id": "uni-uploads",
    }
    files = {
        "files": ("tiny.txt", io.BytesIO(b"hello uploads"), "text/plain"),
    }
    data = {"session_id": "s-upload-1"}

    resp = client.post("/v1/uploads", files=files, data=data, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list) and len(body) == 1
    # Verify a WAL publish occurred with idempotency and universe metadata
    wal = [p for p in overrides.published if p["topic"].endswith("memory.wal")]
    assert wal, "Expected a WAL publish for uploads write-through"
    wal_event = wal[-1]["event"]
    payload = wal_event.get("payload", {})
    meta = payload.get("metadata", {})
    assert meta.get("universe_id") in {"uni-uploads", "test-universe"}
    assert "idempotency_key" in payload
    assert payload.get("type") == "attachment"
    # Attachments array with at least one descriptor
    atts = payload.get("attachments") or []
    assert isinstance(atts, list) and len(atts) == 1
    assert atts[0].get("filename") == "tiny.txt"
