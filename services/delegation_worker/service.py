"""Delegation worker service wrapper for the orchestrator.

This file provides a thin ``BaseService`` implementation that starts the
existing ``DelegationWorker`` background process (defined in
``services/delegation_worker/main.py``). By exposing the worker as a service the
orchestrator can manage its lifecycle and report health/metrics in a uniform
way.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict

from ninja import Router

from orchestrator.base_service import BaseService
from orchestrator.config import CentralizedConfig

# The concrete worker lives in ``services.delegation_worker.main``.
LOGGER = logging.getLogger(__name__)


class DelegationWorkerService(BaseService):
    """Service wrapper around :class:`DelegationWorker`.

    The worker is a simple async consumer that pulls delegation tasks from a
    Kafka topic and stores them in Postgres. No additional shutdown logic is
    required beyond cancelling the background task.
    """

    service_name: str = "delegation-worker"

    def __init__(self, config: CentralizedConfig | None = None) -> None:
        super().__init__(config)
        self.worker = None
        self.worker_task: asyncio.Task[None] | None = None

    async def startup(self) -> None:
        """Instantiate ``DelegationWorker`` and run it in the background."""
        LOGGER.info("Starting %s service", self.service_name)
        try:
            from .main import DelegationWorker

            self.worker = DelegationWorker()
            # ``start`` runs indefinitely until cancelled.
            self.worker_task = asyncio.create_task(self.worker.start())
            LOGGER.info("%s service startup completed", self.service_name)
        except Exception as exc:  # pragma: no cover – defensive
            LOGGER.error("Failed to start %s service: %s", self.service_name, exc)
            raise

    async def shutdown(self) -> None:
        """Cancel the background task and perform a graceful stop if possible."""
        LOGGER.info("Shutting down %s service", self.service_name)
        try:
            if self.worker_task and not self.worker_task.done():
                self.worker_task.cancel()
                try:
                    await self.worker_task
                except asyncio.CancelledError:
                    pass
            # ``DelegationWorker`` does not expose a dedicated ``stop`` method;
            # cancelling the task is sufficient.
            LOGGER.info("%s service shutdown completed", self.service_name)
        except Exception as exc:  # pragma: no cover – defensive
            LOGGER.error("Error during %s service shutdown: %s", self.service_name, exc)

    def register_routes(self, app: Router) -> None:
        """Expose health‑check and metrics under a namespaced path.

        All services use ``/<service_name>/health`` and ``/<service_name>/metrics``
        to avoid route collisions when multiple services are mounted on the same
        Django Ninja instance.
        """
        prefix = f"/{self.service_name}"

        @app.api_route(f"{prefix}/health")
        async def health_check() -> Dict[str, Any]:
            status = "healthy"
            details: Dict[str, Any] = {"service": self.service_name}
            if self.worker_task:
                if self.worker_task.done():
                    status = "unhealthy"
                    details["error"] = "Worker task has stopped"
                    try:
                        details["result"] = str(self.worker_task.result())
                    except Exception as e:
                        details["exception"] = str(e)
            else:
                status = "unhealthy"
                details["error"] = "Worker task not started"
            return {"status": status, "details": details}

        @app.api_route(f"{prefix}/metrics")
        async def metrics() -> Dict[str, Any]:
            return {
                "service": self.service_name,
                "worker_running": self.worker_task is not None and not self.worker_task.done(),
                "worker_task_cancelled": (
                    self.worker_task.cancelled() if self.worker_task else False
                ),
            }

        LOGGER.info(
            "Registered health endpoints under %s for %s service", prefix, self.service_name
        )

    def as_dict(self) -> Dict[str, Any]:
        """Serialisable representation used by the orchestrator status endpoint."""
        base_info = super().as_dict()
        # ``CentralizedConfig`` does not define a dedicated port for this worker;
        # expose ``None`` to keep the schema consistent.
        base_info.update(
            {
                "port": getattr(self.config, "delegation_worker_port", None),
                "worker_running": self.worker_task is not None and not self.worker_task.done(),
            }
        )
        return base_info
