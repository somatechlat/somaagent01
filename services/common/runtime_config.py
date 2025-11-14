"""Canonical runtime configuration - Zero Legacy Edition.

Provides deterministic configuration resolution via canonical registry.
All access flows through FeatureRegistry with zero legacy patterns.
"""

from __future__ import annotations

from typing import Optional

from services.common import env as env_snapshot
from services.common.registry import registry
from services.common.settings_sa01 import SA01Settings

# ---------------------------------------------------------------------------
# Legacy façade – provides the original ``cfg`` API used throughout the codebase
# ---------------------------------------------------------------------------

class _RuntimeState:
    """Simple container for the mutable settings object.

    The original implementation exposed a global ``_STATE`` with a ``settings``
    attribute that could be re‑initialized via ``init_runtime_config``.  We keep
    that contract while delegating the actual values to ``SA01Settings`` which
    itself reads from the environment (or defaults) and is fully compatible with
    the zero‑legacy ``FeatureRegistry``.
    """

    def __init__(self) -> None:
        self.settings: SA01Settings = SA01Settings.from_env()


# Singleton mutable state – mimics the historic module‑level variable.
_STATE: Optional[_RuntimeState] = None


def init_runtime_config() -> None:
    """Re‑initialize the legacy runtime configuration.

    Tests manipulate environment variables between runs.  Calling this function
    rebuilds the internal ``SA01Settings`` instance so that subsequent calls to
    ``settings()`` reflect the updated environment.
    """
    global _STATE
    env_snapshot.refresh()
    _STATE = _RuntimeState()


def settings() -> SA01Settings:
    """Return the mutable ``SA01Settings`` instance.

    If ``init_runtime_config`` has not been called yet, we lazily create the
    state to preserve backward compatibility with code that expects the object
    to exist on first import.
    """
    global _STATE
    if _STATE is None:
        init_runtime_config()
    return _STATE.settings  # type: ignore[return-value]


def env(key: str, default: Optional[str] = None) -> str:
    """Legacy ``cfg.env`` accessor backed by the canonical environment snapshot."""
    value = env_snapshot.get(key, default)
    if value is None:
        return ""
    return value

# ---------------------------------------------------------------------------
# Canonical getters – thin wrappers around the FeatureRegistry for new code.
# ---------------------------------------------------------------------------

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
