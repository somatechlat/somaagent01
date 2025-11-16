"""Gateway service based on BaseService for orchestrator integration.

This service inherits from BaseService to be managed by the orchestrator.
It provides the same HTTP API as the original standalone gateway.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict

from fastapi import FastAPI, Request

from orchestrator.base_service import BaseService
from orchestrator.config import CentralizedConfig

# Import the main gateway module to access its functionality
import services.gateway.main as gateway_module

# LOGGER configuration
LOGGER = logging.getLogger(__name__)


class GatewayService(BaseService):
    """Gateway service that inherits from BaseService for orchestrator integration."""

    service_name: str = "gateway"

    def __init__(self, config: CentralizedConfig | None = None) -> None:
        # Initialize BaseService
        super().__init__(config)
        
        # We'll copy the routes from the existing gateway app
        # This maintains backward compatibility while integrating with orchestrator

    async def startup(self) -> None:
        """Initialize gateway service and all its dependencies."""
        LOGGER.info(f"Starting {self.service_name} service")
        
        # Initialize all the stores and services that the original gateway needs
        # These are normally initialized in the original gateway's startup events
        
        # Import the necessary startup functions from the original gateway
        try:
            from .main import (
                get_event_bus,
                get_publisher,
                get_session_cache,
                get_session_store,
                get_audit_store,
                get_api_key_store,
                get_dlq_store,
                get_replica_store,
                get_export_job_store,
                get_secret_manager,
                get_ui_settings_store,
                get_attachments_store,
                PROFILE_STORE,
                CATALOG_STORE,
                TELEMETRY_STORE,
                REQUEUE_STORE,
                _start_metrics_server,
                start_background_services,
            )
            
            # Start the background services
            await start_background_services()
            
            # Start metrics server (this is a sync function)
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
            if hasattr(gateway_app, 'state') and hasattr(gateway_app.state, 'http_client'):
                await gateway_app.state.http_client.aclose()
            
            # Clean up other resources as needed
            LOGGER.info(f"{self.service_name} service shutdown completed")
            
        except Exception as exc:
            LOGGER.error(f"Error during {self.service_name} service shutdown: {exc}")

    def register_routes(self, app: FastAPI) -> None:
        """Register all gateway routes with the provided FastAPI app."""
        
        # Import the main gateway app from the module
        from .main import app as gateway_app
        
        # Include all routes from the gateway app
        # Mount the entire gateway app under /v1 prefix to avoid conflicts
        app.mount("/v1", gateway_app)
        
        # Add a health check endpoint for the orchestrator
        @app.get("/health")
        async def health_check():
            return {"status": "healthy", "service": self.service_name}
        
        LOGGER.info(f"Mounted gateway app for {self.service_name} service")

    def as_dict(self) -> Dict[str, Any]:
        """Return a serialisable representation of the gateway service."""
        base_info = super().as_dict()
        base_info.update({
            "port": self.config.gateway_port,
            "host": self.config.gateway_host,
            "api_version": "v1",
            "endpoints": len(gateway_app.routes),
        })
        return base_info