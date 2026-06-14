"""Shared utilities for the WebSocket chat consumer."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from asgiref.sync import sync_to_async

from services.common.unified_metrics import UnifiedMetrics

logger = logging.getLogger(__name__)

# Initialize metrics singleton on module load
_metrics = UnifiedMetrics.get_instance()

# Metric shortcuts for backwards compatibility
WS_CONNECTIONS = _metrics.WEBSOCKET_CONNECTIONS
WS_MESSAGES = _metrics.WEBSOCKET_MESSAGES
WS_LATENCY = _metrics.WEBSOCKET_MESSAGE_LATENCY


@dataclass
class WSMessage:
    """WebSocket message structure."""

    type: str
    payload: dict
    id: str = ""
    timestamp: str = ""

    def __post_init__(self):
        """Execute post init."""

        if not self.id:
            self.id = str(uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        """Execute to dict."""

        return {
            "type": self.type,
            "id": self.id,
            "timestamp": self.timestamp,
            "payload": self.payload,
        }


# Message types
MSG_CHAT = "chat.message"
MSG_CHAT_SEND = "chat.send"
MSG_CHAT_LEGACY = "chat"
MSG_CHAT_RESPONSE = "chat.message"
MSG_CHAT_DELTA = "chat.delta"
MSG_CHAT_DONE = "chat.done"
MSG_TITLE_UPDATE = "title_update"
MSG_ERROR = "error"
MSG_PING = "ping"
MSG_PONG = "pong"
MSG_CONNECTED = "connected"
MSG_TYPING = "typing"
MSG_FEEDBACK = "feedback"


class ChatUtilsMixin:
    """Utility helpers for ChatConsumer."""

    async def _preload_context(self):
        """Pre-warm context in background while user is typing.

        Fetches conversation history and relevant memories so they are
        ready when the first message arrives.
        """
        try:
            if not self.conversation_id:
                return

            # Fetch last 20 messages from PostgreSQL
            from admin.chat.models import Message as MessageModel

            @sync_to_async
            def _load_history():
                qs = MessageModel.objects.filter(
                    conversation_id=self.conversation_id
                ).order_by("-created_at")[:20]
                return [
                    {"role": m.role, "content": getattr(m, "content", None) or ""}
                    for m in reversed(list(qs))
                ]

            self._cached_history = await _load_history()

            # Fetch memories from SomaBrain (best effort)
            if self.capsule:
                from admin.core.somabrain_client import SomaBrainClient

                brain_client = await SomaBrainClient.get_async()
                if brain_client:
                    try:
                        mp = self.capsule.memory_pointer or {}
                        memories = await brain_client.recall(
                            query="",
                            top_k=mp.get("recall_limit", 10),
                            tenant=mp.get("tenant", self.tenant_id or "default"),
                            namespace=mp.get("namespace", "chat_history"),
                        )
                        self._cached_memory = memories or []
                    except Exception as exc:
                        logger.debug("Pre-warm memory recall failed: %s", exc)
        except Exception as exc:
            logger.debug("Context pre-warm failed: %s", exc)

    async def _send_error(self, message: str, code: str = "error"):
        """Send error message."""
        await self.send_json(
            WSMessage(
                type=MSG_ERROR,
                payload={
                    "code": code,
                    "message": message,
                },
            ).to_dict()
        )
        _metrics.WEBSOCKET_MESSAGES.labels(direction="outbound", type=MSG_ERROR).inc()

    async def _heartbeat_loop(self):
        """Send periodic heartbeat pings.

        Per design.md Section 7.1:
        - Ping every 30 seconds
        - Detect stale connections
        """
        while True:
            try:
                await asyncio.sleep(self.HEARTBEAT_INTERVAL)

                # Don't send ping during streaming
                if not self.is_streaming:
                    await self.send_json(
                        WSMessage(
                            type=MSG_PING,
                            payload={"timestamp": datetime.now(timezone.utc).isoformat()},
                        ).to_dict()
                    )
                    _metrics.WEBSOCKET_MESSAGES.labels(direction="outbound", type=MSG_PING).inc()

            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Heartbeat error")
                break
