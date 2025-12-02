"""Gateway service based on BaseService for orchestrator integration.

This service inherits from BaseService to be managed by the orchestrator.
It provides the same HTTP API as the original standalone gateway.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import FastAPI

from orchestrator.base_service import BaseService
from orchestrator.config import CentralizedConfig

# Import the new chat router (absolute import from the src package)
from src.gateway.routers import (
    chat as chat_router,
    message as message_router,
    session as session_router,
    sse as sse_router,
)

# LOGGER configuration
LOGGER = logging.getLogger(__name__)


class GatewayService(BaseService):
    """Gateway service that inherits from BaseService for orchestrator integration."""

    service_name: str = "gateway"

    def __init__(self, config: CentralizedConfig | None = None) -> None:
        # Initialize BaseService
        super().__init__(config)

        # Store reference to gateway app for cleanup
        self._gateway_app = None

    async def startup(self) -> None:
        """Initialize gateway service and all its dependencies."""
        LOGGER.info(f"Starting {self.service_name} service")

        # Initialize all the stores and services that the original gateway needs
        # These are normally initialized in the original gateway's startup events

        try:
            # Import the main gateway app to access its state
            from .main import app as gateway_app

            self._gateway_app = gateway_app

            # Start the background services from the original gateway
            from .main import start_background_services

            await start_background_services()

            # Start metrics server (this is a sync function from original gateway)
            from .main import _start_metrics_server

            _start_metrics_server()

            LOGGER.info(f"{self.service_name} service startup completed")

        except Exception as exc:
            LOGGER.error(f"Failed to start {self.service_name} service: {exc}")
            raise

    async def shutdown(self) -> None:
        """Clean up gateway service resources."""
        LOGGER.info(f"Shutting down {self.service_name} service")

        # Clean up resources
        try:
            # Clean up HTTP client if it exists
            if (
                self._gateway_app
                and hasattr(self._gateway_app, "state")
                and hasattr(self._gateway_app.state, "http_client")
            ):
                await self._gateway_app.state.http_client.aclose()

            # Clean up other resources as needed
            LOGGER.info(f"{self.service_name} service shutdown completed")

        except Exception as exc:
            LOGGER.error(f"Error during {self.service_name} service shutdown: {exc}")

    def register_routes(self, app: FastAPI) -> None:
        """Register all gateway routes with the provided FastAPI app."""

        # Import the main gateway app from the module
        from .main import app as gateway_app

        # Include all routes from the original gateway app (legacy)
        # Mount the entire gateway app under /v1 – preserves backward compatibility
        app.mount("/v1", gateway_app)

        # Register the new routers – reachable under /v1/*
        app.include_router(chat_router.router)
        app.include_router(session_router.router)
        app.include_router(sse_router.router)
        app.include_router(message_router.router)

        # Add a health check endpoint for the orchestrator
        @app.get("/health")
        async def health_check():
            return {"status": "healthy", "service": self.service_name}

        LOGGER.info(f"Mounted gateway app for {self.service_name} service")

    def as_dict(self) -> Dict[str, Any]:
        """Return a serialisable representation of the gateway service.

        The legacy implementation accessed ``gateway_port`` and
        ``gateway_host`` attributes directly on the configuration.  With
        the new configuration model these values are available under the
        ``service`` model.  The method now uses ``self.config.service`` to
        maintain compatibility.
        """
        base_info = super().as_dict()
        base_info.update(
            {
                "port": self.config.service.port,
                "host": self.config.service.host,
                "api_version": "v1",
                "endpoints": len(self._gateway_app.routes) if self._gateway_app else 0,
            }
        )
        return base_info
