"""Compatibility facade that forwards all configuration access to the canonical
``src.core.config`` package.

The previous implementation duplicated a bespoke ``FeatureRegistry`` and
shadowed fields that already exist on the central ``Config`` model.  That split
created drift (e.g., mismatched gateway/port names and stale defaults).  To
enforce *one* configuration surface, this module now acts as a very thin proxy
over ``src.core.config``:

- Accessors delegate directly to the validated Pydantic ``Config`` instance
  returned by ``cfg.settings()``.
- Feature flags reuse the central model's ``feature_flags`` mapping and fall
  back to the shared feature registry defined in ``services.common.features``.

No additional state is cached here; callers importing this module will always
observe the same data as any other consumer of ``src.core.config``.
"""

from __future__ import annotations

from typing import Optional

from services.common.features import build_default_registry
from src.core.config import cfg

# --------------------------------------------------------------------------- #
# Core accessors – all values come from the single validated Config instance. #
# --------------------------------------------------------------------------- #

def _settings():
    """Return the canonical Config instance."""
    return cfg.settings()


def deployment_mode() -> str:
    return _settings().service.deployment_mode


def gateway_port() -> int:
    return _settings().service.port


def soma_base_url() -> str:
    return _settings().external.somabrain_base_url


def postgres_dsn() -> str:
    return _settings().database.dsn


def redis_url() -> str:
    return _settings().redis.url


def kafka_bootstrap_servers() -> str:
    return _settings().kafka.bootstrap_servers


def opa_url() -> str:
    return _settings().external.opa_url


# --------------------------------- Flags ---------------------------------- #

def flag(key: str, tenant: Optional[str] = None) -> bool:
    """Return a feature flag value.

    Order of precedence:
    1) Explicit entry in ``Config.feature_flags`` (per‑process overrides).
    2) Default registry profile resolution (``services.common.features``).
    """
    overrides = _settings().feature_flags or {}
    if key in overrides:
        return bool(overrides[key])
    try:
        return build_default_registry().is_enabled(key)
    except Exception:
        return False


# Legacy helper retained for compatibility with a few scripts.
def registry():
    return cfg.settings()


__all__ = [
    "deployment_mode",
    "gateway_port",
    "soma_base_url",
    "postgres_dsn",
    "redis_url",
    "kafka_bootstrap_servers",
    "opa_url",
    "flag",
    "registry",
]
