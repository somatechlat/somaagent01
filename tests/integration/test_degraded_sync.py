"""Integration test for the degraded‑buffer sync workflow.

The test exercises the full path:

1. ``persist_event`` stores a raw event in Redis and publishes it to the WAL.
2. ``DegradedSyncWorker`` reads the buffered event, calls Somabrain (real client),
   publishes the enriched assistant event to the outbound Kafka topic, and
   removes the entry from Redis.

All components used are the actual production implementations – no mocks or
stubs – which complies with the VIBE rule *“no fake implementations”.
The test assumes the Docker‑compose stack (Redis, Kafka, Somabrain) is running.
"""

import asyncio
import uuid

import pytest

from services.common.degraded_persist import persist_event
from services.common.event_bus import KafkaEventBus, KafkaSettings
from services.common.publisher import DurablePublisher
from services.common.redis_client import get_all_events
from services.memory_sync.degraded_worker import DegradedSyncWorker
from src.core.config import cfg


@pytest.mark.asyncio
async def test_degraded_sync_full_flow():
    """Verify that a buffered event is enriched and removed from Redis.

    The test performs the following steps:
    * Create a minimal conversation event.
    * Call ``persist_event`` – this writes the event to Redis and publishes to the
      WAL (Kafka).  The WAL publish is not verified here; the focus is on the
      degraded buffer.
    * Confirm the event exists in Redis via ``get_all_events``.
    * Instantiate ``DegradedSyncWorker`` and invoke its private ``_process``
      method for the stored event.  The method uses the real Somabrain client –
      the Somabrain service must be reachable in the test environment.
    * After processing, ensure the Redis entry has been deleted.
    * Consume a single message from the outbound topic to confirm the assistant
      event was published.
    """

    # ---------------------------------------------------------------------
    # 1️⃣ Build a raw event payload.
    # ---------------------------------------------------------------------
    event_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    raw_event = {
        "event_id": event_id,
        "session_id": session_id,
        "persona_id": None,
        "role": "user",
        "message": "test message for degraded sync",
        "attachments": [],
        "metadata": {"tenant": "test"},
        "version": "sa01-v1",
        "trace_context": {},
    }

    # ---------------------------------------------------------------------
    # 2️⃣ Persist the event (writes to Redis and WAL).
    # ---------------------------------------------------------------------
    await persist_event(
        event=raw_event,
        service_name="gateway",
        publisher=DurablePublisher(
            bus=KafkaEventBus(KafkaSettings.from_env()),
            outbox=None,  # Outbox not needed for this test – publish will succeed.
        ),
        wal_topic=cfg.env("MEMORY_WAL_TOPIC", "memory.wal"),
        tenant="test",
    )

    # ---------------------------------------------------------------------
    # 3️⃣ Verify the event is present in Redis.
    # ---------------------------------------------------------------------
    buffered = await get_all_events()
    assert event_id in buffered, "Event should be stored in Redis buffer"
    assert buffered[event_id]["message"] == raw_event["message"]

    # ---------------------------------------------------------------------
    # 4️⃣ Run the degraded sync worker on this single event.
    # ---------------------------------------------------------------------
    worker = DegradedSyncWorker()
    await worker._process(event_id, buffered[event_id])

    # ---------------------------------------------------------------------
    # 5️⃣ The event must be removed from Redis.
    # ---------------------------------------------------------------------
    remaining = await get_all_events()
    assert event_id not in remaining, "Event should be deleted from Redis after success"

    # ---------------------------------------------------------------------
    # 6️⃣ Consume the assistant event from the outbound Kafka topic to ensure it
    #    was published.  We create a temporary consumer that reads a single
    #    message and then stops.
    # ---------------------------------------------------------------------
    outbound_topic = cfg.env("CONVERSATION_OUTBOUND", "conversation.outbound")
    consumer = KafkaEventBus(KafkaSettings.from_env())

    async def consume_one():
        async for msg in consumer.consume(topic=outbound_topic, group_id=f"test-{uuid.uuid4()}"):
            return msg

    # Wait up to 5 seconds for the assistant message.
    assistant_msg = await asyncio.wait_for(consume_one(), timeout=5.0)
    assert assistant_msg["role"] == "assistant"
    assert assistant_msg["session_id"] == session_id
