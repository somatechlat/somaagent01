"""Memory replicator service based on BaseService for orchestrator integration.

This service inherits from BaseService to be managed by the orchestrator.
It wraps the existing memory replication worker functionality.
"""

from __future__ import annotations

import asyncio
import logging

from ninja import Router

from admin.orchestrator.base_service import BaseService
from admin.orchestrator.config import CentralizedConfig

LOGGER = logging.getLogger(__name__)


class MemoryReplicatorService(BaseService):
    """Memory replicator service that inherits from BaseService for orchestrator integration."""

    service_name: str = "memory-replicator"

    def __init__(self, config: CentralizedConfig | None = None) -> None:
        # Initialize BaseService
        """Initialize the instance."""

        super().__init__(config)

        # Store the worker instance
        self.worker = None
        self.worker_task = None

    async def startup(self) -> None:
        """Initialize memory replicator service and start the worker."""
        LOGGER.info(f"Starting {self.service_name} service")

        try:
            # Import the MemoryReplicator from the original module
            from .main import MemoryReplicator

            # Create the worker instance
            self.worker = MemoryReplicator()

            # Start the worker as a background task
            self.worker_task = asyncio.create_task(self.worker.start())

            LOGGER.info(f"{self.service_name} service startup completed")

        except Exception as exc:
            LOGGER.error(f"Failed to start {self.service_name} service: {exc}")
            raise

    async def shutdown(self) -> None:
        """Clean up memory replicator service resources."""
        LOGGER.info(f"Shutting down {self.service_name} service")

        try:
            # Cancel the worker task
            if self.worker_task and not self.worker_task.done():
                self.worker_task.cancel()
                try:
                    await self.worker_task
                except asyncio.CancelledError:
                    pass

            # Clean up worker resources if needed
            if self.worker:
                # The worker doesn't have explicit cleanup methods,
                # but we can add them if needed
                pass

            LOGGER.info(f"{self.service_name} service shutdown completed")

        except Exception as exc:
            LOGGER.error(f"Error during {self.service_name} service shutdown: {exc}")

    async def _start(self) -> None:
        """Orchestrator lifecycle hook — delegates to startup."""
        await self.startup()

    async def _stop(self) -> None:
        """Orchestrator lifecycle hook — delegates to shutdown."""
        await self.shutdown()

    def register_routes(self, app: Router) -> None:
        """Register API routes for the memory replicator service.

        Args:
            app: The Ninja Router to register routes with.
        """
        pass
