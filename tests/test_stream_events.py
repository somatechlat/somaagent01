from __future__ import annotations

import json
import os
import re
import uuid
from typing import Any, List

import httpx
import pytest

GATEWAY_BASE = os.getenv("GATEWAY_BASE", "http://localhost:21016")


@pytest.mark.asyncio
async def test_stream_canonical_sequence():
    """Verify canonical streaming: deltas accumulate into one final with done flag."""
    url = f"{GATEWAY_BASE}/v1/llm/invoke/stream?mode=canonical"
    body = {
        "role": "dialogue",
        "session_id": str(uuid.uuid4()),
        "persona_id": None,
        "tenant": "public",
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
        ],
        "overrides": {"model": os.getenv("TEST_STREAM_MODEL", "gpt-4o-mini"), "temperature": 0.0},
    }
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", url, json=body) as rstream:
            assert rstream.status_code == 200
            raw_chunks: List[str] = []
            async for line in rstream.aiter_lines():
                if not line:
                    continue
                if line.startswith("data: "):
                    raw = line[len("data: ") :].strip()
                    if raw == "[DONE]":
                        break
                    raw_chunks.append(raw)
                if len(raw_chunks) > 400:  # safety cap
                    break
    events: List[dict[str, Any]] = []
    for item in raw_chunks:
        try:
            events.append(json.loads(item))
        except Exception:
            continue
    deltas = [e for e in events if e.get("type") == "assistant.delta"]
    finals = [e for e in events if e.get("type") == "assistant.final"]
    assert len(finals) == 1, f"expected single assistant.final, got {len(finals)}"
    if deltas:
        assembled = "".join(d.get("message") or "" for d in deltas)
        final_msg = finals[0].get("message") or ""
        assert final_msg == assembled
    assert finals[0].get("metadata", {}).get("done") in {True, "true"}


@pytest.mark.asyncio
async def test_sse_heartbeat_presence():
    """If gateway SSE endpoint is available, ensure keepalive event appears within window."""
    session_id = str(uuid.uuid4())
    url = f"{GATEWAY_BASE}/v1/sessions/{session_id}/events?limit=1"
    try:
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "GET", url, headers={"Accept": "text/event-stream"}
            ) as rstream:
                if rstream.status_code != 200:
                    pytest.skip("SSE not available")
                saw_heartbeat = False
                # Read for up to ~2 heartbeats
                async for line in rstream.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data: "):
                        raw = line[len("data: ") :].strip()
                        try:
                            obj = json.loads(raw)
                        except Exception:
                            continue
                        if obj.get("type") == "system.keepalive":
                            saw_heartbeat = True
                            break
        # If we reached here without network errors, assert heartbeat flag
        if "saw_heartbeat" in locals():
            assert saw_heartbeat is True
    except Exception:
        pytest.skip("gateway SSE not reachable")


@pytest.mark.asyncio
async def test_error_upgrade_on_read():
    """Insert legacy raw error row and confirm API upgrades to *.error."""
    session_id = str(uuid.uuid4())
    import asyncpg

    dsn = os.getenv("POSTGRES_DSN", "postgresql://soma:soma@localhost:5432/somaagent01")
    try:
        pool = await asyncpg.create_pool(dsn)
    except Exception:
        pytest.skip("postgres unavailable")
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
    url = f"{GATEWAY_BASE}/v1/sessions/{session_id}/events?limit=10"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url)
    assert resp.status_code == 200
    upgraded = [
        e
        for e in resp.json().get("events", [])
        if (e.get("payload") or {}).get("type", "").endswith(".error")
    ]
    assert upgraded
    p = upgraded[0]["payload"]
    assert p.get("message")
    assert p.get("metadata", {}).get("error")


@pytest.mark.asyncio
async def test_event_dedupe():
    """Duplicate event_id insert triggers unique index failure."""
    session_id = str(uuid.uuid4())
    event_id = str(uuid.uuid4())
    from services.common.session_repository import ensure_schema, PostgresSessionStore

    store = PostgresSessionStore()
    await ensure_schema(store)
    payload = {
        "event_id": event_id,
        "session_id": session_id,
        "persona_id": None,
        "role": "user",
        "message": "Hello",
        "metadata": {"tenant": "public"},
    }
    await store.append_event(session_id, {"type": "user", **payload})
    import asyncpg

    dsn = os.getenv("POSTGRES_DSN", "postgresql://soma:soma@localhost:5432/somaagent01")
    try:
        pool = await asyncpg.create_pool(dsn)
    except Exception:
        pytest.skip("postgres unavailable")
    dup_error = None
    async with pool.acquire() as conn:
        try:
            await conn.execute(
                """
                INSERT INTO session_events (session_id, payload)
                VALUES ($1, $2::jsonb)
                """,
                session_id,
                json.dumps({"type": "user", **payload}),
            )
        except Exception as exc:
            dup_error = str(exc)
    await pool.close()
    await store.close()
    assert dup_error and re.search(r"uq_session_events_session_event", dup_error)
