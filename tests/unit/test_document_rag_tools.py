"""Document RAG tools — T-1 MemoryGateway only (TOOLS-001 §5.9).

No SFM client, no local FAISS. Fake gateway in tests only proves tool
wiring; production path is real SomaBrain via MemoryGateway.
"""

from __future__ import annotations

import pytest

from services.common.memory_contract import MemoryAck, MemoryHit
from services.tool_executor.assistant_tools.document_rag import (
    DocumentIndexTool,
    DocumentQueryTool,
    chunk_label,
    index_document_text,
    is_chunk_for_document,
    query_document,
    require_tenant,
    split_text,
)
from services.tool_executor.tools import ToolExecutionError


class _FakeAck:
    def __init__(self, coord: str, ok: bool = True, error: str | None = None):
        self.coord = coord
        self.ok = ok
        self.error = error
        self.store = "somabrain"


class _FakeHit:
    def __init__(self, text: str, coord: str, score: float = 0.9):
        self.text = text
        self.coord = coord
        self.score = score
        self.store = "somabrain"
        self.kind = "semantic"
        self.created_at = "2026-10-09T00:00:00Z"


class _FakeGateway:
    def __init__(self):
        self.remembered: list[str] = []
        self.recall_hits: list[_FakeHit] = []

    async def remember_text(self, text, **kwargs):
        self.remembered.append(text)
        idx = len(self.remembered) - 1
        return [_FakeAck(coord=f"c{idx}")]

    async def recall(self, query, k, tenant_id):
        return self.recall_hits[: int(k)]


def test_split_text_empty():
    assert split_text("") == []
    assert split_text("   ") == []


def test_split_text_short_single_chunk():
    chunks = split_text("hello world")
    assert chunks == ["hello world"]


def test_split_text_overlap():
    text = "x" * 2500
    chunks = split_text(text, chunk_size=1000, chunk_overlap=100)
    assert len(chunks) >= 3
    assert all(len(c) <= 1000 for c in chunks)


def test_chunk_label_and_filter():
    label = chunk_label("att-1", 2)
    assert label == "[doc:att-1 #2] "
    assert is_chunk_for_document(label + "body", "att-1")
    assert not is_chunk_for_document("plain memory", "att-1")
    assert not is_chunk_for_document(label + "body", "other")


def test_require_tenant_rejects_placeholder():
    with pytest.raises(ToolExecutionError):
        require_tenant({"tenant_id": "default"})
    with pytest.raises(ToolExecutionError):
        require_tenant({})
    assert require_tenant({"tenant_id": "t-abc"}) == "t-abc"


async def test_index_document_text_writes_labeled_chunks():
    gw = _FakeGateway()
    result = await index_document_text(
        "alpha beta gamma",
        tenant_id="t-1",
        attachment_id="att-9",
        gateway=gw,
    )
    assert result["indexed"] == 1
    assert result["failed"] == 0
    assert gw.remembered[0].startswith("[doc:att-9 #0] ")
    assert "alpha beta gamma" in gw.remembered[0]


async def test_query_document_filters_by_attachment():
    gw = _FakeGateway()
    gw.recall_hits = [
        _FakeHit("[doc:att-1 #0] section one", "c0"),
        _FakeHit("unrelated chat memory", "c1"),
        _FakeHit("[doc:att-2 #0] other doc", "c2"),
    ]
    result = await query_document(
        "section",
        tenant_id="t-1",
        attachment_id="att-1",
        gateway=gw,
    )
    assert result["count"] == 1
    assert "section one" in result["digest"][0]["summary"]
    assert result["digest"][0]["coord"] == "c0"


async def test_query_document_empty_query():
    result = await query_document("", tenant_id="t-1", gateway=_FakeGateway())
    assert result["count"] == 0
    assert result["error"]


async def test_document_query_tool_requires_tenant():
    tool = DocumentQueryTool()
    with pytest.raises(ToolExecutionError):
        await tool.run({"query": "hi"})


async def test_document_index_tool_indexes_provided_text(monkeypatch):
    gw = _FakeGateway()
    monkeypatch.setattr(
        "services.tool_executor.assistant_tools.document_rag._memory_gateway",
        lambda: gw,
    )
    tool = DocumentIndexTool()
    result = await tool.run(
        {
            "attachment_id": "att-x",
            "tenant_id": "t-1",
            "text": "pdf body content",
        }
    )
    assert result["indexed"] == 1
    assert gw.remembered[0].startswith("[doc:att-x #0] ")
