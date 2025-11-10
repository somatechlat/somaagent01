import importlib
import sys
from types import ModuleType, SimpleNamespace

import pytest


def _install_test_stubs() -> None:
    """Register lightweight stand-ins for optional dependencies."""
    if "whisper" not in sys.modules:
        sys.modules["whisper"] = ModuleType("whisper")

    if "python.helpers.git" not in sys.modules:
        fake_git_module = ModuleType("python.helpers.git")

        def _fake_git_info():  # pragma: no cover - trivial stub
            return {
                "branch": "",
                "commit_hash": "",
                "commit_time": "",
                "tag": "",
                "short_tag": "",
                "version": "",
            }

        fake_git_module.get_git_info = _fake_git_info  # type: ignore[attr-defined]
        sys.modules["python.helpers.git"] = fake_git_module

    if "agent" not in sys.modules:
        agent_stub = ModuleType("agent")

        class _AgentStub:  # pragma: no cover - behaviour not exercised
            def __init__(self, *args, **kwargs) -> None:
                pass

        class _LoopDataStub:  # pragma: no cover - behaviour not exercised
            pass

        agent_stub.Agent = _AgentStub  # type: ignore[attr-defined]
        agent_stub.LoopData = _LoopDataStub  # type: ignore[attr-defined]
        sys.modules["agent"] = agent_stub


_install_test_stubs()

memory_load_module = importlib.import_module("python.tools.memory_load")
MemoryLoad = memory_load_module.MemoryLoad
SomaClientError = importlib.import_module("python.integrations.soma_client").SomaClientError


class DummyAgent:
    def __init__(self, universe: str = "test-universe") -> None:
        self.config = SimpleNamespace(memory_subdir=universe)
        self.agent_name = "A0"
        self.read_prompt_calls: list[tuple[str, dict]] = []

    def read_prompt(self, template: str, **kwargs) -> str:
        self.read_prompt_calls.append((template, kwargs))
        query = kwargs.get("query", "")
        return f"NO MEMORIES FOUND FOR: {query}" if query else "NO MEMORIES"


class StubSomaClient:
    def __init__(self, response=None, error: Exception | None = None) -> None:
        self._response = response
        self._error = error
        self.calls: list[dict] = []

    async def recall(self, query, *, top_k, universe=None, **kwargs):
        call = {"query": query, "top_k": top_k, "universe": universe}
        if kwargs:
            call.update(kwargs)
        self.calls.append(call)
        if self._error is not None:
            raise self._error
        return self._response or {}


def make_tool(agent: DummyAgent) -> MemoryLoad:
    return MemoryLoad(agent, "memory_load", None, {}, "", None)


@pytest.mark.asyncio
async def test_execute_returns_messages_from_payload(monkeypatch):
    response_payload = {
        "wm": [{"payload": {"content": "alpha"}}, {"payload": {"text": "beta"}}],
        "memory": [{"content": "gamma"}],
    }
    stub_client = StubSomaClient(response=response_payload)
    monkeypatch.setattr(
        "python.tools.memory_load.SomaClient.get",
        classmethod(lambda cls: stub_client),
    )

    agent = DummyAgent()
    tool = make_tool(agent)

    result = await tool.execute(query="colors", limit="5")

    assert "alpha" in result.message
    assert "beta" in result.message
    assert "gamma" in result.message
    assert stub_client.calls[0]["top_k"] == 5
    assert stub_client.calls[0]["universe"] == agent.config.memory_subdir


@pytest.mark.asyncio
async def test_execute_applies_score_threshold(monkeypatch):
    response_payload = {
        "memory": [
            {"payload": {"content": "keep"}, "score": 0.9},
            {"payload": {"content": "drop"}, "score": 0.2},
        ]
    }
    stub_client = StubSomaClient(response=response_payload)
    monkeypatch.setattr(
        "python.tools.memory_load.SomaClient.get",
        classmethod(lambda cls: stub_client),
    )

    agent = DummyAgent()
    tool = make_tool(agent)

    result = await tool.execute(threshold=0.5)

    assert "keep" in result.message
    assert "drop" not in result.message


@pytest.mark.asyncio
async def test_execute_returns_prompt_on_failure(monkeypatch):
    stub_client = StubSomaClient(error=SomaClientError("boom"))
    monkeypatch.setattr(
        "python.tools.memory_load.SomaClient.get",
        classmethod(lambda cls: stub_client),
    )

    agent = DummyAgent()
    tool = make_tool(agent)

    result = await tool.execute(query="forgotten fact")

    assert result.message.startswith("NO MEMORIES FOUND FOR: forgotten fact")
    assert agent.read_prompt_calls, "read_prompt should be invoked on failure"
