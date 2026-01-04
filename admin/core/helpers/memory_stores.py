"""Memory store implementations for remote SomaBrain.

This module contains the SomaMemory class and its supporting adapters
for remote memory operations via the SomaBrain API.
"""

from __future__ import annotations

import asyncio
import random
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence
from weakref import WeakKeyDictionary

from langchain_core.documents import Document

from admin.agents.services.somabrain_integration import (
    SomaBrainClient,
    SomaClientError,
    SomaMemoryRecord,
)
from admin.core.helpers import guids
from admin.core.helpers.print_style import PrintStyle


class SomaMemory:
    """Remote memory store backed by the SomaBrain API."""

    def __init__(self, agent: Optional[Any], memory_subdir: str, memory_area_enum: Any) -> None:
        """Initialize the instance."""

        self.agent = agent
        self.memory_subdir = memory_subdir or "default"
        self._memory_area_enum = memory_area_enum
        self._client = SomaBrainClient.get()
        self._docstore = _SomaDocStore(self)
        self.db = _SomaDocStoreAdapter(self._docstore)

    @property
    def Area(self):
        """Execute Area.
            """

        return self._memory_area_enum

    @property
    def context(self):
        """Execute context.
            """

        if self.agent and getattr(self.agent, "context", None):
            return self.agent.context
        return None

    async def refresh(self) -> None:
        """Execute refresh.
            """

        await self._docstore.refresh()

    async def preload_knowledge(
        self, log_item: Any, knowledge_dirs: list[str], memory_subdir: str
    ) -> None:
        # SomaBrain handles knowledge centrally; nothing to preload locally.
        """Execute preload knowledge.

            Args:
                log_item: The log_item.
                knowledge_dirs: The knowledge_dirs.
                memory_subdir: The memory_subdir.
            """

        return None

    async def insert_text(self, text: str, metadata: dict | None = None) -> str:
        """Execute insert text.

            Args:
                text: The text.
                metadata: The metadata.
            """

        metadata = dict(metadata or {})
        if "area" not in metadata:
            metadata["area"] = self._memory_area_enum.MAIN.value
        doc = Document(page_content=text, metadata=metadata)
        ids = await self.insert_documents([doc])
        if not ids:
            raise SomaClientError("Failed to insert memory via SomaBrain")
        return ids[0]

    async def insert_documents(self, docs: list[Document]) -> List[str]:
        """Execute insert documents.

            Args:
                docs: The docs.
            """

        return await self._docstore.insert_documents(docs)

    async def update_documents(self, docs: list[Document]) -> List[str]:
        """Execute update documents.

            Args:
                docs: The docs.
            """

        return await self._docstore.update_documents(docs)

    async def search_similarity_threshold(
        self, query: str, limit: int, threshold: float, filter: str = ""
    ) -> List[Document]:
        """Execute search similarity threshold.

            Args:
                query: The query.
                limit: The limit.
                threshold: The threshold.
                filter: The filter.
            """

        return await self._docstore.search_similarity_threshold(query, limit, threshold, filter)

    async def delete_documents_by_query(
        self, query: str, threshold: float, filter: str = ""
    ) -> List[Document]:
        """Execute delete documents by query.

            Args:
                query: The query.
                threshold: The threshold.
                filter: The filter.
            """

        return await self._docstore.delete_documents_by_query(query, threshold, filter)

    async def delete_documents_by_ids(self, ids: list[str]) -> List[Document]:
        """Execute delete documents by ids.

            Args:
                ids: The ids.
            """

        return await self._docstore.delete_documents_by_ids(ids)

    async def get_all_docs(self) -> Dict[str, Document]:
        """Retrieve all docs.
            """

        return await self._docstore.get_all_docs()

    async def get_documents_by_ids(self, ids: Sequence[str]) -> List[Document]:
        """Retrieve documents by ids.

            Args:
                ids: The ids.
            """

        return await self._docstore.get_documents_by_ids(ids)

    async def delete_by_ids(self, ids: Sequence[str]) -> List[Document]:
        """Execute delete by ids.

            Args:
                ids: The ids.
            """

        return await self._docstore.delete_documents_by_ids(list(ids))

    def get_document_by_id(self, doc_id: str) -> Optional[Document]:
        """Retrieve document by id.

            Args:
                doc_id: The doc_id.
            """

        return self._docstore.get_document_by_id_sync(doc_id)

    def get_timestamp(self):
        """Retrieve timestamp.
            """

        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


class _SomaDocStoreAdapter:
    """Adapter exposing a FAISS-like interface expected by legacy call sites."""

    def __init__(self, store: "_SomaDocStore") -> None:
        """Initialize the instance."""

        self._store = store

    async def aget_by_ids(self, ids: Sequence[str]) -> List[Document]:
        """Execute aget by ids.

            Args:
                ids: The ids.
            """

        return await self._store.get_documents_by_ids(ids)

    def get_by_ids(self, ids: Sequence[str]) -> List[Document]:
        """Retrieve by ids.

            Args:
                ids: The ids.
            """

        return self._store.get_documents_by_ids_sync(ids)

    async def adelete(self, ids: Sequence[str]) -> None:
        """Execute adelete.

            Args:
                ids: The ids.
            """

        await self._store.delete_documents_by_ids(list(ids))

    async def aadd_documents(self, documents: list[Document], ids: list[str]) -> None:
        """Execute aadd documents.

            Args:
                documents: The documents.
                ids: The ids.
            """

        for doc, _id in zip(documents, ids, strict=False):
            doc.metadata["id"] = _id
        await self._store.insert_documents(documents)

    def get_all_docs(self) -> Dict[str, Document]:
        """Retrieve all docs.
            """

        return self._store.get_all_docs_sync()


