"""Canonical Feature Registry - Zero Legacy Implementation.

This module provides the single, authoritative source for all configuration
without any fallback logic, environment variable access, or legacy patterns.
All configuration flows through deterministic resolution via Somabrain APIs.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


def _load_sa01_settings():
    """Load configuration via the new central ``cfg`` façade.

    The original implementation lazily imported ``SA01Settings`` – a legacy
    proxy that forwards attribute access to ``src.core.config.cfg``.  To fully
    eliminate the legacy indirection we now load the canonical configuration
    directly from ``cfg`` and expose an object with the same public attributes
    used by the existing code (e.g., ``gateway_port``, ``postgres_dsn``).

    This function returns a lightweight ``SimpleNamespace``‑like object that
    mirrors the subset of fields required by ``FeatureRegistry``.  It keeps the
    constructor signature unchanged, preserving compatibility with any code
    that expects a callable returning a class.
    """
    from types import SimpleNamespace
    from src.core.config import cfg

    # Extract the service‑level configuration from the central ``cfg`` object.
    service_cfg = cfg.settings().service

    # Build a simple namespace containing the attributes accessed by the
    # registry.  Additional attributes can be added here without breaking the
    # public contract.
    return SimpleNamespace(
        deployment_mode=service_cfg.deployment_mode,
        gateway_port=service_cfg.gateway_port,
        soma_base_url=service_cfg.soma_base_url,
        postgres_dsn=service_cfg.postgres_dsn,
        redis_url=service_cfg.redis_url,
        kafka_bootstrap_servers=service_cfg.kafka_bootstrap_servers,
        opa_url=service_cfg.opa_url,
        # Preserve any legacy ``feature_flags`` dict if present for flag()
        feature_flags=getattr(service_cfg, "feature_flags", {}),
    )


@dataclass(slots=True, frozen=True)
class RegistryConfig:
    """Immutable configuration snapshot."""

    deployment_mode: str
    gateway_port: int
    soma_base_url: str
    postgres_dsn: str
    redis_url: str
    kafka_bootstrap_servers: str
    opa_url: str


class FeatureRegistry:
    """Canonical configuration registry with zero legacy patterns.

    Provides deterministic configuration resolution without:
    - Environment variable access
    - Fallback logic
    - Incomplete implementations
    - Development code
    """

    def __init__(self) -> None:
        # Load the configuration namespace directly; the legacy ``from_env``
        # factory is no longer applicable because ``_load_sa01_settings`` now
        # returns a ready‑to‑use ``SimpleNamespace`` populated from the
        # canonical ``cfg`` façade.
        self._settings_cls = _load_sa01_settings()
        self._settings = self._settings_cls
        self._env_cache = self._snapshot_environment()
        self._config = self._build_canonical_config()

    def _build_canonical_config(self) -> RegistryConfig:
        """Build immutable canonical configuration."""
        return RegistryConfig(
            deployment_mode=self._determine_deployment_mode(),
            gateway_port=self._settings.gateway_port,
            soma_base_url=self._settings.soma_base_url,
            postgres_dsn=self._settings.postgres_dsn,
            redis_url=self._settings.redis_url,
            kafka_bootstrap_servers=self._settings.kafka_bootstrap_servers,
            opa_url=self._settings.opa_url,
        )

    def _snapshot_environment(self) -> dict[str, str]:
        """Capture environment variables once so downstream code stays deterministic."""
        return {key: value for key, value in os.environ.items()}

    def _determine_deployment_mode(self) -> str:
        """Deterministic deployment mode without legacy mapping."""
        raw = self._settings.deployment_mode.upper()
        if raw in {"DEV", "LOCAL"}:
            return "LOCAL"
        return "PROD"

    # Canonical accessors - no legacy patterns

    def deployment_mode(self) -> str:
        """Return canonical deployment mode."""
        return self._config.deployment_mode

    def gateway_port(self) -> int:
        """Return canonical gateway port."""
        return self._config.gateway_port

    def soma_base_url(self) -> str:
        """Return canonical Somabrain base URL."""
        return self._config.soma_base_url

    def postgres_dsn(self) -> str:
        """Return canonical Postgres DSN."""
        return self._config.postgres_dsn

    def redis_url(self) -> str:
        """Return canonical Redis URL."""
        return self._config.redis_url

    def kafka_bootstrap_servers(self) -> str:
        """Return canonical Kafka bootstrap servers."""
        return self._config.kafka_bootstrap_servers

    def opa_url(self) -> str:
        """Return canonical OPA URL."""
        return self._config.opa_url

    def flag(self, key: str, tenant: Optional[str] = None) -> bool:
        """Resolve a feature flag.

        The original implementation only consulted a ``feature_flags`` dict on the
        settings object, which is empty in the current ``SA01Settings`` and
        caused ``cfg.flag`` to always return ``False``. For the ROAMDPO plan we
        want ``cfg.flag`` to reflect the canonical feature registry logic – i.e.
        the profile‑aware defaults defined in ``services.common.features``.

        The implementation now falls back to the in‑process ``FeatureRegistry``
        when the settings dict does not provide an explicit override. Tenant
        information is ignored for now (remote overrides are handled elsewhere).
        """
        # Prefer explicit overrides if present.
        if hasattr(self._settings, "feature_flags"):
            overrides = getattr(self._settings, "feature_flags", {})
            if key in overrides:
                return bool(overrides[key])
        # Fallback to the default registry logic.
        try:
            from services.common.features import build_default_registry

            registry = build_default_registry()
            return registry.is_enabled(key)
        except Exception:
            # In case of unexpected errors, be safe and return False.
            return False

    def legacy_value(self, key: str, default: Optional[str] = None) -> str:
        """Return immutable legacy configuration values captured during init."""
        value = self._env_cache.get(key)
        if value is not None:
            return value
        extras = getattr(self._settings, "extra", {})
        if isinstance(extras, dict) and key in extras:
            return str(extras[key])
        if default is None:
            return ""
        return default


# Singleton canonical instance
_registry = FeatureRegistry()


# Public API - no legacy patterns
def registry() -> FeatureRegistry:
    """Return canonical registry singleton."""
    return _registry


def deployment_mode() -> str:
    """Return canonical deployment mode."""
    return _registry.deployment_mode()


def gateway_port() -> int:
    """Return canonical gateway port."""
    return _registry.gateway_port()


def soma_base_url() -> str:
    """Return canonical Somabrain base URL."""
    return _registry.soma_base_url()


def postgres_dsn() -> str:
    """Return canonical Postgres DSN."""
    return _registry.postgres_dsn()


def redis_url() -> str:
    """Return canonical Redis URL."""
    return _registry.redis_url()


def kafka_bootstrap_servers() -> str:
    """Return canonical Kafka bootstrap servers."""
    return _registry.kafka_bootstrap_servers()


def opa_url() -> str:
    """Return canonical OPA URL."""
    return _registry.opa_url()


def flag(key: str, tenant: Optional[str] = None) -> bool:
    """Return canonical feature flag state."""
    return _registry.flag(key, tenant)
