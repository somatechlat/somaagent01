"""Minimal modular Gateway entrypoint.

All HTTP/WS routes are provided by the modular routers in
``services.gateway.routers``. Legacy monolith endpoints and large inline logic
have been removed to comply with VIBE rules (single source, no legacy
duplicates).
"""

from __future__ import annotations

import os
import time
import uvicorn
import httpx
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from services.gateway.routers import build_router

# ---------------------------------------------------------------------------
# Configuration for static UI serving
# ---------------------------------------------------------------------------
# The UI files live in the repository's ``webui`` directory. When running inside
# the Docker container the repository is mounted at ``/git/agent-zero`` (as per
# the compose file). During local development the files are located relative to
# this source tree. We therefore resolve the correct absolute path at runtime:
import pathlib

webui_path = pathlib.Path(__file__).resolve().parents[2] / "webui"
webui_path = str(webui_path)

app = FastAPI(title="SomaAgent Gateway")


# Ensure UI settings table exists at startup so the UI can fetch settings without
# encountering a missing‑table error. This runs once when the FastAPI app starts.
@app.on_event("startup")
async def _ensure_settings_schema() -> None:
    """Ensure the agent_settings table exists at startup."""
    from services.common.agent_settings_store import get_agent_settings_store
    import logging

    store = get_agent_settings_store()
    try:
        await store.ensure_schema()
    except Exception as exc:
        logging.getLogger(__name__).error("Failed to ensure agent_settings schema: %s", exc)


# ---------------------------------------------------------------------------
# Basic health endpoints for the gateway service
# ---------------------------------------------------------------------------
@app.get("/health", tags=["monitoring"])
async def health() -> dict:
    """Return a simple health check for the gateway process."""
    return {"status": "healthy", "timestamp": time.time()}


@app.get("/healths", tags=["monitoring"])
async def aggregated_health() -> dict:
    """Aggregate health of core services (gateway and FastA2A gateway)."""
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


# ---------------------------------------------------------------------------
# UI root endpoint and static file mount
# ---------------------------------------------------------------------------
@app.get("/", include_in_schema=False)
def serve_root() -> FileResponse:
    """Serve the UI ``index.html`` from the mounted ``webui`` directory."""
    return FileResponse(os.path.join(webui_path, "index.html"))


# Serve static assets (JS, CSS, images, etc.) under ``/static``. The ``html`` flag
# is disabled to avoid intercepting HTML requests that should be handled by the
# explicit ``/`` route above.
app.mount("/static", StaticFiles(directory=webui_path, html=False), name="webui")

# Include all modular routers (including the health_full router under ``/v1``).
app.include_router(build_router())

# ---------------------------------------------------------------------------
# Compatibility aliases for UI that expects legacy paths without the ``v1``
# prefix. The UI configuration (``webui/config.js``) defines ``UI_SETTINGS`` as
# ``/settings/sections``. To avoid changing the frontend, expose thin alias
# endpoints that redirect to the new ``/v1`` routes.
# ---------------------------------------------------------------------------
from fastapi.responses import RedirectResponse


# Legacy endpoints removed - use /v1/settings instead via ui_settings router

# ---------------------------------------------------------------------------
# Dependency providers expected by the test suite and legacy routers
# ---------------------------------------------------------------------------
from src.core.config import cfg
from services.common.admin_settings import ADMIN_SETTINGS
from services.common.event_bus import KafkaEventBus, KafkaSettings
from services.common.outbox_repository import OutboxStore, ensure_outbox_schema
from services.common.publisher import DurablePublisher
from services.common.session_repository import RedisSessionCache
import asyncio as _asyncio


def get_bus() -> KafkaEventBus:
    """Create a Kafka event bus using admin settings.

    Mirrors the helper used in other services and provides a single source of
    truth for the broker configuration.
    """
    kafka_settings = KafkaSettings(
        bootstrap_servers=ADMIN_SETTINGS.kafka_bootstrap_servers,
        security_protocol=cfg.env("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
        sasl_mechanism=cfg.env("KAFKA_SASL_MECHANISM"),
        sasl_username=cfg.env("KAFKA_SASL_USERNAME"),
        sasl_password=cfg.env("KAFKA_SASL_PASSWORD"),
    )
    return KafkaEventBus(kafka_settings)


def get_publisher() -> DurablePublisher:
    """Provide a ``DurablePublisher`` instance for FastAPI dependency injection.

    The publisher is constructed lazily; we also ensure the outbox schema is
    present (non‑blocking if the database is unavailable). Tests can override
    this dependency with a stub, so the implementation only needs to be valid.
    """
    bus = get_bus()
    outbox = OutboxStore(dsn=ADMIN_SETTINGS.postgres_dsn)
    # Ensure outbox schema – run in background if an event loop is active.
    try:

        async def _ensure():
            await ensure_outbox_schema(outbox)

        loop = _asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(_ensure())
        else:
            loop.run_until_complete(_ensure())
    except Exception:
        # Schema creation failures should not prevent the app from starting.
        pass
    return DurablePublisher(bus=bus, outbox=outbox)


def get_session_cache() -> RedisSessionCache:
    """Return a Redis‑backed session cache.

    In environments without a valid Redis URL this will raise a connection error
    at runtime, but the test suite overrides the dependency with a stub, so the
    default implementation merely needs to be importable.
    """
    return RedisSessionCache()


def main() -> None:
    uvicorn.run("services.gateway.main:app", host="0.0.0.0", port=8010, reload=False)


if __name__ == "__main__":
    main()
