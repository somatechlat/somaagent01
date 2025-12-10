"""Gateway dependency providers for FastAPI injection."""

from __future__ import annotations

import asyncio as _asyncio

from services.common.api_key_store import ApiKeyStore
from services.common.event_bus import KafkaEventBus, KafkaSettings
from services.common.outbox_repository import ensure_outbox_schema, OutboxStore
from services.common.publisher import DurablePublisher
from services.common.session_repository import RedisSessionCache
from src.core.config import cfg

# Compatibility attributes for test suite
JWKS_CACHE: dict = {}
APP_SETTINGS: dict = {}
# JWT_SECRET must come from config - no hardcoded secrets per VIBE rules
JWT_SECRET = cfg.env("SA01_JWT_SECRET", "")


def get_event_bus() -> KafkaEventBus:
    """Get event bus instance (alias for get_bus)."""
    return get_bus()


def get_bus() -> KafkaEventBus:
    """Create a Kafka event bus using admin settings."""
    kafka_settings = KafkaSettings(
        bootstrap_servers=cfg.settings().kafka.bootstrap_servers,
        security_protocol=cfg.env("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
        sasl_mechanism=cfg.env("KAFKA_SASL_MECHANISM"),
        sasl_username=cfg.env("KAFKA_SASL_USERNAME"),
        sasl_password=cfg.env("KAFKA_SASL_PASSWORD"),
    )
    return KafkaEventBus(kafka_settings)


def get_publisher() -> DurablePublisher:
    """Provide a DurablePublisher instance for FastAPI dependency injection."""
    bus = get_bus()
    outbox = OutboxStore(dsn=cfg.settings().database.dsn)
    try:

        async def _ensure():
            await ensure_outbox_schema(outbox)

        loop = _asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(_ensure())
        else:
            loop.run_until_complete(_ensure())
    except Exception:
        pass
    return DurablePublisher(bus=bus, outbox=outbox)


def get_session_cache() -> RedisSessionCache:
    """Return a Redis-backed session cache."""
    return RedisSessionCache()


def get_llm_credentials_store():
    """Get the LLM credentials store instance."""
    from services.common.secret_manager import SecretManager

    return SecretManager()


def get_api_key_store() -> ApiKeyStore:
    """Return the API key store singleton."""
    from integrations.repositories import get_api_key_store as _repo_get

    return _repo_get()


def get_slm_client():
    """Get the SLM client instance for the gateway."""
    from services.common.slm_client import SLMClient

    return SLMClient()
