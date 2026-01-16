"""Store memory use case - orchestrates memory storage.

This use case coordinates:
- Memory storage via MemoryAdapterPort
- Event publishing via EventBusPort

It contains NO infrastructure code - only business logic coordination.
"""

import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol


class MemoryAdapterPort(Protocol):
    """Port for memory storage operations."""

    async def store_memory(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Store memory payload."""
        ...


class EventBusPort(Protocol):
    """Port for event publishing."""

    async def publish(self, topic: str, payload: Any) -> None:
        """Publish event to topic."""
        ...


@dataclass
class StoreMemoryInput:
    """Input data for store memory use case."""

    session_id: str
    content: str
    memory_type: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class StoreMemoryOutput:
    """Output data from store memory use case."""

    memory_id: str
    stored: bool
    metadata: Dict[str, Any]


class StoreMemoryUseCase:
    """Orchestrates memory storage through domain ports.

    This use case:
    1. Stores memory via memory adapter
    2. Publishes storage event
    """

    def __init__(
        self,
        memory_adapter: MemoryAdapterPort,
        event_bus: EventBusPort,
    ):
        """Initialize the instance."""

        self._memory = memory_adapter
        self._bus = event_bus

    async def execute(self, input_data: StoreMemoryInput) -> StoreMemoryOutput:
        """Store a memory item.

        Args:
            input_data: Memory storage input

        Returns:
            Storage output with memory ID
        """
        # Generate memory ID
        memory_id = str(uuid.uuid4())

        # 1. Store memory
        payload = {
            "id": memory_id,
            "session_id": input_data.session_id,
            "content": input_data.content,
            "memory_type": input_data.memory_type,
            "metadata": input_data.metadata,
        }

        result = await self._memory.store_memory(payload)
        stored = result.get("stored", True)

        # 2. Publish storage event
        await self._bus.publish(
            topic="memory.stored",
            payload={
                "memory_id": memory_id,
                "session_id": input_data.session_id,
                "memory_type": input_data.memory_type,
                "stored": stored,
            },
        )

        return StoreMemoryOutput(
            memory_id=memory_id,
            stored=stored,
            metadata=result.get("metadata", {}),
        )
