import asyncio
import os
import types

import pytest


@pytest.mark.asyncio
async def test_worker_fetches_llm_key_from_gateway(monkeypatch):
    os.environ.setdefault("GATEWAY_INTERNAL_TOKEN", "unit-internal")

    # Lazy import to ensure env is set first
    from services.conversation_worker.main import ConversationWorker

    worker = ConversationWorker()
    # Force non-DEV to ensure env key is ignored
    worker.deployment_mode = "STAGING"
    worker.slm.api_key = None

    # Fake httpx response
    class FakeResp:
        status_code = 200

        def json(self):
            return {"provider": "groq", "secret": "unit-test-key"}

    class FakeClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, url, headers=None):
            assert "/v1/llm/credentials/" in url
            assert headers and headers.get("X-Internal-Token") == os.getenv("GATEWAY_INTERNAL_TOKEN")
            return FakeResp()

    import httpx

    monkeypatch.setattr(httpx, "AsyncClient", FakeClient)

    await worker._ensure_llm_key()
    assert worker.slm.api_key == "unit-test-key"

