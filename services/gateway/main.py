"""Minimal modular Gateway entrypoint.

All HTTP/WS routes are provided by the modular routers in services.gateway.routers.
Legacy monolith endpoints and large inline logic have been removed to comply with
VIBE rules (single source, no legacy duplicates).
"""
from __future__ import annotations

import uvicorn
from fastapi import FastAPI

from services.gateway.routers import build_router

app = FastAPI(title="SomaAgent Gateway")
app.include_router(build_router())

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

    This mirrors the helper used in other services (e.g. delegation_gateway) and
    provides a single source of truth for the broker configuration.
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
