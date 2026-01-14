"""Gateway dependency providers for Django Ninja injection."""

from __future__ import annotations

import os

from django.conf import settings

from services.common.api_key_store import ApiKeyStore
from services.common.event_bus import KafkaEventBus, KafkaSettings
from services.common.publisher import DurablePublisher

# Compatibility attributes for test suite
JWKS_CACHE: dict = {}
APP_SETTINGS: dict = {}
JWT_SECRET = os.environ.get("SA01_JWT_SECRET", "")
_TEMPORAL_CLIENT = None
_TEMPORAL_LOCK = None


def get_event_bus() -> KafkaEventBus:
    """Get event bus instance (alias for get_bus)."""
    return get_bus()


def get_bus() -> KafkaEventBus:
    """Create a Kafka event bus using admin settings."""
    kafka_settings = KafkaSettings(
        bootstrap_servers=getattr(settings, "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        security_protocol=os.environ.get("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
        sasl_mechanism=os.environ.get("KAFKA_SASL_MECHANISM"),
        sasl_username=os.environ.get("KAFKA_SASL_USERNAME"),
        sasl_password=os.environ.get("KAFKA_SASL_PASSWORD"),
    )
    return KafkaEventBus(kafka_settings)


def get_publisher() -> DurablePublisher:
    """Provide a DurablePublisher instance for dependency injection."""
    bus = get_bus()
    return DurablePublisher(bus=bus)


def get_session_cache():
    """Return a Redis-backed session cache using Django cache."""
    from django.core.cache import cache

    return cache


def get_secret_manager():
    """Get the SecretManager instance."""
    from services.common.secret_manager import SecretManager

    return SecretManager()


def get_api_key_store() -> ApiKeyStore:
    """Return the API key store singleton."""
    from integrations.repositories import get_api_key_store as _repo_get

    return _repo_get()


def get_llm_adapter():
    """Get the LLM adapter instance for the gateway."""
    from services.common.llm_adapter import LLMAdapter
    from services.common.secret_manager import SecretManager

    base_url = os.environ.get("SA01_LLM_BASE_URL") or None
    # Prefer per-call secret retrieval to avoid stale keys.
    sm = SecretManager()

    def api_key_resolver():
        return sm.get("provider:openai")  # returns awaitable

    return LLMAdapter(service_url=base_url, api_key_resolver=api_key_resolver)


def get_llm_client():
    """Retrieve llm client."""

    return get_llm_adapter()


def get_asset_store():
    """Get the AssetStore instance for multimodal assets."""
    from services.common.asset_store import AssetStore

    return AssetStore(dsn=os.environ.get("SA01_DB_DSN", ""))


def get_multimodal_executor():
    """Get the MultimodalExecutor instance for multimodal job execution."""
    from services.tool_executor.multimodal_executor import MultimodalExecutor

    return MultimodalExecutor(dsn=os.environ.get("SA01_DB_DSN", ""))


def get_session_store():
    """Get Django ORM Session model."""
    from admin.core.models import Session

    return Session.objects


async def get_temporal_client():
    """Return a singleton Temporal client for the gateway."""
    global _TEMPORAL_CLIENT, _TEMPORAL_LOCK
    from temporalio.client import Client

    if _TEMPORAL_LOCK is None:
        import asyncio

        _TEMPORAL_LOCK = asyncio.Lock()

    async with _TEMPORAL_LOCK:
        if _TEMPORAL_CLIENT is None:
            host = os.environ.get("SA01_TEMPORAL_HOST", "temporal:7233")
            _TEMPORAL_CLIENT = await Client.connect(host)
        return _TEMPORAL_CLIENT
