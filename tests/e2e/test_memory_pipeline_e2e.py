import asyncio
import json
import os
import time

import pytest
from testcontainers.postgres import PostgresContainer
from testcontainers.kafka import KafkaContainer
from aiokafka import AIOKafkaProducer

from services.memory_replicator.main import MemoryReplicator
from services.common.memory_replica_store import MemoryReplicaStore, ensure_schema as ensure_replica_schema
from services.common.dlq_store import DLQStore, ensure_schema as ensure_dlq_schema


@pytest.mark.asyncio
@pytest.mark.integration
async def test_wal_to_replica_happy_path_e2e():
    # Spin up ephemeral Postgres and Kafka
    with PostgresContainer("postgres:14") as pg, KafkaContainer() as kafka:
        pg_url = pg.get_connection_url()
        bootstrap = kafka.get_bootstrap_server()

        # Env configuration for the replicator
        os.environ["POSTGRES_DSN"] = pg_url
        os.environ["KAFKA_BOOTSTRAP_SERVERS"] = bootstrap
        os.environ["MEMORY_WAL_TOPIC"] = "memory.wal"
        os.environ["REPLICATOR_METRICS_PORT"] = "0"  # disable metrics server

        # Ensure schemas
        replica = MemoryReplicaStore(dsn=pg_url)
        dlq_store = DLQStore(dsn=pg_url)
        await ensure_replica_schema(replica)
        await ensure_dlq_schema(dlq_store)

        # Start replicator in background
        worker = MemoryReplicator()
        task = asyncio.create_task(worker.start())
        await asyncio.sleep(1.0)

        # Produce a WAL event
        producer = AIOKafkaProducer(bootstrap_servers=bootstrap)
        await producer.start()
        try:
            event = {
                "type": "memory.write",
                "role": "user",
                "session_id": "s-e2e",
                "persona_id": "p-e2e",
                "tenant": "t-e2e",
                "payload": {"id": "e2e-1", "content": "hello"},
                "result": {"coord": "c-e2e", "trace_id": "tr-e2e", "request_id": "rq-e2e"},
                "timestamp": time.time(),
            }
            await producer.send_and_wait("memory.wal", json.dumps(event).encode("utf-8"))
        finally:
            await producer.stop()

        # Wait until replica observes timestamp
        deadline = time.time() + 20
        seen = False
        while time.time() < deadline:
            ts = await replica.latest_wal_timestamp()
            if ts and ts > 0:
                seen = True
                break
            await asyncio.sleep(0.5)

        # Cancel worker task
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

        assert seen, "replica did not observe WAL timestamp in time"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_replicator_error_routes_to_dlq_unit(monkeypatch):
    # Unit-level: simulate insert error and ensure DLQ store receives a row
    pg_url = os.getenv("TEST_POSTGRES_DSN")
    if not pg_url:
        pytest.skip("TEST_POSTGRES_DSN not set")

    store = DLQStore(dsn=pg_url)
    await ensure_dlq_schema(store)

    worker = MemoryReplicator()
    # Point worker stores to our test DSN
    worker.dlq_store = store

    # Monkeypatch replica.insert_from_wal to raise
    class Boom(Exception):
        pass

    class FakeReplica:
        async def insert_from_wal(self, wal):  # type: ignore
            raise Boom("fail insert")

    worker.replica = FakeReplica()  # type: ignore

    event = {
        "type": "memory.write",
        "role": "user",
        "session_id": "s-x",
        "persona_id": "p-x",
        "tenant": "t-x",
        "payload": {"id": "boom-1"},
        "result": {},
        "timestamp": time.time(),
    }

    await worker._handle_wal(event)

    depth = await store.count(topic=f"{worker.wal_topic}.dlq")
    assert depth >= 1

