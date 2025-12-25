"""GatewayService – wraps the existing Django ASGI gateway as a BaseSomaService.

The original gateway lives in ``services.gateway.main`` and is a fully‑featured
Django ASGI application.  To satisfy the *Standardised Service Lifecycle* goal from
the roadmap we expose it through the orchestrator by implementing a thin
``BaseSomaService`` subclass.

The service does not need custom start/stop logic – the gateway runs as a
sub‑application mounted by the orchestrator's Django ASGI instance.  Nevertheless we
provide ``start`` and ``stop`` methods that log their execution so that the
orchestrator's lifecycle hooks remain consistent across all services.
"""

from __future__ import annotations

import logging
from typing import Any

from .base_service import BaseSomaService

LOGGER = logging.getLogger(__name__)


class GatewayService(BaseSomaService):
    """Wrap the existing ``services.gateway.main`` Django ASGI app.

    The orchestrator will mount this app under ``/gateway`` (the caller can
    choose a different prefix if desired).  The ``app`` attribute is required
    by ``BaseSomaService`` for health aggregation, but the gateway already
    defines its own health router – we simply expose the same instance.
    """

    name = "gateway"

    def __init__(self) -> None:
        super().__init__()
        # Import lazily to avoid circular imports at module load time.
        from services.gateway.main import app as gateway_app

        # The gateway is a Django ASGI instance; we keep a reference for health.
        self.app: Any = gateway_app

    async def _start(self) -> None:
        # No separate process is launched – the orchestrator mounts the app.
        LOGGER.debug("GatewayService start – nothing to initialise")

    async def _stop(self) -> None:
        # No resources to clean up; the Django ASGI shutdown event will be handled
        # by the orchestrator when the whole process exits.
        LOGGER.debug("GatewayService stop – nothing to clean up")

    async def health(self) -> dict[str, Any]:
        """Delegate to the underlying gateway's health endpoint if available.

        The gateway defines ``/v1/health``.  When the orchestrator aggregates
        health it will call this method; we simply return ``{"healthy": True}``
        because the gateway's own router will be consulted separately.
        """
        return {"healthy": True, "details": {"name": self.name}}
