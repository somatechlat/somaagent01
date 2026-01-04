"""Data Transfer Objects for application layer.

DTOs define the input/output contracts for use cases.
They are simple data containers with no business logic.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ProcessMessageInput:
    """Input for ProcessMessage use case."""

    session_id: str
    message: str
    persona_id: Optional[str]
    tenant: str
    metadata: Dict[str, Any]


@dataclass
class ProcessMessageOutput:
    """Output from ProcessMessage use case."""

    response: str
    session_id: str
    tool_calls: List[Dict[str, Any]]
    metadata: Dict[str, Any]


@dataclass
class ExecuteToolInput:
    """Input for ExecuteTool use case."""

    tool_name: str
    args: Dict[str, Any]
    session_id: str
    tenant: str
    persona_id: Optional[str]


@dataclass
class ExecuteToolOutput:
    """Output from ExecuteTool use case."""

    status: str
    result: Dict[str, Any]
    execution_time: float
    logs: List[str]


@dataclass
class StoreMemoryInput:
    """Input for StoreMemory use case."""

    session_id: str
    content: str
    memory_type: str  # "short_term" or "long_term"
    metadata: Dict[str, Any]


@dataclass
class StoreMemoryOutput:
    """Output from StoreMemory use case."""

    memory_id: str
    stored: bool
    metadata: Dict[str, Any]


__all__ = [
    "ProcessMessageInput",
    "ProcessMessageOutput",
    "ExecuteToolInput",
    "ExecuteToolOutput",
    "StoreMemoryInput",
    "StoreMemoryOutput",
]