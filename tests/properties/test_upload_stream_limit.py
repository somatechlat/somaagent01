"""Property: Upload stream limit must be enforced at handler level.

Validates: Requirements 17.x (upload integrity) and clamd stream guard.
"""

import asyncio
import importlib

import pytest


class DummyStore:
    async def create(self, **kwargs):
        return "dummy-id"


def _handler(monkeypatch, *, stream_max_bytes=5_000_000):
    monkeypatch.setenv("SA01_SOMA_BASE_URL", "http://localhost:8000")
    monkeypatch.setenv("SA01_POLICY_URL", "http://localhost:8181")
    module = importlib.import_module("services.gateway.routers.uploads_full")
    # Force in-memory sessions by disabling redis connection.
    class _NoRedis:
        @staticmethod
        def from_url(*args, **kwargs):
            return None

    monkeypatch.setattr(module, "redis", _NoRedis)
    handler_cls = getattr(module, "TUSUploadHandler")
    return handler_cls(
        store=DummyStore(),
        clamd_socket="/var/run/clamav/clamd.sock",
        max_size=10_000_000,
        quarantine_on_error=True,
        clamav_enabled=False,
        stream_max_bytes=stream_max_bytes,
    )


def test_create_rejects_exceeding_stream_limit(monkeypatch):
    handler = _handler(monkeypatch)

    async def _run():
        with pytest.raises(ValueError):
            await handler.create_upload(
                filename="big.bin",
                size=6_000_000,  # exceeds stream limit (5MB)
                mime_type="application/octet-stream",
                tenant_id="t1",
                session_id="s1",
                persona_id=None,
            )

    asyncio.run(_run())


def test_finalize_allows_within_stream_limit(monkeypatch):
    handler = _handler(monkeypatch)

    async def _run():
        sess = await handler.create_upload(
            filename="ok.bin",
            size=1_000_000,
            mime_type="application/octet-stream",
            tenant_id="t1",
            session_id="s1",
            persona_id=None,
        )
        await handler.append_chunk(sess.id, b"x" * 1_000_000, offset=0)
        record = await handler.finalize_upload(sess.id)
        assert record.size == 1_000_000
        assert record.status in ("clean", "quarantined")

    asyncio.run(_run())
