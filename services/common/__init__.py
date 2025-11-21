"""Common infrastructure utilities for SomaAgent 01 services.

This package now re‑exports the central configuration singleton ``cfg`` from
``src.core.config`` so callers can simply do ``from services.common import cfg``
without needing a separate shim module.
"""

from importlib import import_module
from typing import Any

_SUBMODULES = {
    "budget_manager",
    "escalation",
    "event_bus",
    "model_costs",
    "model_profiles",
    "policy_client",
    "requeue_store",
    "router_client",
    "session_repository",
    "settings_base",
    "settings_sa01",
    "slm_client",
    "telemetry",
    "telemetry_store",
    "env",
}

# Export the configuration singleton alongside the other sub‑modules.
__all__ = sorted(_SUBMODULES | {"cfg"})


def __getattr__(name: str) -> Any:
    if name in _SUBMODULES:
        module = import_module(f"{__name__}.{name}")
        globals()[name] = module
        return module
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + list(_SUBMODULES) + ["cfg"])

# Import the real configuration singleton from the core package.
from src.core.config import cfg  # noqa: E402  (import after definitions is intentional)
