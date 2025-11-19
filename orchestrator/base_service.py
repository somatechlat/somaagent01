"""Base class for services managed by the orchestrator.

Every concrete service (gateway, conversation worker, tool executor, etc.)
should inherit from :class:`BaseSomaService` and implement the ``_start``
and ``_stop`` async hooks.  The base class provides a simple ``health``
implementation that reports ``healthy`` when the service has been started.
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
import contextvars

# Import the global tracer (will be a no‑op if OTLP endpoint is not configured)
from observability.tracing import get_tracer

# Create a context variable to hold the current span for nesting
current_span: contextvars.ContextVar = contextvars.ContextVar("current_span", default=None)
from typing import Any, Dict

LOGGER = logging.getLogger("orchestrator.base_service")


class BaseSomaService(ABC):
    """Abstract service with a deterministic lifecycle.

    Sub‑classes must set a ``name`` attribute and implement ``_start`` and
    ``_stop``.  The orchestrator will call ``start`` during startup and ``stop``
    during graceful shutdown.
    """

    #: Human readable name – must be overridden by subclasses.
    name: str

    def __init__(self) -> None:
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
      tracer = get_tracer()
      # Start a span for the service start lifecycle event
      with tracer.start_as_current_span(f"{self.name}.start") as span:
        current_span.set(span)
        LOGGER.info("Starting %s", getattr(self, "name", self.__class__.__name__))
        await self._start()
        self._running.set()
        LOGGER.info("%s started", getattr(self, "name", self.__class__.__name__))

    async def stop(self) -> None:
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
        ``_running`` flag.  Services can override this method to perform deeper
        checks (e.g., DB ping).
        """
        return {
            "healthy": self._running.is_set(),
            "details": {"name": getattr(self, "name", self.__class__.__name__)},
        }

    async def register_metrics(self) -> None:
        """Hook for Prometheus metrics – optional for a concrete service."""
        return None
"""Abstract base class for services managed by the orchestrator.

The project follows the VIBE coding rules and the internal *Interaction
Coding Rules* which prescribe a clear naming scheme:

* All abstract service classes are prefixed with ``Base``.
* Concrete implementations inherit from ``BaseService`` and are named
  ``<Something>Service``.
* Each service owns its own ``FastAPI`` application that can be mounted by the
  orchestrator.

This file implements ``BaseService`` – an ``ABC`` that wires a FastAPI
instance into the typical FastAPI lifecycle (startup/shutdown) and provides
hooks for concrete services to register routes.
"""

from __future__ import annotations

import abc
from typing import Any, Dict

from fastapi import FastAPI

from .config import CentralizedConfig


class BaseService(abc.ABC):
  """Base class for all orchestrated services.

  Sub‑classes must implement :meth:`register_routes` to attach their HTTP
  endpoints to the ``FastAPI`` application.  The base class registers the
  standard ``startup`` and ``shutdown`` events so that services can perform
  asynchronous initialisation (e.g., database connections) and cleanup.
  """

  #: Human readable name used for logging and health checks.
  service_name: str = "base"

  def __init__(self, config: CentralizedConfig | None = None) -> None:
    # Resolve configuration – allow injection for testing.
    self.config: CentralizedConfig = config or CentralizedConfig()
    # Each service gets its own FastAPI instance – the orchestrator can
    # mount it under a prefix or expose it directly.
    self.app: FastAPI = FastAPI(title=self.service_name)
    # Register lifecycle hooks.
    self.app.add_event_handler("startup", self.startup)
    self.app.add_event_handler("shutdown", self.shutdown)
    # Let the concrete class add its own routes.
    self.register_routes(self.app)

  # ---------------------------------------------------------------------
  # Lifecycle hooks – concrete services may override these.
  # ---------------------------------------------------------------------
  async def startup(self) -> None:  # pragma: no cover – default does nothing
    """Hook called when the FastAPI app starts.

    Sub‑classes can perform async initialisation here (e.g., create DB
    pools).  The base implementation is a no‑op.
    """

  async def shutdown(self) -> None:  # pragma: no cover – default does nothing
    """Hook called when the FastAPI app is shutting down.

    Sub‑classes can clean up resources here.  The base implementation is
    a no‑op.
    """

  # ---------------------------------------------------------------------
  # Route registration – **must** be implemented by concrete services.
  # ---------------------------------------------------------------------
  @abc.abstractmethod
  def register_routes(self, app: FastAPI) -> None:
    """Attach HTTP endpoints to the provided ``FastAPI`` instance.

    The method should add routes, middlewares, exception handlers, etc.
    It is called during ``__init__`` after the lifecycle events have been
    attached.
    """

  # ---------------------------------------------------------------------
  # Helper utilities for concrete services.
  # ---------------------------------------------------------------------
  def as_dict(self) -> Dict[str, Any]:
    """Return a serialisable representation of the service configuration.

    This is useful for health‑check endpoints or for the orchestrator to
    expose a concise description of each registered service.
    """
    return {
      "service_name": self.service_name,
      "config": self.config.dict() if hasattr(self.config, "dict") else {},
    }
