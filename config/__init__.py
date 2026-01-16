"""
SOMA Centralized Configuration Package
=======================================

VIBE Rule 100: Centralized Sovereignty
This package is the SINGLE SOURCE OF TRUTH for all configuration.

Usage:
    from config import get_settings
    settings = get_settings()
    print(settings.postgres_host)
"""

from config.settings_registry import (
    BaseSettings,
    get_optional_env,
    get_required_env,
    get_settings,
    SaaSSettings,
    SettingsRegistry,
    StandaloneSettings,
)

__all__ = [
    "SettingsRegistry",
    "BaseSettings",
    "StandaloneSettings",
    "SaaSSettings",
    "get_settings",
    "get_required_env",
    "get_optional_env",
]
