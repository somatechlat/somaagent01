from __future__ import annotations

import os
import json
import uuid
import pytest
import asyncpg

from services.common.session_repository import PostgresSessionStore, ensure_schema


@pytest.mark.asyncio
async def test_masking_applied_to_event_message(monkeypatch):
    # Enable masking flag
    monkeypatch.setenv("SA01_ENABLE_CONTENT_MASKING", "true")
    sid = str(uuid.uuid4())
    store = PostgresSessionStore()
    # Skip cleanly if Postgres not reachable
    try:
        await ensure_schema(store)
    except Exception as e:
        pytest.skip(f"postgres unavailable: {e}")
    secret_text = "Here is my key sk-ABCDEF1234567890 please hide"
    evt = {
        "event_id": str(uuid.uuid4()),
        "session_id": sid,
        "persona_id": None,
        "role": "assistant",
        "type": "assistant.final",
        "message": secret_text,
        "metadata": {"tenant": "public"},
    }
    await store.append_event(sid, evt)
    rows = await store.list_events_after(sid, limit=10)
    assert rows, "expected persisted events"
    payloads = [r["payload"] for r in rows]
    masked = [p for p in payloads if p.get("message") and "[REDACTED_KEY]" in p.get("message")]
    assert masked, "message should be masked"
    assert any("mask_rules" in (m.get("metadata") or {}) for m in masked), "mask_rules metadata expected"
    await store.close()


@pytest.mark.asyncio
async def test_error_classifier_enrichment(monkeypatch):
    monkeypatch.setenv("SA01_ENABLE_ERROR_CLASSIFIER", "true")
    sid = str(uuid.uuid4())
    store = PostgresSessionStore()
    try:
        await ensure_schema(store)
    except Exception as e:
        pytest.skip(f"postgres unavailable: {e}")
    # Simulate raw error event (type=error) so normalization + classifier run
    raw_error = {
        "event_id": str(uuid.uuid4()),
        "session_id": sid,
        "type": "error",
        "message": "Request timed out after 30s",
        "details": "Request timed out",
    }
    await store.append_event(sid, raw_error)
    rows = await store.list_events_after(sid, limit=10)
    assert rows, "expected row after append"
    enriched = [r["payload"] for r in rows if (r["payload"].get("type") or "").endswith(".error")]
    assert enriched, "expected normalized *.error event"
    meta = enriched[0].get("metadata") or {}
    assert meta.get("error_code") in {"timeout", "internal_error", "upstream_error"}, "error_code missing"
    # Timeout text should classify as retriable
    if meta.get("error_code") == "timeout":
        assert meta.get("retriable") is True
    await store.close()
