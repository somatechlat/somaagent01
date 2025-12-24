"""Execution engine adapter wrapping ExecutionEngine.

This adapter implements ExecutionEnginePort by delegating ALL operations
to the existing production ExecutionEngine implementation.
"""

from typing import Any, Dict, Optional

from services.tool_executor.execution_engine import ExecutionEngine
from services.tool_executor.resource_manager import ExecutionLimits, ResourceManager
from services.tool_executor.sandbox_manager import SandboxManager
from services.tool_executor.tool_registry import ToolRegistry
    ExecutionEnginePort,
    ExecutionLimitsDTO,
    ExecutionResultDTO,
)


class ExecutionEngineAdapter(ExecutionEnginePort):
    """Implements ExecutionEnginePort using existing ExecutionEngine.

    Delegates ALL operations to services.tool_executor.execution_engine.ExecutionEngine.
    """

    def __init__(
        self,
        engine: Optional[ExecutionEngine] = None,
        registry: Optional[ToolRegistry] = None,
    ):
        """Initialize adapter with existing engine or create new one.

        Args:
            engine: Existing ExecutionEngine instance (preferred)
            registry: Tool registry for looking up tools
        """
        if engine is not None:
            self._engine = engine
        else:
            # Create default engine with sandbox and resource manager
            sandbox = SandboxManager()
            resources = ResourceManager()
            self._engine = ExecutionEngine(sandbox, resources)

        self._registry = registry or ToolRegistry()

    async def execute(
        self,
        tool_name: str,
        args: Dict[str, Any],
        limits: ExecutionLimitsDTO,
    ) -> ExecutionResultDTO:
        # Look up the tool definition
        tool_def = self._registry.get(tool_name)
        if tool_def is None:
            return ExecutionResultDTO(
                status="error",
                payload={"error": f"Tool not found: {tool_name}"},
                execution_time=0.0,
                logs=[f"Tool '{tool_name}' not found in registry"],
            )

        # Convert DTO to internal limits
        internal_limits = ExecutionLimits(
            timeout_seconds=limits.timeout_seconds,
            max_memory_mb=limits.max_memory_mb,
            max_output_bytes=limits.max_output_bytes,
        )

        # Execute via the engine
        result = await self._engine.execute(tool_def, args, internal_limits)

        return ExecutionResultDTO(
            status=result.status,
            payload=result.payload,
            execution_time=result.execution_time,
            logs=result.logs,
        )
