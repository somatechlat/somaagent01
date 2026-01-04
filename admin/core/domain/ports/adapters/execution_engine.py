"""Execution engine port interface.

This port defines the contract for tool execution orchestration.
The interface matches the existing ExecutionEngine methods exactly
to enable seamless wrapping of the production implementation.

Production Implementation:
    services.tool_executor.execution_engine.ExecutionEngine
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class ExecutionResultDTO:
    """Data transfer object for execution result.

    Mirrors services.tool_executor.execution_engine.ExecutionResult structure.
    """

    status: str
    payload: Dict[str, Any]
    execution_time: float
    logs: List[str]


@dataclass
class ExecutionLimitsDTO:
    """Data transfer object for execution limits.

    Mirrors services.tool_executor.resource_manager.ExecutionLimits structure.
    """

    timeout_seconds: float = 30.0
    max_memory_mb: int = 512
    max_output_bytes: int = 1024 * 1024  # 1MB


class ExecutionEnginePort(ABC):
    """Abstract interface for tool execution orchestration.

    This port wraps the existing ExecutionEngine implementation.
    All methods match the production implementation signature exactly.
    """

    @abstractmethod
    async def execute(
        self,
        tool_name: str,
        args: Dict[str, Any],
        limits: ExecutionLimitsDTO,
    ) -> ExecutionResultDTO:
        """Execute a tool with resource limits.

        Args:
            tool_name: Name of the tool to execute
            args: Tool arguments
            limits: Execution resource limits

        Returns:
            Execution result with status, payload, timing, and logs
        """
        ...