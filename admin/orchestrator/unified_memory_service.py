"""UnifiedMemoryService – initializes the memory replica store.

The architecture includes:

* ``services.memory_replicator`` – reads WAL entries and writes to the
  ``memory_replica`` table.

This service ensures the required database schema is present and holds a
live ``MemoryReplicaStore`` instance for reuse.
"""

from __future__ import annotations

import logging
from typing import Any

# from src.core.infrastructure.repositories import (  # TODO: src/ deleted in Phase 1
#     VectorStoreRepository,
#     ConversationRepository,
# )
from src.core.infrastructure.repositories import (
    ensure_schema as ensure_replica_schema,
    MemoryReplicaStore,
)

from .base_service import BaseSomaService

LOGGER = logging.getLogger(__name__)


class UnifiedMemoryService(BaseSomaService):
    """Initialize and expose the memory replica store."""

    name = "memory"

    def __init__(self) -> None:
        super().__init__()
        # ``MemoryReplicaStore`` defaults to using the admin‑wide Postgres DSN
        # when no explicit DSN is supplied.
        self.replica_store = MemoryReplicaStore()

    async def _start(self) -> None:
        """Create database tables if they do not exist.

        ``ensure_schema`` functions are idempotent – they issue ``CREATE
        TABLE IF NOT EXISTS`` statements, so calling them on every start is safe.
        """
        LOGGER.debug("Ensuring memory replica schema exists")
        await ensure_replica_schema(self.replica_store)
        LOGGER.info("UnifiedMemoryService started – schemas verified")

    async def _stop(self) -> None:
        """Close database connection pools for a clean shutdown."""
        LOGGER.debug("Closing MemoryReplicaStore pool")
        await self.replica_store.close()
        LOGGER.info("UnifiedMemoryService stopped")

    async def health(self) -> dict[str, Any]:
        """Report health – both stores are considered healthy if their pools are
        instantiated.  The orchestrator's ``UnifiedHealthMonitor`` will call
        this method; we simply reflect the internal ``_running`` flag set by the
        base class.
        """
        return {
            "healthy": self._running.is_set(),
            "details": {"name": self.name},
        }
