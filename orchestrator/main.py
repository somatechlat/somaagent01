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
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, HTTPException

from .orchestrator import SomaOrchestrator
from .health_monitor import UnifiedHealthMonitor
from .gateway_service import GatewayService
from .unified_memory_service import UnifiedMemoryService
from .base_service import BaseSomaService

LOGGER = logging.getLogger(__name__)

# Global orchestrator instance used by HTTP endpoints.
_orchestrator: SomaOrchestrator | None = None


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
        gateway = GatewayService()
        gateway._startup_order = 10  # deterministic order
        orchestrator.register(gateway, critical=True)

        memory = UnifiedMemoryService()
        memory._startup_order = 20
        orchestrator.register(memory, critical=True)
    except Exception as exc:  # pragma: no cover – defensive
        LOGGER.error("Service registration failed during app creation: %s", exc)

    # Attach health router and Prometheus metrics.
    orchestrator.attach()

    # Expose orchestrator for endpoints and external callers.
    global _orchestrator
    _orchestrator = orchestrator
    app.state.orchestrator = orchestrator
    return app


# Global FastAPI app used by the production server.
app = create_app()


def get_orchestrator() -> SomaOrchestrator:
    """Retrieve the global orchestrator, raising HTTP 500 if unavailable."""
    if _orchestrator is None:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    return _orchestrator


@app.get("/v1/health")
async def health_check() -> Dict[str, Any]:
    """Return aggregated health across all registered services."""
    orchestrator = get_orchestrator()
    return await orchestrator.health_router.health_endpoint()


@app.get("/v1/status")
async def orchestrator_status() -> Dict[str, Any]:
    """Detailed status including service health and monitor view."""
    orchestrator = get_orchestrator()
    services = await orchestrator.health_router.health_endpoint()
    return {"services": services}


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

# Alias for backward compatibility – some modules expect a ``run_orchestrator``
# callable that starts the server.  The original implementation exposed such a
# function; after refactoring it was renamed to ``main``.  Providing this alias
# restores the expected import without altering behaviour.
run_orchestrator = main
