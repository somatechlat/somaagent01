import asyncio
import json
import os
import time

import pytest
from aiokafka import AIOKafkaConsumer
from testcontainers.kafka import KafkaContainer
from testcontainers.postgres import PostgresContainer

from services.common.memory_write_outbox import ensure_schema as ensure_mw_schema, MemoryWriteOutbox
from services.memory_sync.main import MemorySyncWorker


@pytest.mark.asyncio
@pytest.mark.integration
async def test_memory_sync_drains_after_outage_e2e():
    # Bring up ephemeral Postgres+Kafka
    with PostgresContainer("postgres:14") as pg, KafkaContainer() as kafka:
        pg_url = pg.get_connection_url()
        bootstrap = kafka.get_bootstrap_server()

        os.environ["SA01_DB_DSN"] = pg_url
        os.environ["SA01_KAFKA_BOOTSTRAP_SERVERS"] = bootstrap
        os.environ["SA01_MEMORY_WAL_TOPIC"] = "memory.wal"
        os.environ["MEMORY_SYNC_METRICS_PORT"] = "0"

        # Outbox schema and seed one item
        outbox = MemoryWriteOutbox(dsn=pg_url)
        await ensure_mw_schema(outbox)
        payload = {
            "id": "outage-1",
            "type": "conversation_event",
            "role": "assistant",
            "content": "hello",
            "session_id": "s-sync",
            "metadata": {"tenant": "t-sync"},
        }
        await outbox.enqueue(
            payload=payload, tenant="t-sync", session_id="s-sync", idempotency_key="outage-1"
        )

        # Patch SomaClient.remember to fail at first, then succeed
        class Boom(Exception):
            pass

        attempts = {"n": 0}

        async def fake_remember(_payload):
            attempts["n"] += 1
            if attempts["n"] <= 2:
                raise Boom("SomaBrain down")
            return {"coordinate": "coord-1", "trace_id": "tr-1", "request_id": "rq-1"}

        worker = MemorySyncWorker()
        # Inject fake remember on the instance
        worker.soma.remember = fake_remember  # type: ignore

        # Start worker and a consumer to observe WAL
        consumer = AIOKafkaConsumer(
            "memory.wal",
            bootstrap_servers=bootstrap,
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            group_id="test-memory-sync-recovery",
        )
        await consumer.start()
        task = asyncio.create_task(worker.start())

        # Wait until we observe a WAL message (success after retries)
        found = False
        deadline = time.time() + 30
        try:
            while time.time() < deadline and not found:
                msgs = await consumer.getmany(timeout_ms=1000)
                for tp, batch in msgs.items():
                    for record in batch:
                        evt = json.loads(record.value.decode("utf-8"))
                        if (
                            evt.get("type") == "memory.write"
                            and (evt.get("payload") or {}).get("id") == "outage-1"
                        ):
                            found = True
                            break
                    if found:
                        break
        finally:
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            await consumer.stop()

        assert found, "memory_sync did not publish WAL after outage recovery"
