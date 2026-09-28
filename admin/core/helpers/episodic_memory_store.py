"""Episodic write-path operations for remote SomaBrain memory stores.

This module contains the write-side mixin used by ``_SomaDocStore`` to
persist, update, and remove memory documents.
"""

from __future__ import annotations

from typing import List

from langchain_core.documents import Document

from admin.core.helpers import guids
from admin.core.helpers.memory_store_base import _SomaDocStoreBase
from admin.core.helpers.print_style import PrintStyle
from admin.core.somabrain_client import SomaClientError


class _SomaDocStoreWriteMixin:
    """Write operations (insert/update/delete) for the SomaBrain-backed doc store."""

    async def insert_documents(self: _SomaDocStoreBase, docs: list[Document]) -> List[str]:
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
                client = self._require_client()
                coord_str = self._format_coord(coord)
                result = await client.remember(
                    payload,
                    coord=coord_str,
                    universe=self.memory.memory_subdir,
                    namespace=self.memory.memory_subdir,
                )
            except SomaClientError as exc:
                PrintStyle.error(f"Failed to store memory via SomaBrain: {exc}")
                continue
            else:
                if isinstance(result, dict):
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

    async def update_documents(self: _SomaDocStoreBase, docs: list[Document]) -> List[str]:
        """Execute update documents.

        Args:
            docs: The docs.
        """

        ids = [doc.metadata.get("id") for doc in docs if doc.metadata.get("id")]
        if ids:
            await self.delete_documents_by_ids([str(i) for i in ids if i])
        return await self.insert_documents(docs)

    async def delete_documents_by_ids(self: _SomaDocStoreBase, ids: list[str]) -> List[Document]:
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
                client = self._require_client()
                await client.delete(coord_list)
            except SomaClientError as exc:
                PrintStyle.error(f"Failed to delete memory {doc_id}: {exc}")
                continue
            removed.append(doc)
            self._cache.pop(doc_id, None)
        return removed
