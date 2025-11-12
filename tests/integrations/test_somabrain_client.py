"""Integration tests for the :pymod:`python.integrations.somabrain_client` helper.

The tests use ``respx`` to mock the underlying HTTP calls made by the client.
They verify that:

* The request URL is correctly constructed from ``SA01_SOMA_BASE_URL``.
* The JSON payload is forwarded for POST requests.
* Successful 2xx responses are parsed and returned.
* Non‑2xx responses raise :class:`SomaClientError`.
"""

from __future__ import annotations

import pytest
import respx

# Import after setting env var in each test to ensure the module picks up the value.


@pytest.fixture(autouse=True)
def reset_env(monkeypatch):
    """Ensure a clean environment for each test."""
    # Remove any existing SA01_SOMA_BASE_URL to avoid cross‑test contamination.
    monkeypatch.delenv("SA01_SOMA_BASE_URL", raising=False)
    yield


def test_get_weights_success(monkeypatch):
    monkeypatch.setenv("SA01_SOMA_BASE_URL", "http://example.com")
    with respx.mock(base_url="http://example.com") as mock:
        route = mock.get("/v1/weights").respond(json={"weights": [1, 2, 3]})
        from python.integrations.somabrain_client import get_weights

        result = get_weights()
        assert result == {"weights": [1, 2, 3]}
        assert route.called


def test_update_weights_success(monkeypatch):
    monkeypatch.setenv("SA01_SOMA_BASE_URL", "http://example.com")
    payload = {"new": "value"}
    with respx.mock(base_url="http://example.com") as mock:
        route = mock.post("/v1/weights/update", json=payload).respond(json={"ok": True})
        from python.integrations.somabrain_client import update_weights

        result = update_weights(payload)
        assert result == {"ok": True}
        assert route.called


def test_build_context_error(monkeypatch):
    monkeypatch.setenv("SA01_SOMA_BASE_URL", "http://example.com")
    payload = {"foo": "bar"}
    with respx.mock(base_url="http://example.com") as mock:
        mock.post("/v1/context/build", json=payload).respond(status_code=400, json={"error": "bad"})
        from python.integrations.somabrain_client import build_context, SomaClientError

        with pytest.raises(SomaClientError) as exc:
            build_context(payload)
        # Ensure the underlying HTTP status is reflected in the error message.
        assert "400" in str(exc.value)


def test_get_tenant_flag_success(monkeypatch):
    monkeypatch.setenv("SA01_SOMA_BASE_URL", "http://example.com")
    with respx.mock(base_url="http://example.com") as mock:
        route = mock.get("/v1/flags/tenant123/featureX").respond(json={"enabled": True})
        from python.integrations.somabrain_client import get_tenant_flag

        flag = get_tenant_flag("tenant123", "featureX")
        assert flag is True
        assert route.called


@pytest.mark.asyncio
async def test_get_weights_async(monkeypatch):
    monkeypatch.setenv("SA01_SOMA_BASE_URL", "http://example.com")
    with respx.mock(base_url="http://example.com") as mock:
        route = mock.get("/v1/weights").respond(json={"weights": [42]})
        from python.integrations.somabrain_client import get_weights_async

        result = await get_weights_async()
        assert result == {"weights": [42]}
        assert route.called


@pytest.mark.asyncio
async def test_build_context_async(monkeypatch):
    monkeypatch.setenv("SA01_SOMA_BASE_URL", "http://example.com")
    payload = {"session_id": "s", "messages": []}
    with respx.mock(base_url="http://example.com") as mock:
        route = mock.post("/v1/context/build", json=payload).respond(json=[{"role": "system", "content": "ok"}])
        from python.integrations.somabrain_client import build_context_async

        result = await build_context_async(payload)
        assert isinstance(result, list)
        assert route.called


@pytest.mark.asyncio
async def test_publish_reward_async(monkeypatch):
    monkeypatch.setenv("SA01_SOMA_BASE_URL", "http://example.com")
    payload = {"session_id": "s", "signal": "reward", "value": 1.0}
    with respx.mock(base_url="http://example.com") as mock:
        route = mock.post("/v1/learning/reward", json=payload).respond(json={"ok": True})
        from python.integrations.somabrain_client import publish_reward_async

        result = await publish_reward_async(payload)
        assert result == {"ok": True}
        assert route.called


@pytest.mark.asyncio
async def test_get_tenant_flag_async(monkeypatch):
    monkeypatch.setenv("SA01_SOMA_BASE_URL", "http://example.com")
    with respx.mock(base_url="http://example.com") as mock:
        route = mock.get("/v1/flags/public/test").respond(json={"enabled": False})
        from python.integrations.somabrain_client import get_tenant_flag_async

        flag = await get_tenant_flag_async("public", "test")
        assert flag is False
        assert route.called


def test_get_persona(monkeypatch):
    monkeypatch.setenv("SA01_SOMA_BASE_URL", "http://example.com")
    persona_doc = {"id": "persona-1", "properties": {"settings": {"foo": "bar"}}}
    with respx.mock(base_url="http://example.com") as mock:
        route = mock.get("/persona/persona-1").respond(json=persona_doc)
        from python.integrations.somabrain_client import get_persona

        result = get_persona("persona-1")
        assert result == persona_doc
        assert route.called


def test_put_persona(monkeypatch):
    monkeypatch.setenv("SA01_SOMA_BASE_URL", "http://example.com")
    payload = {"id": "persona-1", "properties": {"settings": {"foo": "bar"}}}
    with respx.mock(base_url="http://example.com") as mock:
        route = mock.put("/persona/persona-1", json=payload).respond(json=payload)
        from python.integrations.somabrain_client import put_persona

        result = put_persona("persona-1", payload)
        assert result == payload
        assert route.called
