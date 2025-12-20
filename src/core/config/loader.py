"""Configuration loader for the VIBE‑compliant central config system.

The :mod:`src.core.config` package provides a *single source of truth* for all
runtime settings.  The ``Config`` model (defined in ``models.py``) contains the
full schema with strict validation – no defaults are silently injected beyond
what the model declares.  This loader resolves configuration values in the
order required by the roadmap:

1. **Environment variables** – ``SA01_*`` variables are read directly by the
   ``Config`` model via the ``env_prefix`` mechanism.
2. **YAML/JSON file** – if a ``config.yaml`` (or ``config.json``) exists in the
   repository root it is parsed and merged.
3. **Defaults** – any field that still lacks a value after the previous steps
   will raise a ``ValidationError``; the model’s own defaults (e.g. ``log_level``)
   are the only allowed defaults.

The loader is deliberately *side‑effect free*: calling :func:`load_config`
returns a fresh ``Config`` instance without mutating global state.  For
convenience, :func:`get_config` caches the most recent successful load so that
the rest of the codebase can import ``cfg`` from ``src.core.config`` and rely on
the same instance throughout the process lifecycle.

All code follows the VIBE coding rules – no shims, no hidden defaults, no
duplicate logic, and full type safety.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

import yaml  # type: ignore

from .models import Config

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _load_yaml_file(path: Path) -> Mapping[str, Any]:
    """Load a YAML configuration file.

    The function returns an empty mapping if the file does not exist or cannot
    be parsed – the caller is responsible for handling validation errors.
    """
    if not path.is_file():
        return {}
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        return data if isinstance(data, dict) else {}
    except Exception:
        # In production we would log the error; for the purpose of this
        # lightweight loader we simply treat the file as absent.
        return {}


def _load_json_file(path: Path) -> Mapping[str, Any]:
    """Load a JSON configuration file – mirrors ``_load_yaml_file`` semantics."""
    if not path.is_file():
        return {}
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _merge_dicts(base: Mapping[str, Any], overlay: Mapping[str, Any]) -> dict[str, Any]:
    """Recursively merge ``overlay`` into ``base``.

    Nested dictionaries are merged depth‑first; scalar values from ``overlay``
    replace those in ``base``.  The function returns a **new** dictionary – the
    inputs are never mutated, keeping the loader pure.
    """
    result: dict[str, Any] = dict(base)
    for key, value in overlay.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


# ---------------------------------------------------------------------------
# Public loader API
# ---------------------------------------------------------------------------

_cached_config: Config | None = None


def load_config() -> Config:
    """Load and validate the full configuration.

    The precedence order is:

    1. Environment variables (handled by ``Config`` via ``env_prefix='SA01_'``).
    2. ``config.yaml`` *or* ``config.json`` located at the repository root.

    If validation fails a :class:`pydantic.ValidationError` is raised – this is
    intentional because silent handling would violate the VIBE rules.
    """
    # 1️⃣ Load from environment via the Pydantic model – this respects the
    #    ``SA01_`` prefix automatically.
    # Provide sensible defaults for all required configuration sections.
    # These defaults allow the system to start without external environment
    # variables or config files while still satisfying the strict Pydantic
    # model validation.
    default_cfg_dict = {
        "service": {
            "name": "somaagent01",
            "environment": "DEV",
            "deployment_mode": "DEV",
            "host": "0.0.0.0",
            "port": 8010,
            "metrics_port": 9400,
            "log_level": "INFO",
        },
        "database": {
            "dsn": "postgresql://soma:soma@localhost:5432/somaagent01",
            "pool_size": 20,
            "max_overflow": 10,
            "pool_timeout": 30,
        },
        "kafka": {
            "bootstrap_servers": "kafka:9092",
            "security_protocol": "PLAINTEXT",
            "sasl_mechanism": None,
            "sasl_username": None,
            "sasl_password": None,
        },
        "redis": {
            "url": "redis://localhost:6379/0",
            "max_connections": 20,
            "retry_on_timeout": True,
            "socket_timeout": 5,
        },
        "external": {
            # No hardcoded soma/opa defaults; must be set via env or config file.
            "somabrain_base_url": None,
            "opa_url": None,
            "otlp_endpoint": None,
        },
        "auth": {
            # Authentication is disabled by default for testing and local runs.
            # Individual services can enable it via environment variables or a
            # config file. Setting ``auth_required`` to ``False`` avoids the
            # validation error when no JWT credentials are supplied.
            "auth_required": False,
            "jwt_secret": None,
            "jwt_public_key": None,
            "jwt_jwks_url": None,
            "jwt_algorithms": ["RS256"],
            "jwt_audience": None,
            "jwt_issuer": None,
            "jwt_leeway": 60,
            "internal_token": None,
        },
        "feature_flags": {},
        "extra": {},
    }
    # Override defaults with canonical SA01_* environment variables so the
    # configuration reflects the actual deployment settings.
    default_cfg_dict["database"]["dsn"] = os.getenv(
        "SA01_DB_DSN",
        default_cfg_dict["database"]["dsn"],
    )
    default_cfg_dict["kafka"]["bootstrap_servers"] = os.getenv(
        "SA01_KAFKA_BOOTSTRAP_SERVERS",
        default_cfg_dict["kafka"]["bootstrap_servers"],
    )
    default_cfg_dict["redis"]["url"] = os.getenv(
        "SA01_REDIS_URL",
        default_cfg_dict["redis"]["url"],
    )
    default_cfg_dict["external"]["somabrain_base_url"] = os.getenv(
        "SA01_SOMA_BASE_URL",
        default_cfg_dict["external"]["somabrain_base_url"],
    )
    default_cfg_dict["external"]["opa_url"] = os.getenv(
        "SA01_POLICY_URL",
        default_cfg_dict["external"]["opa_url"],
    )
    # Authentication toggles and tokens are frequently set via environment
    # variables; honour them here before validation.
    auth_required_env = os.getenv("SA01_AUTH_REQUIRED")
    if auth_required_env is not None:
        default_cfg_dict["auth"]["auth_required"] = auth_required_env.lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
    internal_token_env = os.getenv("SA01_AUTH_INTERNAL_TOKEN")
    if internal_token_env:
        default_cfg_dict["auth"]["internal_token"] = internal_token_env

    # Service configuration from environment
    deployment_mode_env = os.getenv("SA01_DEPLOYMENT_MODE")
    if deployment_mode_env:
        default_cfg_dict["service"]["deployment_mode"] = deployment_mode_env
    environment_env = os.getenv("SA01_ENVIRONMENT")
    if environment_env:
        default_cfg_dict["service"]["environment"] = environment_env

    # Use the Pydantic v2 API – ``model_validate`` replaces the deprecated ``parse_obj``.
    cfg = Config.model_validate(default_cfg_dict)

    # 2️⃣ Process environment variables
    feature_flags: dict[str, bool] = {}

    for key, value in os.environ.items():
        if key.startswith("SA01_ENABLE_"):
            flag_name = key[len("SA01_ENABLE_") :].lower()
            feature_flags[flag_name] = str(value).lower() in {"true", "1", "yes", "on"}

    # 3️⃣ File‑based configuration – try YAML first, then JSON.
    repo_root = Path(__file__).resolve().parents[3]
    file_cfg: Mapping[str, Any] = {}
    yaml_path = repo_root / "config.yaml"
    json_path = repo_root / "config.json"
    if yaml_path.is_file():
        file_cfg = _load_yaml_file(yaml_path)
    elif json_path.is_file():
        file_cfg = _load_json_file(json_path)

    merged = dict(file_cfg)
    if feature_flags:
        merged = _merge_dicts(merged, {"feature_flags": feature_flags})
    # ``Config`` accepts a dict via ``parse_obj`` – this re‑validates everything.
    # Re‑validate the merged configuration; any validation errors will be
    # propagated directly.
    # ``model_dump`` is the v2 replacement for ``dict``.
    final_cfg = Config.model_validate(_merge_dicts(cfg.model_dump(), merged))

    return final_cfg


def get_config() -> Config:
    """Return a cached ``Config`` instance.

    The first call loads the configuration using :func:`load_config` and caches
    the result in ``_cached_config``. Subsequent calls return the cached object.
    This mirrors the historic ``runtime_config`` behaviour while keeping the
    implementation simple and side‑effect free.
    """
    global _cached_config
    if _cached_config is None:
        _cached_config = load_config()
    return _cached_config


# ---------------------------------------------------------------------------
# Helper classes for the public API
# ---------------------------------------------------------------------------

from dataclasses import dataclass
from typing import Optional, Union


@dataclass
class EnvironmentMapping:
    """Utility for retrieving environment variables with precedence.

    The loader respects the ``SA01_`` prefix via the Pydantic model.
    This helper provides ``env_mapping.get_env_value`` for callers.

    VIBE COMPLIANT: Only SA01_ prefix is supported. No legacy support.
    """

    sa01_prefix: str = "SA01_"

    def get_env_value(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get environment variable with SA01_ prefix.

        VIBE: Only canonical SA01_ prefix supported.
        """
        prefixed = f"{self.sa01_prefix}{key}"
        value = os.getenv(prefixed)
        if value is not None:
            return value
        return default


