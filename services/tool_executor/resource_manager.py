"""Resource management helpers for the tool executor."""

from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass


@dataclass
class ExecutionLimits:
    """Executionlimits class implementation."""

    cpu_seconds: float | None = None
    memory_mb: int | None = None
    timeout_seconds: float | None = 60.0


class ResourceManager:
    """Tracks concurrent executions to avoid exhausting the host."""

    def __init__(self, max_concurrent: int | None = None) -> None:
        """Initialize the instance."""

        raw_limit = os.environ.get("TOOL_EXECUTOR_MAX_CONCURRENT", "4")
        try:
            limit = int(raw_limit)
        except (TypeError, ValueError):
            limit = 4
        self._limit = max_concurrent or limit
        self._semaphore = asyncio.Semaphore(max(1, self._limit))

    async def initialize(self) -> None:
        # Implementation for future resource discovery hooks (GPU, CPU quotas, etc.).
        """Execute initialize."""

        return None

    async def can_execute(self) -> bool:
        """Execute can execute."""

        try:
            self._semaphore.acquire_nowait()
        except ValueError:
            return False
        else:
            self._semaphore.release()
            return True

    @asynccontextmanager
    async def reserve(self) -> Any:  # type: ignore[return]
        """Execute reserve."""

        await self._semaphore.acquire()
        try:
            yield
        finally:
            self._semaphore.release()


def default_limits() -> ExecutionLimits:
    """Execute default limits."""

    def _float(name: str, default: float) -> float:
        """Execute float.

        Args:
            name: The name.
            default: The default.
        """

        raw = os.environ.get(name, str(default))
        try:
            return float(raw)
        except (TypeError, ValueError):
            return default

    def _int(name: str, default: int) -> int:
        """Execute int.

        Args:
            name: The name.
            default: The default.
        """

        raw = os.environ.get(name, str(default))
        try:
            return int(raw)
        except (TypeError, ValueError):
            return default

    return ExecutionLimits(
        cpu_seconds=_float("TOOL_EXECUTOR_CPU_SECONDS", 15.0),
        memory_mb=_int("TOOL_EXECUTOR_MEMORY_MB", 512),
        timeout_seconds=_float("TOOL_EXECUTOR_TIMEOUT", 60.0),
    )
