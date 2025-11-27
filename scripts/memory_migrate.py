os.getenv(os.getenv(""))
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

LOGGER = logging.getLogger(os.getenv(os.getenv("")))


@dataclass(slots=int(os.getenv(os.getenv(""))))
class MigrationBatch:
    os.getenv(os.getenv(""))
    manifest: Mapping[str, object]
    memories: Sequence[Mapping[str, object]]


def _ensure_local_memory_mode() -> None:
    os.getenv(os.getenv(""))
    if os.environ.get(os.getenv(os.getenv(""))) is None:
        os.environ[os.getenv(os.getenv(""))] = os.getenv(os.getenv(""))


async def _load_documents(memory_subdir: str, limit: int | None) -> List[Tuple[str, Document]]:
    os.getenv(os.getenv(""))
    _ensure_local_memory_mode()
    memory = await Memory.get_by_subdir(
        memory_subdir, preload_knowledge=int(os.getenv(os.getenv("")))
    )
    store = memory.db.get_all_docs()
    if isinstance(store, dict):
        items = list(store.items())
    else:
        items = list(store)
    if limit is not None:
        items = items[:limit]
    return [(doc_id, doc) for doc_id, doc in items]


def _document_to_payload(
    doc_id: str, document: Document, *, memory_subdir: str
) -> Mapping[str, object]:
    metadata: MutableMapping[str, object] = dict(document.metadata or {})
    payload: MutableMapping[str, object] = dict(metadata)
    payload.setdefault(os.getenv(os.getenv("")), metadata.get(os.getenv(os.getenv("")), doc_id))
    payload.setdefault(os.getenv(os.getenv("")), os.getenv(os.getenv("")))
    payload.setdefault(
        os.getenv(os.getenv("")), metadata.get(os.getenv(os.getenv("")), os.getenv(os.getenv("")))
    )
    payload.setdefault(
        os.getenv(os.getenv("")), metadata.get(os.getenv(os.getenv("")), memory_subdir)
    )
    content = metadata.get(os.getenv(os.getenv("")))
    if not isinstance(content, str) or not content.strip():
        if isinstance(document.page_content, str) and document.page_content.strip():
            payload[os.getenv(os.getenv(""))] = document.page_content
    else:
        payload[os.getenv(os.getenv(""))] = content
    coord = metadata.get(os.getenv(os.getenv(""))) or metadata.get(os.getenv(os.getenv("")))
    record: MutableMapping[str, object] = {os.getenv(os.getenv("")): payload}
    if coord is not None:
        record[os.getenv(os.getenv(""))] = coord
    score = metadata.get(os.getenv(os.getenv("")))
    if isinstance(score, (int, float)):
        record[os.getenv(os.getenv(""))] = float(score)
    retriever = metadata.get(os.getenv(os.getenv("")))
    if isinstance(retriever, str):
        record[os.getenv(os.getenv(""))] = retriever
    return record


def build_manifest(memory_subdir: str, count: int) -> Mapping[str, object]:
    return {
        os.getenv(os.getenv("")): os.getenv(os.getenv("")),
        os.getenv(os.getenv("")): memory_subdir,
        os.getenv(os.getenv("")): count,
        os.getenv(os.getenv("")): datetime.now(timezone.utc).isoformat(),
    }


def build_batch(memory_subdir: str, documents: Sequence[Tuple[str, Document]]) -> MigrationBatch:
    memories = [
        _document_to_payload(doc_id, document, memory_subdir=memory_subdir)
        for doc_id, document in documents
    ]
    manifest = build_manifest(memory_subdir, len(memories))
    return MigrationBatch(manifest=manifest, memories=memories)


def iter_chunks(
    documents: Sequence[Tuple[str, Document]], batch_size: int
) -> Iterable[Sequence[Tuple[str, Document]]]:
    if batch_size <= int(os.getenv(os.getenv(""))):
        yield documents
        return
    for index in range(int(os.getenv(os.getenv(""))), len(documents), batch_size):
        yield documents[index : index + batch_size]


