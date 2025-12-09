"""Minimal modular Gateway entrypoint.

All HTTP/WS routes are provided by the modular routers in
``services.gateway.routers``. Auth and providers extracted to separate modules.
"""
from __future__ import annotations

import os
import pathlib
import time

import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from services.gateway.routers import build_router
from src.core.config import cfg

# Re-export auth and providers for backward compatibility
from services.gateway.auth import (
    authorize_request, jwt_module, SomaBrainClient, REQUIRE_AUTH,
    _resolve_signing_key, _get_policy_client, _evaluate_opa
)
from services.gateway.providers import (
    get_event_bus, get_bus, get_publisher, get_session_cache,
    get_llm_credentials_store, get_api_key_store, get_slm_client,
    JWKS_CACHE, APP_SETTINGS, JWT_SECRET
)

# Re-exports for test compatibility
from services.common.event_bus import KafkaEventBus, KafkaSettings
from services.common.policy_client import PolicyClient, PolicyRequest
from services.common.outbox_repository import ensure_outbox_schema, OutboxStore
from services.common.publisher import DurablePublisher
from services.common.session_repository import RedisSessionCache
from services.common.api_key_store import ApiKeyStore
import jwt

webui_path = str(pathlib.Path(__file__).resolve().parents[2] / "webui")
app = FastAPI(title="SomaAgent Gateway")


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
    services = {
        "gateway": cfg.env("GATEWAY_HEALTH_URL"),
        "fasta2a_gateway": cfg.env("FASTA2A_HEALTH_URL"),
    }
    results: dict[str, dict] = {}
    async with httpx.AsyncClient() as client:
        for name, url in services.items():
            try:
                resp = await client.get(url, timeout=2.0)
                results[name] = {"status": "healthy" if resp.status_code == 200 else "unhealthy", "code": resp.status_code}
            except Exception as exc:
                results[name] = {"status": "unhealthy", "error": str(exc)}
    overall = "healthy" if all(r.get("status") == "healthy" for r in results.values()) else "unhealthy"
    return {"overall": overall, "components": results}


@app.get("/", include_in_schema=False)
def serve_root() -> FileResponse:
    """Serve the UI index.html from the mounted webui directory."""
    return FileResponse(os.path.join(webui_path, "index.html"))


app.mount("/static", StaticFiles(directory=webui_path, html=False), name="webui")
app.include_router(build_router())


def main() -> None:
    uvicorn.run("services.gateway.main:app", host="0.0.0.0", port=8010, reload=False)


if __name__ == "__main__":
    main()