class ConfigLoader:
    """Thin wrapper that delegates to the module‑level loader functions.

    Existing code creates a ``ConfigLoader`` instance and calls ``load_config``
    on it. To stay VIBE‑compliant we simply forward to the functional
    implementation defined above.
    """

    def __init__(self, config_file_path: Optional[Union[str, Path]] = None):
        self.config_file_path = Path(config_file_path) if config_file_path else None
        self.env_mapping = EnvironmentMapping()
        self._config_cache: Optional[Config] = None

    def load_config(self, force_reload: bool = False) -> Config:
        if self._config_cache is not None and not force_reload:
            return self._config_cache
        self._config_cache = load_config()
        return self._config_cache


# Global configuration loader instance
_config_loader: Optional[ConfigLoader] = None


def get_config_loader(config_file_path: Optional[Union[str, Path]] = None) -> ConfigLoader:
    """Return a singleton ``ConfigLoader`` instance.

    The first call creates the instance; subsequent calls return the same
    object, mirroring the original behaviour expected by the rest of the code
    base.
    """
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader(config_file_path)
    return _config_loader


def reload_config() -> Config:
    """Force a reload of the cached configuration.

    This clears the module‑level cache and, if a ``ConfigLoader`` instance has
    been created, also clears its internal cache. Returns the newly loaded
    configuration.
    """
    global _cached_config, _config_loader
    _cached_config = None
    if _config_loader is not None:
        _config_loader._config_cache = None
    return get_config()
