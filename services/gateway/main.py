"""Minimal modular Gateway entrypoint.

All HTTP/WS routes are provided by the modular routers in
``services.gateway.routers``. Auth and providers extracted to separate modules.
"""

from __future__ import annotations

import os
import pathlib
import time

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Re-exports for test compatibility
# Re-export auth and providers for backward compatibility
from services.gateway.routers import build_router
from services.gateway import providers
from services.gateway.limiter import limiter
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from src.core.config import cfg

webui_path = str(pathlib.Path(__file__).resolve().parents[2] / "webui")
app = FastAPI(title="SomaAgent Gateway")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


@app.on_event("startup")
async def _ensure_settings_schema() -> None:
    """Ensure the agent_settings table exists at startup."""
    import logging

    from services.common.agent_settings_store import get_agent_settings_store

    store = get_agent_settings_store()
    try:
        await store.ensure_schema()
    except Exception as exc:
        logging.getLogger(__name__).error("Failed to ensure agent_settings schema: %s", exc)


@app.get("/health", tags=["monitoring"])
async def health() -> dict:
    """Return a simple health check for the gateway process."""
    return {"status": "ok", "timestamp": time.time()}


@app.get("/healths", tags=["monitoring"])
async def aggregated_health() -> dict:
    """Aggregate health of core services."""
    import httpx

    services = {
        "gateway": cfg.env("GATEWAY_HEALTH_URL"),
        "fasta2a_gateway": cfg.env("FASTA2A_HEALTH_URL"),
    }
    results: dict[str, dict] = {}
    async with httpx.AsyncClient() as client:
        for name, url in services.items():
            try:
                resp = await client.get(url, timeout=2.0)
                results[name] = {
                    "status": "healthy" if resp.status_code == 200 else "unhealthy",
                    "code": resp.status_code,
                }
            except Exception as exc:
                results[name] = {"status": "unhealthy", "error": str(exc)}
    overall = (
        "healthy" if all(r.get("status") == "healthy" for r in results.values()) else "unhealthy"
    )
    return {"overall": overall, "components": results}


@app.get("/", include_in_schema=False)
def serve_root() -> FileResponse:
    """Serve the UI index.html from the mounted webui directory."""
    return FileResponse(os.path.join(webui_path, "index.html"))


app.mount("/static", StaticFiles(directory=webui_path, html=False), name="webui")
app.include_router(build_router())


# ---------------------------------------------------------------------------
# Compatibility helpers for routers/tests (centralised in providers)
# ---------------------------------------------------------------------------
def get_secret_manager():
    return providers.get_secret_manager()


def _gateway_llm_client():
    return providers.get_llm_client()


# Compatibility getters used by integration tests to override dependencies.
def get_event_bus():
    return providers.get_event_bus()


def get_session_cache():
    return providers.get_session_cache()


def get_session_store():
    return providers.get_session_store()


def main() -> None:
    uvicorn.run("services.gateway.main:app", host="0.0.0.0", port=8010, reload=False)


if __name__ == "__main__":
    main()
