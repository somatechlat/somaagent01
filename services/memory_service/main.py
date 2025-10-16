"""gRPC MemoryService implementation for SomaAgent 01."""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import uuid
from typing import Any, Optional

import asyncpg
import grpc
from grpc import aio

from services.common.logging_config import setup_logging
from services.common.settings_sa01 import SA01Settings
from services.common.tracing import setup_tracing
from services.memory_service.grpc_generated import memory_pb2, memory_pb2_grpc

LOGGER = logging.getLogger(__name__)


class MemoryRepository:
    """Lightweight Postgres-backed memory store."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        self._pool: asyncpg.Pool | None = None

    async def _pool(self) -> asyncpg.Pool:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(self.dsn, min_size=1, max_size=5)
        return self._pool

    async def ensure_schema(self) -> None:
        pool = await self._pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    tenant TEXT NOT NULL,
                    persona_id TEXT,
                    content TEXT NOT NULL,
                    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                );
                """
            )

    async def create_memory(
        self,
        *,
        tenant: str,
        persona_id: str | None,
        content: str,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        record_id = uuid.uuid4().hex
        payload = metadata or {}
        pool = await self._pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO memories (id, tenant, persona_id, content, metadata)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id, tenant, persona_id, content, metadata,
                          EXTRACT(EPOCH FROM created_at) AS created_at
                """,
                record_id,
                tenant,
                persona_id,
                content,
                payload,
            )
        if not row:
            raise RuntimeError("failed to insert memory record")
        return dict(row)

    async def get_memory(self, *, memory_id: str) -> Optional[dict[str, Any]]:
        pool = await self._pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, tenant, persona_id, content, metadata, EXTRACT(EPOCH FROM created_at) AS created_at
                FROM memories
                WHERE id = $1
                """,
                memory_id,
            )
        if not row:
            return None
        return dict(row)

    async def list_memories(
        self,
        *,
        tenant: str,
        persona_id: Optional[str],
        limit: int,
    ) -> list[dict[str, Any]]:
        pool = await self._pool()
        async with pool.acquire() as conn:
            if persona_id:
                rows = await conn.fetch(
                    """
                    SELECT id, tenant, persona_id, content, metadata, EXTRACT(EPOCH FROM created_at) AS created_at
                    FROM memories
                    WHERE tenant = $1 AND persona_id = $2
                    ORDER BY created_at DESC
                    LIMIT $3
                    """,
                    tenant,
                    persona_id,
                    limit,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT id, tenant, persona_id, content, metadata, EXTRACT(EPOCH FROM created_at) AS created_at
                    FROM memories
                    WHERE tenant = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                    """,
                    tenant,
                    limit,
                )
        return [dict(row) for row in rows]


class MemoryService(memory_pb2_grpc.MemoryServiceServicer):
    def __init__(self, repository: MemoryRepository) -> None:
        self.repository = repository

    @staticmethod
    def _to_proto(record: dict[str, Any]) -> memory_pb2.MemoryRecord:
        return memory_pb2.MemoryRecord(
            id=record.get("id", ""),
            tenant=record.get("tenant", ""),
            persona_id=record.get("persona_id") or "",
            content=record.get("content", ""),
            metadata=record.get("metadata") or {},
            created_at_ms=int(float(record.get("created_at", 0.0)) * 1000),
        )

    async def CreateMemory(self, request, context):  # type: ignore[override]
        record = await self.repository.create_memory(
            tenant=request.tenant,
            persona_id=request.persona_id or None,
            content=request.content,
            metadata=dict(request.metadata),
        )
        return memory_pb2.CreateMemoryResponse(record=self._to_proto(record))

    async def GetMemory(self, request, context):  # type: ignore[override]
        record = await self.repository.get_memory(memory_id=request.id)
        if not record:
            await context.abort(grpc.StatusCode.NOT_FOUND, "memory not found")
        return memory_pb2.GetMemoryResponse(record=self._to_proto(record))

    async def ListMemories(self, request, context):  # type: ignore[override]
        limit = request.limit if request.limit > 0 else 20
        rows = await self.repository.list_memories(
            tenant=request.tenant,
            persona_id=request.persona_id or None,
            limit=limit,
        )
        return memory_pb2.ListMemoriesResponse(records=[self._to_proto(row) for row in rows])


async def _serve(settings: SA01Settings) -> None:
    setup_logging()
    setup_tracing("memory-service", endpoint=settings.otlp_endpoint)

    repository = MemoryRepository(settings.postgres_dsn)
    await repository.ensure_schema()

    server = aio.server()
    memory_pb2_grpc.add_MemoryServiceServicer_to_server(MemoryService(repository), server)

    port = int(os.getenv("MEMORY_SERVICE_PORT", "20017"))
    listen_addr = f"0.0.0.0:{port}"
    server.add_insecure_port(listen_addr)
    LOGGER.info("MemoryService starting", extra={"listen": listen_addr})

    await server.start()

    stop_event = asyncio.Event()

    def _handle_signal(*_: Any) -> None:
        LOGGER.info("MemoryService shutdown signal received")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _handle_signal)

    await stop_event.wait()
    await server.stop(5)
    LOGGER.info("MemoryService stopped")


def main() -> None:
    settings = SA01Settings.from_env()
    asyncio.run(_serve(settings))


if __name__ == "__main__":
    main()
