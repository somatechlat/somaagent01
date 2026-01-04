"""Domain ports - interfaces for external dependencies.

Ports define abstract interfaces that the domain layer uses to interact with
external systems (databases, caches, message queues, external services).
Infrastructure adapters implement these ports.

This follows the Ports and Adapters (Hexagonal) architecture pattern.
"""

from .adapters import (
    EventBusPort,
    ExecutionEnginePort,
    ExecutionLimitsDTO,
    ExecutionResultDTO,
    MemoryAdapterPort,
    PolicyAdapterPort,
    SecretManagerPort,
    ToolDefinitionDTO,
    ToolRegistryPort,
)
from .adapters.policy_adapter import PolicyRequestDTO
from .repositories import (
    MemoryReplicaRowDTO,
    MemoryReplicaStorePort,
    SessionCachePort,
    SessionRepositoryPort,
)

__all__ = [
    # Repository ports
    "SessionRepositoryPort",
    "SessionCachePort",
    "MemoryReplicaStorePort",
    "MemoryReplicaRowDTO",
    # Adapter ports
    "MemoryAdapterPort",
    "PolicyAdapterPort",
    "PolicyRequestDTO",
    "EventBusPort",
    "SecretManagerPort",
    "ToolRegistryPort",
    "ToolDefinitionDTO",
    "ExecutionEnginePort",
    "ExecutionResultDTO",
    "ExecutionLimitsDTO",
]
