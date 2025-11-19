"""Simple orchestrator – registers services, starts them, and provides a unified health endpoint.

The project’s *canonical* roadmap specifies a single orchestrator implementation.  The previous
file accidentally contained two completely different orchestrator classes – a lightweight
``BaseSomaService``‑based version and a much larger process‑manager version.  Keeping both
confuses type‑checkers and makes the public API ambiguous.  According to the VIBE rules we must
provide a **single, well‑documented implementation**.

This file now contains only the lightweight version that works with ``BaseSomaService``
sub‑classes (e.g. ``GatewayService`` and ``UnifiedMemoryService``).  The more complex
implementation has been removed.
"""

from __future__ import annotations

import logging
from typing import List

from fastapi import FastAPI

from .base_service import BaseSomaService
from .health_monitor import UnifiedHealthMonitor, attach_to_app
from prometheus_client import make_asgi_app

LOGGER = logging.getLogger("orchestrator")


class ServiceRegistry:
    """Container for service instances with an optional ``critical`` flag.

    The orchestrator uses this registry to start services in registration order and
    to expose their health information via :class:`UnifiedHealthMonitor`.
    """

    def __init__(self) -> None:
        self._services: List[BaseSomaService] = []

    def register(self, service: BaseSomaService, critical: bool = False) -> None:
        # Attach a ``_critical`` attribute used by the orchestrator during startup.
        setattr(service, "_critical", critical)
        self._services.append(service)

    @property
    def services(self) -> List[BaseSomaService]:
        return self._services


class SomaOrchestrator:
    """Main orchestrator – wires services into a FastAPI app and manages them.

    The orchestrator is deliberately minimal: it registers a health router, then
    starts and stops each ``BaseSomaService`` instance in the order they were
    registered.  This satisfies the *single‑orchestrator* goal from the roadmap
    and follows the VIBE rule **NO UNNECESSARY FILES** – we keep only one
    implementation.
    """

    def __init__(self, app: FastAPI) -> None:
        self.app = app
        self.registry = ServiceRegistry()
        # The health monitor receives the live list of services from the registry.
        self.health_monitor = UnifiedHealthMonitor(self.registry.services)

    # ------------------------------------------------------------------
    # Registration API – concrete services import this module and call
    # ``orchestrator.register(MyService(), critical=True)``.
    # ------------------------------------------------------------------
    def register(self, service: BaseSomaService, critical: bool = False) -> None:
        self.registry.register(service, critical)

    # ------------------------------------------------------------------
    # Lifecycle management.
    # ------------------------------------------------------------------
    async def _start_all(self) -> None:
        LOGGER.info("Starting %d services", len(self.registry.services))
        for svc in self.registry.services:
            try:
                await svc.start()
            except Exception as exc:
                LOGGER.error("Failed to start %s: %s", getattr(svc, "name", svc.__class__.__name__), exc)
                if getattr(svc, "_critical", False):
                    raise
        LOGGER.info("All services started")

    async def _stop_all(self) -> None:
        LOGGER.info("Shutting down services")
        for svc in reversed(self.registry.services):
            try:
                await svc.stop()
            except Exception as exc:  # pragma: no cover – defensive
                LOGGER.warning("Error stopping %s: %s", getattr(svc, "name", svc.__class__.__name__), exc)
        LOGGER.info("All services stopped")

    def attach(self) -> None:
        """Hook the orchestrator into FastAPI lifecycle events and health router."""

        # Attach health endpoint before services start.
        attach_to_app(self.app, self.health_monitor)
        # Expose Prometheus metrics at /metrics using the shared registry.
        # ``make_asgi_app`` creates a lightweight ASGI app that serves the
        # ``/metrics`` endpoint.  Mounting it makes the metrics available on the
        # same host/port as the orchestrator, simplifying deployment and
        # adhering to the VIBE rule of keeping the system minimal.
        self.app.mount("/metrics", make_asgi_app())

        @self.app.on_event("startup")
        async def _startup() -> None:  # noqa: D401
            await self._start_all()

        @self.app.on_event("shutdown")
        async def _shutdown() -> None:  # noqa: D401
            await self._stop_all()
# NOTE: The original complex process‑manager implementation has been removed.
# The lightweight ``BaseSomaService``‑based orchestrator defined above is the
# single source of truth for the project, satisfying the VIBE rule
# **NO UNNECESSARY FILES**.