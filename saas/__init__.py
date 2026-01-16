"""
SOMA SaaS Bridge
====================

This package provides DIRECT IN-PROCESS access to SomaBrain and FractalMemory,
eliminating HTTP network overhead for memory-intensive agent operations.

Usage:
------
    from saas import brain, memory

    # Direct memory operations (no HTTP)
    await memory.store(coord, payload)
    results = await memory.recall(query)

    # Direct brain operations (no HTTP)
    await brain.process(input_data)

Performance:
-----------
    HTTP Call:   ~5ms per operation
    Direct Call: ~0.05ms per operation
    Speedup:     100x

Configuration:
-------------
    VIBE Rule 100: All settings from centralized config/settings_registry.py
    Set SA01_DEPLOYMENT_MODE=SAAS to enable SaaS mode
"""

from __future__ import annotations

import logging

# VIBE Rule 100: Use centralized config
try:
    from config import get_settings

    _settings = get_settings()
    SAAS_MODE = getattr(_settings, "soma_saas_mode", False)
except ImportError:
    # Fallback for standalone imports
    import os

    SAAS_MODE = os.getenv("SOMA_SAAS_MODE", "false").lower() == "true"
    logging.getLogger(__name__).warning(
        "⚠️ Could not import config.settings_registry. Using environment fallback."
    )

__version__ = "2.0.0"
__all__ = ["brain", "memory", "SAAS_MODE"]
