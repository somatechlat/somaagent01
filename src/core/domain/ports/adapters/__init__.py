"""Adapter port interfaces for external services.

These abstract interfaces define contracts for external service integrations.
Infrastructure layer provides concrete implementations that wrap existing
production clients.
"""

from .event_bus import EventBusPort
from .memory_adapter import MemoryAdapterPort
from .policy_adapter import PolicyAdapterPort

__all__ = [
    "MemoryAdapterPort",
    "PolicyAdapterPort",
    "EventBusPort",
]
