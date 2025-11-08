from __future__ import annotations

import json
import os
import re
import uuid
from typing import Any, List

import httpx
import pytest

# Assumes gateway is running on localhost:21016 during test execution.
GATEWAY_BASE = os.getenv("GATEWAY_BASE", "http://localhost:21016")


@pytest.mark.asyncio
async def test_stream_canonical_produces_deltas_then_single_final():
    """Invoke streaming and verify assistant.delta accumulation and single assistant.final with done flag."""
    url = f"{GATEWAY_BASE}/v1/llm/invoke/stream?mode=canonical"
    # Minimal payload: dialogue role with two messages
    body = {
        "role": "dialogue",
        "session_id": str(uuid.uuid4()),
        "persona_id": None,
        "tenant": "public",
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ],
        "overrides": {"model": os.getenv("TEST_STREAM_MODEL", "gpt-4o-mini"), "temperature": 0.0},
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json=body)
        assert resp.status_code == 200, f"stream invoke failed: {resp.status_code} {resp.text}"

    # The response is an SSE stream; we re-request with stream semantics using raw client
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", url, json=body) as rstream:
            assert rstream.status_code == 200, f"stream status {rstream.status_code}"
            raw_chunks: List[str] = []
            async for line in rstream.aiter_lines():
                if not line:
                    continue
                if line.startswith("data: "):
                    raw = line[len("data: ") :].strip()
                    raw_chunks.append(raw)
                if line.strip() == "data: [DONE]":
                    break
            # Filter JSON payloads only
            events: List[dict[str, Any]] = []
            for item in raw_chunks:
                if item == "[DONE]":
                    continue
                try:
                    events.append(json.loads(item))
                except Exception:
                    continue
    # Extract canonical events
    deltas = [e for e in events if e.get("type") == "assistant.delta"]
    finals = [e for e in events if e.get("type") == "assistant.final"]
    # There should be at least one delta (model dependent); allow zero only if provider returns empty content
    assert len(finals) == 1, f"expected single assistant.final, got {len(finals)}"
    if deltas:
        # Final message should equal concatenation of deltas
        assembled = "".join(d.get("message") or "" for d in deltas)
        final_msg = finals[0].get("message") or ""
        assert final_msg == assembled, "final message does not equal assembled deltas"
    # done flag present
    assert finals[0].get("metadata", {}).get("done") in {True, "true"}


@pytest.mark.asyncio
async def test_error_normalization_upgrade_on_read():
    """Insert a legacy raw error payload and confirm list endpoint upgrades to *.error format."""
    session_id = str(uuid.uuid4())
    # Direct legacy insertion via session_events table (simulate rogue writer)
    import asyncpg

    dsn = os.getenv("POSTGRES_DSN", "postgresql://soma:soma@localhost:5432/somaagent01")
    pool = await asyncpg.create_pool(dsn)
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO session_events (session_id, payload)
            VALUES ($1, $2::jsonb)
            """,
            session_id,
            json.dumps(
                {
                    "event_id": str(uuid.uuid4()),
                    "session_id": session_id,
                    "type": "error",
                    "message": "",
                }
            ),
        )
    await pool.close()
    # Fetch via list API
    url = f"{GATEWAY_BASE}/v1/sessions/{session_id}/events?limit=10"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url)
    assert resp.status_code == 200
    data = resp.json()
    upgraded = [
        e
        for e in data.get("events", [])
        if (e.get("payload") or {}).get("type", "").endswith(".error")
    ]
    assert upgraded, "expected upgraded *.error event"
    evt = upgraded[0]["payload"]
    assert evt.get("message"), "normalized error should have user-facing message"
    assert evt.get("metadata", {}).get("error"), "normalized error should include metadata.error"


@pytest.mark.asyncio
async def test_event_dedupe_enforcement():
    """Appending same event_id twice should yield one row due to unique index + event_exists checks."""
    session_id = str(uuid.uuid4())
    event_id = str(uuid.uuid4())
    # Use session repository append_event which will respect dedupe logic for event_exists only if second write checks DB.
    from services.common.session_repository import ensure_schema, PostgresSessionStore

    store = PostgresSessionStore()
    await ensure_schema(store)
    payload_base = {
        "event_id": event_id,
        "session_id": session_id,
        "persona_id": None,
        "role": "user",
        "message": "Hello",
        "metadata": {"tenant": "public"},
    }
    await store.append_event(session_id, {"type": "user", **payload_base})
    # Attempt duplicate insert bypassing event_exists (direct low-level insertion) and expect unique index violation
    import asyncpg

    dsn = os.getenv("POSTGRES_DSN", "postgresql://soma:soma@localhost:5432/somaagent01")
    pool = await asyncpg.create_pool(dsn)
    dup_error = None
    async with pool.acquire() as conn:
        try:
            await conn.execute(
                """
                INSERT INTO session_events (session_id, payload)
                VALUES ($1, $2::jsonb)
                """,
                session_id,
                json.dumps({"type": "user", **payload_base}),
            )
        except Exception as exc:  # unique constraint should trigger
            dup_error = str(exc)
    await pool.close()
    # Verify unique constraint fired
    assert dup_error and re.search(
        r"uq_session_events_session_event", dup_error
    ), "duplicate insert should fail unique constraint"
    await store.close()
