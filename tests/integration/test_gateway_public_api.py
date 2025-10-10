import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from services.gateway import main as gateway_main


class StubKafkaBus:
    def __init__(self) -> None:
        self.published: list[tuple[str, dict[str, object]]] = []

    async def publish(self, topic: str, event: dict[str, object]) -> None:
        self.published.append((topic, event))

    async def healthcheck(self) -> None:  # pragma: no cover - used in health test
        return None

    async def close(self) -> None:  # pragma: no cover - used in health test
        return None


class StubSessionCache:
    def __init__(self) -> None:
        self._store: dict[str, dict[str, object]] = {}

    def format_key(self, session_id: str) -> str:
        return f"session:{session_id}"

    async def get(self, key: str):
        return self._store.get(key)

    async def write_context(self, session_id: str, persona_id, metadata):
        self._store[self.format_key(session_id)] = {
            "persona_id": persona_id or "",
            "metadata": dict(metadata or {}),
        }

    async def ping(self) -> None:
        return None


class StubSessionStore:
    def __init__(self) -> None:
        self.appended: list[dict[str, object]] = []

    async def get_envelope(self, session_id: str):
        return None

    async def append_event(self, session_id: str, event: dict[str, object]) -> None:
        self.appended.append({"session_id": session_id, **event})

    async def ping(self) -> None:
        return None


class HealthKafkaBus:
    instances: list["HealthKafkaBus"] = []

    def __init__(self) -> None:
        self.health_checked = False
        self.closed = False
        HealthKafkaBus.instances.append(self)

    async def publish(
        self, topic: str, event: dict[str, object]
    ) -> None:  # pragma: no cover - not used
        return None

    async def healthcheck(self) -> None:
        self.health_checked = True

    async def close(self) -> None:
        self.closed = True


@pytest.fixture(autouse=True)
def _reset_overrides(monkeypatch):
    """Ensure fresh dependency overrides and OpenAPI cache per test."""

    monkeypatch.setattr(gateway_main, "_OPENAPI_CACHE", None)
    overrides = gateway_main.app.dependency_overrides
    overrides.clear()
    yield
    overrides.clear()
    monkeypatch.setattr(gateway_main, "_OPENAPI_CACHE", None)


@pytest.mark.asyncio
async def test_openapi_alias_route_returns_schema():
    transport = ASGITransport(app=gateway_main.app)
    async with AsyncClient(transport=transport, base_url="http://gateway") as client:
        response = await client.get("/openapi.json")

    assert response.status_code == 200
    payload = response.json()
    assert payload["info"]["title"] == "SomaAgent 01 Gateway"
    assert payload["openapi"].startswith("3.")


@pytest.mark.asyncio
async def test_enqueue_message_endpoint_publishes_event(monkeypatch):
    monkeypatch.setattr(gateway_main, "REQUIRE_AUTH", False)
    monkeypatch.setattr(gateway_main, "JWT_SECRET", None)
    monkeypatch.setattr(gateway_main, "JWT_PUBLIC_KEY", None)
    monkeypatch.setattr(gateway_main, "JWT_JWKS_URL", None)

    bus = StubKafkaBus()
    cache = StubSessionCache()
    store = StubSessionStore()

    app = gateway_main.app
    app.dependency_overrides[gateway_main.get_event_bus] = lambda: bus
    app.dependency_overrides[gateway_main.get_session_cache] = lambda: cache
    app.dependency_overrides[gateway_main.get_session_store] = lambda: store

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://gateway") as client:
        response = await client.post(
            "/v1/session/message",
            json={"message": "hello", "attachments": [], "metadata": {}},
        )

    assert response.status_code == 200
    body = response.json()
    assert uuid.UUID(body["session_id"])
    assert uuid.UUID(body["event_id"])

    assert len(bus.published) == 1
    topic, event = bus.published[0]
    assert topic == "conversation.inbound"
    assert event["message"] == "hello"
    assert event["role"] == "user"


@pytest.mark.asyncio
async def test_health_endpoint_uses_stubbed_dependencies(monkeypatch):
    monkeypatch.setattr(gateway_main, "KafkaEventBus", HealthKafkaBus)

    cache = StubSessionCache()
    store = StubSessionStore()
    app = gateway_main.app
    app.dependency_overrides[gateway_main.get_session_cache] = lambda: cache
    app.dependency_overrides[gateway_main.get_session_store] = lambda: store

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://gateway") as client:
        response = await client.get("/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["components"]["postgres"]["status"] == "ok"
    assert payload["components"]["redis"]["status"] == "ok"
    assert payload["components"]["kafka"]["status"] == "ok"

    assert HealthKafkaBus.instances
    last_bus = HealthKafkaBus.instances[-1]
    assert last_bus.health_checked is True
    assert last_bus.closed is True
