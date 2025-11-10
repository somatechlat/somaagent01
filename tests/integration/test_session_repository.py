from __future__ import annotations

import json
from typing import AsyncIterator

import asyncpg
import pytest
import pytest_asyncio

from services.common.session_repository import (
    ensure_schema,
    PostgresSessionStore,
    RedisSessionCache,
    SESSION_CACHE_EVENTS,
    SESSION_ENVELOPE_REFRESH_TOTAL,
    SESSION_ENVELOPE_VALIDATION_FAILURES,
    SESSION_ENVELOPE_WRITE_TOTAL,
)


@pytest_asyncio.fixture()
async def postgres_pool() -> AsyncIterator[asyncpg.Pool]:
    dsn = "postgresql://soma:soma@localhost:5432/somaagent01"
    try:
        pool = await asyncpg.create_pool(dsn)
    except Exception as exc:  # pragma: no cover - requires local postgres
        pytest.skip(f"Postgres not available for session repository tests: {exc}")
        return
    async with pool.acquire() as conn:
        await conn.execute("TRUNCATE session_events RESTART IDENTITY CASCADE")
        await conn.execute("TRUNCATE session_envelopes")
    try:
        yield pool
    finally:
        await pool.close()


@pytest_asyncio.fixture()
async def store(postgres_pool: asyncpg.Pool) -> AsyncIterator[PostgresSessionStore]:
    repo = PostgresSessionStore()
    await ensure_schema(repo)
    try:
        yield repo
    finally:
        await repo.close()


async def _insert_event(
    conn: asyncpg.Connection, session_id: str, payload: dict[str, object]
) -> None:
    await conn.execute(
        """
        INSERT INTO session_events (session_id, payload)
        VALUES ($1, $2::jsonb)
        """,
        session_id,
        json.dumps(payload),
    )


@pytest.mark.asyncio
async def test_append_event_upserts_envelope(
    postgres_pool: asyncpg.Pool, store: PostgresSessionStore
) -> None:
    session_id = "00000000-0000-0000-0000-000000000001"
    event = {
        "session_id": session_id,
        "persona_id": "persona-1",
        "metadata": {
            "tenant": "t-1",
            "subject": "user-123",
            "analysis": {"intent": "greeting"},
        },
    }

    await store.append_event(session_id, event)

    async with postgres_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT session_id, persona_id, tenant, metadata, analysis FROM session_envelopes WHERE session_id = $1",
            session_id,
        )

    assert row is not None
    assert str(row["session_id"]) == session_id
    assert row["persona_id"] == "persona-1"
    assert row["tenant"] == "t-1"
    assert row["metadata"]["tenant"] == "t-1"
    assert row["analysis"] == {"intent": "greeting"}


@pytest.mark.asyncio
async def test_get_envelope_returns_none_for_missing(store: PostgresSessionStore) -> None:
    envelope = await store.get_envelope("00000000-0000-0000-0000-000000000777")
    assert envelope is None


@pytest.mark.asyncio
async def test_backfill_envelope_overwrites_metadata(
    postgres_pool: asyncpg.Pool, store: PostgresSessionStore
) -> None:
    session_id = "00000000-0000-0000-0000-000000000999"

    async with postgres_pool.acquire() as conn:
        await _insert_event(
            conn,
            session_id,
            {
                "session_id": session_id,
                "persona_id": "persona-a",
                "metadata": {"tenant": "tenant-a", "analysis": {"intent": "explore"}},
            },
        )

    await store.append_event(
        session_id,
        {
            "session_id": session_id,
            "persona_id": "persona-b",
            "metadata": {"tenant": "tenant-b", "scope": "read"},
        },
    )

    await store.backfill_envelope(
        session_id=session_id,
        persona_id="persona-final",
        tenant="tenant-final",
        subject="subject-1",
        issuer="issuer-1",
        scope="scope-1",
        metadata={"tenant": "tenant-final", "flags": {"foo": True}},
        analysis={"intent": "final"},
        created_at=None,
        updated_at=None,
    )

    envelope = await store.get_envelope(session_id)
    assert envelope is not None
    assert envelope.persona_id == "persona-final"
    assert envelope.tenant == "tenant-final"
    assert envelope.metadata["tenant"] == "tenant-final"
    assert envelope.metadata["flags"] == {"foo": True}
    assert envelope.analysis == {"intent": "final"}


@pytest.mark.asyncio
async def test_compose_envelope_skips_incomplete_event(store: PostgresSessionStore) -> None:
    event = {"metadata": {"foo": "bar"}}
    payload = store._compose_envelope_payload(event)
    assert payload is None


def _counter_value(counter, *label_values: str) -> float:
    return counter.labels(*label_values)._value.get()


@pytest.mark.asyncio
async def test_refresh_metrics_increment_on_missing(store: PostgresSessionStore) -> None:
    before = _counter_value(SESSION_ENVELOPE_REFRESH_TOTAL, "missing")
    envelope = await store.get_envelope("00000000-0000-0000-0000-000000001234")
    assert envelope is None
    after = _counter_value(SESSION_ENVELOPE_REFRESH_TOTAL, "missing")
    assert after == pytest.approx(before + 1.0)


