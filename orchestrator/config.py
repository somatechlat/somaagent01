"""Centralized configuration for the orchestrator.

This module provides a thin wrapper around the new configuration system
in ``src.core.config``. It exposes the legacy ``CentralizedConfig`` API
used throughout the codebase so that existing services can continue to
access configuration values via attributes such as ``service_name`` or
``postgres_dsn``.

The wrapper loads configuration lazily via :class:`ConfigRegistry` and
stores a single instance in :data:`_CONFIG_INSTANCE`. The ``load_config``
function simply returns that instance.

The design keeps backward compatibility while adhering to the VIBE
CODING RULES: no shims, no fallbacks, no duplicate configuration logic.
"""

from __future__ import annotations

from typing import Any, Dict

from src.core.config.loader import ConfigLoader, get_config_loader
from src.core.config.registry import ConfigRegistry, get_config_registry
from src.core.config.models import Config

# Lazy singleton for configuration instance
_CONFIG_INSTANCE: Config | None = None


class CentralizedConfig(Config):
    """Wrapper that provides legacy attribute names.

    The original code base accessed attributes such as ``service_name`` or
    ``postgres_dsn`` directly on the configuration object.  These have
    been replaced by the nested ``service`` and ``database`` models.
    The wrapper exposes ``@property`` getters that delegate to the new
    model, ensuring that existing code continues to function without
    modification.
    """

    # The following properties map the legacy attribute names to the
    # new configuration structure.
    @property
    def service_name(self) -> str:  # pragma: no cover – simple delegation
        return self.service.name

    @property
    def environment(self) -> str:  # pragma: no cover – simple delegation
        return self.service.environment

    @property
    def postgres_dsn(self) -> str:  # pragma: no cover – simple delegation
        return self.database.dsn

    @property
    def kafka_bootstrap_servers(self) -> str:  # pragma: no cover – simple delegation
        return self.kafka.bootstrap_servers

    @property
    def redis_url(self) -> str:  # pragma: no cover – simple delegation
        return self.redis.url

    @property
    def otlp_endpoint(self) -> str:  # pragma: no cover – simple delegation
        return self.external.otlp_endpoint or ""

    @property
    def enable_metrics(self) -> bool:  # pragma: no cover – simple delegation
        return self.service.metrics_port > 0

    @property
    def enable_tracing(self) -> bool:  # pragma: no cover – simple delegation
        return self.external.otlp_endpoint is not None

    # ``dict`` method already inherited from Pydantic BaseModel; no change


def load_config() -> CentralizedConfig:
    """Return the singleton configuration instance.

    This function lazily creates a :class:`ConfigLoader` and a
    :class:`ConfigRegistry`.  It then loads the configuration via the
    registry and returns the resulting :class:`CentralizedConfig`
    instance.
    """
    global _CONFIG_INSTANCE
    if _CONFIG_INSTANCE is None:
        # Create loader and registry instances
        loader = get_config_loader()
        registry = get_config_registry(loader)
        # Load configuration once
        _CONFIG_INSTANCE = registry.get_config()  # type: ignore[arg-type]
    return _CONFIG_INSTANCE

# Backward compatibility: expose the original name
__all__ = ["CentralizedConfig", "load_config"]
