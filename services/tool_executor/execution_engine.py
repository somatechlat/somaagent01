"""Execution engine orchestration for the SomaAgent 01 tool executor."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict

from python.helpers.circuit_breaker import (
    circuit_breaker,
    CircuitOpenError,
    ensure_metrics_exporter,
)
from services.tool_executor.resource_manager import ExecutionLimits, ResourceManager
from services.tool_executor.sandbox_manager import (
    SandboxExecutionResult,
    SandboxManager,
)
from services.tool_executor.tool_registry import ToolDefinition
from src.core.config import cfg

LOGGER = logging.getLogger(__name__)


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
        ensure_metrics_exporter()
        try:
            self._circuit_failure_threshold = int(
                cfg.env("TOOL_EXECUTOR_CIRCUIT_FAILURE_THRESHOLD", "5")
            )
        except (TypeError, ValueError):
            self._circuit_failure_threshold = 5
        try:
            self._circuit_reset_timeout = float(
                cfg.env("TOOL_EXECUTOR_CIRCUIT_RESET_TIMEOUT_SECONDS", "30")
            )
        except (TypeError, ValueError):
            self._circuit_reset_timeout = 30.0
        self._tool_breakers: dict[str, Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]] = {}

    async def execute(
        self,
        tool: ToolDefinition,
        args: Dict[str, Any],
        limits: ExecutionLimits,
    ) -> ExecutionResult:
        breaker = self._tool_breakers.get(tool.name)
        if breaker is None:
            breaker = circuit_breaker(
                failure_threshold=self._circuit_failure_threshold,
                reset_timeout=self._circuit_reset_timeout,
            )(tool.run)
            self._tool_breakers[tool.name] = breaker

        try:
            async with self._resources.reserve():
                sandbox_result: SandboxExecutionResult = await self._sandbox.run(
                    breaker,
                    args,
                    limits,
                )
        except CircuitOpenError:
            LOGGER.warning(
                "Tool execution circuit open; rejecting request",
                extra={
                    "tool": getattr(tool, "name", "unknown"),
                    "failure_threshold": self._circuit_failure_threshold,
                    "reset_timeout_seconds": self._circuit_reset_timeout,
                },
            )
            return ExecutionResult(
                status="circuit_open",
                payload={
                    "message": (
                        "Tool execution temporarily disabled after repeated failures. "
                        "Please retry after the circuit resets."
                    )
                },
                execution_time=0.0,
                logs=[
                    "Circuit breaker open for tool executor",
                ],
            )
        return ExecutionResult(
            status=sandbox_result.status,
            payload=sandbox_result.payload,
            execution_time=sandbox_result.execution_time,
            logs=sandbox_result.logs,
        )
