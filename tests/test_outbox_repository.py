import asyncpg
import pytest
from testcontainers.postgres import PostgresContainer

from services.common.outbox_repository import ensure_schema, OutboxStore


@pytest.fixture(scope="module")
def pg_container():
    with PostgresContainer("postgres:15-alpine") as pg:
        pg.start()
        yield pg


@pytest.fixture
async def store(pg_container):
    dsn = pg_container.get_connection_url()
    # Map to asyncpg DSN format
    # testcontainers returns postgresql://test:test@0.0.0.0:XXXXX/test
    repo = OutboxStore(dsn=dsn)
    await ensure_schema(repo)
    yield repo
    await repo.close()


async def _fetch_row(dsn: str, msg_id: int) -> dict:
    pool = await asyncpg.create_pool(dsn, min_size=1, max_size=2)
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM message_outbox WHERE id = $1", msg_id)
    await pool.close()
    return dict(row)


@pytest.mark.asyncio
async def test_enqueue_claim_mark_sent(store: OutboxStore, pg_container: PostgresContainer):
    id1 = await store.enqueue(topic="test.topic", payload={"a": 1}, dedupe_key="k1")
    assert id1 is not None
    # Duplicate should be deduped
    id_dup = await store.enqueue(topic="test.topic", payload={"a": 1}, dedupe_key="k1")
    assert id_dup is None

    id2 = await store.enqueue(topic="test.topic", payload={"b": 2})
    assert id2 is not None

    batch = await store.claim_batch(limit=10)
    got_ids = {m.id for m in batch}
    assert {id1, id2}.issubset(got_ids)

    # Mark first as sent
    await store.mark_sent(id1)
    row1 = await _fetch_row(store.dsn, id1)
    assert row1["status"] == "sent"
    # Retry second with backoff
    await store.mark_retry(id2, backoff_seconds=1.0, error="test error")
    row2 = await _fetch_row(store.dsn, id2)
    assert row2["status"] == "pending"
    assert row2["retry_count"] == 1


@pytest.mark.asyncio
async def test_mark_failed(store: OutboxStore, pg_container: PostgresContainer):
    msg_id = await store.enqueue(topic="test.topic", payload={"x": 1})
    assert msg_id is not None
    # Claim and then mark failed
    _ = await store.claim_batch(limit=1)
    await store.mark_failed(msg_id, error="fatal")
    row = await _fetch_row(store.dsn, msg_id)
    assert row["status"] == "failed"
    assert row["last_error"] == "fatal"
