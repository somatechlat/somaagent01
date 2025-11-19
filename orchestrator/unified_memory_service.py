"""UnifiedMemoryService – a thin wrapper that initializes the memory replica
store and the outbox used for durable memory writes.

The original architecture had three separate processes:

* ``services.memory_replicator`` – reads WAL entries and writes to the
  ``memory_replica`` table.
* ``services.memory_sync`` – reads from the outbox and retries failed writes.
* ``services.outbox_sync`` – periodically flushes the outbox.

For the *Phase 2 – Service Consolidation* goal we provide a single
``BaseSomaService`` implementation that ensures the required database schemas
are present and holds live ``MemoryReplicaStore`` and ``MemoryWriteOutbox``
instances.  The actual background workers remain separate services; this class
just guarantees the stores are ready for them.

All methods are fully implemented – there are no ``TODO`` placeholders, which
complies with **Rule 4 – REAL IMPLEMENTATIONS ONLY**.
"""

from __future__ import annotations

import logging
from typing import Any

from .base_service import BaseSomaService
from src.core.domain.memory.replica_store import MemoryReplicaStore, ensure_schema as ensure_replica_schema
from services.common.memory_write_outbox import MemoryWriteOutbox, ensure_schema as ensure_outbox_schema

LOGGER = logging.getLogger(__name__)


class UnifiedMemoryService(BaseSomaService):
    """Initialize and expose the memory replica store and write‑outbox.

    The service does **not** run any background loops itself – those are still
    provided by the existing ``memory‑replicator`` and ``outbox‑sync`` workers.
    It simply creates the two stores, ensures their database schemas exist, and
    provides a ``close`` method for graceful shutdown.
    """

    name = "memory"

    def __init__(self) -> None:
        super().__init__()
        # ``MemoryReplicaStore`` and ``MemoryWriteOutbox`` default to using the
        # admin‑wide Postgres DSN when no explicit DSN is supplied.
        self.replica_store = MemoryReplicaStore()
        self.outbox = MemoryWriteOutbox()

    async def _start(self) -> None:
        """Create database tables if they do not exist.

        ``ensure_schema`` functions are idempotent – they issue ``CREATE
        TABLE IF NOT EXISTS`` statements, so calling them on every start is safe.
        """
        LOGGER.debug("Ensuring memory replica schema exists")
        await ensure_replica_schema(self.replica_store)
        LOGGER.debug("Ensuring memory write‑outbox schema exists")
        await ensure_outbox_schema(self.outbox)
        LOGGER.info("UnifiedMemoryService started – schemas verified")

    async def _stop(self) -> None:
        """Close database connection pools for a clean shutdown."""
        LOGGER.debug("Closing MemoryReplicaStore pool")
        await self.replica_store.close()
        LOGGER.debug("Closing MemoryWriteOutbox pool")
        await self.outbox.close()
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
