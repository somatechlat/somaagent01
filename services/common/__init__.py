"""Common infrastructure utilities for SomaAgent 01 services."""

from importlib import import_module
from typing import Any

_SUBMODULES = {
    "chat_schemas",
    "chat_memory",
    "circuit_breaker",
    "unified_metrics",
    "simple_governor",
    "health_monitor",
    "simple_context_builder",
    "unified_secret_manager",
    "litellm_client",
    "model_costs",
    "model_profiles",
    "telemetry",
    "telemetry_store",
}

__all__ = sorted(_SUBMODULES)


def __getattr__(name: str) -> Any:
    """Execute getattr  .

    Args:
        name: The name.
    """

    if name in _SUBMODULES:
        module = import_module(f"{__name__}.{name}")
        globals()[name] = module
        return module
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__() -> list[str]:
    """Execute dir  ."""

    return sorted(list(globals().keys()) + list(_SUBMODULES))
