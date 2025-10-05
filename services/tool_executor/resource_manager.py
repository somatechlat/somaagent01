"""Resource management helpers for the tool executor."""
from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass


@dataclass
class ExecutionLimits:
    cpu_seconds: float | None = None
    memory_mb: int | None = None
    timeout_seconds: float | None = 60.0


class ResourceManager:
    """Tracks concurrent executions to avoid exhausting the host."""

    def __init__(self, max_concurrent: int | None = None) -> None:
        limit = max_concurrent or int(os.getenv("TOOL_EXECUTOR_MAX_CONCURRENT", "4"))
        self._semaphore = asyncio.Semaphore(max(1, limit))

    @asynccontextmanager
    async def reserve(self) -> asyncio.Semaphore:
        await self._semaphore.acquire()
        try:
            yield
        finally:
            self._semaphore.release()


def default_limits() -> ExecutionLimits:
    return ExecutionLimits(
        cpu_seconds=float(os.getenv("TOOL_EXECUTOR_CPU_SECONDS", "15")),
        memory_mb=int(os.getenv("TOOL_EXECUTOR_MEMORY_MB", "512")),
        timeout_seconds=float(os.getenv("TOOL_EXECUTOR_TIMEOUT", "60")),
    )
