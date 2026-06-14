"""Semantic search-path operations for remote SomaBrain memory stores.

This module contains the search/recall-side mixin used by ``_SomaDocStore``
to retrieve and filter memory documents by similarity.
"""

from __future__ import annotations

from typing import Any, List, Optional

from langchain_core.documents import Document

from admin.core.helpers.memory_store_base import _SomaDocStoreBase
from admin.core.helpers.print_style import PrintStyle
from admin.core.somabrain_client import SomaClientError


class _SomaDocStoreSearchMixin:
    """Search/recall operations for the SomaBrain-backed doc store."""

    async def search_similarity_threshold(
        self: _SomaDocStoreBase, query: str, limit: int, threshold: float, filter: str = ""
    ) -> List[Document]:
        """Execute search similarity threshold.

        Args:
            query: The query.
            limit: The limit.
            threshold: The threshold.
            filter: The filter.
        """

        try:
            client = self._require_client()
            response = await client.recall(
                query,
                top_k=limit or 3,
                universe=self.memory.memory_subdir,
                namespace=self.memory.memory_subdir,
            )
        except SomaClientError as exc:
            PrintStyle.error(f"SomaBrain recall failed: {exc}")
            return []

        memory_items: Optional[List[Any]] = None
        if isinstance(response, dict):
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
        self: _SomaDocStoreBase, query: str, threshold: float, filter: str
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
