"""Domain ports - interfaces for external dependencies.

Ports define abstract interfaces that the domain layer uses to interact with
external systems (databases, caches, message queues, external services).
Infrastructure adapters implement these ports.

This follows the Ports and Adapters (Hexagonal) architecture pattern.
"""

from .adapters import EventBusPort, MemoryAdapterPort, PolicyAdapterPort
from .repositories import SessionCachePort, SessionRepositoryPort

__all__ = [
    # Repository ports
    "SessionRepositoryPort",
    "SessionCachePort",
    # Adapter ports
    "MemoryAdapterPort",
    "PolicyAdapterPort",
    "EventBusPort",
]
