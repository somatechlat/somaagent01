"""CLI utility for migrating local FAISS snapshots into SomaBrain.

The tool reads a memory sub-directory from the prior FAISS store used by
Agent Zero and converts every ``langchain`` document into the payload structure
expected by ``SomaClient.migrate_import``.  Operators can dry-run the
transformation, emit the intermediate JSON to disk, or stream the payloads to
SomaBrain in batches.

Example usage::

    # Inspect the payload that would be uploaded (no network calls).
    python scripts/memory_migrate.py --memory-subdir default --dry-run

    # Export the transformed records to a JSON file for manual review.
    python scripts/memory_migrate.py --memory-subdir default --output /tmp/memories.json

    # Push the FAISS snapshot to SomaBrain in batches of 250 records.
    python scripts/memory_migrate.py --memory-subdir default --batch-size 250

The script assumes the existing ``initialize.py`` bootstrap can resolve the
model configuration required to hydrate the FAISS store.  Set ``SOMA_ENABLED``
to ``false`` when running the tool so the ``Memory`` helper loads the local
indices rather than the remote SomaBrain adaptor (the CLI does this
automatically unless the environment already overrides the flag).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Mapping, MutableMapping, Sequence, Tuple

from langchain_core.documents import Document

from python.helpers.memory import Memory
from python.integrations.somabrain_client import SomaBrainClient, SomaClientError

LOGGER = logging.getLogger("memory_migrate")


@dataclass(slots=True)
class MigrationBatch:
    """Represents a set of memory documents prepared for ingestion."""

    manifest: Mapping[str, object]
    memories: Sequence[Mapping[str, object]]


def _ensure_local_memory_mode() -> None:
    """Force the memory helpers to load the prior FAISS backend."""

    if os.environ.get("SOMA_ENABLED") is None:
        os.environ["SOMA_ENABLED"] = "false"


async def _load_documents(memory_subdir: str, limit: int | None) -> List[Tuple[str, Document]]:
    """Load documents from the local FAISS index for the given sub-directory."""

    _ensure_local_memory_mode()
    memory = await Memory.get_by_subdir(memory_subdir, preload_knowledge=False)
    store = memory.db.get_all_docs()
    if isinstance(store, dict):
        items = list(store.items())
    else:  # pragma: no cover - defensive branch
        items = list(store)
    if limit is not None:
        items = items[:limit]
    return [(doc_id, doc) for doc_id, doc in items]


def _document_to_payload(
    doc_id: str, document: Document, *, memory_subdir: str
) -> Mapping[str, object]:
    metadata: MutableMapping[str, object] = dict(document.metadata or {})
    payload: MutableMapping[str, object] = dict(metadata)
    payload.setdefault("id", metadata.get("id", doc_id))
    payload.setdefault("source", "agent-zero-faiss")
    payload.setdefault("area", metadata.get("area", "main"))
    payload.setdefault("universe", metadata.get("universe", memory_subdir))

    content = metadata.get("content")
    if not isinstance(content, str) or not content.strip():
        if isinstance(document.page_content, str) and document.page_content.strip():
            payload["content"] = document.page_content
    else:
        payload["content"] = content

    coord = metadata.get("coord") or metadata.get("soma_coord")
    record: MutableMapping[str, object] = {"payload": payload}
    if coord is not None:
        record["coord"] = coord
    score = metadata.get("score")
    if isinstance(score, (int, float)):
        record["score"] = float(score)
    retriever = metadata.get("retriever")
    if isinstance(retriever, str):
        record["retriever"] = retriever
    return record


def build_manifest(memory_subdir: str, count: int) -> Mapping[str, object]:
    return {
        "source": "agent-zero-faiss",
        "memory_subdir": memory_subdir,
        "snapshot_items": count,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def build_batch(
    memory_subdir: str,
    documents: Sequence[Tuple[str, Document]],
) -> MigrationBatch:
    memories = [
        _document_to_payload(doc_id, document, memory_subdir=memory_subdir)
        for doc_id, document in documents
    ]
    manifest = build_manifest(memory_subdir, len(memories))
    return MigrationBatch(manifest=manifest, memories=memories)


def iter_chunks(
    documents: Sequence[Tuple[str, Document]],
    batch_size: int,
) -> Iterable[Sequence[Tuple[str, Document]]]:
    if batch_size <= 0:
        yield documents
        return
    for index in range(0, len(documents), batch_size):
        yield documents[index : index + batch_size]


async def _ingest_batches(
    batches: Sequence[MigrationBatch],
    *,
    replace: bool,
) -> None:
    client = SomaBrainClient.get()
    for idx, batch in enumerate(batches, start=1):
        try:
            response = await client.migrate_import(
                manifest=batch.manifest,
                memories=batch.memories,
                replace=replace,
            )
        except SomaClientError as exc:
            LOGGER.error("SomaBrain migration failed", extra={"error": str(exc), "batch": idx})
            raise
        LOGGER.info(
            "Uploaded batch %s/%s (memories=%s)",
            idx,
            len(batches),
            len(batch.memories),
            extra={"response": response},
        )


def _write_output(path: Path, batches: Sequence[MigrationBatch]) -> None:
    payload = [
        {
            "manifest": batch.manifest,
            "memories": batch.memories,
        }
        for batch in batches
    ]
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    LOGGER.info("Wrote transformed payload to %s", path)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Migrate FAISS snapshots into SomaBrain using migrate_import",
    )
    parser.add_argument(
        "--memory-subdir",
        default="default",
        help="Memory sub-directory to export (default: default)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional cap on the number of documents to migrate.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=0,
        help="Number of documents per migrate_import call (0 = single batch).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not call SomaBrain; emit a summary instead.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to write the transformed payload as JSON.",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Ask SomaBrain to replace existing data for the memory subdir.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO).",
    )
    return parser.parse_args(argv)


async def _run(args: argparse.Namespace) -> int:
    logging.basicConfig(level=getattr(logging, args.log_level), format="%(levelname)s %(message)s")
    LOGGER.debug("Starting migration", extra={"args": vars(args)})

    documents = await _load_documents(args.memory_subdir, args.limit)
    if not documents:
        LOGGER.warning("No documents found for memory subdir '%s'", args.memory_subdir)
        return 0

    batches = [
        build_batch(args.memory_subdir, chunk) for chunk in iter_chunks(documents, args.batch_size)
    ]

    if args.output:
        _write_output(args.output, batches)

    LOGGER.info(
        "Prepared %s batches (%s documents total) for subdir '%s'",
        len(batches),
        len(documents),
        args.memory_subdir,
    )

    if args.dry_run:
        return 0

    await _ingest_batches(batches, replace=args.replace)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        return asyncio.run(_run(args))
    except SomaClientError:
        return 2


if __name__ == "__main__":  # pragma: no cover - manual entry point
    raise SystemExit(main())
