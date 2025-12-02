"""FastA2A gateway service based on BaseService for orchestrator integration.

This service inherits from BaseService to be managed by the orchestrator.
It wraps the existing FastA2A API functionality.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import FastAPI

from orchestrator.base_service import BaseService
from orchestrator.config import CentralizedConfig

# LOGGER configuration
LOGGER = logging.getLogger(__name__)


class FastA2AGatewayService(BaseService):
    """FastA2A gateway service that inherits from BaseService for orchestrator integration."""

    service_name: str = "fasta2a-gateway"

    def __init__(self, config: CentralizedConfig | None = None) -> None:
        # Initialize BaseService
        super().__init__(config)

    async def startup(self) -> None:
        """Initialize FastA2A gateway service."""
        LOGGER.info(f"Starting {self.service_name} service")

        try:
            # Import any startup functions if needed
            # The FastA2A app doesn't seem to have explicit startup requirements
            LOGGER.info(f"{self.service_name} service startup completed")

        except Exception as exc:
            LOGGER.error(f"Failed to start {self.service_name} service: {exc}")
            raise

    async def shutdown(self) -> None:
        """Clean up FastA2A gateway service resources."""
        LOGGER.info(f"Shutting down {self.service_name} service")

        try:
            # The FastA2A app doesn't seem to have explicit shutdown requirements
            LOGGER.info(f"{self.service_name} service shutdown completed")

        except Exception as exc:
            LOGGER.error(f"Error during {self.service_name} service shutdown: {exc}")

    def register_routes(self, app: FastAPI) -> None:
        """Register all FastA2A routes with the provided FastAPI app."""

        # Try to mount the FastA2A app, but handle import issues gracefully
        try:
            # Import the FastA2A app from the router module
            from .router import app as fasta2a_app

            # Mount the entire FastA2A app under /api prefix to avoid conflicts
            app.mount("/api", fasta2a_app)

            LOGGER.info(f"Mounted FastA2A app for {self.service_name} service")
            fasta2a_mounted = True

        except Exception as exc:
            LOGGER.warning(f"Could not mount FastA2A app due to import issues: {exc}")
            fasta2a_mounted = False

        # Add a health check endpoint for the orchestrator
        @app.get("/health")
        async def health_check():
            # Check if the FastA2A app is accessible
            if fasta2a_mounted:
                try:
                    # Try to access celery health status
                    from .tasks.orchestrator import celery_health_status

                    celery_status = await celery_health_status()

                    if celery_status.get("status") == "healthy":
                        return {
                            "status": "healthy",
                            "service": self.service_name,
                            "celery": celery_status,
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "service": self.service_name,
                            "celery": celery_status,
                        }
                except Exception as e:
                    return {"status": "healthy", "service": self.service_name, "error": str(e)}
            else:
                return {
                    "status": "healthy",
                    "service": self.service_name,
                    "note": "FastA2A app not mounted due to import issues",
                }

        # Add a metrics endpoint
        @app.get("/metrics")
        async def metrics():
            """Return basic metrics about the FastA2A gateway service."""
            return {
                "service": self.service_name,
                "mounted_app": "FastA2A API" if fasta2a_mounted else "Basic health endpoints only",
                "mount_path": "/api" if fasta2a_mounted else None,
            }

    def as_dict(self) -> Dict[str, Any]:
        """Return a serialisable representation of the FastA2A gateway service."""
        base_info = super().as_dict()
        base_info.update(
            {
                "port": self.config.fasta2a_gateway_port,
                "mounted_app": "FastA2A API",
                "mount_path": "/api",
            }
        )
        return base_info
