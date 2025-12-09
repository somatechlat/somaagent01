"""Memory store implementations for local FAISS and remote SomaBrain.

This module contains the SomaMemory class and its supporting adapters
for remote memory operations via the SomaBrain API.
"""

from __future__ import annotations

import asyncio
import random
from datetime import datetime
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence
from weakref import WeakKeyDictionary

from python.helpers import guids
from python.helpers.print_style import PrintStyle
from python.integrations.somabrain_client import SomaBrainClient, SomaClientError, SomaMemoryRecord

# Import Document - handle both LC and fallback
try:
    from langchain_core.documents import Document
except Exception:
    class Document:
        def __init__(self, page_content: str = "", metadata: dict | None = None):
            self.page_content = page_content
            self.metadata = metadata or {}


class MemoryAreaEnum:
    MAIN = "main"
    FRAGMENTS = "fragments"
    SOLUTIONS = "solutions"
    INSTRUMENTS = "instruments"


class SomaMemory:
    """Remote memory store backed by the SomaBrain API."""

    Area = MemoryAreaEnum

    def __init__(self, agent: Optional[Any], memory_subdir: str) -> None:
        self.agent = agent
        self.memory_subdir = memory_subdir or "default"
        self._client = SomaBrainClient.get()
        self._docstore = _SomaDocStore(self)
        self.db = _SomaDocStoreAdapter(self._docstore)

    @property
    def context(self):
        if self.agent and getattr(self.agent, "context", None):
            return self.agent.context
        return None

    async def refresh(self) -> None:
        await self._docstore.refresh()

    async def preload_knowledge(self, log_item: Any, knowledge_dirs: list[str], memory_subdir: str) -> None:
        return None

    async def insert_text(self, text: str, metadata: dict | None = None) -> str:
        metadata = dict(metadata or {})
        if "area" not in metadata:
            metadata["area"] = MemoryAreaEnum.MAIN
        doc = Document(page_content=text, metadata=metadata)
        ids = await self.insert_documents([doc])
        if not ids:
            raise SomaClientError("Failed to insert memory via SomaBrain")
        return ids[0]

    async def insert_documents(self, docs: list[Document]) -> List[str]:
        return await self._docstore.insert_documents(docs)

    async def update_documents(self, docs: list[Document]) -> List[str]:
        return await self._docstore.update_documents(docs)

    async def search_similarity_threshold(self, query: str, limit: int, threshold: float, filter: str = "") -> List[Document]:
        return await self._docstore.search_similarity_threshold(query, limit, threshold, filter)

    async def delete_documents_by_query(self, query: str, threshold: float, filter: str = "") -> List[Document]:
        return await self._docstore.delete_documents_by_query(query, threshold, filter)

    async def delete_documents_by_ids(self, ids: list[str]) -> List[Document]:
        return await self._docstore.delete_documents_by_ids(ids)

    async def get_all_docs(self) -> Dict[str, Document]:
        return await self._docstore.get_all_docs()

    async def get_documents_by_ids(self, ids: Sequence[str]) -> List[Document]:
        return await self._docstore.get_documents_by_ids(ids)

    async def delete_by_ids(self, ids: Sequence[str]) -> List[Document]:
        return await self._docstore.delete_documents_by_ids(list(ids))

    def get_document_by_id(self, doc_id: str) -> Optional[Document]:
        return self._docstore.get_document_by_id_sync(doc_id)

    def get_timestamp(self):
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


class _SomaDocStoreAdapter:
    """Adapter exposing a FAISS-like interface expected by legacy call sites."""

    def __init__(self, store: "_SomaDocStore") -> None:
        self._store = store

    async def aget_by_ids(self, ids: Sequence[str]) -> List[Document]:
        return await self._store.get_documents_by_ids(ids)

    def get_by_ids(self, ids: Sequence[str]) -> List[Document]:
        return self._store.get_documents_by_ids_sync(ids)

    async def adelete(self, ids: Sequence[str]) -> None:
        await self._store.delete_documents_by_ids(list(ids))

    async def aadd_documents(self, documents: list[Document], ids: list[str]) -> None:
        for doc, _id in zip(documents, ids, strict=False):
            doc.metadata["id"] = _id
        await self._store.insert_documents(documents)

    def get_all_docs(self) -> Dict[str, Document]:
        return self._store.get_all_docs_sync()



