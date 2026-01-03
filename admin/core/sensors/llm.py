"""LLM Sensor.

VIBE COMPLIANT - Django ORM + ZDL pattern.
Captures every LLM completion for cognitive learning.

PhD Dev: This IS thinking. Prompt + response = reasoning trace.
"""

from __future__ import annotations

import logging
from typing import Any

from admin.core.sensors.base import BaseSensor

logger = logging.getLogger(__name__)


class LLMSensor(BaseSensor):
    """Sensor for LLM operations.

    Captures:
    - Completions (prompt + response)
    - Token usage
    - Model selection
    - Errors and fallbacks
    """

    SENSOR_NAME = "llm"
    TARGET_SERVICE = "flink"  # Goes to Flink for analytics

    def on_event(self, event_type: str, data: Any) -> None:
        """Handle LLM events."""
        self.capture(event_type, data if isinstance(data, dict) else {"data": data})

    def completion(
        self,
        prompt: str,
        response: str,
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        latency_ms: float = 0.0,
        cost: float = 0.0,
        metadata: dict = None,
    ) -> None:
        """Capture LLM completion."""
        self.capture(
            "completion",
            {
                "prompt": prompt[:1000],  # Truncate for storage
                "response": response[:2000],  # Truncate for storage
                "model": model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "latency_ms": latency_ms,
                "cost": cost,
                "metadata": metadata or {},
            },
        )

    def embedding(
        self,
        text: str,
        model: str,
        dimensions: int = 0,
        tokens: int = 0,
        latency_ms: float = 0.0,
    ) -> None:
        """Capture embedding generation."""
        self.capture(
            "embedding",
            {
                "text_length": len(text),
                "model": model,
                "dimensions": dimensions,
                "tokens": tokens,
                "latency_ms": latency_ms,
            },
        )

    def error(
        self,
        model: str,
        error_type: str,
        error_message: str,
        fallback_model: str = None,
    ) -> None:
        """Capture LLM error and fallback."""
        self.capture(
            "error",
            {
                "model": model,
                "error_type": error_type,
                "error_message": error_message,
                "fallback_model": fallback_model,
            },
        )

    def model_switch(
        self,
        from_model: str,
        to_model: str,
        reason: str,
    ) -> None:
        """Capture model switch (degradation/upgrade)."""
        self.capture(
            "model_switch",
            {
                "from_model": from_model,
                "to_model": to_model,
                "reason": reason,
            },
        )
