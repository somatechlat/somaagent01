"""Base class for services managed by the orchestrator.

Every concrete service (gateway, conversation worker, tool executor, etc.)
should inherit from :class:`BaseSomaService` and implement the ``_start``
and ``_stop`` async hooks.  The base class provides a simple ``health``
implementation that reports ``healthy`` when the service has been started.
"""

from __future__ import annotations

# Restored core BaseSomaService implementation (used throughout the project).
import asyncio
import contextvars
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

from admin.core.observability.tracing import get_tracer

LOGGER = logging.getLogger("orchestrator.base_service")

# Context variable to hold the current OpenTelemetry span for nesting.
current_span: contextvars.ContextVar = contextvars.ContextVar("current_span", default=None)


class BaseSomaService(ABC):
    """Abstract service with a deterministic lifecycle.

    Sub‑classes must define a ``name`` attribute and implement ``_start`` and
    ``_stop``. The orchestrator calls ``start`` during startup and ``stop``
    during graceful shutdown.
    """

    #: Human readable name – must be overridden by subclasses.
    name: str

    def __init__(self) -> None:
        """Initialize the instance."""

        self._running = asyncio.Event()

    # ------------------------------------------------------------------
    # Lifecycle hooks – concrete services implement the real work.
    # ------------------------------------------------------------------
    @abstractmethod
    async def _start(self) -> None:
        """Initialize resources (DB connections, background tasks, …)."""
        ...

    @abstractmethod
    async def _stop(self) -> None:
        """Clean up resources and stop background tasks."""
        ...

    # ------------------------------------------------------------------
    # Public API used by the orchestrator.
    # ------------------------------------------------------------------
    async def start(self) -> None:
        """Execute start."""

        tracer = get_tracer()
        with tracer.start_as_current_span(f"{self.name}.start") as span:
            current_span.set(span)
            LOGGER.info("Starting %s", getattr(self, "name", self.__class__.__name__))
            await self._start()
            self._running.set()
            LOGGER.info("%s started", getattr(self, "name", self.__class__.__name__))

    async def stop(self) -> None:
        """Execute stop."""

        tracer = get_tracer()
        with tracer.start_as_current_span(f"{self.name}.stop") as span:
            current_span.set(span)
            LOGGER.info("Stopping %s", getattr(self, "name", self.__class__.__name__))
            await self._stop()
            self._running.clear()
            LOGGER.info("%s stopped", getattr(self, "name", self.__class__.__name__))

    async def health(self) -> Dict[str, Any]:
        """Return a health dictionary.

        The default implementation reports ``healthy`` based on the internal
        ``_running`` flag. Services can override this method for deeper checks.
        """
        return {
            "healthy": self._running.is_set(),
            "details": {"name": getattr(self, "name", self.__class__.__name__)},
        }

    async def register_metrics(self) -> None:
        """Hook for Prometheus metrics – optional for a concrete service."""
        return None


# Alias for existing imports.
BaseService = BaseSomaService
