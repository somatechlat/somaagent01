"""Bridge worker service — BaseService wrapper for the orchestrator.

Pattern: ``services/conversation_worker/service.py``.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict

from ninja import Router

from admin.orchestrator.base_service import BaseService
from admin.orchestrator.config import CentralizedConfig

logger = logging.getLogger(__name__)


class BridgeWorkerService(BaseService):
    """Managed bridge worker (WhatsApp + Telegram Capsule bridges, WP D3/D4)."""

    service_name: str = "bridge-worker"

    def __init__(self, config: CentralizedConfig | None = None) -> None:
        """Initialize the instance."""
        super().__init__(config)
        self.worker = None
        self.worker_task = None

    async def startup(self) -> None:
        """Start the bridge worker loop as a background task."""
        logger.info("Starting %s service", self.service_name)
        try:
            from services.bridge_worker.main import BridgeWorker

            self.worker = BridgeWorker()
            self.worker_task = asyncio.create_task(self.worker.start())
            logger.info("%s service startup completed", self.service_name)
        except Exception as exc:
            logger.error("Failed to start %s service: %s", self.service_name, exc)
            raise

    async def shutdown(self) -> None:
        """Stop the worker loop and close drivers."""
        logger.info("Shutting down %s service", self.service_name)
        try:
            if self.worker is not None:
                await self.worker.stop()
            if self.worker_task and not self.worker_task.done():
                self.worker_task.cancel()
                try:
                    await self.worker_task
                except asyncio.CancelledError:
                    pass
            logger.info("%s service shutdown completed", self.service_name)
        except Exception as exc:
            logger.error("Error during %s service shutdown: %s", self.service_name, exc)

    async def _start(self) -> None:
        await self.startup()

    async def _stop(self) -> None:
        await self.shutdown()

    def register_routes(self, app: Router) -> None:
        """Health + metrics endpoints for the orchestrator."""

        @app.get("/health")
        async def health_check():
            status = "healthy"
            details: Dict[str, Any] = {"service": self.service_name}
            if self.worker_task:
                if self.worker_task.done():
                    status = "unhealthy"
                    details["error"] = "Worker task has stopped"
                    try:
                        details["result"] = str(self.worker_task.result())
                    except Exception as exc:  # noqa: BLE001
                        details["exception"] = str(exc)
            else:
                status = "unhealthy"
                details["error"] = "Worker task not started"
            return {"status": status, "details": details}

        @app.get("/metrics")
        async def metrics():
            return {
                "service": self.service_name,
                "worker_running": self.worker_task is not None and not self.worker_task.done(),
                "worker_task_cancelled": (
                    self.worker_task.cancelled() if self.worker_task else False
                ),
            }

        logger.info("Registered health endpoints for %s service", self.service_name)

    def as_dict(self) -> Dict[str, Any]:
        base_info = super().as_dict()
        base_info.update(
            {
                "port": getattr(self.config, "bridge_worker_port", None),
                "worker_running": self.worker_task is not None and not self.worker_task.done(),
            }
        )
        return base_info
