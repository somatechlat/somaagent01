"""Memory store implementations for remote SomaBrain.

This module contains the public ``SomaMemory`` class, the FAISS-compatible
``_SomaDocStoreAdapter``, and the assembled ``_SomaDocStore`` class that
composes the base store with episodic write and semantic search mixins.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

from langchain_core.documents import Document

from admin.core.helpers.episodic_memory_store import _SomaDocStoreWriteMixin
from admin.core.helpers.memory_store_base import _SomaDocStoreBase
from admin.core.helpers.semantic_memory_store import _SomaDocStoreSearchMixin
from admin.core.somabrain_client import SomaBrainClient, SomaClientError


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
        """Execute Area."""

        return self._memory_area_enum

    @property
    def context(self):
        """Execute context."""

        if self.agent and getattr(self.agent, "context", None):
            return self.agent.context
        return None

    async def refresh(self) -> None:
        """Execute refresh."""

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
        """Retrieve all docs."""

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
        """Retrieve timestamp."""

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
        """Retrieve all docs."""

        return self._store.get_all_docs_sync()


class _SomaDocStore(_SomaDocStoreWriteMixin, _SomaDocStoreSearchMixin, _SomaDocStoreBase):
    """Handles caching and transformations for SomaBrain memory payloads."""