class _SomaDocStore:
    """Handles caching and transformations for SomaBrain memory payloads."""

    def __init__(self, memory: SomaMemory) -> None:
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

    def _get_lock(self) -> asyncio.Lock:
        """Execute get lock.
            """

        loop = asyncio.get_running_loop()
        lock = self._locks.get(loop)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[loop] = lock
        return lock

    async def refresh(self) -> Dict[str, Document]:
        """Execute refresh.
            """

        async with self._get_lock():
            try:
                data = await self._client.migrate_export(
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
        """Execute ensure cache.
            """

        if not self._cache_valid:
            return await self.refresh()
        return self._cache

    def _ensure_cache_sync(self) -> Dict[str, Document]:
        """Execute ensure cache sync.
            """

        if self._cache_valid:
            return self._cache
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(self.refresh())
            return self._cache
        return loop.run_until_complete(self.refresh())

    async def get_all_docs(self) -> Dict[str, Document]:
        """Retrieve all docs.
            """

        return await self._ensure_cache()

    def get_all_docs_sync(self) -> Dict[str, Document]:
        """Retrieve all docs sync.
            """

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

    async def insert_documents(self, docs: list[Document]) -> List[str]:
        """Execute insert documents.

            Args:
                docs: The docs.
            """

        await self._ensure_cache()
        ids: List[str] = []
        for doc in docs:
            metadata = dict(doc.metadata)
            doc_id = metadata.get("id") or guids.generate_id(10)
            metadata["id"] = doc_id
            coord = (
                metadata.get("coord") or metadata.get("soma_coord") or self._generate_coord(doc_id)
            )
            metadata["coord"] = coord
            metadata["soma_coord"] = coord
            payload = self._build_payload(metadata, doc.page_content)
            try:
                coord_str = self._format_coord(coord)
                result = await self._client.remember(
                    payload,
                    coord=coord_str,
                    universe=self.memory.memory_subdir,
                    namespace=self.memory.memory_subdir,
                )
            except SomaClientError as exc:
                PrintStyle.error(f"Failed to store memory via SomaBrain: {exc}")
                continue
            else:
                if isinstance(result, Mapping):
                    returned_coord = result.get("coordinate") or result.get("coord")
                    if returned_coord:
                        metadata["coord"] = returned_coord
                        metadata["soma_coord"] = returned_coord
                    if result.get("trace_id"):
                        metadata["trace_id"] = result["trace_id"]
                    if result.get("request_id"):
                        metadata["request_id"] = result["request_id"]
            doc.metadata = metadata
            self._cache[doc_id] = doc
            ids.append(doc_id)
        self._cache_valid = True
        return ids

    async def update_documents(self, docs: list[Document]) -> List[str]:
        """Execute update documents.

            Args:
                docs: The docs.
            """

        ids = [doc.metadata.get("id") for doc in docs if doc.metadata.get("id")]
        if ids:
            await self.delete_documents_by_ids([str(i) for i in ids if i])
        return await self.insert_documents(docs)

    async def delete_documents_by_ids(self, ids: list[str]) -> List[Document]:
        """Execute delete documents by ids.

            Args:
                ids: The ids.
            """

        await self._ensure_cache()
        removed: List[Document] = []
        for doc_id in ids:
            doc = self._cache.get(doc_id)
            if not doc:
                continue
            coord = doc.metadata.get("coord") or doc.metadata.get("soma_coord")
            if coord is None:
                continue
            coord_list = self._parse_coord(coord)
            try:
                await self._client.delete(coord_list)
            except SomaClientError as exc:
                PrintStyle.error(f"Failed to delete memory {doc_id}: {exc}")
                continue
            removed.append(doc)
            self._cache.pop(doc_id, None)
        return removed

    async def search_similarity_threshold(
        self, query: str, limit: int, threshold: float, filter: str
    ) -> List[Document]:
        """Execute search similarity threshold.

            Args:
                query: The query.
                limit: The limit.
                threshold: The threshold.
                filter: The filter.
            """

        try:
            response = await self._client.recall(
                query,
                top_k=limit or 3,
                universe=self.memory.memory_subdir,
                namespace=self.memory.memory_subdir,
            )
        except SomaClientError as exc:
            PrintStyle.error(f"SomaBrain recall failed: {exc}")
            return []

        memory_items: Optional[List[Any]] = None
        if isinstance(response, Mapping):
            candidates = response.get("memory")
            if isinstance(candidates, list):
                memory_items = candidates
            else:
                candidates = response.get("results")
                if isinstance(candidates, list):
                    memory_items = candidates
        if not isinstance(memory_items, list):
            return []

        # Import comparator function from memory module to avoid circular import
        comparator = None
        if filter:
            try:
                from admin.core.helpers.memory import Memory

                comparator = Memory._get_comparator(filter)
            except Exception:
                pass

        docs: List[Document] = []
        for raw in memory_items:
            record = self._convert_memory_record(raw)
            if record is None:
                continue
            if record.score is not None and record.score < threshold:
                continue
            doc = self._record_to_document(record)
            if comparator and not comparator(doc.metadata):
                continue
            docs.append(doc)
        return docs

    async def delete_documents_by_query(
        self, query: str, threshold: float, filter: str
    ) -> List[Document]:
        """Execute delete documents by query.

            Args:
                query: The query.
                threshold: The threshold.
                filter: The filter.
            """

        matches = await self.search_similarity_threshold(query, 100, threshold, filter)
        ids = [doc.metadata.get("id") for doc in matches if doc.metadata.get("id")]
        ids = [str(i) for i in ids if i]
        if ids:
            await self.delete_documents_by_ids(ids)
        return matches

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
        if not isinstance(payload, Mapping):
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