from __future__ import annotations

from datetime import datetime

import pytest

pytest.importorskip("langchain_community")
pytest.importorskip("langchain_core.documents")

from langchain_core.documents import Document

from scripts import memory_migrate


@pytest.mark.parametrize(
    "content,metadata_expected",
    [
        ("hello", {"content": "hello"}),
        ("", {}),
    ],
)
def test_document_to_payload_includes_content_when_missing(
    content: str, metadata_expected: dict[str, str]
) -> None:
    document = Document(page_content=content, metadata={})
    result = memory_migrate._document_to_payload("doc-1", document, memory_subdir="default")

    assert result["payload"]["id"] == "doc-1"
    assert result["payload"]["universe"] == "default"
    for key, value in metadata_expected.items():
        assert result["payload"][key] == value


def test_document_to_payload_preserves_coord_and_score() -> None:
    document = Document(
        page_content="content",
        metadata={
            "coord": "1.0,2.0,3.0",
            "score": 0.42,
            "retriever": "semantic",
            "content": "existing",
        },
    )
    result = memory_migrate._document_to_payload("doc-2", document, memory_subdir="default")

    assert result["coord"] == "1.0,2.0,3.0"
    assert result["score"] == pytest.approx(0.42)
    assert result["retriever"] == "semantic"
    assert result["payload"]["content"] == "existing"


def test_build_manifest_contains_timestamp() -> None:
    manifest = memory_migrate.build_manifest("custom", 5)
    assert manifest["memory_subdir"] == "custom"
    assert manifest["snapshot_items"] == 5
    timestamp = datetime.fromisoformat(manifest["generated_at"])  # type: ignore[arg-type]
    assert isinstance(timestamp, datetime)


def test_iter_chunks_handles_batch_size_zero() -> None:
    docs = [(str(i), Document(page_content=str(i))) for i in range(3)]
    chunks = list(memory_migrate.iter_chunks(docs, batch_size=0))
    assert len(chunks) == 1
    assert chunks[0] == docs


def test_iter_chunks_splits_documents() -> None:
    docs = [(str(i), Document(page_content=str(i))) for i in range(5)]
    chunks = list(memory_migrate.iter_chunks(docs, batch_size=2))
    assert len(chunks) == 3
    assert sum(len(chunk) for chunk in chunks) == 5


@pytest.mark.asyncio
async def test_build_batch_integration() -> None:
    docs = [("a", Document(page_content="hello")), ("b", Document(page_content="world"))]
    batch = memory_migrate.build_batch("default", docs)
    assert batch.manifest["snapshot_items"] == 2
    assert len(batch.memories) == 2
    assert batch.memories[0]["payload"]["id"] == "a"
