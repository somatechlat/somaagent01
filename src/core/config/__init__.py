"""Centralised configuration package.

Single source of truth for all runtime configuration.
"""

from __future__ import annotations

import os
from typing import Any


def env(name: str, default: Any = None) -> Any:
    """Return a configuration value using the **real** loader.

    This implementation delegates to :func:`src.core.config.registry.get_config`
    which returns a validated ``Config`` instance built by ``loader.py``.  The
    function also supports *dot‑notation* (e.g. ``DATABASE_DSN`` maps to
    ``cfg.database.dsn``) for convenience.
    """
    # The loader caches the configuration, so a cheap call is fine.
    from .registry import get_config  # Imported lazily to avoid circular imports.

    cfg_obj = get_config()

    # Support dot‑notation: split on '_' and walk the nested Pydantic model.
    if "_" in name:
        parts = name.lower().split("_")
        current: Any = cfg_obj
        for part in parts:
            if hasattr(current, part):
                current = getattr(current, part)
            else:
                current = None
                break
        if current is not None:
            return current

    # Direct attribute access for flat keys (e.g., DEPLOYMENT_MODE).
    if hasattr(cfg_obj, name.lower()):
        return getattr(cfg_obj, name.lower())

    # Fall back to process environment if not mapped in config.
    env_val = os.getenv(name)
    if env_val is not None:
        return env_val

    # Return the caller supplied default.
    return default


def settings():
    """Return the validated Config object."""
    from .registry import get_config

    return get_config()


# -----------------------------------------------------------------------------
# Convenience getters for common configuration values.
# -----------------------------------------------------------------------------
def flag(key: str, tenant: Any = None) -> bool:
    # First check the feature_flags dictionary in the config
    from .registry import get_config

    config = get_config()
    if key.lower() in config.feature_flags:
        return config.feature_flags[key.lower()]

    return False


def deployment_mode() -> str:
    return str(env("DEPLOYMENT_MODE", "DEV"))


def gateway_port() -> int:
    return int(env("GATEWAY_PORT", 8000))


def soma_base_url() -> str:
    """Get SomaBrain base URL.

    VIBE COMPLIANT: Only SA01_SOMA_BASE_URL is supported.
    No legacy SOMA_BASE_URL support.
    """
    cfg_obj = settings()
    url = cfg_obj.external.somabrain_base_url or env("SA01_SOMA_BASE_URL")
    if not url:
        raise RuntimeError(
            "SA01_SOMA_BASE_URL must be set explicitly. No alternate sources allowed per VIBE rules."
        )
    return str(url).rstrip("/")


def postgres_dsn() -> str:
    return str(env("POSTGRES_DSN", "postgresql://postgres:postgres@localhost:5432/soma"))


def redis_url() -> str:
    return str(env("REDIS_URL", "redis://localhost:6379/0"))


def kafka_bootstrap_servers() -> str:
    return str(env("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"))


def opa_url() -> str:
    return str(env("OPA_URL", "http://openfga:8080"))


# Export a convenient singleton that mimics the historic ``runtime_config``
class _CfgFacade:
    def env(self, name: str, default: Any = None) -> Any:  # pragma: no cover – thin wrapper
        return env(name, default)

    def settings(self):
        return settings()

    @property
    def _STATE(self):
        """State attribute for tests."""
        from .registry import get_config

        class StateWrapper:
            def __init__(self, config):
                self.settings = config

            def __getattr__(self, name):
                return getattr(self.settings, name)

        return StateWrapper(get_config())

    @property
    def postgres_dsn(self):
        """Postgres DSN attribute."""
        return postgres_dsn()

    @property
    def redis_url(self):
        """Redis URL attribute."""
        return redis_url()

    def flag(self, key: str, tenant: Any = None) -> bool:  # pragma: no cover
        """Check feature flag.

        Checks the feature_flags dictionary in the config first, then falls back
        to the ``SA01_ENABLE_<KEY>`` environment variable.
        """
        config = self.settings()
        if key.lower() in config.feature_flags:
            return config.feature_flags[key.lower()]

        val = env(f"SA01_ENABLE_{key.upper()}", default="false")
        return str(val).lower() in {"true", "1", "yes", "on"}

    def get_somabrain_url(self) -> str:  # pragma: no cover
        """Return the SomaBrain base URL."""
        return soma_base_url()

    def get_opa_url(self) -> str:  # pragma: no cover
        """Return the OPA service URL."""
        return opa_url()

    def __getattr__(self, name: str):  # pragma: no cover
        """Forward attribute access to the underlying Config instance."""
        return getattr(self.settings(), name)


cfg = _CfgFacade()
"""Centralized Configuration System for SomaAgent01.

Real configuration. Single source of truth.
Production-ready implementation with modern patterns.
"""

# Test support attributes
JWKS_CACHE = {}
APP_SETTINGS = {}

from .loader import (
    ConfigLoader,
    EnvironmentMapping,
    get_config_loader,
    load_config as _load_config,
    reload_config,
)
from .models import (
    AuthConfig,
    Config,
    DatabaseConfig,
    ExternalServiceConfig,
    KafkaConfig,
    RedisConfig,
    ServiceConfig,
)

# Expose the ``load_config`` function at the package level.
load_config = _load_config
from .registry import (
    config_context,
    ConfigRegistry,
    ConfigSubscription,
    get_auth_config,
    get_config,
    get_config_registry,
    get_config_summary,
    get_database_config,
    get_external_config,
    get_extra_config,
    get_feature_flag,
    get_kafka_config,
    get_redis_config,
    get_service_config,
    initialize_config,
    refresh_config,
    subscribe_to_config,
    unsubscribe_from_config,
    validate_config,
)

__all__ = [
    # Models
    "Config",
    "ServiceConfig",
    "DatabaseConfig",
    "KafkaConfig",
    "RedisConfig",
    "ExternalServiceConfig",
    "AuthConfig",
    # Loader
    "ConfigLoader",
    "EnvironmentMapping",
    "get_config_loader",
    "reload_config",
    "load_config",
    # Registry
    "ConfigRegistry",
    "ConfigSubscription",
    "get_config_registry",
    "initialize_config",
    "get_config",
    "refresh_config",
    "subscribe_to_config",
    "unsubscribe_from_config",
    "get_service_config",
    "get_database_config",
    "get_kafka_config",
    "get_redis_config",
    "get_external_config",
    "get_auth_config",
    "get_feature_flag",
    "get_extra_config",
    "config_context",
    "validate_config",
    "get_config_summary",
]

# Single source of truth for all configuration
# This eliminates 5 duplicate configuration systems:
# - services/common/settings_sa01.py
# - services/common/admin_settings.py
# - services/common/runtime_config.py
# - services/common/registry.py
# - services/common/settings_registry.py
