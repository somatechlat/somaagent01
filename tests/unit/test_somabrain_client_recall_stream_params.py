import asyncio
import json
import types
import pytest

from python.integrations.soma_client import SomaClient, SomaClientError


@pytest.mark.asyncio
async def test_recall_stream_prefers_query_param(monkeypatch):
    client = SomaClient(base_url="http://localhost:9696")

    calls = []

    async def fake_request(method, path, *, json=None, params=None, headers=None, allow_404=False):
        calls.append({
            "method": method,
            "path": path,
            "json": json,
            "params": params,
            "allow_404": allow_404,
        })
        return {"ok": True}

    monkeypatch.setattr(client, "_request", fake_request)

    payload = {"query": "hello", "top_k": 5}
    res = await client.recall_stream(payload)
    assert res == {"ok": True}

    # First call must use ?payload= param and no JSON body
    assert len(calls) >= 1
    first = calls[0]
    assert first["path"] == "/memory/recall/stream"
    assert first["params"] and "payload" in first["params"]
    # The payload should be a compact JSON string
    p = first["params"]["payload"]
    assert isinstance(p, str) and p.startswith("{") and p.endswith("}")
    assert first["json"] is None


@pytest.mark.asyncio
async def test_recall_stream_fallbacks_to_json_body(monkeypatch):
    client = SomaClient(base_url="http://localhost:9696")

    calls = []
    attempt = {"n": 0}

    async def fake_request(method, path, *, json=None, params=None, headers=None, allow_404=False):
        calls.append({
            "method": method,
            "path": path,
            "json": json,
            "params": params,
            "allow_404": allow_404,
        })
        # First attempt (with params) fails to trigger fallback
        if attempt["n"] == 0 and params is not None:
            attempt["n"] += 1
            raise SomaClientError("simulated transport error")
        return {"ok": True}

    monkeypatch.setattr(client, "_request", fake_request)

    payload = {"query": "hello", "top_k": 5}
    res = await client.recall_stream(payload)
    assert res == {"ok": True}

    # We expect two calls: first with params (failing), then fallback with JSON body
    assert len(calls) >= 2
    assert calls[0]["params"] is not None and calls[0]["json"] is None
    assert calls[1]["json"] is not None and calls[1]["params"] is None
