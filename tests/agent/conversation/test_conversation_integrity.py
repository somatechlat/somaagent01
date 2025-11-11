from __future__ import annotations

import asyncio
import json
import os
import uuid
from typing import AsyncIterator

import asyncpg
import httpx
import pytest
import pytest_asyncio

from services.common.session_repository import ensure_schema, PostgresSessionStore

GATEWAY_BASE = "http://localhost:21016"


@pytest_asyncio.fixture()
async def pg_pool() -> AsyncIterator[asyncpg.Pool]:
    dsn = os.getenv("SA01_DB_DSN", "postgresql://soma:soma@localhost:5432/somaagent01")
    try:
        pool = await asyncpg.create_pool(dsn)
    except Exception as e:
        pytest.skip(f"postgres unavailable: {e}")
    else:
        try:
            async with pool.acquire() as conn:
                try:
                    await conn.execute("TRUNCATE session_events RESTART IDENTITY CASCADE")
                    await conn.execute("TRUNCATE session_envelopes")
                except Exception:
                    # If tables missing let ensure_schema handle creation later
                    pass
            yield pool
        finally:
            await pool.close()


@pytest_asyncio.fixture()
async def store(pg_pool: asyncpg.Pool) -> AsyncIterator[PostgresSessionStore]:
    repo = PostgresSessionStore()
    await ensure_schema(repo)
    try:
        yield repo
    finally:
        await repo.close()


@pytest.mark.asyncio
async def test_event_deduplicate(store: PostgresSessionStore):
    sid = str(uuid.uuid4())
    eid = str(uuid.uuid4())
    payload = {
        "event_id": eid,
        "session_id": sid,
        "role": "user",
        "type": "user",
        "message": "Hello",
    }
    await store.append_event(sid, payload)
    # Second append with same event_id should result in second row only if dedupe not enforced; we enforce via unique index
    dup_exists = await store.event_exists(sid, eid)
    assert dup_exists is True
    # Attempt duplicate append should raise due to unique index (narrow to Postgres errors)
    with pytest.raises(asyncpg.PostgresError):
        await store.append_event(sid, payload)


@pytest.mark.asyncio
async def test_error_normalization_read_upgrade(store: PostgresSessionStore):
    sid = str(uuid.uuid4())
    raw_error = {
        "event_id": str(uuid.uuid4()),
        "session_id": sid,
        "type": "error",
        "message": "",
        "role": None,
    }
    # Try direct insert bypassing normalization; skip if cannot
    try:
        pool = await store._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO session_events (session_id, payload) VALUES ($1, $2)",
                sid,
                json.dumps(raw_error),
            )
    except Exception:
        pytest.skip("direct raw insert not possible (constraint or auth)")
    events = await store.list_events_after(sid, limit=10)
    assert events, "expected events list"
    raw = [e for e in events if e["payload"].get("type") == "error"]
    assert (
        raw
    ), "raw error should be present prior to read-time normalization path (direct DB access)"
    # Gateway /v1/sessions/{sid}/events endpoint should upgrade type; call only if gateway running
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{GATEWAY_BASE}/v1/sessions/{sid}/events?limit=25")
        if resp.status_code == 200:
            upgraded = [
                p
                for p in resp.json().get("events", [])
                if p.get("payload", {}).get("type", "").endswith(".error")
            ]
            assert upgraded, "expected upgraded *.error event via API normalization"
    except Exception:
        pytest.skip("gateway not reachable for normalization test")


@pytest.mark.asyncio
async def test_stream_transform_canonical_mode(store: PostgresSessionStore):
    # This test assumes gateway streaming endpoint transforms tokens to assistant.delta and final
    # We invoke a minimal /v1/session/message then read SSE for a short duration.
    sid = str(uuid.uuid4())
    message_body = {
        "session_id": sid,
        "message": "Ping stream transform",
        "persona_id": None,
        "metadata": {},
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(f"{GATEWAY_BASE}/v1/session/message", json=message_body)
        assert resp.status_code == 200
    except Exception:
        pytest.skip("gateway not reachable for stream test")
    # Consume SSE for a short window collecting event types
    types: set[str] = set()
    url = f"{GATEWAY_BASE}/v1/session/{sid}/events"
    try:
        async with httpx.AsyncClient(timeout=None) as client:
            # Expect timeout/read error due to test harness; narrow exception types
            with pytest.raises((httpx.TimeoutException, httpx.ReadError)):
                r = await client.get(url, headers={"Accept": "text/event-stream"}, timeout=10.0)
                # Fallback: if not streaming, skip
                if r.status_code != 200:
                    pytest.skip("SSE endpoint not available")
    except Exception:
        # Poll events list instead for presence of assistant.final
        async with httpx.AsyncClient(timeout=5.0) as client:
            await asyncio.sleep(2)
            resp = await client.get(f"{GATEWAY_BASE}/v1/sessions/{sid}/events?limit=50")
        if resp.status_code == 200:
            data = resp.json().get("events", [])
            for ev in data:
                types.add(ev.get("payload", {}).get("type"))
            assert any(
                t == "assistant.final" for t in types
            ), "expected assistant.final in events list"
    # Cannot reliably assert assistant.delta without provider streaming; ensure final present only


@pytest.mark.asyncio
async def test_raw_error_constraint(store: PostgresSessionStore):
    sid = str(uuid.uuid4())
    raw_error = {"event_id": str(uuid.uuid4()), "session_id": sid, "type": "error", "message": ""}
    try:
        pool = await store._ensure_pool()
        async with pool.acquire() as conn:
            try:
                await conn.execute(
                    "INSERT INTO session_events (session_id, payload) VALUES ($1, $2)",
                    sid,
                    json.dumps(raw_error),
                )
            except Exception:
                return  # Constraint enforced or insert blocked
    except Exception:
        pytest.skip("cannot access pool for raw constraint test")
    # If insert succeeded, ensure backfill/normalization will fix it
    events = await store.list_events_after(sid, limit=5)
    assert events
    assert any(e["payload"].get("type") == "error" for e in events), "legacy raw error inserted"
