"""Helper settings facade bridging legacy helper code with the central config.

Resolution (no hardcoded product behavior):

    Capsule.persona_config["settings"]  →  AgentSetting ORM  →  Django settings

Env is for URLs/hosts/ports. Vault owns secrets (AgentSetting.is_secret).
Categories are ISO-style — see docs/iso/SOMA-SETTINGS-MODEL-001.md and
``admin.core.helpers.capsule_settings``.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from admin.core.helpers.settings_defaults import get_default_settings
from admin.core.helpers.settings_model import SettingsModel

_SETTINGS_CACHE: SettingsModel | None = None


def get_settings(
    *,
    capsule: Any = None,
    agent_id: Optional[str] = None,
) -> SettingsModel:
    """Return helper settings, overlaid with Capsule / AgentSetting when given."""
    global _SETTINGS_CACHE
    if _SETTINGS_CACHE is None:
        _SETTINGS_CACHE = get_default_settings()
    if capsule is None and agent_id is None:
        return _SETTINGS_CACHE

    from admin.core.helpers.capsule_settings import merge_settings_model

    overlay = merge_settings_model(capsule=capsule, agent_id=agent_id)
    if not overlay:
        return _SETTINGS_CACHE
    merged = _SETTINGS_CACHE.model_dump()
    for key, value in overlay.items():
        # SettingsModel uses snake_case; Django keys are UPPER.
        snake = key.lower()
        if snake in merged and value is not None:
            merged[snake] = value
        elif key in merged and value is not None:
            merged[key] = value
    try:
        return SettingsModel(**merged)
    except Exception:
        return _SETTINGS_CACHE


def set_settings(data: SettingsModel | Dict[str, Any]) -> SettingsModel:
    """Replace the cached settings (used by UI settings routes)."""
    global _SETTINGS_CACHE
    _SETTINGS_CACHE = data if isinstance(data, SettingsModel) else SettingsModel(**data)
    return _SETTINGS_CACHE


def refresh_settings() -> SettingsModel:
    """Clear and reload default settings."""
    global _SETTINGS_CACHE
    _SETTINGS_CACHE = get_default_settings()
    return _SETTINGS_CACHE


__all__ = ["get_settings", "set_settings", "refresh_settings", "SettingsModel"]
