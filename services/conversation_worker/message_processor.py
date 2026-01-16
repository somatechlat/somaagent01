"""Message processing for conversation worker."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

from prometheus_client import Counter, Histogram

LOGGER = logging.getLogger(__name__)

# Metrics
MESSAGE_PROCESSING_COUNTER = Counter(
    "conversation_worker_messages_total",
    "Total number of conversation events processed",
    labelnames=("result",),
)
MESSAGE_LATENCY = Histogram(
    "conversation_worker_processing_seconds",
    "Time spent handling conversation events",
    labelnames=("path",),
)


class MessageProcessor:
    """Process incoming conversation messages."""

    def __init__(self, worker: Any):
        """Initialize the instance."""

        self.worker = worker

    async def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single conversation message.

        Args:
            message: The message payload to process

        Returns:
            Response payload or None
        """
        start_time = time.time()
        path = message.get("type", "unknown")

        try:
            # Validate message
            if not self._validate_message(message):
                MESSAGE_PROCESSING_COUNTER.labels(result="invalid").inc()
                return {"error": "Invalid message format"}

            # Route to appropriate handler
            result = await self._route_message(message)

            MESSAGE_PROCESSING_COUNTER.labels(result="success").inc()
            MESSAGE_LATENCY.labels(path=path).observe(time.time() - start_time)

            return result

        except Exception as e:
            LOGGER.error(f"Error processing message: {e}")
            MESSAGE_PROCESSING_COUNTER.labels(result="error").inc()
            MESSAGE_LATENCY.labels(path=path).observe(time.time() - start_time)
            return {"error": str(e)}

    def _validate_message(self, message: Dict[str, Any]) -> bool:
        """Validate message structure.

        Args:
            message: The message to validate

        Returns:
            True if valid
        """
        required_fields = ["type", "session_id"]
        return all(field in message for field in required_fields)

    async def _route_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Route message to appropriate handler.

        Args:
            message: The message to route

        Returns:
            Handler result
        """
        msg_type = message.get("type", "")

        handlers = {
            "chat": self._handle_chat,
            "tool_result": self._handle_tool_result,
            "feedback": self._handle_feedback,
            "context_update": self._handle_context_update,
        }

        handler = handlers.get(msg_type)
        if handler:
            return await handler(message)

        LOGGER.warning(f"Unknown message type: {msg_type}")
        return None

    async def _handle_chat(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle chat message."""
        # Delegate to worker's chat handling
        return await self.worker.handle_chat_message(message)

    async def _handle_tool_result(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool result message."""
        return await self.worker.handle_tool_result(message)

    async def _handle_feedback(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle feedback message."""
        return await self.worker.handle_feedback(message)

    async def _handle_context_update(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle context update message."""
        return await self.worker.handle_context_update(message)
