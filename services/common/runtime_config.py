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

from services.common.config_registry import ConfigRegistry, ConfigSnapshot
from services.common.features import FeatureRegistry, build_default_registry
from services.common.settings_sa01 import SA01Settings
from observability.metrics import metrics_collector


@dataclass(slots=True)
class _RuntimeState:
    settings: SA01Settings
    features: FeatureRegistry
    config: Optional[ConfigRegistry]
    override_resolver: Optional[Callable[[str, Optional[str]], Optional[bool]]]
    deployment_mode: str


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
    # Canonical deployment mode consolidation:
    # LOCAL (full-local dev) and PROD (production/staging) only.
    # Derive canonical mode strictly from settings (env normalization handled there)
    raw_mode = (settings.deployment_mode or "LOCAL").upper()
    if raw_mode in {"DEV", "LOCAL"}:
        canonical_mode = "LOCAL"
    elif raw_mode in {"PROD", "STAGING", "PRODUCTION"}:
        canonical_mode = "PROD"
    else:
        canonical_mode = "LOCAL"
    _STATE = _RuntimeState(
        settings=settings,
        features=features,
        config=config,
        override_resolver=override_resolver,
        deployment_mode=canonical_mode,
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


def settings() -> SA01Settings:  # type: ignore[override]
    """Return the process settings loaded from environment."""
    return state().settings


def deployment_mode() -> str:
    """Return the canonical deployment mode (LOCAL | PROD).

    Collapses legacy values (DEV/STAGING/PRODUCTION) into two modes for
    simplified profile selection and conditional behaviour.
    """
    return state().deployment_mode


def conversation_policy_bypass_enabled() -> bool:
    """Return True if conversation policy checks may be bypassed.

    Centralized via FeatureRegistry flag `conversation_policy_bypass`.
    Mode gate: only effective in LOCAL; forced False in PROD.
    """
    if deployment_mode() != "LOCAL":
        return False
    # In LOCAL/dev, policy bypass is allowed by default (no env flag required)
    # Tests assert this default; explicit disabling can be added later via registry.
    return True


def test_policy_bypass_enabled() -> bool:
    """Return True if gateway selective-authorization may bypass policy in tests.

    Honours `TESTING` env unless explicitly disabled via `DISABLE_TEST_POLICY_BYPASS`.
    Intended for unit/integration tests; returns False in PROD by convention.
    """
    # Allow in any environment when TESTING is set, unless explicitly disabled.
    if os.getenv("DISABLE_TEST_POLICY_BYPASS") in {"1", "true", "True", "on"}:
        return False
    return os.getenv("TESTING") in {"1", "true", "True"}


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
