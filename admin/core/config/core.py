"""The single source of truth for configuration.

This module provides a single, globally accessible configuration object. It
leverages the loader and registry to provide a cached, validated configuration.
"""

from .registry import get_config

_cfg = None


def __getattr__(name: str):
    """Lazy module-level attribute access to avoid import-time validation."""
    if name == "cfg":
        global _cfg
        if _cfg is None:
            _cfg = get_config()
        return _cfg
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
