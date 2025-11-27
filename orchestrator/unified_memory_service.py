import os

os.getenv(os.getenv(""))
from __future__ import annotations

import logging
from typing import Any

from services.common.memory_write_outbox import (
    ensure_schema as ensure_outbox_schema,
    MemoryWriteOutbox,
)
from src.core.domain.memory.replica_store import (
    ensure_schema as ensure_replica_schema,
    MemoryReplicaStore,
)

from .base_service import BaseSomaService

LOGGER = logging.getLogger(__name__)


class UnifiedMemoryService(BaseSomaService):
    os.getenv(os.getenv(""))
    name = os.getenv(os.getenv(""))

    def __init__(self) -> None:
        super().__init__()
        self.replica_store = MemoryReplicaStore()
        self.outbox = MemoryWriteOutbox()

    async def _start(self) -> None:
        os.getenv(os.getenv(""))
        LOGGER.debug(os.getenv(os.getenv("")))
        await ensure_replica_schema(self.replica_store)
        LOGGER.debug(os.getenv(os.getenv("")))
        await ensure_outbox_schema(self.outbox)
        LOGGER.info(os.getenv(os.getenv("")))

    async def _stop(self) -> None:
        os.getenv(os.getenv(""))
        LOGGER.debug(os.getenv(os.getenv("")))
        await self.replica_store.close()
        LOGGER.debug(os.getenv(os.getenv("")))
        await self.outbox.close()
        LOGGER.info(os.getenv(os.getenv("")))

    async def health(self) -> dict[str, Any]:
        os.getenv(os.getenv(""))
        return {
            os.getenv(os.getenv("")): self._running.is_set(),
            os.getenv(os.getenv("")): {os.getenv(os.getenv("")): self.name},
        }
