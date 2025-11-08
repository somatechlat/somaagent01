import pytest
from starlette.requests import Request

from services.gateway import main as gateway_main


def _make_request(path: str = "/v1/admin/memory/metrics") -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "path": path,
        "raw_path": path.encode("latin-1"),
        "query_string": b"",
        "headers": [],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
        "scheme": "http",
    }
    return Request(scope)


@pytest.fixture(autouse=True)
def _force_auth(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(gateway_main, "REQUIRE_AUTH", True, raising=False)

    # No-op rate limiter
    async def no_rl(req):
        return None

    monkeypatch.setattr(gateway_main, "_enforce_admin_rate_limit", no_rl)


@pytest.mark.asyncio
async def test_admin_memory_metrics_proxies_soma(monkeypatch: pytest.MonkeyPatch):
    async def fake_auth(*_, **__):
        return {"scope": "admin"}

    class StubClient:
        async def memory_metrics(self, *, tenant: str, namespace: str):
            return {"ok": True, "tenant": tenant, "namespace": namespace}

    monkeypatch.setattr(gateway_main, "authorize_request", fake_auth)
    monkeypatch.setattr(gateway_main.SomaBrainClient, "get", staticmethod(lambda: StubClient()))

    req = _make_request()
    resp = await gateway_main.admin_memory_metrics(req, tenant="tenant-1", namespace="wm")
    assert resp.status_code == 200
    import json as _json

    data = _json.loads(resp.body)
    assert data["tenant"] == "tenant-1"
    assert data["namespace"] == "wm"


@pytest.mark.asyncio
async def test_admin_migrate_export_proxies_soma(monkeypatch: pytest.MonkeyPatch):
    async def fake_auth(*_, **__):
        return {"scope": "admin"}

    class StubClient:
        async def migrate_export(self, *, include_wm: bool, wm_limit: int):
            return {"include_wm": include_wm, "wm_limit": wm_limit}

    monkeypatch.setattr(gateway_main, "authorize_request", fake_auth)
    monkeypatch.setattr(gateway_main.SomaBrainClient, "get", staticmethod(lambda: StubClient()))

    payload = gateway_main.MigrateExportPayload(include_wm=False, wm_limit=42)
    req = _make_request(path="/v1/admin/migrate/export")
    resp = await gateway_main.admin_migrate_export(payload, req)
    assert resp.status_code == 200
    import json as _json

    data = _json.loads(resp.body)
    assert data == {"include_wm": False, "wm_limit": 42}


@pytest.mark.asyncio
async def test_admin_migrate_import_proxies_soma(monkeypatch: pytest.MonkeyPatch):
    async def fake_auth(*_, **__):
        return {"scope": "admin"}

    class StubClient:
        async def migrate_import(self, *, manifest, memories, wm=None, replace=False):
            return {
                "manifest": manifest,
                "memories_count": len(memories or []),
                "wm_count": len(wm or []),
                "replace": replace,
            }

    monkeypatch.setattr(gateway_main, "authorize_request", fake_auth)
    monkeypatch.setattr(gateway_main.SomaBrainClient, "get", staticmethod(lambda: StubClient()))

    payload = gateway_main.MigrateImportPayload(
        manifest={"version": 1},
        memories=[{"id": "a"}, {"id": "b"}],
        wm=[{"id": "c"}],
        replace=True,
    )
    req = _make_request(path="/v1/admin/migrate/import")
    resp = await gateway_main.admin_migrate_import(payload, req)
    assert resp.status_code == 200
    import json as _json

    data = _json.loads(resp.body)
    assert data["manifest"] == {"version": 1}
    assert data["memories_count"] == 2
    assert data["wm_count"] == 1
    assert data["replace"] is True
