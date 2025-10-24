"""FastAPI entrypoint for the UI Proxy service."""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI
from prometheus_client import (
    CollectorRegistry,
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    generate_latest,
)
from starlette.responses import Response

from services.common.logging_config import setup_logging
from services.common.settings_sa01 import SA01Settings
from services.common.tracing import setup_tracing
from services.ui_proxy.routes import router as ui_router

setup_logging()
LOGGER = logging.getLogger(__name__)

APP_SETTINGS = SA01Settings.from_env()
setup_tracing("ui-proxy", endpoint=APP_SETTINGS.otlp_endpoint)

app = FastAPI(title="SomaAgent 01 UI Proxy")
app.include_router(ui_router)

_registry = CollectorRegistry()
REQUESTS_TOTAL = Counter("ui_proxy_requests_total", "UI Proxy requests", registry=_registry)
HEALTH_STATUS = Gauge("ui_proxy_health", "UI Proxy health status", registry=_registry)


@app.get("/metrics")
async def metrics() -> Response:
    return Response(generate_latest(_registry), media_type=CONTENT_TYPE_LATEST)


@app.on_event("startup")
async def startup_event() -> None:
    HEALTH_STATUS.set(1)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8081")))
