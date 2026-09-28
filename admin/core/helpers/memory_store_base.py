"""Base infrastructure and shared helpers for remote SomaBrain memory stores.

This module contains the low-level ``_SomaDocStoreBase`` class used by both
the episodic write-path mixin and the semantic search-path mixin.
"""

from __future__ import annotations

import asyncio
import random
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence
from weakref import WeakKeyDictionary

from langchain_core.documents import Document

from admin.core.helpers import guids
from admin.core.helpers.print_style import PrintStyle
from admin.core.somabrain_client import (
    SomaBrainClient,
    SomaClientError,
    SomaMemoryRecord,
)


class _SomaDocStoreBase:
    """Base class with cache lifecycle, coordinate handling, and payload helpers."""

    def __init__(self, memory: Any) -> None:
        """Initialize the instance."""

        self.memory = memory
        self._client = memory._client
        self._cache: Dict[str, Document] = {}
        self._cache_valid = False
        self._locks: WeakKeyDictionary[asyncio.AbstractEventLoop, asyncio.Lock] = (
            WeakKeyDictionary()
        )
        # Import env flags - these are set by the memory module
        self._soma_cache_include_wm = False
        self._soma_cache_wm_limit = 128

    def configure(self, include_wm: bool, wm_limit: int) -> None:
        """Configure cache settings from parent module."""
        self._soma_cache_include_wm = include_wm
        self._soma_cache_wm_limit = wm_limit

    def _require_client(self) -> SomaBrainClient:
        """Return the SomaBrain client or raise if not configured."""
        if self._client is None:
            raise SomaClientError("SomaBrain not configured", status_code=503)
        return self._client

    def _get_lock(self) -> asyncio.Lock:
        """Execute get lock."""

        loop = asyncio.get_running_loop()
        lock = self._locks.get(loop)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[loop] = lock
        return lock

    async def refresh(self) -> Dict[str, Document]:
        """Execute refresh."""

        async with self._get_lock():
            try:
                client = self._require_client()
                data = await client.migrate_export(
                    include_wm=self._soma_cache_include_wm,
                    wm_limit=self._soma_cache_wm_limit,
                )
                memories = data.get("memories", []) if isinstance(data, Mapping) else []
                self._cache = self._parse_memories(memories)
                self._cache_valid = True
            except SomaClientError as exc:
                PrintStyle.error(f"SomaBrain export failed (cache kept): {exc}")
                self._cache_valid = False
            return self._cache

    async def _ensure_cache(self) -> Dict[str, Document]:
        """Execute ensure cache."""

        if not self._cache_valid:
            return await self.refresh()
        return self._cache

    def _ensure_cache_sync(self) -> Dict[str, Document]:
        """Execute ensure cache sync."""

        if self._cache_valid:
            return self._cache
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(self.refresh())
            return self._cache
        return loop.run_until_complete(self.refresh())

    async def get_all_docs(self) -> Dict[str, Document]:
        """Retrieve all docs."""

        return await self._ensure_cache()

    def get_all_docs_sync(self) -> Dict[str, Document]:
        """Retrieve all docs sync."""

        return self._ensure_cache_sync()

    async def get_documents_by_ids(self, ids: Sequence[str]) -> List[Document]:
        """Retrieve documents by ids.

        Args:
            ids: The ids.
        """

        cache = await self._ensure_cache()
        return [cache[id] for id in ids if id in cache]

    def get_documents_by_ids_sync(self, ids: Sequence[str]) -> List[Document]:
        """Retrieve documents by ids sync.

        Args:
            ids: The ids.
        """

        cache = self._ensure_cache_sync()
        return [cache[id] for id in ids if id in cache]

    def get_document_by_id_sync(self, doc_id: str) -> Optional[Document]:
        """Retrieve document by id sync.

        Args:
            doc_id: The doc_id.
        """

        cache = self._ensure_cache_sync()
        return cache.get(doc_id)

    def _build_payload(self, metadata: MutableMapping[str, Any], content: str) -> Dict[str, Any]:
        """Execute build payload.

        Args:
            metadata: The metadata.
            content: The content.
        """

        payload: Dict[str, Any] = dict(metadata)
        area_enum = self.memory._memory_area_enum
        payload.setdefault("memory_type", metadata.get("memory_type", "episodic"))
        payload.setdefault("importance", metadata.get("importance", 1))
        payload.setdefault("area", metadata.get("area", area_enum.MAIN.value))
        payload.setdefault("universe", metadata.get("universe", self.memory.memory_subdir))

        timestamp_val = metadata.get("timestamp")
        numeric_timestamp: float | None = None
        if isinstance(timestamp_val, (int, float)):
            numeric_timestamp = float(timestamp_val)
        elif isinstance(timestamp_val, str):
            try:
                numeric_timestamp = float(timestamp_val)
            except ValueError:
                try:
                    numeric_timestamp = datetime.fromisoformat(timestamp_val).timestamp()
                except ValueError:
                    numeric_timestamp = None

        if numeric_timestamp is None:
            numeric_timestamp = datetime.now(timezone.utc).timestamp()
            metadata["timestamp"] = datetime.now(timezone.utc).isoformat()

        payload["timestamp"] = numeric_timestamp
        payload["content"] = content
        payload["metadata"] = dict(metadata)
        return payload

    def _parse_coord(self, coord: Any) -> List[float]:
        """Execute parse coord.

        Args:
            coord: The coord.
        """

        if isinstance(coord, (list, tuple)):
            return [float(x) for x in coord[:3]]
        if isinstance(coord, str):
            parts = coord.split(",")
            return [float(p.strip()) for p in parts[:3]]
        raise ValueError(f"Unsupported coordinate format: {coord}")

    def _format_coord(self, coord: Any) -> str:
        """Execute format coord.

        Args:
            coord: The coord.
        """

        if isinstance(coord, str):
            return coord
        if isinstance(coord, (list, tuple)):
            return ",".join(f"{float(c):.6f}" for c in coord[:3])
        return str(coord)

    def _generate_coord(self, seed: str) -> str:
        """Execute generate coord.

        Args:
            seed: The seed.
        """

        rng = random.Random(seed)
        return ",".join(f"{rng.uniform(-10.0, 10.0):.6f}" for _ in range(3))

    def _parse_memories(self, memories: Iterable[Any]) -> Dict[str, Document]:
        """Execute parse memories.

        Args:
            memories: The memories.
        """

        cache: Dict[str, Document] = {}
        for raw in memories:
            record = self._convert_memory_record(raw)
            if not record:
                continue
            doc = self._record_to_document(record)
            cache[record.identifier] = doc
        return cache

    def _convert_memory_record(self, raw: Any) -> Optional[SomaMemoryRecord]:
        """Execute convert memory record.

        Args:
            raw: The raw.
        """

        if not isinstance(raw, Mapping):
            return None
        payload = raw.get("payload")
        if not isinstance(payload, dict):
            payload = {}
        identifier = (
            str(payload.get("id"))
            if payload.get("id")
            else str(raw.get("key") or raw.get("coord") or guids.generate_id(10))
        )
        coord_raw = raw.get("coord") or payload.get("coord")
        coordinate: Optional[List[float]] = None
        if coord_raw is not None:
            try:
                coordinate = self._parse_coord(coord_raw)
            except Exception:
                coordinate = None
        score = raw.get("score")
        try:
            score_val = float(score) if score is not None else None
        except (TypeError, ValueError):
            score_val = None
        retriever = raw.get("retriever")
        return SomaMemoryRecord(
            identifier=identifier,
            payload=payload,
            score=score_val,
            coordinate=coordinate,
            retriever=retriever if isinstance(retriever, str) else None,
        )

    def _record_to_document(self, record: SomaMemoryRecord) -> Document:
        """Execute record to document.

        Args:
            record: The record.
        """

        metadata = dict(record.payload)
        metadata.setdefault("id", record.identifier)
        if record.coordinate:
            coord_str = ",".join(f"{c:.6f}" for c in record.coordinate)
            metadata["coord"] = coord_str
            metadata["soma_coord"] = coord_str
        if record.score is not None:
            metadata["score"] = record.score
        if record.retriever:
            metadata["retriever"] = record.retriever
        content_candidates = [
            metadata.get("content"),
            metadata.get("what"),
            metadata.get("text"),
            metadata.get("summary"),
            metadata.get("value"),
        ]
        content = next((c for c in content_candidates if isinstance(c, str)), "")
        area_enum = self.memory._memory_area_enum
        metadata.setdefault("area", metadata.get("area", area_enum.MAIN.value))
        metadata.setdefault("universe", metadata.get("universe", self.memory.memory_subdir))
        return Document(page_content=content, metadata=metadata)
