"""Compatibility shim for the degradation monitor.

The original implementation of the degradation monitor lives in
``services.gateway.degradation_monitor``.  Several parts of the codebase import it
via ``services.common.degradation_monitor`` for historical reasons.  To avoid
breaking those imports (and to satisfy VIBE's rule of a single source of truth)
we provide a thin re‑export module that forwards all attributes.
"""

from services.gateway.degradation_monitor import *  # noqa: F403,F401

__all__ = [
    "DegradationLevel",
    "ComponentHealth",
    "DegradationStatus",
    "DegradationMonitor",
]
