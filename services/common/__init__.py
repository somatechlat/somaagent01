"""Common infrastructure utilities for SomaAgent 01 services."""

from importlib import import_module
from typing import Any

_SUBMODULES = {
    "budget_manager",
    "degradation_monitor",
    "escalation",
    "event_bus",
    "model_costs",
    "model_profiles",
    "policy_client",
    "requeue_store",
    "router_client",
    "session_repository",
    "telemetry",
    "telemetry_store",
}

__all__ = sorted(_SUBMODULES)


def __getattr__(name: str) -> Any:
    if name in _SUBMODULES:
        module = import_module(f"{__name__}.{name}")
        globals()[name] = module
        return module
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + list(_SUBMODULES))
