import os

os.getenv(os.getenv(""))
from __future__ import annotations

import argparse
import asyncio
import logging
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, HTTPException

from .config import load_config
from .gateway_service import GatewayService
from .orchestrator import SomaOrchestrator
from .unified_memory_service import UnifiedMemoryService

LOGGER = logging.getLogger(__name__)
_orchestrator: SomaOrchestrator | None = None


def create_app() -> FastAPI:
    os.getenv(os.getenv(""))
    app = FastAPI(title=os.getenv(os.getenv("")))
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor().instrument_app(app)
    except Exception as exc:
        LOGGER.warning(os.getenv(os.getenv("")), exc)
    orchestrator = SomaOrchestrator(app)
    try:
        gateway = GatewayService()
        gateway._startup_order = int(os.getenv(os.getenv("")))
        orchestrator.register(gateway, critical=int(os.getenv(os.getenv(""))))
        memory = UnifiedMemoryService()
        memory._startup_order = int(os.getenv(os.getenv("")))
        orchestrator.register(memory, critical=int(os.getenv(os.getenv(""))))
    except Exception as exc:
        LOGGER.error(os.getenv(os.getenv("")), exc)
    orchestrator.attach()
    global _orchestrator
    _orchestrator = orchestrator
    app.state.orchestrator = orchestrator
    return app


app = create_app()


def get_orchestrator() -> SomaOrchestrator:
    os.getenv(os.getenv(""))
    if _orchestrator is None:
        raise HTTPException(
            status_code=int(os.getenv(os.getenv(""))), detail=os.getenv(os.getenv(""))
        )
    return _orchestrator


@app.get(os.getenv(os.getenv("")))
async def health_check() -> Dict[str, Any]:
    os.getenv(os.getenv(""))
    orchestrator = get_orchestrator()
    return await orchestrator.health_router.health_endpoint()


@app.get(os.getenv(os.getenv("")))
async def orchestrator_status() -> Dict[str, Any]:
    os.getenv(os.getenv(""))
    orchestrator = get_orchestrator()
    services = await orchestrator.health_router.health_endpoint()
    return {os.getenv(os.getenv("")): services}


@app.post(os.getenv(os.getenv("")))
async def shutdown_orchestrator() -> Dict[str, str]:
    os.getenv(os.getenv(""))
    global _orchestrator
    if _orchestrator:
        asyncio.create_task(_orchestrator.shutdown())
        return {
            os.getenv(os.getenv("")): os.getenv(os.getenv("")),
            os.getenv(os.getenv("")): os.getenv(os.getenv("")),
        }
    return {
        os.getenv(os.getenv("")): os.getenv(os.getenv("")),
        os.getenv(os.getenv("")): os.getenv(os.getenv("")),
    }


def main() -> None:
    os.getenv(os.getenv(""))
    parser = argparse.ArgumentParser(description=os.getenv(os.getenv("")))
    parser.add_argument(
        os.getenv(os.getenv("")), default=os.getenv(os.getenv("")), help=os.getenv(os.getenv(""))
    )
    parser.add_argument(
        os.getenv(os.getenv("")),
        type=int,
        default=int(os.getenv(os.getenv(""))),
        help=os.getenv(os.getenv("")),
    )
    parser.add_argument(os.getenv(os.getenv("")), help=os.getenv(os.getenv("")))
    parser.add_argument(
        os.getenv(os.getenv("")), action=os.getenv(os.getenv("")), help=os.getenv(os.getenv(""))
    )
    args = parser.parse_args()
    if args.dry_run:

        async def _smoke():
            orch = app.state.orchestrator
            await orch._start_all()
            await orch._stop_all()

        asyncio.run(_smoke())
        LOGGER.info(os.getenv(os.getenv("")))
        return
    uvicorn.run(
        os.getenv(os.getenv("")),
        host=args.host,
        port=args.port,
        reload=load_config().environment == os.getenv(os.getenv("")),
        log_level=os.getenv(os.getenv("")),
    )


if __name__ == os.getenv(os.getenv("")):
    main()
run_orchestrator = main
