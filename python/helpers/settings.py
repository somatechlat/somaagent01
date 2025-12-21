"""Helper settings facade bridging legacy helper code with the central config."""

from __future__ import annotations

from typing import Any, Dict

from python.helpers.settings_defaults import get_default_settings
from python.helpers.settings_model import SettingsModel

_SETTINGS_CACHE: SettingsModel | None = None


def get_settings() -> SettingsModel:
    """Return cached helper settings."""
    global _SETTINGS_CACHE
    if _SETTINGS_CACHE is None:
        _SETTINGS_CACHE = get_default_settings()
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
