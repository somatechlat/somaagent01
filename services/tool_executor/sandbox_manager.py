"""Sandbox manager for executing tools with basic resource controls."""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from services.tool_executor.resource_manager import ExecutionLimits
from services.tool_executor.tools import ToolExecutionError


@dataclass
class SandboxExecutionResult:
    status: str
    payload: dict[str, Any]
    execution_time: float
    logs: list[str]


class SandboxManager:
    """Minimal sandbox manager.

    Future iterations will offload execution into dedicated containers. For now we
    execute in-process but centralise timeout and logging.
    """

    async def run(
        self,
        func: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]],
        args: dict[str, Any],
        limits: ExecutionLimits,
    ) -> SandboxExecutionResult:
        start = time.time()
        logs: list[str] = []
        try:
            payload = await asyncio.wait_for(func(args), timeout=limits.timeout_seconds)
            status = "success"
        except ToolExecutionError:
            raise
        except asyncio.TimeoutError:
            status = "timeout"
            payload = {"message": "Tool execution timed out"}
            logs.append("Execution exceeded timeout")
        except Exception as exc:  # pragma: no cover - defensive
            status = "error"
            payload = {"message": str(exc)}
            logs.append(f"Unhandled exception: {exc}")
        duration = time.time() - start
        return SandboxExecutionResult(status=status, payload=payload, execution_time=duration, logs=logs)
