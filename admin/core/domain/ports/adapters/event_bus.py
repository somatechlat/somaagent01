"""Event bus port interface.

This port defines the contract for event publishing and consuming.
The interface matches the existing KafkaEventBus methods exactly
to enable seamless wrapping of the production implementation.

Production Implementation:
    services.common.event_bus.KafkaEventBus
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional


class EventBusPort(ABC):
    """Abstract interface for event bus operations.

    This port wraps the existing KafkaEventBus implementation.
    All methods match the production implementation signature exactly.
    """

    @abstractmethod
    async def publish(
        self,
        topic: str,
        payload: Any,
        headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Publish an event to a topic.

        Args:
            topic: Target topic name
            payload: Event payload (will be JSON serialized)
            headers: Optional message headers
        """
        ...

    @abstractmethod
    async def consume(
        self,
        topic: str,
        group_id: str,
        handler: Callable[[Dict[str, Any]], Any],
        stop_event: Optional[asyncio.Event] = None,
    ) -> None:
        """Consume events from a topic.

        Args:
            topic: Source topic name
            group_id: Consumer group identifier
            handler: Async handler function for events
            stop_event: Optional event to signal consumer shutdown
        """
        ...

    @abstractmethod
    async def healthcheck(self) -> None:
        """Verify event bus connectivity."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Close connections and release resources."""
        ...