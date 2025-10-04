"""Conversation worker prototype for SomaAgent 01."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from dataclasses import dataclass
from typing import Any

from services.common.event_bus import KafkaEventBus
from services.common.session_repository import PostgresSessionStore, RedisSessionCache

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))


@dataclass
class WorkerSettings:
    inbound_topic: str = os.getenv("CONVERSATION_INBOUND", "conversation.inbound")
    outbound_topic: str = os.getenv("CONVERSATION_OUTBOUND", "conversation.outbound")
    group_id: str = os.getenv("CONVERSATION_GROUP", "conversation-worker")


class ConversationWorker:
    def __init__(self, settings: WorkerSettings | None = None) -> None:
        self.settings = settings or WorkerSettings()
        self.bus = KafkaEventBus()
        self.cache = RedisSessionCache()
        self.store = PostgresSessionStore()

    async def start(self) -> None:
        await self.store.append_event("system", {"type": "startup", "ts": asyncio.get_running_loop().time()})
        await self.bus.consume(self.settings.inbound_topic, self.settings.group_id, self._handle_event)

    async def _handle_event(self, event: dict[str, Any]) -> None:
        session_id = event.get("session_id")
        LOGGER.info("Processing inbound event", extra={"session_id": session_id})

        # Store the incoming message for traceability.
        await self.store.append_event(session_id, {"type": "user", **event})

        # Placeholder SLM+LLM pipeline (to be replaced in later sprints).
        response = {
            "event_id": str(uuid.uuid4()),
            "session_id": session_id,
            "persona_id": event.get("persona_id"),
            "role": "assistant",
            "message": f"[placeholder-response] {event.get('message')}",
            "metadata": {"debug": "conversation worker stub"},
        }

        await self.store.append_event(session_id, {"type": "assistant", **response})
        await self.bus.publish(self.settings.outbound_topic, response)


async def main() -> None:
    worker = ConversationWorker()
    await worker.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        LOGGER.info("Conversation worker stopped")
