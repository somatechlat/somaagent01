"""Async gRPC client for the MemoryService."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import grpc
from grpc import aio

from services.common.settings_sa01 import SA01Settings
from services.memory_service.grpc_generated import memory_pb2, memory_pb2_grpc


def _default_target(settings: SA01Settings) -> str:
    profile = settings.environment_profile() or {}
    memory_section = profile.get("memory_service", {})
    if isinstance(memory_section, dict) and memory_section.get("target"):
        return str(memory_section["target"])
    return settings.memory_service_target


@dataclass(slots=True)
class MemoryRecord:
    id: str
    tenant: str
    persona_id: str | None
    content: str
    metadata: dict[str, str]
    created_at_ms: int

    @classmethod
    def from_proto(cls, record: memory_pb2.MemoryRecord) -> "MemoryRecord":
        return cls(
            id=record.id,
            tenant=record.tenant,
            persona_id=record.persona_id or None,
            content=record.content,
            metadata=dict(record.metadata),
            created_at_ms=record.created_at_ms,
        )


class MemoryClient:
    def __init__(self, target: Optional[str] = None, *, settings: SA01Settings | None = None) -> None:
        self.settings = settings or SA01Settings.from_env()
        default_target = _default_target(self.settings)
        self.target = target or os.getenv("MEMORY_SERVICE_TARGET", default_target)
        self._channel: aio.Channel | None = None
        self._stub: memory_pb2_grpc.MemoryServiceStub | None = None

    async def _stub_instance(self) -> memory_pb2_grpc.MemoryServiceStub:
        if self._channel is None:
            self._channel = aio.insecure_channel(self.target)
        if self._stub is None:
            self._stub = memory_pb2_grpc.MemoryServiceStub(self._channel)
        return self._stub

    async def close(self) -> None:
        if self._channel is not None:
            await self._channel.close()
            self._channel = None
            self._stub = None

    async def create_memory(
        self,
        *,
        tenant: str,
        persona_id: Optional[str],
        content: str,
        metadata: Optional[dict[str, str]] = None,
    ) -> MemoryRecord:
        stub = await self._stub_instance()
        response = await stub.CreateMemory(
            memory_pb2.CreateMemoryRequest(
                tenant=tenant,
                persona_id=persona_id or "",
                content=content,
                metadata=metadata or {},
            )
        )
        return MemoryRecord.from_proto(response.record)

    async def get_memory(self, memory_id: str) -> Optional[MemoryRecord]:
        stub = await self._stub_instance()
        try:
            response = await stub.GetMemory(memory_pb2.GetMemoryRequest(id=memory_id))
        except grpc.aio.AioRpcError as exc:
            if exc.code() == grpc.StatusCode.NOT_FOUND:
                return None
            raise
        return MemoryRecord.from_proto(response.record)

    async def list_memories(
        self,
        *,
        tenant: str,
        persona_id: Optional[str],
        limit: int = 20,
    ) -> list[MemoryRecord]:
        stub = await self._stub_instance()
        response = await stub.ListMemories(
            memory_pb2.ListMemoriesRequest(
                tenant=tenant,
                persona_id=persona_id or "",
                limit=limit,
            )
        )
        return [MemoryRecord.from_proto(record) for record in response.records]

    async def __aenter__(self) -> "MemoryClient":
        await self._stub_instance()
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self.close()
