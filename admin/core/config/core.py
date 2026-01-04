"""The single source of truth for configuration.

This module provides a single, globally accessible configuration object. It
leverages the loader and registry to provide a cached, validated configuration.
"""

from .registry import get_config

# The globally accessible configuration object.
cfg = get_config()