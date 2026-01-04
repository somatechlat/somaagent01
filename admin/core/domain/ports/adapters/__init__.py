"""Adapter port interfaces for external services.

These abstract interfaces define contracts for external service integrations.
Infrastructure layer provides concrete implementations that wrap existing
production clients.
"""

from .event_bus import EventBusPort
from .execution_engine import ExecutionEnginePort, ExecutionLimitsDTO, ExecutionResultDTO
from .memory_adapter import MemoryAdapterPort
from .policy_adapter import PolicyAdapterPort
from .secret_manager import SecretManagerPort
from .tool_registry import ToolDefinitionDTO, ToolRegistryPort

__all__ = [
    "MemoryAdapterPort",
    "PolicyAdapterPort",
    "EventBusPort",
    "SecretManagerPort",
    "ToolRegistryPort",
    "ToolDefinitionDTO",
    "ExecutionEnginePort",
    "ExecutionResultDTO",
    "ExecutionLimitsDTO",
]