"""Execution engine orchestration for the SomaAgent 01 tool executor."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from services.tool_executor.resource_manager import ExecutionLimits, ResourceManager
from services.tool_executor.sandbox_manager import SandboxExecutionResult, SandboxManager
from services.tool_executor.tool_registry import ToolDefinition


@dataclass
class ExecutionResult:
    status: str
    payload: Dict[str, Any]
    execution_time: float
    logs: list[str]


class ExecutionEngine:
    """Coordinates tool execution across sandbox and resource controls."""

    def __init__(self, sandbox: SandboxManager, resources: ResourceManager) -> None:
        self._sandbox = sandbox
        self._resources = resources

    async def execute(
        self,
        tool: ToolDefinition,
        args: Dict[str, Any],
        limits: ExecutionLimits,
    ) -> ExecutionResult:
        async with self._resources.reserve():
            sandbox_result: SandboxExecutionResult = await self._sandbox.run(
                tool.run,
                args,
                limits,
            )
        return ExecutionResult(
            status=sandbox_result.status,
            payload=sandbox_result.payload,
            execution_time=sandbox_result.execution_time,
            logs=sandbox_result.logs,
        )

