"""Canonical runtime configuration - Zero Legacy Edition.

Provides deterministic configuration resolution via canonical registry.
All access flows through FeatureRegistry with zero legacy patterns.
"""

from __future__ import annotations

from services.common.registry import registry
import os
from typing import Optional

def env(key: str, default: Optional[str] = None) -> str:
    """Retrieve an environment variable with an optional default.

    This helper restores the legacy ``cfg.env`` accessor expected by various
    modules (e.g., ``settings_sa01``). It intentionally bypasses the feature
    registry to provide a straightforward, fail‑closed configuration source.
    """
    # ``os.getenv`` returns ``None`` when the variable is missing; we coerce to
    # ``str`` to match the original return type expectations.
    return os.getenv(key, default) or ""

# Canonical exports - no legacy patterns
def deployment_mode() -> str:
    """Return canonical deployment mode."""
    return registry().deployment_mode()

def gateway_port() -> int:
    """Return canonical gateway port."""
    return registry().gateway_port()

def soma_base_url() -> str:
    """Return canonical Somabrain base URL."""
    return registry().soma_base_url()

def postgres_dsn() -> str:
    """Return canonical Postgres DSN."""
    return registry().postgres_dsn()

def redis_url() -> str:
    """Return canonical Redis URL."""
    return registry().redis_url()

def kafka_bootstrap_servers() -> str:
    """Return canonical Kafka bootstrap servers."""
    return registry().kafka_bootstrap_servers()

def opa_url() -> str:
    """Return canonical OPA URL."""
    return registry().opa_url()

def flag(key: str, tenant: Optional[str] = None) -> bool:
    """Return canonical feature flag state."""
    return registry().flag(key, tenant)
