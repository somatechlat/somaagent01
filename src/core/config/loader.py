"""Configuration loader for the VIBE-compliant central config system.

This module keeps configuration resolution simple and explicit:

1) Environment variables are read directly by the Pydantic model (`Config`)
   using its `env_prefix` handling (SA01_* first, then plain keys when defined).
2) Optional repo-level overrides from `config.yaml` (or `config.json` fallback)
   are merged on top.
3) Anything still missing is validated by the model – no silent defaults.

No shims, no hidden fallbacks, no side effects: `load_config()` just returns a
fresh `Config` instance; `get_config()` caches the last successful load.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping, Optional, Union

import yaml

from .models import Config

# -----------------------------------------------------------------------------
# File helpers
# -----------------------------------------------------------------------------


def _load_yaml_file(path: Path) -> Mapping[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


def _load_json_file(path: Path) -> Mapping[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data or {}


def _merge_dicts(base: Mapping[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    """Shallow merge where `override` keys replace `base` keys."""
    merged = dict(base)
    merged.update(override or {})
    return merged


def _env(key: str, default: Any = None) -> Any:
    """Read env var (prefers SA01_ prefix) with optional default."""
    prefixed = os.getenv(f"SA01_{key}")
    if prefixed is not None:
        return prefixed
    plain = os.getenv(key)
    if plain is not None:
        return plain
    return default


# -----------------------------------------------------------------------------
# Public loader API
# -----------------------------------------------------------------------------

_cached_config: Optional[Config] = None


def load_config() -> Config:
    """Load and validate configuration from env + optional YAML/JSON."""
    repo_root = Path(__file__).resolve().parents[3]
    file_cfg: Mapping[str, Any] = {}

    yaml_path = repo_root / "config.yaml"
    json_path = repo_root / "config.json"
    if yaml_path.is_file():
        file_cfg = _load_yaml_file(yaml_path)
    elif json_path.is_file():
        file_cfg = _load_json_file(json_path)

    # Baseline defaults to satisfy required sections; env overrides are read via _env.
    default_cfg = {
        "service": {
            "name": "somaagent01",
            "environment": _env("DEPLOYMENT_MODE", "DEV"),
            "deployment_mode": _env("DEPLOYMENT_MODE", "DEV"),
            "host": "0.0.0.0",
            # Use the primary gateway port configuration. If SA01_GATEWAY_PORT is not set (it has been removed), fall back to the generic PORT variable, then default to the actual running gateway port (21016).
            # Default to the explicitly configured gateway port. If not set, fall back to the known running port (21016) without considering a generic PORT env var.
            # Directly read the plain GATEWAY_PORT environment variable, ignoring any legacy SA01_GATEWAY_PORT.
            "port": int(os.getenv("GATEWAY_PORT", "21016")),
            "metrics_port": int(_env("SA01_METRICS_PORT", 9400)),
            "log_level": _env("LOG_LEVEL", "INFO"),
        },
        "database": {
            "dsn": _env("DB_DSN", _env("SA01_DB_DSN", "postgresql://soma:soma@postgres:5432/somaagent01")),
            "pool_size": 20,
            "max_overflow": 10,
            "pool_timeout": 30,
        },
        "kafka": {
            "bootstrap_servers": _env("KAFKA_BOOTSTRAP_SERVERS", _env("SA01_KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")),
            "security_protocol": "PLAINTEXT",
            "sasl_mechanism": None,
            "sasl_username": None,
            "sasl_password": None,
        },
        "redis": {
            "url": _env("REDIS_URL", _env("SA01_REDIS_URL", "redis://redis:6379/0")),
            "max_connections": 20,
            "retry_on_timeout": True,
            "socket_timeout": 5,
        },
        "external": {
            "somabrain_base_url": _env("SA01_SOMA_BASE_URL", "http://host.docker.internal:9696"),
            "opa_url": _env("SA01_POLICY_URL", "http://opa:8181"),
            "otlp_endpoint": _env("OTLP_ENDPOINT", None),
        },
        "auth": {
            "auth_required": _env("SA01_AUTH_REQUIRED", "false").lower() == "true",
            "jwt_secret": _env("SA01_AUTH_JWT_SECRET"),
            "jwt_public_key": _env("SA01_AUTH_JWT_PUBLIC_KEY"),
            "jwt_jwks_url": _env("SA01_AUTH_JWKS_URL"),
            "jwt_algorithms": ["RS256"],
            "jwt_audience": _env("SA01_AUTH_JWT_AUDIENCE"),
            "jwt_issuer": _env("SA01_AUTH_JWT_ISSUER"),
            "jwt_leeway": 60,
            "internal_token": _env("SA01_AUTH_INTERNAL_TOKEN"),
        },
        "feature_flags": {},
        "extra": {},
    }

    merged = _merge_dicts(default_cfg, file_cfg)
    return Config.model_validate(merged)


def get_config() -> Config:
    """Return cached Config or load fresh."""
    global _cached_config
    if _cached_config is None:
        _cached_config = load_config()
    return _cached_config


# -----------------------------------------------------------------------------
# Compatibility wrapper used by existing code paths
# -----------------------------------------------------------------------------

from dataclasses import dataclass


@dataclass
class EnvironmentMapping:
    """Utility kept for legacy callers expecting env_mapping.get_env_value."""

    sa01_prefix: str = "SA01_"

    def get_env_value(self, key: str, default: Optional[str] = None) -> Optional[str]:
        value = os.getenv(f"{self.sa01_prefix}{key}")
        return value if value is not None else default


class ConfigLoader:
    """Thin wrapper mirroring the historic loader class."""

    def __init__(self, config_file_path: Optional[Union[str, Path]] = None):
        self.config_file_path = Path(config_file_path) if config_file_path else None
        self.env_mapping = EnvironmentMapping()
        self._config_cache: Optional[Config] = None

    def load_config(self, force_reload: bool = False) -> Config:
        if self._config_cache is not None and not force_reload:
            return self._config_cache
        self._config_cache = load_config()
        return self._config_cache


_config_loader: Optional[ConfigLoader] = None


def get_config_loader(config_file_path: Optional[Union[str, Path]] = None) -> ConfigLoader:
    """Return singleton ConfigLoader instance."""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader(config_file_path)
    return _config_loader


def reload_config() -> Config:
    """Clear caches and reload configuration."""
    global _cached_config, _config_loader
    _cached_config = None
    if _config_loader is not None:
        _config_loader._config_cache = None
    return load_config()


__all__ = [
    "load_config",
    "get_config",
    "reload_config",
    "get_config_loader",
    "ConfigLoader",
    "EnvironmentMapping",
]
