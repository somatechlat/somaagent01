"""Canonical runtime configuration - Zero Legacy Edition.

Provides deterministic configuration resolution via canonical registry.
All access flows through FeatureRegistry with zero legacy patterns.
"""

from __future__ import annotations

from services.common.registry import registry

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
