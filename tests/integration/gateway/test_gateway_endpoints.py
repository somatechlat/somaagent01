import asyncio
from datetime import datetime
from types import SimpleNamespace

import httpx
import pytest

from services.gateway import main as gateway_main


class InMemoryBus:
    def __init__(self):
        self.published = []

    async def publish(self, topic: str, event: dict) -> None:
        # record published events for inspection
        self.published.append((topic, event))


class InMemoryCache:
    def __init__(self):
        self.store = {}

    async def set(self, key: str, value: dict) -> None:
        self.store[key] = value


class InMemoryStore:
    def __init__(self):
        self._events = []
        self._next_id = 1
        self.sessions = {}

    async def append_event(self, session_id: str, envelope: dict) -> None:
        entry = {
            "id": self._next_id,
            "occurred_at": datetime.utcnow(),
            "payload": envelope,
        }
        self._next_id += 1
        self._events.append((session_id, entry))

        # update session envelope summary
        sess = self.sessions.get(session_id)
        if not sess:
            sess = SimpleNamespace(
                session_id=session_id,
                persona_id=envelope.get("persona_id"),
                tenant=envelope.get("metadata", {}).get("tenant"),
                subject=None,
                issuer=None,
                scope=None,
                metadata=envelope.get("metadata", {}),
                analysis={},
                created_at=entry["occurred_at"],
                updated_at=entry["occurred_at"],
            )
            self.sessions[session_id] = sess
        else:
            sess.updated_at = entry["occurred_at"]

    async def list_events_after(
        self, session_id: str, after_id: int | None = None, limit: int = 100
    ):
        items = [e for sid, e in self._events if sid == session_id]
        if after_id is not None:
            items = [e for e in items if e["id"] > after_id]
        return items[:limit]

    async def list_sessions(self, limit: int = 50, tenant: str | None = None):
        items = list(self.sessions.values())
        if tenant is not None:
            items = [s for s in items if s.tenant == tenant]
        return items[:limit]

    async def close(self):
        return None


@pytest.mark.asyncio
async def test_enqueue_and_list_via_gateway():
    app = gateway_main.app

    bus = InMemoryBus()
    cache = InMemoryCache()
    store = InMemoryStore()

    # Override dependencies to use in-memory implementations
    app.dependency_overrides[gateway_main.get_event_bus] = lambda: bus
    app.dependency_overrides[gateway_main.get_session_cache] = lambda: cache
    app.dependency_overrides[gateway_main.get_session_store] = lambda: store

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        # post a user message
        r = await ac.post("/v1/sessions/message", json={"message": "Hello there"})
        assert r.status_code == 200
        data = r.json()
        assert "session_id" in data and "event_id" in data

        session_id = data["session_id"]

        # allow any async background tasks to settle
        await asyncio.sleep(0)

        # list sessions
        r = await ac.get("/v1/sessions")
        assert r.status_code == 200
        sessions = r.json()
        assert any(s.get("session_id") == session_id for s in sessions)

        # list events for the session
        r = await ac.get(f"/v1/sessions/{session_id}/events")
        assert r.status_code == 200
        events_payload = r.json()
        assert events_payload.get("session_id") == session_id
        assert len(events_payload.get("events", [])) >= 1

    # cleanup overrides
    app.dependency_overrides.clear()
