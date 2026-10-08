"""Gateway dependency providers for Django Ninja injection."""

from __future__ import annotations

from django.conf import settings

from config.settings_registry import get_settings
from services.common.api_key_store import ApiKeyStore
from services.common.event_bus import (
    KafkaEventBus,
    KafkaSettings,
    resolve_kafka_sasl_password,
)
from services.common.publisher import DurablePublisher

# Compatibility attributes for test suite
JWKS_CACHE: dict = {}
APP_SETTINGS: dict = {}
# VIBE SECURITY (Rule 164): the JWT signing secret is a credential. It comes
# from Vault at secret/agent/credentials/jwt_secret — never from the
# environment. No empty fallback: a missing key means JWT operations fail fast
# rather than run unsigned.
from services.common.unified_secret_manager import get_secret_manager

_jwt_secret = get_secret_manager().get_credential("jwt_secret")
JWT_SECRET = _jwt_secret or None
_TEMPORAL_CLIENT = None
_TEMPORAL_LOCK = None


def get_event_bus() -> KafkaEventBus:
    """Get event bus instance (alias for get_bus)."""
    return get_bus()


def get_bus() -> KafkaEventBus:
    """Create a Kafka event bus using admin settings."""
    cfg = get_settings()
    kafka_settings = KafkaSettings(
        bootstrap_servers=getattr(settings, "KAFKA_BOOTSTRAP_SERVERS", None)
        or cfg.kafka_bootstrap_servers,
        security_protocol=cfg.kafka_security_protocol,
        sasl_mechanism=cfg.kafka_sasl_mechanism or None,
        sasl_username=cfg.kafka_sasl_username or None,
        sasl_password=resolve_kafka_sasl_password(),
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
    from services.common.unified_secret_manager import get_secret_manager as _get_sm

    return _get_sm()


def get_api_key_store() -> ApiKeyStore:
    """Return the API key store singleton."""
    from integrations.repositories import get_api_key_store as _repo_get  # type: ignore[import]

    return _repo_get()


def get_llm_adapter():
    """Get the LLM adapter instance for the gateway."""
    from services.common.llm_adapter import LLMAdapter
    from services.common.unified_secret_manager import get_secret_manager

    base_url = get_settings().llm_base_url or None
    # Prefer per-call secret retrieval to avoid stale keys.
    sm = get_secret_manager()

    def api_key_resolver():
        return sm.get_provider_key("openai")

    return LLMAdapter(service_url=base_url, api_key_resolver=api_key_resolver)


def get_llm_client():
    """Retrieve llm client."""

    return get_llm_adapter()


def get_asset_store():
    """Get the AssetStore instance for multimodal assets."""
    from services.common.asset_store import AssetStore

    return AssetStore()


def get_multimodal_executor():
    """Get the MultimodalExecutor instance for multimodal job execution."""
    from services.tool_executor.multimodal_executor import MultimodalExecutor

    return MultimodalExecutor()


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
            # Single host authority: SA01_TEMPORAL_HOST, read once in
            # services/gateway/settings.py. Do not use registry.temporal_host
            # here — that was a second connect authority (F07).
            host = (settings.TEMPORAL_HOST or "").strip()
            if not host:
                raise RuntimeError(
                    "SA01_TEMPORAL_HOST is not configured. It is deployment "
                    "topology (operator parameter); there is no default scheduler."
                )
            _TEMPORAL_CLIENT = await Client.connect(host)
        return _TEMPORAL_CLIENT
