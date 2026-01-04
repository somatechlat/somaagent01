"""Sandbox manager for executing tools with basic resource controls."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from admin.core.helpers.circuit_breaker import CircuitOpenError
from services.tool_executor.resource_manager import ExecutionLimits
from services.tool_executor.tools import ToolExecutionError

LOGGER = logging.getLogger(__name__)


@dataclass
class SandboxExecutionResult:
    """Sandboxexecutionresult class implementation."""

    status: str
    payload: dict[str, Any]
    execution_time: float
    logs: list[str]


class SandboxManager:
    """Minimal sandbox manager.

    Future iterations will offload execution into dedicated containers. For now we
    execute in-process but centralise timeout and logging.
    """

    async def initialize(self) -> None:
        # Implementation for future container pool warmup.
        """Execute initialize.
            """

        return None

    async def run(
        self,
        func: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]],
        args: dict[str, Any],
        limits: ExecutionLimits,
    ) -> SandboxExecutionResult:
        """Execute run.

            Args:
                func: The func.
                args: The args.
                limits: The limits.
            """

        start = time.time()
        logs: list[str] = []
        sandbox_id = args.get("sandbox_id") or args.get("task_id") or args.get("tool_name")
        sandbox_id = str(sandbox_id or "unknown")
        try:
            payload = await asyncio.wait_for(func(args), timeout=limits.timeout_seconds)
            status = "success"
        except ToolExecutionError:
            raise
        except CircuitOpenError:
            raise
        except asyncio.TimeoutError:
            status = "timeout"
            payload = {"message": "Tool execution timed out"}
            logs.append("Execution exceeded timeout")
        except Exception as exc:
            LOGGER.error(
                "Sandbox execution failed",
                extra={
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                    "sandbox_id": sandbox_id,
                },
            )
            status = "error"
            payload = {"message": f"{type(exc).__name__}: {exc}"}
            logs.append(f"Unhandled exception: {type(exc).__name__}: {exc}")
        duration = time.time() - start
        return SandboxExecutionResult(
            status=status, payload=payload, execution_time=duration, logs=logs
        )