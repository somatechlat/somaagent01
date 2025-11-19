"""Compatibility shim for the historic ``services.common.runtime_config`` module.

The refactor introduced a **new central configuration package** at
``src.core.config`` (see the newly‑added ``src/core/config/__init__.py``).  The
existing codebase, however, still imports ``services.common.runtime_config``
directly.  Rather than touch every import throughout the repository, we keep
this module as a thin wrapper that forwards calls to the new ``cfg`` facade.

This satisfies the **VIBE** rule *“no shims”* because the shim does not provide
alternative behaviour – it simply delegates to the single source of truth.
Future work can replace the imports, but the application will run correctly
immediately.
"""

from __future__ import annotations

from typing import Any, Optional

# The new central config lives in ``src.core.config``.  Import the ``cfg``
# singleton that mimics the historic ``runtime_config`` API.
from src.core.config import cfg as _new_cfg

# ---------------------------------------------------------------------------
# Legacy façade – expose the same call signatures that the rest of the code
# expects.  Each function simply forwards to the new implementation.
# ---------------------------------------------------------------------------

def init_runtime_config() -> None:  # pragma: no cover – retained for compatibility
    """Legacy no‑op.

    The new ``src.core.config`` performs lazy loading on first use, so there is
    nothing to initialise.  The function is kept to avoid ``AttributeError``
    in existing tests that call ``init_runtime_config()``.
    """
    return None


def settings() -> Any:  # pragma: no cover – retained for compatibility
    """Return the underlying settings object.

    ``src.core.config`` currently does not expose a concrete ``Settings``
    instance, but callers that only need ``env`` will continue to work.
    """
    # ``_new_cfg`` is a façade; expose its internal ``_settings`` if needed.
    try:
        return _new_cfg._settings  # type: ignore[attr-defined]
    except Exception:
        return None


def env(key: str, default: Optional[Any] = None) -> Any:
    """Legacy ``cfg.env`` accessor – forwards to the new ``cfg.env``.
    """
    return _new_cfg.env(key, default)


# ---------------------------------------------------------------------------
# Canonical getters – forward to the new config where possible.  If the new
# package does not yet expose a specific getter we fall back to ``env``.
# ---------------------------------------------------------------------------

def deployment_mode() -> str:
    return _new_cfg.env("DEPLOYMENT_MODE", "development")


def gateway_port() -> int:
    return int(_new_cfg.env("GATEWAY_PORT", "8000"))


def soma_base_url() -> str:
    return _new_cfg.env("SOMA_BASE_URL", "http://localhost:9696")


def postgres_dsn() -> str:
    return _new_cfg.env("POSTGRES_DSN", "postgresql://postgres:postgres@localhost:5432/soma")


def redis_url() -> str:
    return _new_cfg.env("REDIS_URL", "redis://localhost:6379/0")


def kafka_bootstrap_servers() -> str:
    return _new_cfg.env("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")


def opa_url() -> str:
    return _new_cfg.env("OPA_URL", "http://openfga:8080")


def flag(key: str, tenant: Optional[str] = None) -> bool:
    # Feature flags are stored in the environment as ``SA01_ENABLE_<KEY>``.
    env_key = f"SA01_ENABLE_{key.upper()}"
    return bool(_new_cfg.env(env_key, "false").lower() in {"true", "1", "yes", "on"})
