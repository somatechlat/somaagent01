"""Health monitoring for conversation worker."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict

from prometheus_client import Counter, Gauge

LOGGER = logging.getLogger(__name__)

# Metrics
SOMABRAIN_STATUS_GAUGE = Gauge(
    "conversation_worker_somabrain_status",
    "Current SomaBrain connectivity status for this worker (1=up, 0=down)",
)
SOMABRAIN_BUFFER_GAUGE = Gauge(
    "conversation_worker_somabrain_buffered_items",
    "Number of memory payloads buffered locally while SomaBrain is unavailable",
)
SESSION_CACHE_SYNC = Counter(
    "conversation_worker_session_cache_sync_total",
    "Conversation worker attempts to synchronise session cache entries",
    labelnames=("result",),
)


class HealthMonitor:
    """Monitor health of conversation worker dependencies."""

    def __init__(self):
        """Initialize the instance."""

        self._somabrain_healthy = True
        self._last_check = 0.0
        self._check_interval = 30.0  # seconds
        self._buffered_items = 0

    def set_somabrain_status(self, healthy: bool) -> None:
        """Update SomaBrain health status."""
        self._somabrain_healthy = healthy
        SOMABRAIN_STATUS_GAUGE.set(1 if healthy else 0)

    def set_buffered_items(self, count: int) -> None:
        """Update count of buffered memory items."""
        self._buffered_items = count
        SOMABRAIN_BUFFER_GAUGE.set(count)

    def record_cache_sync(self, success: bool) -> None:
        """Record a cache sync attempt."""
        SESSION_CACHE_SYNC.labels(result="success" if success else "error").inc()

    def is_healthy(self) -> bool:
        """Check if worker is healthy."""
        return self._somabrain_healthy

    def get_status(self) -> Dict[str, Any]:
        """Get current health status."""
        return {
            "somabrain_healthy": self._somabrain_healthy,
            "buffered_items": self._buffered_items,
            "last_check": self._last_check,
        }

    async def check_dependencies(self, soma_client: Any) -> bool:
        """Check health of all dependencies.

        Args:
            soma_client: SomaBrain client instance

        Returns:
            True if all dependencies are healthy
        """
        now = time.time()
        if now - self._last_check < self._check_interval:
            return self._somabrain_healthy

        self._last_check = now

        try:
            # Check SomaBrain connectivity
            await soma_client.health_check()
            self.set_somabrain_status(True)
            return True
        except Exception as e:
            LOGGER.warning(f"SomaBrain health check failed: {e}")
            self.set_somabrain_status(False)
            return False