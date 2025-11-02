import asyncio

import pytest

from services.tool_executor.execution_engine import ExecutionEngine, ExecutionResult
from services.tool_executor.resource_manager import ExecutionLimits, ResourceManager
from services.tool_executor.sandbox_manager import SandboxManager


class FakeTool:
    def __init__(self) -> None:
        self.name = "demo"
        self._attempts = 0

    async def run(self, args: dict[str, object]) -> dict[str, object]:
        self._attempts += 1
        if self._attempts <= 2:
            raise RuntimeError("boom")
        return {"status": "ok"}


@pytest.mark.asyncio
async def test_execution_engine_reports_circuit_open(monkeypatch):
    monkeypatch.setenv("TOOL_EXECUTOR_CIRCUIT_FAILURE_THRESHOLD", "2")
    monkeypatch.setenv("TOOL_EXECUTOR_CIRCUIT_RESET_TIMEOUT_SECONDS", "0.05")

    sandbox = SandboxManager()
    resources = ResourceManager(max_concurrent=1)
    engine = ExecutionEngine(sandbox, resources)
    tool = FakeTool()
    limits = ExecutionLimits(timeout_seconds=0.1)

    result1 = await engine.execute(tool, {}, limits)
    assert isinstance(result1, ExecutionResult)
    assert result1.status == "error"
    assert "boom" in result1.payload.get("message", "")

    result2 = await engine.execute(tool, {}, limits)
    assert result2.status == "error"

    result3 = await engine.execute(tool, {}, limits)
    assert result3.status == "circuit_open"
    assert "temporarily disabled" in result3.payload["message"]

    await asyncio.sleep(0.06)

    result4 = await engine.execute(tool, {}, limits)
    assert result4.status == "success"
    assert result4.payload == {"status": "ok"}
