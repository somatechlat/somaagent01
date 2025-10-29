import json
import os

import pytest
from fastapi.testclient import TestClient

from services.gateway.main import app


class _FakeCreds:
    def __init__(self, secret: str = "test-secret") -> None:
        self._secret = secret

    async def get(self, provider: str):
        # Always return the same secret for simplicity
        return self._secret


class _FakeSLMClient:
    def __init__(self):
        self.api_key = None

    async def chat(self, messages, *, model, base_url, temperature=None, **kwargs):
        # Validate that credentials were injected
        assert self.api_key == "test-secret"
        content = "ok-content"
        usage = {"input_tokens": 7, "output_tokens": 3}
        return content, usage

    async def close(self):
        pass


@pytest.mark.asyncio
async def test_llm_invoke_audit_success(monkeypatch):
    # In-memory audit store and open gateway
    monkeypatch.setenv("AUDIT_STORE_MODE", "memory")
    monkeypatch.setenv("GATEWAY_REQUIRE_AUTH", "false")
    monkeypatch.setenv("GATEWAY_INTERNAL_TOKEN", "itok")

    # Fake creds store and SLM client factory (patch module-level functions)
    from services import gateway as gw_pkg  # type: ignore
    monkeypatch.setattr(gw_pkg.main, "get_llm_credentials_store", lambda: _FakeCreds())
    monkeypatch.setattr(gw_pkg.main, "_gateway_slm_client", lambda: _FakeSLMClient())

    client = TestClient(app)

    payload = {
        "role": "dialogue",
        "session_id": "sess-llm-1",
        "tenant": "public",
        "messages": [
            {"role": "user", "content": "hi"}
        ],
        "overrides": {
            "model": "gpt-4o-mini",
            "base_url": "https://api.openai.com/v1",
            "temperature": 0.1,
            "kwargs": {"top_p": 1.0}
        }
    }

    r = client.post("/v1/llm/invoke", json=payload, headers={"X-Internal-Token": "itok"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["content"] == "ok-content"
    assert body["usage"] == {"input_tokens": 7, "output_tokens": 3}

    # Fetch audit export and assert llm.invoke entry exists with status ok
    r2 = client.get("/v1/admin/audit/export", params={"action": "llm.invoke"})
    assert r2.status_code == 200
    lines = [ln for ln in r2.text.splitlines() if ln.strip()]
    assert len(lines) >= 1
    records = [json.loads(ln) for ln in lines]
    assert any(rec.get("action") == "llm.invoke" and rec.get("details", {}).get("status") == "ok" for rec in records)