class _SomaDocStore:
    """Handles caching and transformations for SomaBrain memory payloads."""

    # Import env flags from memory module
    SOMA_CACHE_INCLUDE_WM = False
    SOMA_CACHE_WM_LIMIT = 128

    def __init__(self, memory: SomaMemory) -> None:
        self.memory = memory
        self._client = memory._client
        self._cache: Dict[str, Document] = {}
        self._cache_valid = False
        self._locks: WeakKeyDictionary[asyncio.AbstractEventLoop, asyncio.Lock] = WeakKeyDictionary()

    def _get_lock(self) -> asyncio.Lock:
        loop = asyncio.get_running_loop()
        lock = self._locks.get(loop)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[loop] = lock
        return lock

    async def refresh(self) -> Dict[str, Document]:
        async with self._get_lock():
            try:
                data = await self._client.migrate_export(
                    include_wm=self.SOMA_CACHE_INCLUDE_WM,
                    wm_limit=self.SOMA_CACHE_WM_LIMIT,
                )
                memories = data.get("memories", []) if isinstance(data, Mapping) else []
                self._cache = self._parse_memories(memories)
                self._cache_valid = True
            except SomaClientError as exc:
                PrintStyle.error(f"SomaBrain export failed: {exc}")
                self._cache_valid = False
            return self._cache

    async def _ensure_cache(self) -> Dict[str, Document]:
        if not self._cache_valid:
            return await self.refresh()
        return self._cache

    def _ensure_cache_sync(self) -> Dict[str, Document]:
        if self._cache_valid:
            return self._cache
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(self.refresh())
            return self._cache
        return loop.run_until_complete(self.refresh())

    async def get_all_docs(self) -> Dict[str, Document]:
        return await self._ensure_cache()

    def get_all_docs_sync(self) -> Dict[str, Document]:
        return self._ensure_cache_sync()

    async def get_documents_by_ids(self, ids: Sequence[str]) -> List[Document]:
        cache = await self._ensure_cache()
        return [cache[id] for id in ids if id in cache]

    def get_documents_by_ids_sync(self, ids: Sequence[str]) -> List[Document]:
        cache = self._ensure_cache_sync()
        return [cache[id] for id in ids if id in cache]

    def get_document_by_id_sync(self, doc_id: str) -> Optional[Document]:
        cache = self._ensure_cache_sync()
        return cache.get(doc_id)

    async def insert_documents(self, docs: list[Document]) -> List[str]:
        await self._ensure_cache()
        ids: List[str] = []
        for doc in docs:
            metadata = dict(doc.metadata)
            doc_id = metadata.get("id") or guids.generate_id(10)
            metadata["id"] = doc_id
            coord = metadata.get("coord") or metadata.get("soma_coord") or self._generate_coord(doc_id)
            metadata["coord"] = coord
            metadata["soma_coord"] = coord
            payload = self._build_payload(metadata, doc.page_content)
            try:
                coord_str = self._format_coord(coord)
                result = await self._client.remember(
                    payload, coord=coord_str,
                    universe=self.memory.memory_subdir,
                    namespace=self.memory.memory_subdir,
                )
            except SomaClientError as exc:
                PrintStyle.error(f"Failed to store memory: {exc}")
                continue
            else:
                if isinstance(result, Mapping):
                    returned_coord = result.get("coordinate") or result.get("coord")
                    if returned_coord:
                        metadata["coord"] = returned_coord
                        metadata["soma_coord"] = returned_coord
            doc.metadata = metadata
            self._cache[doc_id] = doc
            ids.append(doc_id)
        self._cache_valid = True
        return ids

    async def update_documents(self, docs: list[Document]) -> List[str]:
        ids = [doc.metadata.get("id") for doc in docs if doc.metadata.get("id")]
        if ids:
            await self.delete_documents_by_ids([str(i) for i in ids if i])
        return await self.insert_documents(docs)

    async def delete_documents_by_ids(self, ids: list[str]) -> List[Document]:
        await self._ensure_cache()
        removed: List[Document] = []
        for doc_id in ids:
            doc = self._cache.get(doc_id)
            if not doc:
                continue
            coord = doc.metadata.get("coord")
            if coord is None:
                continue
            try:
                await self._client.delete(self._parse_coord(coord))
            except SomaClientError as exc:
                PrintStyle.error(f"Failed to delete memory {doc_id}: {exc}")
                continue
            removed.append(doc)
            self._cache.pop(doc_id, None)
        return removed

    async def search_similarity_threshold(self, query: str, limit: int, threshold: float, filter: str) -> List[Document]:
        try:
            response = await self._client.recall(
                query, top_k=limit or 3,
                universe=self.memory.memory_subdir,
                namespace=self.memory.memory_subdir,
            )
        except SomaClientError as exc:
            PrintStyle.error(f"SomaBrain recall failed: {exc}")
            return []

        memory_items = None
        if isinstance(response, Mapping):
            memory_items = response.get("memory") or response.get("results")
        if not isinstance(memory_items, list):
            return []

        docs: List[Document] = []
        for raw in memory_items:
            record = self._convert_memory_record(raw)
            if record is None or (record.score is not None and record.score < threshold):
                continue
            docs.append(self._record_to_document(record))
        return docs

    async def delete_documents_by_query(self, query: str, threshold: float, filter: str) -> List[Document]:
        matches = await self.search_similarity_threshold(query, 100, threshold, filter)
        ids = [str(doc.metadata.get("id")) for doc in matches if doc.metadata.get("id")]
        if ids:
            await self.delete_documents_by_ids(ids)
        return matches

    def _build_payload(self, metadata: MutableMapping[str, Any], content: str) -> Dict[str, Any]:
        payload: Dict[str, Any] = dict(metadata)
        payload.setdefault("memory_type", "episodic")
        payload.setdefault("importance", 1)
        payload.setdefault("area", MemoryAreaEnum.MAIN)
        payload.setdefault("universe", self.memory.memory_subdir)
        timestamp_val = metadata.get("timestamp")
        if isinstance(timestamp_val, (int, float)):
            payload["timestamp"] = float(timestamp_val)
        elif isinstance(timestamp_val, str):
            try:
                payload["timestamp"] = float(timestamp_val)
            except ValueError:
                payload["timestamp"] = datetime.utcnow().timestamp()
        else:
            payload["timestamp"] = datetime.utcnow().timestamp()
        payload["content"] = content
        payload["metadata"] = dict(metadata)
        return payload

    def _parse_coord(self, coord: Any) -> List[float]:
        if isinstance(coord, (list, tuple)):
            return [float(x) for x in coord[:3]]
        if isinstance(coord, str):
            return [float(p.strip()) for p in coord.split(",")[:3]]
        raise ValueError(f"Unsupported coordinate format: {coord}")

    def _format_coord(self, coord: Any) -> str:
        if isinstance(coord, str):
            return coord
        if isinstance(coord, (list, tuple)):
            return ",".join(f"{float(c):.6f}" for c in coord[:3])
        return str(coord)

    def _generate_coord(self, seed: str) -> str:
        rng = random.Random(seed)
        return ",".join(f"{rng.uniform(-10.0, 10.0):.6f}" for _ in range(3))

    def _parse_memories(self, memories: Iterable[Any]) -> Dict[str, Document]:
        cache: Dict[str, Document] = {}
        for raw in memories:
            record = self._convert_memory_record(raw)
            if record:
                cache[record.identifier] = self._record_to_document(record)
        return cache

    def _convert_memory_record(self, raw: Any) -> Optional[SomaMemoryRecord]:
        if not isinstance(raw, Mapping):
            return None
        payload = raw.get("payload", {})
        if not isinstance(payload, Mapping):
            payload = {}
        identifier = str(payload.get("id") or raw.get("key") or raw.get("coord") or guids.generate_id(10))
        coord_raw = raw.get("coord") or payload.get("coord")
        coordinate = None
        if coord_raw:
            try:
                coordinate = self._parse_coord(coord_raw)
            except Exception:
                pass
        score = raw.get("score")
        try:
            score_val = float(score) if score is not None else None
        except (TypeError, ValueError):
            score_val = None
        return SomaMemoryRecord(
            identifier=identifier, payload=payload, score=score_val,
            coordinate=coordinate, retriever=raw.get("retriever") if isinstance(raw.get("retriever"), str) else None,
        )

    def _record_to_document(self, record: SomaMemoryRecord) -> Document:
        metadata = dict(record.payload)
        metadata.setdefault("id", record.identifier)
        if record.coordinate:
            coord_str = ",".join(f"{c:.6f}" for c in record.coordinate)
            metadata["coord"] = coord_str
            metadata["soma_coord"] = coord_str
        if record.score is not None:
            metadata["score"] = record.score
        content = next((metadata.get(k) for k in ["content", "what", "text", "summary", "value"] if isinstance(metadata.get(k), str)), "")
        metadata.setdefault("area", MemoryAreaEnum.MAIN)
        metadata.setdefault("universe", self.memory.memory_subdir)
        return Document(page_content=content, metadata=metadata)
