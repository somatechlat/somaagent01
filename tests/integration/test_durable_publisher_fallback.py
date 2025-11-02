import uuid

import pytest
from aiokafka.errors import KafkaError
from testcontainers.postgres import PostgresContainer

from services.common.outbox_repository import ensure_schema, OutboxStore
from services.common.publisher import DurablePublisher


class FailingBus:
    async def publish(self, topic: str, payload: dict):
        # Simulate a Kafka failure with the real aiokafka KafkaError type
        raise KafkaError("broker unavailable")


@pytest.mark.asyncio
async def test_durable_publisher_fallback_enqueues_to_outbox(event_loop):
    # Spin up a real Postgres with Testcontainers
    with PostgresContainer("postgres:16-alpine") as pg:
        dsn = pg.get_connection_url()  # e.g. postgresql://test:test@0.0.0.0:5432/test
        store = OutboxStore(dsn=dsn)
        await ensure_schema(store)

        publisher = DurablePublisher(bus=FailingBus(), outbox=store)

        topic = "conversation.inbound"
        session_id = str(uuid.uuid4())
        event_id = str(uuid.uuid4())
        payload = {
            "event_id": event_id,
            "session_id": session_id,
            "message": "hello",
            "metadata": {"tenant": "t1"},
        }

        result = await publisher.publish(
            topic,
            payload,
            dedupe_key=event_id,
            session_id=session_id,
            tenant="t1",
        )

        assert result["published"] is False
        assert result["enqueued"] is True
        msg_id = result["id"]
        assert isinstance(msg_id, int)

        # Validate row in outbox
        pool = await store._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM message_outbox WHERE id = $1", msg_id)
            assert row is not None
            assert row["topic"] == topic
            assert row["dedupe_key"] == event_id
            assert row["session_id"] == session_id
            assert row["tenant"] == "t1"
            assert row["status"] == "pending"

        await store.close()
