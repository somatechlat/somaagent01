"""
SOMA Centralized Configuration Package
=======================================

VIBE Rule 100: Centralized Sovereignty
This package is the SINGLE SOURCE OF TRUTH for all configuration.

Usage:
    from config import get_settings
    settings = get_settings()
    host = settings.postgres_host  # example
"""

from config.settings_registry import (
    AAASSettings,
    BaseSettings,
    get_settings,
    SettingsRegistry,
    StandaloneSettings,
)

# `get_required_env` / `get_optional_env` were removed on purpose. They read
# os.environ, which is the config store Rule 100 retires: topology now lives
# on the mode class in settings_registry, secrets in Vault, per-agent
# behaviour in AgentSetting. Importing them here would be a second source of
# truth wearing the package's own name.

__all__ = [
    "SettingsRegistry",
    "BaseSettings",
    "StandaloneSettings",
    "AAASSettings",
    "get_settings",
]