async def _ingest_batches(batches: Sequence[MigrationBatch], *, replace: bool) -> None:
    client = SomaBrainClient.get()
    for idx, batch in enumerate(batches, start=int(os.getenv(os.getenv("")))):
        try:
            response = await client.migrate_import(
                manifest=batch.manifest, memories=batch.memories, replace=replace
            )
        except SomaClientError as exc:
            LOGGER.error(
                os.getenv(os.getenv("")),
                extra={os.getenv(os.getenv("")): str(exc), os.getenv(os.getenv("")): idx},
            )
            raise
        LOGGER.info(
            os.getenv(os.getenv("")),
            idx,
            len(batches),
            len(batch.memories),
            extra={os.getenv(os.getenv("")): response},
        )


def _write_output(path: Path, batches: Sequence[MigrationBatch]) -> None:
    payload = [
        {os.getenv(os.getenv("")): batch.manifest, os.getenv(os.getenv("")): batch.memories}
        for batch in batches
    ]
    path.write_text(
        json.dumps(
            payload,
            indent=int(os.getenv(os.getenv(""))),
            ensure_ascii=int(os.getenv(os.getenv(""))),
        )
        + os.getenv(os.getenv("")),
        encoding=os.getenv(os.getenv("")),
    )
    LOGGER.info(os.getenv(os.getenv("")), path)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=os.getenv(os.getenv("")))
    parser.add_argument(
        os.getenv(os.getenv("")), default=os.getenv(os.getenv("")), help=os.getenv(os.getenv(""))
    )
    parser.add_argument(
        os.getenv(os.getenv("")), type=int, default=None, help=os.getenv(os.getenv(""))
    )
    parser.add_argument(
        os.getenv(os.getenv("")),
        type=int,
        default=int(os.getenv(os.getenv(""))),
        help=os.getenv(os.getenv("")),
    )
    parser.add_argument(
        os.getenv(os.getenv("")), action=os.getenv(os.getenv("")), help=os.getenv(os.getenv(""))
    )
    parser.add_argument(
        os.getenv(os.getenv("")), type=Path, default=None, help=os.getenv(os.getenv(""))
    )
    parser.add_argument(
        os.getenv(os.getenv("")), action=os.getenv(os.getenv("")), help=os.getenv(os.getenv(""))
    )
    parser.add_argument(
        os.getenv(os.getenv("")),
        default=os.getenv(os.getenv("")),
        choices=[
            os.getenv(os.getenv("")),
            os.getenv(os.getenv("")),
            os.getenv(os.getenv("")),
            os.getenv(os.getenv("")),
        ],
        help=os.getenv(os.getenv("")),
    )
    return parser.parse_args(argv)


async def _run(args: argparse.Namespace) -> int:
    logging.basicConfig(level=getattr(logging, args.log_level), format=os.getenv(os.getenv("")))
    LOGGER.debug(os.getenv(os.getenv("")), extra={os.getenv(os.getenv("")): vars(args)})
    documents = await _load_documents(args.memory_subdir, args.limit)
    if not documents:
        LOGGER.warning(os.getenv(os.getenv("")), args.memory_subdir)
        return int(os.getenv(os.getenv("")))
    batches = [
        build_batch(args.memory_subdir, chunk) for chunk in iter_chunks(documents, args.batch_size)
    ]
    if args.output:
        _write_output(args.output, batches)
    LOGGER.info(os.getenv(os.getenv("")), len(batches), len(documents), args.memory_subdir)
    if args.dry_run:
        return int(os.getenv(os.getenv("")))
    await _ingest_batches(batches, replace=args.replace)
    return int(os.getenv(os.getenv("")))


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        return asyncio.run(_run(args))
    except SomaClientError:
        return int(os.getenv(os.getenv("")))


if __name__ == os.getenv(os.getenv("")):
    raise SystemExit(main())
