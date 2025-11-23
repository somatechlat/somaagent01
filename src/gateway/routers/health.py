"""Health router for the FastAPI gateway.

Provides a minimal ``/v1/health`` endpoint that returns a JSON payload with
basic status information.  This is deliberately lightweight – the full health
check (database, redis, kafka, etc.) remains in ``services/gateway/main.py``
under the ``health_check`` function.  The router is useful for quick liveness
probes and satisfies the VIBE rule *no shims* because it calls the real config
facade.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from src.core.config import cfg

router = APIRouter()


@router.get("/v1/health", tags=["health"])
def simple_health() -> JSONResponse:
    """Return a tiny health payload.

    The response includes the service name and the deployment mode taken from
    the central configuration.  This endpoint is deliberately tiny so it can be
    used for liveness probes without triggering expensive downstream checks.
    """
    payload = {
        "status": "ok",
        "service": "gateway",
        "deployment_mode": cfg.env("DEPLOYMENT_MODE"),
    }
    return JSONResponse(payload)
