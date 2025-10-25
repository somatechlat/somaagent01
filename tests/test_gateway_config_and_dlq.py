import asyncio
import os

import pytest
from fastapi.testclient import TestClient

import services.gateway.main as gw
from services.gateway.main import app, _refresh_dlq_depth_once, GATEWAY_DLQ_DEPTH


class _StubDLQ:
    def __init__(self, mapping):
        self.mapping = mapping

    async def count(self, *, topic: str) -> int:  # type: ignore[override]
        return int(self.mapping.get(topic, 0))


def test_ui_runtime_config_endpoint(monkeypatch):
    monkeypatch.setenv("SOMA_NAMESPACE", "univ-1")
    monkeypatch.setenv("SOMA_MEMORY_NAMESPACE", "wm")
    client = TestClient(app)
    resp = client.get("/ui/config.json")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("api_base", "").startswith("/")
    assert data.get("universe_default") == "univ-1"
    assert data.get("namespace_default") == "wm"
    assert set(data.get("features", {}).keys()) >= {"write_through", "write_through_async", "require_auth"}


@pytest.mark.asyncio
async def test_refresh_dlq_depth_once_sets_gauge(monkeypatch):
    mapping = {"memory.wal.dlq": 5, "tool.results.dlq": 2}

    # Monkeypatch dlq store used by gateway
    monkeypatch.setattr(gw, "get_dlq_store", lambda: _StubDLQ(mapping))

    result = await _refresh_dlq_depth_once(["memory.wal.dlq", "tool.results.dlq"])  # type: ignore[arg-type]
    assert result == mapping

    # Verify gauge is updated (best-effort; uses internal prom API)
    assert int(GATEWAY_DLQ_DEPTH.labels("memory.wal.dlq")._value.get()) == 5  # type: ignore[attr-defined]
    assert int(GATEWAY_DLQ_DEPTH.labels("tool.results.dlq")._value.get()) == 2  # type: ignore[attr-defined]

