from __future__ import annotations

import grpc
import pytest

from services.common.memory_client import MemoryClient
from services.common.settings_sa01 import SA01Settings
from services.memory_service.grpc_generated import memory_pb2, memory_pb2_grpc


class InMemoryServicer(memory_pb2_grpc.MemoryServiceServicer):
    def __init__(self) -> None:
        self._records: dict[str, memory_pb2.MemoryRecord] = {}

    async def CreateMemory(self, request, context):  # type: ignore[override]
        record = memory_pb2.MemoryRecord(
            id=f"mem-{len(self._records)+1}",
            tenant=request.tenant,
            persona_id=request.persona_id,
            content=request.content,
            metadata=request.metadata,
            created_at_ms=1234,
        )
        self._records[record.id] = record
        return memory_pb2.CreateMemoryResponse(record=record)

    async def GetMemory(self, request, context):  # type: ignore[override]
        record = self._records.get(request.id)
        if not record:
            await context.abort(grpc.StatusCode.NOT_FOUND, "missing")
        return memory_pb2.GetMemoryResponse(record=record)

    async def ListMemories(self, request, context):  # type: ignore[override]
        results = [record for record in self._records.values() if record.tenant == request.tenant]
        return memory_pb2.ListMemoriesResponse(records=results)


@pytest.mark.asyncio
async def test_memory_client_roundtrip() -> None:
    server = grpc.aio.server()
    servicer = InMemoryServicer()
    memory_pb2_grpc.add_MemoryServiceServicer_to_server(servicer, server)
    port = server.add_insecure_port("localhost:0")

    await server.start()

    target = f"localhost:{port}"
    settings = SA01Settings.for_environment(
        "DEV",
        overrides={
            "model_profiles_path": "conf/model_profiles.yaml",
            "deployment_mode": "LOCAL",
            "postgres_dsn": "postgresql://test",
            "kafka_bootstrap_servers": "kafka:9092",
            "redis_url": "redis://redis:6379/0",
            "otlp_endpoint": "http://otel:4317",
        },
    )
    client = MemoryClient(target=target, settings=settings)

    record = await client.create_memory(
        tenant="tenant-a",
        persona_id="persona-1",
        content="payload",
        metadata={"model": "gpt"},
    )

    fetched = await client.get_memory(record.id)
    assert fetched is not None
    assert fetched.id == record.id
    assert fetched.metadata["model"] == "gpt"

    results = await client.list_memories(tenant="tenant-a", persona_id="persona-1", limit=10)
    assert len(results) == 1
    assert results[0].id == record.id

    await client.close()
    await server.stop(0)
