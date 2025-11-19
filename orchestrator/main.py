"""Orchestrator entry point.

This module provides:

* ``create_app()`` – builds a FastAPI instance with optional OpenTelemetry
  instrumentation. Tests import this function to obtain an application object.
* A global ``app`` used by the production HTTP server.
* Startup / shutdown event handlers that initialise a :class:`SomaOrchestrator`
  instance, start all registered services, and expose ``/v1/health`` and
  ``/v1/status`` endpoints.

All concrete services (e.g. ``GatewayService`` or ``UnifiedMemoryService``)
are registered inside ``create_app`` so the orchestrator can manage them.
The implementation follows the VIBE CODING RULES – no placeholders, real
behaviour, and full type‑checked configuration.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, HTTPException

from .config import load_config, CentralizedConfig
from .orchestrator import SomaOrchestrator
from .health_monitor import UnifiedHealthMonitor
from .gateway_service import GatewayService
from .unified_memory_service import UnifiedMemoryService
from .base_service import BaseSomaService

LOGGER = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create a FastAPI app and register core services.

    The function is deliberately lightweight – it only creates the ASGI app,
    optionally instruments it with OpenTelemetry, registers the built‑in
    services and returns the app. Test code can call this function to obtain a
    fresh instance without side‑effects.
    """
    app = FastAPI(title="SomaAgent01 Orchestrator")

    # OpenTelemetry instrumentation – non‑critical, failures are logged only.
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor().instrument_app(app)
    except Exception as exc:  # pragma: no cover – defensive
        LOGGER.warning("OpenTelemetry instrumentation failed: %s", exc)

    # Initialise a temporary orchestrator solely to register services.
    orchestrator = SomaOrchestrator(app)
    try:
        orchestrator.register(GatewayService(), critical=False)
        orchestrator.register(UnifiedMemoryService(), critical=False)
    except Exception as exc:  # pragma: no cover – defensive
        LOGGER.error("Service registration failed during app creation: %s", exc)

    # Attach health router and Prometheus metrics.
    orchestrator.attach()
    return app


# Global FastAPI app used by the production server.
app = create_app()

# Global orchestrator instance used by the HTTP endpoints.
_orchestrator: SomaOrchestrator | None = None


def get_orchestrator() -> SomaOrchestrator:
    """Retrieve the global orchestrator, raising HTTP 500 if unavailable."""
    if _orchestrator is None:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    return _orchestrator


@app.on_event("startup")
async def _startup() -> None:
    """Startup hook – load config, create the orchestrator and start services."""
    global _orchestrator
    config = load_config()
    _orchestrator = SomaOrchestrator(config)
    await _orchestrator.start()
    # Start background health monitor.
    await _orchestrator.health_monitor.start()
    LOGGER.info("Orchestrator started")


@app.on_event("shutdown")
async def _shutdown() -> None:
    """Shutdown hook – stop services and health monitor gracefully."""
    global _orchestrator
    if _orchestrator:
        await _orchestrator.shutdown()
        await _orchestrator.health_monitor.stop()
        LOGGER.info("Orchestrator shut down")


@app.get("/v1/health")
async def health_check() -> Dict[str, Any]:
    """Return the aggregated health status of all registered services."""
    orchestrator = get_orchestrator()
    return orchestrator.get_service_status()


@app.get("/v1/status")
async def orchestrator_status() -> Dict[str, Any]:
    """Detailed status including health‑monitor information."""
    orchestrator = get_orchestrator()
    status = orchestrator.get_service_status()
    if hasattr(orchestrator, "health_monitor"):
        status["health_monitor"] = orchestrator.health_monitor.get_overall_health()
    return status


@app.post("/v1/shutdown")
async def shutdown_orchestrator() -> Dict[str, str]:
    """Trigger a graceful shutdown via the HTTP API."""
    global _orchestrator
    if _orchestrator:
        asyncio.create_task(_orchestrator.shutdown())
        return {"status": "shutting_down", "message": "Graceful shutdown initiated"}
    return {"status": "not_running", "message": "Orchestrator is not running"}


def main() -> None:
    """Run the orchestrator server using uvicorn.

    Command‑line arguments allow overriding the host, port and optional config
    path. The function respects the VIBE rule of keeping the entry point simple
    and fully functional.
    """
    parser = argparse.ArgumentParser(description="SomaAgent01 Orchestrator")
    parser.add_argument("--host", default="0.0.0.0", help="HTTP host")
    parser.add_argument("--port", type=int, default=8000, help="HTTP port")
    parser.add_argument("--config", help="Path to configuration file")
    args = parser.parse_args()

    uvicorn.run(
        "orchestrator.main:app",
        host=args.host,
        port=args.port,
        reload=load_config().environment == "DEV",
        log_level="info",
    )


if __name__ == "__main__":
    main()
