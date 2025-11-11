import os

import pytest
from fastapi.testclient import TestClient

from python.integrations.soma_client import SomaClientError
from services.common.memory_write_outbox import ensure_schema as ensure_mw_schema, MemoryWriteOutbox
from services.gateway.main import app


class AlwaysFailSoma:
    @classmethod
    def get(cls):  # type: ignore
        return cls()

    async def remember(self, payload):
        raise SomaClientError("503 Service Unavailable")


@pytest.mark.asyncio
async def test_gateway_enqueues_memory_on_soma_failure(monkeypatch):
    dsn = os.getenv("TEST_SA01_DB_DSN")
    if not dsn:
        pytest.skip("TEST_SA01_DB_DSN not set; skipping integration test")

    # Configure env for write-through path
    monkeypatch.setenv("SA01_GATEWAY_WRITE_THROUGH", "true")
    monkeypatch.setenv("SA01_GATEWAY_WRITE_THROUGH_ASYNC", "false")
    monkeypatch.setenv("SA01_DB_DSN", dsn)

    # Ensure outbox schema exists
    store = MemoryWriteOutbox(dsn=dsn)
    await ensure_mw_schema(store)

    # Monkeypatch SomaBrain client to always fail
    import services.gateway.main as gw

    monkeypatch.setattr(gw, "SomaBrainClient", AlwaysFailSoma)

    client = TestClient(app)
    payload = {"message": "hello", "attachments": [], "metadata": {"tenant": "t1"}}
    resp = client.post("/v1/session/message", json=payload)
    assert resp.status_code == 200

    # Verify outbox has at least one pending row
    pending = await store.count_pending()
    assert pending >= 1
