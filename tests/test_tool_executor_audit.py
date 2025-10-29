import asyncio
import os

import pytest

from services.tool_executor.main import ToolExecutor
from services.tool_executor.execution_engine import ExecutionResult
from services.tool_executor.tools import ToolExecutionError
from services.tool_executor.tools import EchoTool


@pytest.mark.asyncio
async def test_tool_executor_audit_success(monkeypatch):
    monkeypatch.setenv("AUDIT_STORE_MODE", "memory")

    exec = ToolExecutor()
    # Ensure registry contains the tool so we don't hit unknown_tool
    exec.tool_registry.register(EchoTool())

    # Avoid real side effects
    monkeypatch.setattr(exec, "_publish_result", lambda *a, **k: asyncio.sleep(0))
    monkeypatch.setattr(exec, "_enqueue_requeue", lambda *a, **k: asyncio.sleep(0))
    async def _allow(**k):
        return True
    monkeypatch.setattr(exec, "_check_policy", _allow)
    # Force success result
    async def _fake_execute(tool, args, limits):
        return ExecutionResult(status="success", payload={"ok": True}, execution_time=0.012, logs=[])
    monkeypatch.setattr(exec.execution_engine, "execute", _fake_execute)

    event = {
        "event_id": "evt-1",
        "session_id": "sess-1",
        "persona_id": None,
        "tool_name": "echo",
        "args": {"text": "hi"},
        "metadata": {"tenant": "public"},
    }

    await exec._handle_request(event)

    store = exec.get_audit_store()
    rows = await store.list(session_id="sess-1")
    actions = [r.action for r in rows]
    assert "tool.execute.start" in actions
    assert "tool.execute.finish" in actions
    fin = [r for r in rows if r.action == "tool.execute.finish"][0]
    assert fin.details.get("status") == "success"
    assert isinstance(fin.details.get("latency_ms"), int)


@pytest.mark.asyncio
async def test_tool_executor_audit_blocked(monkeypatch):
    monkeypatch.setenv("AUDIT_STORE_MODE", "memory")

    exec = ToolExecutor()
    exec.tool_registry.register(EchoTool())

    # Avoid side effects
    monkeypatch.setattr(exec, "_publish_result", lambda *a, **k: asyncio.sleep(0))
    monkeypatch.setattr(exec, "_enqueue_requeue", lambda *a, **k: asyncio.sleep(0))
    # Deny by policy
    async def _deny(**k):
        return False
    monkeypatch.setattr(exec, "_check_policy", _deny)

    event = {
        "event_id": "evt-2",
        "session_id": "sess-2",
        "persona_id": None,
        "tool_name": "echo",
        "args": {"text": "hi"},
        "metadata": {"tenant": "public"},
    }

    await exec._handle_request(event)

    store = exec.get_audit_store()
    rows = await store.list(session_id="sess-2")
    fin = [r for r in rows if r.action == "tool.execute.finish"][0]
    assert fin.details.get("status") == "blocked"
    assert fin.details.get("reason") == "policy_denied"


@pytest.mark.asyncio
async def test_tool_executor_audit_execution_error(monkeypatch):
    monkeypatch.setenv("AUDIT_STORE_MODE", "memory")

    exec = ToolExecutor()
    exec.tool_registry.register(EchoTool())

    # Avoid side effects
    monkeypatch.setattr(exec, "_publish_result", lambda *a, **k: asyncio.sleep(0))
    monkeypatch.setattr(exec, "_enqueue_requeue", lambda *a, **k: asyncio.sleep(0))
    async def _allow2(**k):
        return True
    monkeypatch.setattr(exec, "_check_policy", _allow2)

    async def _raise_exec(*args, **kwargs):
        raise ToolExecutionError("boom")
    monkeypatch.setattr(exec.execution_engine, "execute", _raise_exec)

    event = {
        "event_id": "evt-3",
        "session_id": "sess-3",
        "persona_id": None,
        "tool_name": "echo",
        "args": {"text": "hi"},
        "metadata": {"tenant": "public"},
    }

    await exec._handle_request(event)

    store = exec.get_audit_store()
    rows = await store.list(session_id="sess-3")
    fin = [r for r in rows if r.action == "tool.execute.finish"][0]
    assert fin.details.get("status") == "error"
    assert fin.details.get("reason") == "execution_error"
