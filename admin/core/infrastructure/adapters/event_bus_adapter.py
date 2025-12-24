"""Event bus adapter wrapping KafkaEventBus.

This adapter implements EventBusPort by delegating ALL operations
to the existing production KafkaEventBus implementation.
"""

import asyncio
from typing import Any, Callable, Dict, Optional

from services.common.event_bus import KafkaEventBus, KafkaSettings
# from src.core.domain.ports.adapters.event_bus import EventBusPort


class KafkaEventBusAdapter(EventBusPort):
    """Implements EventBusPort using existing KafkaEventBus.

    Delegates ALL operations to services.common.event_bus.KafkaEventBus.
    """

    def __init__(
        self,
        bus: Optional[KafkaEventBus] = None,
        settings: Optional[KafkaSettings] = None,
    ):
        """Initialize adapter with existing bus or create new one.

        Args:
            bus: Existing KafkaEventBus instance (preferred)
            settings: Kafka settings (used if bus not provided)
        """
        self._bus = bus or KafkaEventBus(settings)

    async def publish(
        self,
        topic: str,
        payload: Any,
        headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        await self._bus.publish(topic, payload, headers)

    async def consume(
        self,
        topic: str,
        group_id: str,
        handler: Callable[[Dict[str, Any]], Any],
        stop_event: Optional[asyncio.Event] = None,
    ) -> None:
        await self._bus.consume(topic, group_id, handler, stop_event)

    async def healthcheck(self) -> None:
        await self._bus.healthcheck()

    async def close(self) -> None:
        await self._bus.close()
