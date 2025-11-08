import pytest
from starlette.requests import Request

from services.gateway import main as gateway_main


def _make_request(method: str = "GET", path: str = "/constitution/version") -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "path": path,
        "raw_path": path.encode("latin-1"),
        "query_string": b"",
        "headers": [(b"user-agent", b"pytest")],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
        "scheme": "http",
    }
    return Request(scope)


@pytest.fixture(autouse=True)
def _force_auth(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(gateway_main, "REQUIRE_AUTH", True, raising=False)


@pytest.mark.asyncio
async def test_constitution_version_proxies(monkeypatch: pytest.MonkeyPatch):
    async def fake_auth(*_, **__):
        return {"scope": "admin"}

    class StubClient:
        async def constitution_version(self):
            return {"checksum": "abc123", "version": 7}

    monkeypatch.setattr(gateway_main, "authorize_request", fake_auth)
    monkeypatch.setattr(gateway_main.SomaBrainClient, "get", staticmethod(lambda: StubClient()))

    req = _make_request("GET", "/constitution/version")
    resp = await gateway_main.constitution_version(req)
    assert resp.status_code == 200
    import json as _json

    data = _json.loads(resp.body)
    assert data["checksum"] == "abc123"
    assert data["version"] == 7


@pytest.mark.asyncio
async def test_constitution_validate_proxies(monkeypatch: pytest.MonkeyPatch):
    async def fake_auth(*_, **__):
        return {"scope": "admin"}

    class StubClient:
        async def constitution_validate(self, payload):
            # ensure payload flowing through
            assert payload == {"document": {"rules": []}}
            return {"ok": True}

    monkeypatch.setattr(gateway_main, "authorize_request", fake_auth)
    monkeypatch.setattr(gateway_main.SomaBrainClient, "get", staticmethod(lambda: StubClient()))

    req = _make_request("POST", "/constitution/validate")
    resp = await gateway_main.constitution_validate({"document": {"rules": []}}, req)
    assert resp.status_code == 200
    import json as _json

    data = _json.loads(resp.body)
    assert data == {"ok": True}


@pytest.mark.asyncio
async def test_constitution_load_triggers_policy_regen(monkeypatch: pytest.MonkeyPatch):
    async def fake_auth(*_, **__):
        return {"scope": "admin"}

    class StubClient:
        def __init__(self):
            self.regen_called = False

        async def constitution_load(self, payload):
            assert payload == {"document": {"rules": [1]}}
            return {"loaded": True}

        async def update_opa_policy(self):
            self.regen_called = True

    stub = StubClient()
    monkeypatch.setattr(gateway_main, "authorize_request", fake_auth)
    monkeypatch.setattr(gateway_main.SomaBrainClient, "get", staticmethod(lambda: stub))

    req = _make_request("POST", "/constitution/load")
    resp = await gateway_main.constitution_load({"document": {"rules": [1]}}, req)
    assert resp.status_code == 200
    import json as _json

    data = _json.loads(resp.body)
    assert data == {"loaded": True}
    assert stub.regen_called is True
