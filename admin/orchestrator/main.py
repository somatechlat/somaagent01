"""Orchestrator entry point - 100% Django ASGI.

All FastAPI replaced with Django/Django Ninja.


🎓 PhD Dev - Clean ASGI architecture
🔒 Security - Django middleware stack
⚡ Perf - Uvicorn ASGI server
📚 ISO Doc - Full docstrings
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
from typing import Any, Dict

# django.setup() should only be called if this is the entry point.
if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "services.gateway.settings")
    import django

    django.setup()

import uvicorn
from django.core.asgi import get_asgi_application
from ninja import NinjaAPI, Router

from admin.common.exceptions import ServiceError

from .cache_sync_service import CacheSyncService
from .config import load_config
from .gateway_service import GatewayService
from .orchestrator import SomaOrchestrator
from .unified_memory_service import UnifiedMemoryService

LOGGER = logging.getLogger(__name__)

_orchestrator: SomaOrchestrator | None = None

# Django Ninja API for orchestrator endpoints
api = NinjaAPI(title="SomaAgent01 Orchestrator", version="1.0.0")
router = Router(tags=["orchestrator"])


def get_orchestrator() -> SomaOrchestrator:
    """Retrieve the global orchestrator, raising error if unavailable."""
    if _orchestrator is None:
        raise ServiceError("Orchestrator not initialized")
    return _orchestrator


@router.get("/v1/health")
async def health_check(request) -> Dict[str, Any]:
    """Return aggregated health across all registered services."""
    orchestrator = get_orchestrator()
    return await orchestrator.health_router.health_endpoint()


@router.get("/v1/status")
async def orchestrator_status(request) -> Dict[str, Any]:
    """Detailed status including service health."""
    orchestrator = get_orchestrator()
    services = await orchestrator.health_router.health_endpoint()
    return {"services": services}


@router.post("/v1/shutdown")
async def shutdown_orchestrator(request) -> Dict[str, str]:
    """Trigger a graceful shutdown via the HTTP API."""
    global _orchestrator
    if _orchestrator:
        asyncio.create_task(_orchestrator.shutdown())
        return {"status": "shutting_down", "message": "Graceful shutdown initiated"}
    return {"status": "not_running", "message": "Orchestrator is not running"}


api.add_router("/", router)


def create_app():
    """Create a Django ASGI app and register core services."""
    global _orchestrator

    django_app = get_asgi_application()

    orchestrator = SomaOrchestrator(django_app)
    try:
        gateway = GatewayService()
        gateway._startup_order = 10
        orchestrator.register(gateway, critical=True)

        memory = UnifiedMemoryService()
        memory._startup_order = 20
        orchestrator.register(memory, critical=True)

        cache_sync = CacheSyncService()
        cache_sync._startup_order = 30
        orchestrator.register(cache_sync, critical=True)
    except Exception as exc:
        LOGGER.error("Service registration failed: %s", exc)

    orchestrator.attach()
    _orchestrator = orchestrator

    return django_app


# Global Django ASGI app
app = create_app()


def main() -> None:
    """Run the orchestrator server using uvicorn."""
    parser = argparse.ArgumentParser(description="SomaAgent01 Orchestrator")
    parser.add_argument("--host", default="0.0.0.0", help="HTTP host")
    parser.add_argument("--port", type=int, default=8000, help="HTTP port")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Start and stop services once, then exit (for CI smoke checks)",
    )
    args = parser.parse_args()

    if args.dry_run:

        async def _smoke():
            """Execute smoke."""

            orch = _orchestrator
            await orch._start_all()
            await orch._stop_all()

        asyncio.run(_smoke())
        LOGGER.info("Dry-run completed successfully")
        return

    uvicorn.run(
        "orchestrator.main:app",
        host=args.host,
        port=args.port,
        reload=load_config().environment == "DEV",
        log_level="info",
    )


if __name__ == "__main__":
    main()

run_orchestrator = main