@pytest.mark.asyncio
async def test_write_metrics_increment_on_append(store: PostgresSessionStore) -> None:
    session_id = "00000000-0000-0000-0000-000000009999"
    metric_before = _counter_value(SESSION_ENVELOPE_WRITE_TOTAL, "append", "success")

    await store.append_event(
        session_id,
        {
            "session_id": session_id,
            "persona_id": "persona-metrics",
            "metadata": {"tenant": "tenant-metrics"},
        },
    )

    metric_after = _counter_value(SESSION_ENVELOPE_WRITE_TOTAL, "append", "success")
    assert metric_after == pytest.approx(metric_before + 1.0)


@pytest.mark.asyncio
async def test_validation_metrics_increment(store: PostgresSessionStore) -> None:
    metric_before = _counter_value(SESSION_ENVELOPE_VALIDATION_FAILURES, "missing_session_id")
    payload = store._compose_envelope_payload({"metadata": {"foo": "bar"}})
    assert payload is None
    metric_after = _counter_value(SESSION_ENVELOPE_VALIDATION_FAILURES, "missing_session_id")
    assert metric_after == pytest.approx(metric_before + 1.0)


class _StubRedisClient:
    def __init__(
        self, *, get_values: list[str | None] | None = None, delete_result: int = 0
    ) -> None:
        self.set_calls: list[tuple[str, str]] = []
        self.setex_calls: list[tuple[str, int, str]] = []
        self.get_values = get_values or []
        self.delete_result = delete_result

    async def setex(self, key: str, ttl: int, value: str) -> None:
        self.setex_calls.append((key, ttl, value))

    async def set(self, key: str, value: str) -> None:
        self.set_calls.append((key, value))

    async def get(self, key: str) -> str | None:
        if self.get_values:
            return self.get_values.pop(0)
        return None

    async def delete(self, key: str) -> int:
        return self.delete_result


@pytest.mark.asyncio
async def test_cache_set_uses_default_ttl_and_emits_metric() -> None:
    cache = RedisSessionCache(default_ttl=123)
    stub = _StubRedisClient()
    cache._client = stub  # type: ignore[assignment]

    before = _counter_value(SESSION_CACHE_EVENTS, "set", "success")

    await cache.set("session:test", {"foo": "bar"})

    assert stub.setex_calls and not stub.set_calls
    assert stub.setex_calls[0][1] == 123

    after = _counter_value(SESSION_CACHE_EVENTS, "set", "success")
    assert after == pytest.approx(before + 1.0)


@pytest.mark.asyncio
async def test_cache_get_tracks_hit_and_miss_metrics() -> None:
    encoded = json.dumps({"foo": "bar"})
    cache = RedisSessionCache(default_ttl=0)
    stub = _StubRedisClient(get_values=[None, encoded])
    cache._client = stub  # type: ignore[assignment]

    miss_before = _counter_value(SESSION_CACHE_EVENTS, "get", "miss")
    hit_before = _counter_value(SESSION_CACHE_EVENTS, "get", "hit")

    result_none = await cache.get("session:test2")
    assert result_none is None

    result_value = await cache.get("session:test2")
    assert result_value == {"foo": "bar"}

    miss_after = _counter_value(SESSION_CACHE_EVENTS, "get", "miss")
    hit_after = _counter_value(SESSION_CACHE_EVENTS, "get", "hit")

    assert miss_after == pytest.approx(miss_before + 1.0)
    assert hit_after == pytest.approx(hit_before + 1.0)


def test_cache_format_key() -> None:
    cache = RedisSessionCache(default_ttl=0)
    assert cache.format_key("abc") == "session:abc:meta"


@pytest.mark.asyncio
async def test_cache_write_context_respects_default_ttl() -> None:
    cache = RedisSessionCache(default_ttl=42)
    stub = _StubRedisClient()
    cache._client = stub  # type: ignore[assignment]

    await cache.write_context("session-ttl", "persona-x", {"tenant": "demo"})

    assert stub.setex_calls, "expected setex to be used when default TTL is set"
    key, ttl, payload = stub.setex_calls[0]
    assert key == "session:session-ttl:meta"
    assert ttl == 42
    decoded = json.loads(payload)
    assert decoded["persona_id"] == "persona-x"
    assert decoded["metadata"] == {"tenant": "demo"}


class _FailingRedisClient:
    def __init__(self, *, error: Exception) -> None:
        self.error = error

    async def set(self, *args, **kwargs):  # pragma: no cover - interface completeness
        raise self.error

    async def setex(self, *args, **kwargs):
        raise self.error


@pytest.mark.asyncio
async def test_cache_set_reports_errors() -> None:
    cache = RedisSessionCache(default_ttl=0)
    error = RuntimeError("boom")
    cache._client = _FailingRedisClient(error=error)  # type: ignore[assignment]

    before = _counter_value(SESSION_CACHE_EVENTS, "set", "error")

    with pytest.raises(RuntimeError):
        await cache.set("session:oops", {"foo": "bar"})

    after = _counter_value(SESSION_CACHE_EVENTS, "set", "error")
    assert after == pytest.approx(before + 1.0)
