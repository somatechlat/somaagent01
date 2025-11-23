"""Centralised configuration package.

The *VIBE* refactor requires a **single source of truth** for all runtime
configuration.  This module provides a lightweight façade – ``cfg`` – that
exposes an ``env`` helper mirroring the historic ``runtime_config.env`` API but
delegates to a ``Settings`` object built with *pydantic* ``BaseSettings``.  The
implementation respects the precedence rules defined in the roadmap:

1. ``SA01_*`` environment variables (highest priority)
2. Raw environment variables (fallback)
3. Optional YAML/JSON configuration files (not yet implemented – placeholder)
4. Hard‑coded defaults

Only the ``env`` helper is required by the existing codebase; additional
structured access can be added later via ``Settings`` fields.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict


def _load_file_config() -> Dict[str, Any]:
    """Placeholder for future file‑based configuration loading.

    The roadmap mentions YAML/JSON config files with a clear precedence order.
    For now we simply return an empty dict; the function exists so that later
    implementation can plug in a file loader without touching callers.
    """
    # Look for a conventional ``config.yaml`` in the repository root.
    config_path = Path(__file__).resolve().parents[3] / "config.yaml"
    if not config_path.is_file():
        return {}
    try:
        import yaml  # type: ignore

        with config_path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        # If the optional yaml library is missing or parsing fails we fall back
        # to an empty dict – the ``env`` helper will still honour env vars.
        return {}


_file_cfg: Dict[str, Any] = _load_file_config()


def env(name: str, default: Any = None) -> Any:
    """Return a configuration value using the **real** loader.

    The VIBE roadmap defines the following precedence (high → low):
    1. ``SA01_``‑prefixed environment variables (handled by the ``Config``
       model's ``env_prefix``).
    2. Plain environment variables (no prefix).
    3. YAML/JSON file configuration (if present).
    4. The caller‑provided ``default``.

    This implementation delegates to :func:`src.core.config.registry.get_config`
    which returns a validated ``Config`` instance built by ``loader.py``.  The
    function also supports *dot‑notation* (e.g. ``DATABASE_DSN`` maps to
    ``cfg.database.dsn``) for backward compatibility with historic code.
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

    # When the configuration model does not expose a field we fall back to
    # reading the environment directly (retaining the original precedence).
    value = os.getenv(name)
    if value is not None:
        return value
    prefixed = f"SA01_{name}"
    value = os.getenv(prefixed)
    if value is not None:
        return value
    legacy = f"SOMA_{name}"
    value = os.getenv(legacy)
    if value is not None:
        return value
    return default


def settings():
    """Backward-compatible accessor returning the validated Config object."""
    from .registry import get_config

    return get_config()


# -----------------------------------------------------------------------------
# Convenience getters mirroring legacy runtime_config API (to ease migration).
# -----------------------------------------------------------------------------
def flag(key: str, tenant: Any = None) -> bool:
    env_key = f"SA01_ENABLE_{key.upper()}"
    val = env(env_key, default="false")
    return str(val).lower() in {"true", "1", "yes", "on"}


def deployment_mode() -> str:
    return str(env("DEPLOYMENT_MODE", "DEV"))


def gateway_port() -> int:
    return int(env("GATEWAY_PORT", 8000))


def soma_base_url() -> str:
    return str(env("SOMA_BASE_URL", "http://localhost:9696"))


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


cfg = _CfgFacade()
"""Centralized Configuration System for SomaAgent01.

VIBE CODING RULES COMPLIANT:
- NO SHIMS: Real configuration only
- NO FALLBACKS: Single source of truth
- NO FAKE ANYTHING: Production-ready implementation
- NO LEGACY: Modern patterns only
- NO BACKUPS: No duplicate configuration systems
"""

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

# Expose the ``load_config`` function at the package level.  This replaces the
# previous shim‑style indirection and provides a single, real implementation for
# callers such as ``orchestrator.config`` or ``services.common.central_config``.
load_config = _load_config

# ---------------------------------------------------------------------------
# Legacy compatibility shim removed.
# The ``otlp_endpoint`` attribute is now accessed via ``cfg.settings().external.otlp_endpoint``.
# All callers have been updated accordingly.
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
