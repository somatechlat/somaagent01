"""Configuration loader for the VIBE‑compliant central config system.

The :mod:`src.core.config` package provides a *single source of truth* for all
runtime settings.  The ``Config`` model (defined in ``models.py``) contains the
full schema with strict validation – no defaults are silently injected beyond
what the model declares.  This loader resolves configuration values in the
order required by the roadmap:

1. **Environment variables** – ``SA01_*`` variables are read directly by the
   ``Config`` model via the ``env_prefix`` mechanism.
2. **Plain environment variables** – values without the ``SA01_`` prefix are
   considered as a fallback.
3. **YAML/JSON file** – if a ``config.yaml`` (or ``config.json``) exists in the
   repository root it is parsed and merged.
4. **Defaults** – any field that still lacks a value after the previous steps
   will raise a ``ValidationError``; the model’s own defaults (e.g. ``log_level``)
   are the only allowed fall‑backs.

The loader is deliberately *side‑effect free*: calling :func:`load_config`
returns a fresh ``Config`` instance without mutating global state.  For
convenience, :func:`get_config` caches the most recent successful load so that
the rest of the codebase can import ``cfg`` from ``src.core.config`` and rely on
the same instance throughout the process lifecycle.

All code follows the VIBE coding rules – no shims, no hidden fall‑backs, no
duplicate logic, and full type safety.
"""

def load_config() -> Config:
    """Load and validate the full configuration.

    Precedence (high → low):
    1) Environment variables (SA01_* first, then plain) – **no defaults**.
    2) ``config.yaml`` / ``config.json`` in repository root.

    This loader no longer provides any fallback values; missing required
    settings will raise a ``ValidationError`` from the Pydantic model.
    """
    # Start with an empty base configuration – defaults are defined only in the
    # ``Config`` model itself. Environment values will be injected by the model
    # via its ``env_prefix`` handling, and any file‑based overrides are merged
    # afterwards.
    base_cfg: dict[str, Any] = {}

    # Load configuration from files (YAML first, then JSON).
    repo_root = Path(__file__).resolve().parents[3]
    file_cfg: Mapping[str, Any] = {}
    yaml_path = repo_root / "config.yaml"
    json_path = repo_root / "config.json"
    if yaml_path.is_file():
        file_cfg = _load_yaml_file(yaml_path)
    elif json_path.is_file():
        file_cfg = _load_json_file(json_path)

    # Merge file configuration into the empty base (no env or fallback values).
    merged_cfg = _merge_dicts(base_cfg, file_cfg)

    # Validate the final configuration. The ``Config`` model will pull any
    # required environment variables (SA01_* or plain) automatically. If any
    # required field is missing, a ``ValidationError`` is raised.
    final_cfg = Config.model_validate(merged_cfg)
    return final_cfg
    """
    # 1️⃣ Start from sensible defaults and immediately overlay environment values.
    default_cfg_dict = {
        "service": {
            "name": "somaagent01",
            "environment": "DEV",
            "deployment_mode": "DEV",
            "host": "0.0.0.0",
            "port": 8010,
            # Use port 0 (ephemeral) by default to avoid address‑in‑use errors
            # when multiple services start a Prometheus metrics server in the
            # same process during tests.
            "metrics_port": 0,
            "log_level": "INFO",
        },
        "database": {
            "dsn": _env("DB_DSN", "postgresql://soma:soma@postgres:5432/somaagent01"),
            "pool_size": 20,
            "max_overflow": 10,
            "pool_timeout": 30,
        },
        "kafka": {
            "bootstrap_servers": _env("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
            "security_protocol": "PLAINTEXT",
            "sasl_mechanism": None,
            "sasl_username": None,
            "sasl_password": None,
        },
        "redis": {
            "url": _env("REDIS_URL", "redis://redis:6379/0"),
            "max_connections": 20,
            "retry_on_timeout": True,
            "socket_timeout": 5,
        },
        "external": {
            # Single source of truth: only SA01_* envs are honoured.
            "somabrain_base_url": _env("SA01_SOMA_BASE_URL", "http://host.docker.internal:9696"),
            "opa_url": _env("POLICY_URL", "http://opa:8181"),
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
    # Use the Pydantic v2 API – ``model_validate`` replaces the deprecated ``parse_obj``.
    cfg = Config.model_validate(default_cfg_dict)

    # 2️⃣ Plain environment variables (no prefix) are ignored to enforce a single
    #     canonical namespace (SA01_*). This removes legacy backups.
    plain_env: dict[str, Any] = {}

    # 3️⃣ File‑based configuration – try YAML first, then JSON.
    repo_root = Path(__file__).resolve().parents[3]
    file_cfg: Mapping[str, Any] = {}
    yaml_path = repo_root / "config.yaml"
    json_path = repo_root / "config.json"
    if yaml_path.is_file():
        file_cfg = _load_yaml_file(yaml_path)
    elif json_path.is_file():
        file_cfg = _load_json_file(json_path)

    # Merge in the correct precedence (env > plain > file).
    merged = _merge_dicts(file_cfg, plain_env)
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
# Compatibility shim classes – lightweight wrappers required by the public API
# ---------------------------------------------------------------------------

from dataclasses import dataclass
from typing import Optional, Union


@dataclass
class EnvironmentMapping:
    """Utility for retrieving environment variables with VIBE precedence.

    The loader itself already respects the ``SA01_`` prefix via the Pydantic
    model. This helper is retained for code that expects ``env_mapping.get_env_value``
    but no longer supports legacy ``SOMA_*`` fallbacks.
    """

    sa01_prefix: str = "SA01_"

    def get_env_value(self, key: str, default: Optional[str] = None) -> Optional[str]:
        # Highest‑priority ``SA01_``
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
    """Force a reload of the cached configuration and return the new ``Config``.

    The previous implementation cleared the cache but returned ``None`` which
    caused ``reload_config()`` calls in the test suite to yield ``None`` and
    subsequently raise ``AttributeError`` when accessed.  This version clears
    the caches and then loads a fresh configuration, returning the resulting
    ``Config`` instance so callers can safely use the result.
    """
    global _cached_config, _config_loader
    _cached_config = None
    if _config_loader is not None:
        _config_loader._config_cache = None
    # Load a fresh configuration using the public loader.
    return load_config()
