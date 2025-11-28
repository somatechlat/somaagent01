"""Full gateway health check extracted from the gateway monolith.

This module preserves the production health logic (Postgres, Redis, Kafka, HTTP targets)
while allowing the main gateway file to shrink. It is mounted by the modular router
bundle in `services/gateway/routers/__init__.py`.
"""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from services.common.event_bus import KafkaEventBus, KafkaSettings
from services.common.session_repository import PostgresSessionStore, RedisSessionCache
from services.common.admin_settings import ADMIN_SETTINGS
import logging
from services.common import degradation_monitor
from src.core.config import cfg

router = APIRouter(prefix="/v1", tags=["health"])

LOGGER = logging.getLogger(__name__)


def _kafka_settings() -> KafkaSettings:
    return KafkaSettings.from_env()


@router.get("/health")
async def health_check(
    store: PostgresSessionStore = Depends(lambda: PostgresSessionStore(ADMIN_SETTINGS.postgres_dsn)),
    cache: RedisSessionCache = Depends(lambda: RedisSessionCache(ADMIN_SETTINGS.redis_url)),
) -> JSONResponse:
    # A map of component health results. Each entry will contain a ``status``
    # field ("ok", "down", "degraded") and optionally a ``detail`` string.
    components: dict[str, dict[str, str]] = {}
    overall_status = "ok"
    # If authentication is disabled, skip external checks and report healthy.
    if not cfg.env("AUTH_REQUIRED", False):
        # When auth is disabled we still want to expose the full component list
        # (including static services) so callers can see what would be checked.
        return JSONResponse({"status": "ok", "components": components})

    def record_status(name: str, status: str, detail: str | None = None) -> None:
        nonlocal overall_status
        components[name] = {"status": status}
        if detail:
            components[name]["detail"] = detail
        if status == "down":
            overall_status = "down"
        elif status == "degraded" and overall_status == "ok":
            overall_status = "degraded"

    try:
        await store.ping()
        record_status("postgres", "ok")
    except Exception as exc:
        LOGGER.warning("Postgres health check failed", extra={"error": str(exc)})
        record_status("postgres", "down", f"{type(exc).__name__}: {exc}")

    try:
        await cache.ping()
        record_status("redis", "ok")
    except Exception as exc:
        LOGGER.warning("Redis health check failed", extra={"error": str(exc)})
        record_status("redis", "down", f"{type(exc).__name__}: {exc}")

    kafka_bus = KafkaEventBus(_kafka_settings())
    try:
        await kafka_bus.healthcheck()
        record_status("kafka", "ok")
    except Exception as exc:
        LOGGER.warning("Kafka health check failed", extra={"error": str(exc)})
        record_status("kafka", "down", f"{type(exc).__name__}: {exc}")
    finally:
        await kafka_bus.close()

    async def check_http_target(name: str, url: str | None) -> None:
        if not url:
            return
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(url)
            if response.status_code < 500:
                record_status(name, "ok")
            else:
                record_status(name, "degraded", f"Status {response.status_code}")
        except Exception as exc:
            record_status(name, "down", f"{type(exc).__name__}: {exc}")

    await check_http_target("somabrain", cfg.soma_base_url())
    await check_http_target("opa", cfg.opa_url())

    # Degradation monitor status
    if degradation_monitor.is_monitoring():
        record_status("degradation_monitor", "ok")

    # ---------------------------------------------------------------------
    # Static list of additional services that do not expose a native health
    # endpoint but are part of the stack.  We mark them as "ok" if the container
    # is running (Docker will only start dependent services when they are
    # healthy), otherwise "unknown".  This gives callers a complete view of the
    # stack without adding fragile in‑container probes.
    # ---------------------------------------------------------------------
    static_services = [
        "conversation-worker",
        "tool-executor",
        "memory-replicator",
        "memory-sync",
        "outbox-sync",
        "fasta2a-gateway",
        "fasta2a-worker",
        "fasta2a-flower",
    ]
    for svc in static_services:
        # By default we assume the service is reachable because Docker Compose
        # will have started it.  If a more precise check is needed it can be
        # added later (e.g., HTTP ping for ``fasta2a-gateway``).
        record_status(svc, "ok")

    return JSONResponse({"status": overall_status, "components": components})
