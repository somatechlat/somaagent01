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
        self._limit = max_concurrent or int(
            os.getenv("TOOL_EXECUTOR_MAX_CONCURRENT", "4")
        )
        self._semaphore = asyncio.Semaphore(max(1, self._limit))

    async def initialize(self) -> None:
        # Placeholder for future resource discovery hooks (GPU, CPU quotas, etc.).
        return None

    async def can_execute(self) -> bool:
        try:
            self._semaphore.acquire_nowait()
        except ValueError:
            return False
        else:
            self._semaphore.release()
            return True

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
