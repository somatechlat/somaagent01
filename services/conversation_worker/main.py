"""Conversation worker for SomaAgent 01."""
from __future__ import annotations

import asyncio
import logging
import os
import uuid
from typing import Any

from services.common.event_bus import KafkaEventBus
from services.common.session_repository import (
    PostgresSessionStore,
    RedisSessionCache,
    ensure_schema,
)
from services.common.slm_client import ChatMessage, SLMClient

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))


class ConversationWorker:
    def __init__(self) -> None:
        self.settings = {
            "inbound": os.getenv("CONVERSATION_INBOUND", "conversation.inbound"),
            "outbound": os.getenv("CONVERSATION_OUTBOUND", "conversation.outbound"),
            "group": os.getenv("CONVERSATION_GROUP", "conversation-worker"),
        }
        self.bus = KafkaEventBus()
        self.cache = RedisSessionCache()
        self.store = PostgresSessionStore()
        self.slm = SLMClient()

    async def start(self) -> None:
        await ensure_schema(self.store)
        await self.store.append_event(
            "system",
            {
                "type": "worker_start",
                "event_id": str(uuid.uuid4()),
                "message": "Conversation worker online",
            },
        )
        await self.bus.consume(
            self.settings["inbound"],
            self.settings["group"],
            self._handle_event,
        )

    async def _handle_event(self, event: dict[str, Any]) -> None:
        session_id = event.get("session_id")
        if not session_id:
            LOGGER.warning("Received event without session_id", extra={"event": event})
            return

        LOGGER.info("Processing message", extra={"session_id": session_id})
        await self.store.append_event(session_id, {"type": "user", **event})

        # Build conversation history (last 20 events).
        history = await self.store.list_events(session_id, limit=20)
        messages: list[ChatMessage] = []
        for item in reversed(history):  # stored newest first
            if item.get("type") == "user":
                messages.append(ChatMessage(role="user", content=item.get("message", "")))
            elif item.get("type") == "assistant":
                messages.append(ChatMessage(role="assistant", content=item.get("message", "")))

        if not messages or messages[-1].role != "user":
            messages.append(ChatMessage(role="user", content=event.get("message", "")))

        try:
            response_text = await self.slm.chat(messages)
        except Exception as exc:
            LOGGER.exception("SLM request failed")
            response_text = "I encountered an error while generating a reply."
            await self.store.append_event(
                session_id,
                {
                    "type": "error",
                    "event_id": str(uuid.uuid4()),
                    "details": str(exc),
                },
            )

        response_event = {
            "event_id": str(uuid.uuid4()),
            "session_id": session_id,
            "persona_id": event.get("persona_id"),
            "role": "assistant",
            "message": response_text,
            "metadata": {"source": "slm"},
        }

        await self.store.append_event(session_id, {"type": "assistant", **response_event})
        await self.bus.publish(self.settings["outbound"], response_event)


async def main() -> None:
    worker = ConversationWorker()
    try:
        await worker.start()
    finally:
        await worker.slm.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        LOGGER.info("Conversation worker stopped")
