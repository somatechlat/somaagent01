"""Tool executor service based on BaseService for orchestrator integration.

This service inherits from BaseService to be managed by the orchestrator.
It wraps the existing tool executor functionality.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict

from ninja import Router

from orchestrator.base_service import BaseService
from orchestrator.config import CentralizedConfig

# LOGGER configuration
LOGGER = logging.getLogger(__name__)


class ToolExecutorService(BaseService):
    """Tool executor service that inherits from BaseService for orchestrator integration."""

    service_name: str = "tool-executor"

    def __init__(self, config: CentralizedConfig | None = None) -> None:
        # Initialize BaseService
        """Initialize the instance."""

        super().__init__(config)

        # Store the worker instance
        self.worker = None
        self.worker_task = None

    async def startup(self) -> None:
        """Initialize tool executor service and start the worker."""
        LOGGER.info(f"Starting {self.service_name} service")

        try:
            # Import the ToolExecutor from the original module
            from .main import ToolExecutor

            # Create the worker instance
            self.worker = ToolExecutor()

            # Start the worker as a background task
            self.worker_task = asyncio.create_task(self.worker.start())

            LOGGER.info(f"{self.service_name} service startup completed")

        except Exception as exc:
            LOGGER.error(f"Failed to start {self.service_name} service: {exc}")
            raise

    async def shutdown(self) -> None:
        """Clean up tool executor service resources."""
        LOGGER.info(f"Shutting down {self.service_name} service")

        try:
            # Cancel the worker task
            if self.worker_task and not self.worker_task.done():
                self.worker_task.cancel()
                try:
                    await self.worker_task
                except asyncio.CancelledError:
                    pass

            # Close worker connections gracefully
            if self.worker:
                try:
                    await self.worker.policy.close()
                    await self.worker.soma.close()
                except Exception as e:
                    LOGGER.debug(f"Error closing worker connections: {e}")

            LOGGER.info(f"{self.service_name} service shutdown completed")

        except Exception as exc:
            LOGGER.error(f"Error during {self.service_name} service shutdown: {exc}")

    def register_routes(self, app: Router) -> None:
        """Register health check endpoints for the tool executor service."""

        # Add a health check endpoint for the orchestrator
        @app.api_route("/health")
        async def health_check():
            """Execute health check.
                """

            status = "healthy"
            details = {"service": self.service_name}

            # Check if worker task is running
            if self.worker_task:
                if self.worker_task.done():
                    status = "unhealthy"
                    details["error"] = "Worker task has stopped"
                    try:
                        # Check if there was an exception
                        result = self.worker_task.result()
                        details["result"] = str(result)
                    except Exception as e:
                        details["exception"] = str(e)
            else:
                status = "unhealthy"
                details["error"] = "Worker task not started"

            return {"status": status, "details": details}

        # Add a metrics endpoint
        @app.api_route("/metrics")
        async def metrics():
            """Return basic metrics about the tool executor service."""
            return {
                "service": self.service_name,
                "worker_running": self.worker_task is not None and not self.worker_task.done(),
                "worker_task_cancelled": (
                    self.worker_task.cancelled() if self.worker_task else False
                ),
            }

        LOGGER.info(f"Registered health endpoints for {self.service_name} service")

    def as_dict(self) -> Dict[str, Any]:
        """Return a serialisable representation of the tool executor service."""
        base_info = super().as_dict()
        base_info.update(
            {
                "port": self.config.tool_executor_port,
                "worker_running": self.worker_task is not None and not self.worker_task.done(),
            }
        )
        return base_info