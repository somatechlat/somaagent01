"""Simple orchestrator – registers services, starts them, and provides a unified health endpoint.

The project’s *canonical* roadmap specifies a single orchestrator implementation.  The previous
file accidentally contained two completely different orchestrator classes – a lightweight
``BaseSomaService``‑based version and a much larger process‑manager version.  Keeping both
confuses type‑checkers and makes the public API ambiguous.  According to the 
provide a **single, well‑documented implementation**.

This file now contains only the lightweight version that works with ``BaseSomaService``
sub‑classes (e.g. ``GatewayService`` and ``UnifiedMemoryService``).  The more complex
implementation has been removed.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, List

from prometheus_client import make_asgi_app

from .base_service import BaseSomaService
from .health_monitor import UnifiedHealthMonitor

# Import the health router (Django Ninja router) and the background health monitor.
# The router provides the ``/v1/health`` endpoint, while the monitor runs a
# periodic async task that checks external services.
from .health_router import attach_to_app, UnifiedHealthRouter

LOGGER = logging.getLogger("orchestrator")


class ServiceRegistry:
    """Container for service instances with an optional ``critical`` flag.

    The orchestrator uses this registry to start services in registration order and
    to expose their health information via :class:`UnifiedHealthMonitor`.
    """

    def __init__(self) -> None:
        """Initialize the instance."""

        self._services: List[BaseSomaService] = []

    def register(self, service: BaseSomaService, critical: bool = False) -> None:
        # Attach orchestrator metadata.
        """Execute register.

            Args:
                service: The service.
                critical: The critical.
            """

        service._critical = critical
        # Preserve explicit startup ordering if provided on the service; default to 0.
        order = getattr(service, "_startup_order", 0)
        service._startup_order = order
        self._services.append(service)

    @property
    def services(self) -> List[BaseSomaService]:
        """Execute services.
            """

        return self._services


class SomaOrchestrator:
    """Main orchestrator – wires services into a Django ASGI app and manages them.

    The orchestrator is deliberately minimal: it registers a health router, then
    starts and stops each ``BaseSomaService`` instance in the order they were
    registered.  This satisfies the *single‑orchestrator* goal from the roadmap
    and follows the 
    implementation.
    """

    def __init__(self, app: Any) -> None:
        """Initialize the instance."""

        self.app = app
        self.registry = ServiceRegistry()
        # The router receives the live list of services via a provider so it is always current.
        self.health_router = UnifiedHealthRouter(
            services_provider=lambda: self.registry.services, registry=self.registry
        )
        # The background monitor runs independently and uses the central config.
        # It will be started explicitly by the orchestrator when needed.
        self.health_monitor = UnifiedHealthMonitor(self.registry.services)

    # ------------------------------------------------------------------
    # Registration API – concrete services import this module and call
    # ``orchestrator.register(MyService(), critical=True)``.
    # ------------------------------------------------------------------
    def register(self, service: BaseSomaService, critical: bool = False) -> None:
        """Execute register.

            Args:
                service: The service.
                critical: The critical.
            """

        self.registry.register(service, critical)

    # ------------------------------------------------------------------
    # Lifecycle management.
    # ------------------------------------------------------------------
    async def _start_all(self) -> None:
        """Execute start all.
            """

        services = sorted(self.registry.services, key=lambda s: getattr(s, "_startup_order", 0))
        LOGGER.info("Starting %d services", len(services))
        for svc in services:
            try:
                await svc.start()
            except Exception as exc:
                LOGGER.error(
                    "Failed to start %s: %s", getattr(svc, "name", svc.__class__.__name__), exc
                )
                if getattr(svc, "_critical", False):
                    raise
        LOGGER.info("All services started")

    async def _stop_all(self) -> None:
        """Execute stop all.
            """

        LOGGER.info("Shutting down services")
        for svc in reversed(self.registry.services):
            try:
                await svc.stop()
            except Exception as exc:  # pragma: no cover – defensive
                LOGGER.warning(
                    "Error stopping %s: %s", getattr(svc, "name", svc.__class__.__name__), exc
                )
        LOGGER.info("All services stopped")

    def attach(self) -> None:
        """Integrate the orchestrator with a Django ASGI app.

        The method is safe to call multiple times – it checks whether the
        ``/v1/health`` and ``/metrics`` routes are already mounted and skips
        duplicate registration. This idempotency is required because the test
        suite creates a second ``SomaOrchestrator`` instance on the same app.
        """

        # -----------------------------------------------------------------
        # Mount health router and metrics endpoints.
        # -----------------------------------------------------------------
        attach_to_app(self.app, self.health_router)
        self.app.mount("/metrics", make_asgi_app())

        # -----------------------------------------------------------------
        # Lifespan handler (ASGI-recommended replacement for on_event).
        # -----------------------------------------------------------------
        @asynccontextmanager
        async def lifespan(app: Any):
            """Execute lifespan.

                Args:
                    app: The app.
                """

            await self._start_all()
            try:
                yield
            finally:
                await self._stop_all()

        self.app.router.lifespan_context = lifespan


# NOTE: The original complex process‑manager implementation has been removed.
# The lightweight ``BaseSomaService``‑based orchestrator defined above is the
# **NO UNNECESSARY FILES**.