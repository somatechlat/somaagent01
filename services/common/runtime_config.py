"""Runtime configuration facade for SomaAgent 01.

Combines static service settings, feature flags, and dynamic config into a
single, importable access surface. This module intentionally keeps transport
concerns out; callers can wire remote updates by invoking the provided
update hooks.

Capabilities (C0 minimal):
- Load `SA01Settings` from environment with environment-based defaults.
- Build a `FeatureRegistry` from local descriptors and profile env.
- Initialize a `ConfigRegistry` using the JSON Schema at
  `schemas/config/registry.v1.schema.json` when available, and load minimal
  defaults if present.
- Provide convenience accessors for flags and config lookups.

Future sprints (C1+):
- Replace scattered env-based feature toggles with `flag()` calls.
- Add checksum + source metrics emission.
- Support tenant-aware remote overrides via callback/provider.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

from observability.metrics import metrics_collector
from services.common.config_registry import ConfigRegistry, ConfigSnapshot
from services.common.features import build_default_registry, FeatureRegistry
from services.common.settings_sa01 import SA01Settings


@dataclass(slots=True)
class _RuntimeState:
    settings: SA01Settings
    features: FeatureRegistry
    config: Optional[ConfigRegistry]
    override_resolver: Optional[Callable[[str, Optional[str]], Optional[bool]]]
    deployment_mode: str
    external_mode: str


_STATE: Optional[_RuntimeState] = None


def _load_config_registry() -> Optional[ConfigRegistry]:
    """Attempt to construct a ConfigRegistry with defaults.

    Returns None if the schema file is missing or invalid. Callers can still
    use flags and settings when the registry is unavailable.
    """
    schema_path = Path(os.getcwd()) / "schemas/config/registry.v1.schema.json"
    if not schema_path.exists():
        return None
    try:
        with schema_path.open("r", encoding="utf-8") as f:
            schema = json.load(f)
        registry = ConfigRegistry(schema)
        # Minimal default payload per schema expectations
        defaults = {"version": "0", "overlays": {}}
        snap = registry.load_defaults(defaults)
        try:
            metrics_collector.record_runtime_config_update(
                version=snap.version, checksum=snap.checksum, source="default"
            )
        except Exception:
            pass
        return registry
    except Exception:
        # If schema or defaults aren't usable, operate without registry
        return None


def init_runtime_config(
    *,
    override_resolver: Optional[Callable[[str, Optional[str]], Optional[bool]]] = None,
) -> None:
    """Initialize the runtime config singleton.

    - `override_resolver`: optional callback receiving `(flag_key, tenant_id)`
      and returning an override boolean or None. This enables tenant-aware
      remote flag overrides without coupling this module to HTTP/Kafka.
    """
    global _STATE
    settings = SA01Settings.from_env()
    features = build_default_registry()
    config = _load_config_registry()
    # Deployment mode centralization
    # External switch via SA01_DEPLOYMENT_MODE (DEV|PROD) overrides prior settings
    ext = (os.getenv("SA01_DEPLOYMENT_MODE") or "").strip().upper()
    if ext not in {"DEV", "PROD", ""}:
        # invalid value -> default to DEV semantics (strict like prod) but log-safe fallback
        ext = "DEV"
    # Determine internal canonical mode used by existing code paths: LOCAL|PROD
    # Map DEV -> LOCAL (development profiles), PROD/STAGING/PRODUCTION -> PROD
    raw_mode = (settings.deployment_mode or "LOCAL").upper()
    if ext:
        external_mode = ext
    else:
        # Derive external from prior envs
        external_mode = "DEV" if raw_mode in {"DEV", "LOCAL"} else "PROD"
    if external_mode == "DEV":
        canonical_mode = "LOCAL"
    else:
        canonical_mode = "PROD"
    _STATE = _RuntimeState(
        settings=settings,
        features=features,
        config=config,
        override_resolver=override_resolver,
        deployment_mode=canonical_mode,
        external_mode=external_mode,
    )
    try:
        # Emit deployment mode metric once at init
        metrics_collector.record_deployment_mode(canonical_mode)
    except Exception:
        pass


def state() -> _RuntimeState:
    global _STATE
    if _STATE is None:
        init_runtime_config()
    assert _STATE is not None
    return _STATE


def set_override_resolver(resolver: Callable[[str, Optional[str]], Optional[bool]]) -> None:
    st = state()
    st.override_resolver = resolver


def settings() -> SA01Settings:  # type: ignore[override]
    """Return the process settings loaded from environment."""
    return state().settings


def deployment_mode() -> str:
    """Return the canonical deployment mode (LOCAL | PROD).

    Collapses historical values (DEV/STAGING/PRODUCTION) into two modes for
    simplified profile selection and conditional behaviour.
    """
    return state().deployment_mode


def external_deployment_mode() -> str:
    """Return external deployment mode switch (DEV | PROD).

    This reflects `SA01_DEPLOYMENT_MODE` if provided; otherwise derived from
    prior settings. DEV is enforced to behave like PROD (no bypass), but
    remains a distinct label for observability/logging.
    """
    return state().external_mode


# Hard delete: no policy bypass functions; all policy checks enforced uniformly


def flag(key: str, tenant_id: Optional[str] = None) -> bool:
    """Resolve a feature flag with optional tenant override.

    Resolution order (C0):
    1) If an `override_resolver` is provided and returns a bool, use it.
    2) Fall back to local FeatureRegistry (profile/env-aware).
    """
    st = state()
    if st.override_resolver is not None:
        try:
            ov = st.override_resolver(key, tenant_id)
        except Exception:
            ov = None
        if ov is not None:
            return bool(ov)
    return st.features.is_enabled(key)


def env(key: str, default: Optional[str] = None) -> str:
    """Centralized environment access.

    Business logic modules should use this instead of calling os.getenv directly.
    Only settings/bootstrap modules may access os.getenv themselves.
    Returns default (or empty string if default is None) when not set.
    """
    val = os.getenv(key)
    if val is None:
        try:
            metrics_collector.record_runtime_config_layer("default")
        except Exception:
            pass
        return "" if default is None else str(default)
    try:
        metrics_collector.record_runtime_config_layer("environment")
    except Exception:
        pass
    return val


def db_dsn(default: Optional[str] = None) -> str:
    """Return canonical Postgres DSN (SA01_DB_DSN) with fallback."""
    val = env("SA01_DB_DSN")
    if val:
        return val
    return default or settings().postgres_dsn


def redis_url(default: Optional[str] = None) -> str:
    """Return canonical Redis URL."""
    val = env("SA01_REDIS_URL")
    if val:
        return val
    return default or settings().redis_url


def kafka_bootstrap_servers(default: Optional[str] = None) -> str:
    """Return canonical Kafka bootstrap servers."""
    val = env("SA01_KAFKA_BOOTSTRAP_SERVERS")
    if val:
        return val
    return default or settings().kafka_bootstrap_servers


def policy_url(default: Optional[str] = None) -> str:
    val = env("SA01_POLICY_URL")
    if val:
        return val
    return default or settings().opa_url


def policy_decision_path(default: Optional[str] = None) -> str:
    val = env("SA01_POLICY_DECISION_PATH")
    if val:
        return val
    return default or ""


def soma_base_url(default: Optional[str] = None) -> str:
    val = env("SA01_SOMA_BASE_URL")
    if val:
        return val
    return default or (settings().soma_base_url or "")


def memory_wal_topic(default: Optional[str] = None) -> str:
    val = env("SA01_MEMORY_WAL_TOPIC")
    if val:
        return val
    return default or "memory.wal"


def conversation_inbound(default: Optional[str] = None) -> str:
    val = env("SA01_CONVERSATION_INBOUND")
    if val:
        return val
    return default or "conversation.inbound"


def conversation_outbound(default: Optional[str] = None) -> str:
    val = env("SA01_CONVERSATION_OUTBOUND")
    if val:
        return val
    return default or "conversation.outbound"


def conversation_group(default: Optional[str] = None) -> str:
    val = env("SA01_CONVERSATION_GROUP")
    if val:
        return val
    return default or "conversation-worker"


def tool_requests_topic(default: Optional[str] = None) -> str:
    val = env("SA01_TOOL_REQUESTS_TOPIC")
    if val:
        return val
    return default or "tool.requests"


def tool_results_topic(default: Optional[str] = None) -> str:
    val = env("SA01_TOOL_RESULTS_TOPIC")
    if val:
        return val
    return default or "tool.results"


def notifications_topic(default: Optional[str] = None) -> str:
    val = env("SA01_UI_NOTIFICATIONS_TOPIC")
    if val:
        return val
    return default or "ui.notifications"


def config_snapshot() -> Optional[ConfigSnapshot]:
    """Return the current config snapshot, if registry is initialized."""
    return state().config.get() if state().config else None


def config_get(path: str, default: Any | None = None) -> Any:
    """Get a value from the current config snapshot using dotted path.

    Example: config_get("overlays.ui.theme", default="light")
    """
    snap = config_snapshot()
    if not snap:
        return default
    try:
        metrics_collector.record_runtime_config_layer("dynamic")
    except Exception:
        pass
    node: Any = snap.payload
    for part in path.split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return default
    return node


def apply_config_update(payload: dict[str, Any]) -> Optional[ConfigSnapshot]:
    """Validate and apply a dynamic config update to the registry.

    Returns the applied snapshot or None if the registry is unavailable.
    Silently ignores invalid updates (returns existing snapshot) while
    recording an error counter in the future (placeholder TODO).
    """
    cfg = state().config
    if not cfg:
        return None
    try:
        snap = cfg.apply_update(payload)
    except Exception:
        return cfg.get()
    try:
        metrics_collector.record_runtime_config_update(
            version=snap.version, checksum=snap.checksum, source="dynamic"
        )
    except Exception:
        pass
    return snap


# Eagerly initialize on import for convenience in long-lived processes
init_runtime_config()
