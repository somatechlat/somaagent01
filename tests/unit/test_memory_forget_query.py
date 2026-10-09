"""memory_forget query mode — multi-row erase of fact + chat echoes (T-1)."""

from __future__ import annotations

import pytest

from services.tool_executor.memory_tools import MemoryForgetTool
from services.tool_executor.tools import ToolExecutionError


class _Hit:
    def __init__(self, text: str, coord: str, score: float = 0.9):
        self.text = text
        self.coord = coord
        self.score = score
        self.store = "somabrain"
        self.kind = "semantic"


class _FakeGateway:
    def __init__(self, hits=None):
        self.hits = hits or []
        self.forgot: list[str] = []

    async def recall(self, query, k, tenant_id):
        return self.hits[: int(k)]

    async def forget(self, coord, tenant_id):
        self.forgot.append(coord)
        return True


@pytest.fixture
def gw(monkeypatch):
    g = _FakeGateway(
        hits=[
            _Hit("User's name is Zoe.", "c-fact"),
            _Hit("User: what is my name\nAssistant: Your name is Zoe.", "c-echo"),
            _Hit("unrelated weather note", "c-other"),
            _Hit("?", "c-stub"),
        ]
    )
    monkeypatch.setattr(
        "services.tool_executor.memory_tools._memory_gateway", lambda: g
    )
    return g


async def test_forget_query_deletes_fact_and_echoes(gw):
    tool = MemoryForgetTool()
    result = await tool.run({"tenant_id": "t-1", "query": "Zoe"})
    assert result["mode"] == "query"
    assert result["forgotten"] is True
    assert result["deleted"] == 2
    assert "c-fact" in result["coords"]
    assert "c-echo" in result["coords"]
    assert "c-other" not in result["coords"]
    assert gw.forgot == ["c-fact", "c-echo"]


async def test_forget_query_no_match_is_honest(gw):
    tool = MemoryForgetTool()
    result = await tool.run({"tenant_id": "t-1", "query": "nonexistent-xyzzy"})
    assert result["forgotten"] is False
    assert result["deleted"] == 0
    assert result["coords"] == []


async def test_forget_requires_coord_or_query():
    tool = MemoryForgetTool()
    with pytest.raises(ToolExecutionError):
        await tool.run({"tenant_id": "t-1"})


async def test_forget_single_coord(gw):
    tool = MemoryForgetTool()
    result = await tool.run({"tenant_id": "t-1", "coord": "c-fact"})
    assert result["mode"] == "coord"
    assert result["forgotten"] is True
    assert gw.forgot == ["c-fact"]
