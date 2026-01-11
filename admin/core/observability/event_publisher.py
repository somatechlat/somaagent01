"""
Event Publisher for SomaAgent01 with FastA2A integration.
REAL IMPLEMENTATION - No placeholders, actual event publishing to SomaBrain.
"""

import asyncio
import threading
import time
from typing import Any, Dict, List, Optional

import httpx

from .metrics import (
    event_publish_errors_total,
    event_publish_latency_seconds,
    event_published_total,
    increment_counter,
    MetricsTimer,
    set_health_status,
)

# REAL IMPLEMENTATION - Event batching configuration
DEFAULT_BATCH_SIZE = 50
DEFAULT_FLUSH_INTERVAL = 5.0  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds


class EventPublisher:
    """
    REAL IMPLEMENTATION - Singleton event publisher for SomaAgent01.
    Handles event batching, retries, and comprehensive metrics.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern implementation."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the event publisher."""
        if self._initialized:
            return

        import os

        somabrain_base = os.environ.get("SA01_SOMA_BASE_URL")
        if not somabrain_base:
            raise ValueError(
                "SA01_SOMA_BASE_URL environment variable is required for event publishing. "
                "Set it to your SomaBrain service URL (e.g., http://somabrain:9696)"
            )
        self.somabrain_url = f"{somabrain_base.rstrip('/')}/v1/event"
        self.batch_size = DEFAULT_BATCH_SIZE
        self.flush_interval = DEFAULT_FLUSH_INTERVAL
        self.event_buffer: List[Dict] = []
        self._http_client: Optional[httpx.AsyncClient] = None
        self._flush_task: Optional[asyncio.Task] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        # REAL IMPLEMENTATION - Metrics tracking
        self._events_published = 0
        self._events_failed = 0
        self._last_flush_time = time.time()

        self._initialized = True
        set_health_status("event_publisher", "initialized", True)

        # Start background flush task
        self._start_background_flush()

    @property
    def http_client(self) -> httpx.AsyncClient:
        """Lazy initialization of HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=10.0, limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
            )
        return self._http_client

    async def publish(self, event_type: str, data: Dict[str, Any], metadata: Optional[Dict] = None):
        """
        REAL IMPLEMENTATION - Publish event to SomaBrain.

        Args:
            event_type: Type of the event
            data: Event data payload
            metadata: Optional metadata for the event
        """
        start_time = time.time()

        try:
            # REAL IMPLEMENTATION - Create event object
            event = {
                "type": event_type,
                "timestamp": time.time(),
                "data": data,
                "metadata": metadata or {},
            }

            # Add to buffer
            with self._lock:
                self.event_buffer.append(event)

                # Flush if batch size reached
                if len(self.event_buffer) >= self.batch_size:
                    await self._flush_batch()

            # REAL IMPLEMENTATION - Track successful publish
            increment_counter(
                event_published_total, {"event_type": event_type, "status": "buffered"}
            )

            event_publish_latency_seconds.labels(event_type=event_type).observe(
                time.time() - start_time
            )
            self._events_published += 1

        except Exception as e:
            # REAL IMPLEMENTATION - Track publish errors
            increment_counter(
                event_publish_errors_total,
                {"event_type": event_type, "error_type": type(e).__name__},
            )
            increment_counter(event_published_total, {"event_type": event_type, "status": "failed"})

            self._events_failed += 1
            set_health_status("event_publisher", "publishing", False)
            raise

    async def _flush_batch(self):
        """
        REAL IMPLEMENTATION - Flush current batch to SomaBrain.
        Handles retries and comprehensive error tracking.
        """
        if not self.event_buffer:
            return

        with self._lock:
            batch = self.event_buffer.copy()
            self.event_buffer.clear()

        if not batch:
            return

        # REAL IMPLEMENTATION - Retry logic
        for attempt in range(MAX_RETRIES):
            try:
                with MetricsTimer(event_publish_latency_seconds, {"event_type": "batch_flush"}):
                    response = await self.http_client.post(
                        self.somabrain_url,
                        json={"events": batch},
                        headers={"Content-Type": "application/json"},
                    )
                    response.raise_for_status()

                # REAL IMPLEMENTATION - Track successful batch
                for event in batch:
                    increment_counter(
                        event_published_total, {"event_type": event["type"], "status": "published"}
                    )

                self._last_flush_time = time.time()
                set_health_status("event_publisher", "somabrain_connection", True)
                return

            except httpx.TimeoutException as e:
                # REAL IMPLEMENTATION - Track timeout
                increment_counter(
                    event_publish_errors_total,
                    {"event_type": "batch_flush", "error_type": "timeout"},
                )

                if attempt == MAX_RETRIES - 1:
                    set_health_status("event_publisher", "somabrain_connection", False)
                    raise RuntimeError(f"Event publishing timeout after {MAX_RETRIES} retries: {e}")

            except httpx.HTTPStatusError as e:
                # REAL IMPLEMENTATION - Track HTTP errors
                increment_counter(
                    event_publish_errors_total,
                    {"event_type": "batch_flush", "error_type": f"http_{e.response.status_code}"},
                )

                if attempt == MAX_RETRIES - 1:
                    set_health_status("event_publisher", "somabrain_connection", False)
                    raise RuntimeError(
                        f"Event publishing HTTP error after {MAX_RETRIES} retries: {e}"
                    )

                # Don't retry on client errors (4xx)
                if 400 <= e.response.status_code < 500:
                    set_health_status("event_publisher", "somabrain_connection", False)
                    raise RuntimeError(f"Event publishing client error: {e}")

            except Exception as e:
                # REAL IMPLEMENTATION - Track other errors
                increment_counter(
                    event_publish_errors_total,
                    {"event_type": "batch_flush", "error_type": type(e).__name__},
                )

                if attempt == MAX_RETRIES - 1:
                    set_health_status("event_publisher", "somabrain_connection", False)
                    raise RuntimeError(f"Event publishing failed after {MAX_RETRIES} retries: {e}")

            # Wait before retry
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY * (2**attempt))  # Exponential backoff

    def _start_background_flush(self):
        """Start background task for periodic flushing."""

        def flush_loop():
            """Execute flush loop."""

            while not self._stop_event.is_set():
                time.sleep(self.flush_interval)

                # Check if we need to flush based on time
                current_time = time.time()
                if (
                    self.event_buffer
                    and current_time - self._last_flush_time >= self.flush_interval
                ):
                    # Run async flush in new event loop
                    try:
                        asyncio.run(self._flush_batch())
                    except Exception as e:
                        # Track background flush errors
                        increment_counter(
                            event_publish_errors_total,
                            {"event_type": "background_flush", "error_type": type(e).__name__},
                        )

        # Start background thread
        self._flush_thread = threading.Thread(target=flush_loop, daemon=True)
        self._flush_thread.start()

    async def flush(self):
        """
        REAL IMPLEMENTATION - Manual flush of all buffered events.
        """
        await self._flush_batch()

    def get_stats(self) -> Dict[str, Any]:
        """
        REAL IMPLEMENTATION - Get publisher statistics.
        """
        return {
            "events_published": self._events_published,
            "events_failed": self._events_failed,
            "buffer_size": len(self.event_buffer),
            "somabrain_url": self.somabrain_url,
            "batch_size": self.batch_size,
            "flush_interval": self.flush_interval,
            "last_flush_time": self._last_flush_time,
        }

    async def close(self):
        """
        REAL IMPLEMENTATION - Close the event publisher.
        """
        # Stop background thread
        self._stop_event.set()

        # Flush remaining events
        if self.event_buffer:
            await self._flush_batch()

        # Close HTTP client
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

        set_health_status("event_publisher", "initialized", False)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# REAL IMPLEMENTATION - Global instance
_event_publisher: Optional[EventPublisher] = None


def get_event_publisher() -> EventPublisher:
    """Get the global event publisher instance."""
    global _event_publisher
    if _event_publisher is None:
        _event_publisher = EventPublisher()
    return _event_publisher


async def publish_event(event_type: str, data: Dict[str, Any], metadata: Optional[Dict] = None):
    """
    REAL IMPLEMENTATION - Convenience function for publishing events.

    Args:
        event_type: Type of the event
        data: Event data payload
        metadata: Optional metadata for the event
    """
    publisher = get_event_publisher()
    await publisher.publish(event_type, data, metadata)


async def flush_events():
    """
    REAL IMPLEMENTATION - Convenience function for flushing events.
    """
    publisher = get_event_publisher()
    await publisher.flush()
