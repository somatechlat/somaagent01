"""Memory Sensor.

VIBE COMPLIANT - Django ORM + ZDL pattern.
Captures every memory operation for cognitive learning.

PhD Dev: This IS learning. Every remember/recall shapes future behavior.
"""

from __future__ import annotations

import logging
from typing import Any

from admin.core.sensors.base import BaseSensor

logger = logging.getLogger(__name__)


class MemorySensor(BaseSensor):
    """Sensor for memory operations.

    Captures:
    - Memory creation (remember)
    - Memory recall (search)
    - Memory consolidation (sleep)
    - Memory deletion (forget)
    """

    SENSOR_NAME = "memory"
    TARGET_SERVICE = "somabrain"

    def on_event(self, event_type: str, data: Any) -> None:
        """Handle memory events."""
        self.capture(event_type, data if isinstance(data, dict) else {"data": data})

    def remember(
        self,
        content: str,
        memory_type: str = "episodic",
        importance: float = 0.5,
        metadata: dict = None,
    ) -> None:
        """Capture memory creation."""
        self.capture(
            "create",
            {
                "content": content,
                "memory_type": memory_type,
                "importance": importance,
                "metadata": metadata or {},
            },
        )

    def recall(
        self,
        query: str,
        results_count: int = 0,
        top_score: float = 0.0,
        latency_ms: float = 0.0,
        metadata: dict = None,
    ) -> None:
        """Capture memory recall/search."""
        self.capture(
            "recall",
            {
                "query": query,
                "results_count": results_count,
                "top_score": top_score,
                "latency_ms": latency_ms,
                "metadata": metadata or {},
            },
        )

    def consolidate(
        self,
        memories_processed: int = 0,
        memories_pruned: int = 0,
        duration_seconds: float = 0.0,
    ) -> None:
        """Capture memory consolidation (during sleep)."""
        self.capture(
            "consolidate",
            {
                "memories_processed": memories_processed,
                "memories_pruned": memories_pruned,
                "duration_seconds": duration_seconds,
            },
        )

    def forget(
        self,
        memory_id: str,
        reason: str = "explicit",
    ) -> None:
        """Capture memory deletion."""
        self.capture(
            "delete",
            {
                "memory_id": memory_id,
                "reason": reason,
            },
        )
