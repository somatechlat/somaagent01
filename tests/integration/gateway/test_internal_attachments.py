import os
import uuid
import pytest
from httpx import AsyncClient
from httpx import ASGITransport

from services.gateway import main as gateway_main
from services.common.attachments_store import AttachmentsStore


@pytest.mark.asyncio
async def test_internal_attachments_requires_token(monkeypatch):
    # Ensure schema and insert a test attachment
    store = AttachmentsStore()
    await store.ensure_schema()
    att_id = await store.insert(
        tenant="test",
        session_id=str(uuid.uuid4()),
        persona_id=None,
        filename="test.txt",
        mime="text/plain",
        size=5,
        sha256="e3b0c44298fc1c149afbf4c8996fb924",  # dummy
        status="clean",
        quarantine_reason=None,
        content=b"hello",
    )

    app = gateway_main.app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Missing token -> 403
        r = await ac.get(f"/internal/attachments/{att_id}/binary")
        assert r.status_code == 403

    # With token set
    monkeypatch.setenv("GATEWAY_INTERNAL_TOKEN", "secret-token")
    headers = {"X-Internal-Token": "secret-token", "X-Tenant-Id": "test"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # HEAD provides metadata headers without body
        rh = await ac.head(f"/internal/attachments/{att_id}/binary", headers=headers)
        assert rh.status_code == 200
        assert rh.headers.get("x-attachment-status") == "clean"
        assert rh.headers.get("x-attachment-size") == "5"

        # GET returns content
        rg = await ac.get(f"/internal/attachments/{att_id}/binary", headers=headers)
        assert rg.status_code == 200
        assert rg.headers.get("content-type") == "text/plain"
        assert rg.content == b"hello"
