"""Conversation Sensor.

VIBE COMPLIANT - Django ORM + ZDL pattern.
Captures every message in/out for cognitive learning.

PhD Dev: This is the agent's working memory sensor.
"""

from __future__ import annotations

import logging
from typing import Any

from admin.core.sensors.base import BaseSensor

logger = logging.getLogger(__name__)


class ConversationSensor(BaseSensor):
    """Sensor for conversation events.

    Captures:
    - Message received (user input)
    - Message sent (agent output)
    - Conversation start/end
    - Context updates
    """

    SENSOR_NAME = "conversation"
    TARGET_SERVICE = "somabrain"

    def on_event(self, event_type: str, data: Any) -> None:
        """Handle conversation events."""
        self.capture(event_type, data if isinstance(data, dict) else {"data": data})

    def message_received(
        self,
        message: str,
        conversation_id: str,
        metadata: dict = None,
    ) -> None:
        """Capture incoming user message."""
        self.capture(
            "message.received",
            {
                "conversation_id": conversation_id,
                "role": "user",
                "content": message,
                "metadata": metadata or {},
            },
        )

    def message_sent(
        self,
        message: str,
        conversation_id: str,
        thoughts: list = None,
        latency_ms: float = 0.0,
        metadata: dict = None,
    ) -> None:
        """Capture outgoing agent message."""
        self.capture(
            "message.sent",
            {
                "conversation_id": conversation_id,
                "role": "assistant",
                "content": message,
                "thoughts": thoughts or [],
                "latency_ms": latency_ms,
                "metadata": metadata or {},
            },
        )

    def conversation_start(
        self,
        conversation_id: str,
        context: dict = None,
    ) -> None:
        """Capture conversation start."""
        self.capture(
            "start",
            {
                "conversation_id": conversation_id,
                "context": context or {},
            },
        )

    def conversation_end(
        self,
        conversation_id: str,
        turn_count: int = 0,
        duration_seconds: float = 0.0,
    ) -> None:
        """Capture conversation end."""
        self.capture(
            "end",
            {
                "conversation_id": conversation_id,
                "turn_count": turn_count,
                "duration_seconds": duration_seconds,
            },
        )
