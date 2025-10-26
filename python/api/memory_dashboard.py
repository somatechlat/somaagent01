import os
import time
from typing import Any, Dict, List, Optional

import httpx
from python.helpers import files
from python.helpers.memory import Document  # use runtime-safe Document (real or shim)
from python.helpers.api import ApiHandler, Request, Response
from python.helpers.memory import Memory


class MemoryDashboard(ApiHandler):
    async def _use_gateway(self) -> bool:
        flag = os.getenv("UI_USE_GATEWAY", "false").strip().lower()
        return flag in {"1", "true", "yes", "on"}

    def _gateway_base(self) -> str:
        return os.getenv("UI_GATEWAY_BASE", os.getenv("GATEWAY_BASE_URL", "http://localhost:20016")).rstrip("/")

    def _auth_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {}
        if (bearer := os.getenv("UI_GATEWAY_BEARER")):
            headers["Authorization"] = f"Bearer {bearer}"
        return headers

    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            action = input.get("action", "search")
            if action == "get_memory_subdirs":
                return await self._get_memory_subdirs()
            elif action == "get_current_memory_subdir":
                return await self._get_current_memory_subdir(input)
            elif action == "search":
                # Prefer Gateway admin API when enabled
                if await self._use_gateway():
                    return await self._gateway_search(input)
                return await self._search_memories(input)
            elif action == "delete":
                if await self._use_gateway():
                    return await self._gateway_delete(input)
                return await self._delete_memory(input)
            elif action == "bulk_delete":
                if await self._use_gateway():
                    return await self._gateway_bulk_delete(input)
                return await self._bulk_delete_memories(input)
            elif action == "update":
                # Update via Gateway is not supported yet; fall back to local only
                if await self._use_gateway():
                    return {"success": False, "error": "Update not supported via Gateway"}
                return await self._update_memory(input)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "memories": [],
                    "total_count": 0,
                }

        except Exception as e:
            return {"success": False, "error": str(e), "memories": [], "total_count": 0}

    # -----------------------------
    # Gateway-backed implementations
    # -----------------------------

    async def _gateway_search(self, input: dict) -> dict:
        base = self._gateway_base()
        params: Dict[str, Any] = {}
        q = input.get("search") or ""
        area = input.get("area") or ""
        if q and area:
            params["q"] = f"{q} {area}"
        elif q:
            params["q"] = q
        elif area:
            params["q"] = area
        limit = int(input.get("limit") or 100)
        params["limit"] = limit
        # If universe/namespace are configured, pass as hints
        universe = os.getenv("SOMA_NAMESPACE")
        namespace = os.getenv("SOMA_MEMORY_NAMESPACE")
        if universe:
            params["universe"] = universe
        if namespace:
            params["namespace"] = namespace

        url = f"{base}/v1/admin/memory"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params, headers=self._auth_headers())
        resp.raise_for_status()
        data = resp.json() or {}
        items: List[Dict[str, Any]] = data.get("items", [])
        formatted: List[Dict[str, Any]] = []
        for it in items:
            payload = (it.get("payload") or {})
            meta = payload.get("metadata") or {}
            content = payload.get("content") or payload.get("text") or payload.get("message") or ""
            area_val = meta.get("area") or (payload.get("area") if isinstance(payload.get("area"), str) else None) or "unknown"
            ts = it.get("wal_timestamp")
            iso = _iso_utc(ts) if ts else meta.get("timestamp") or "unknown"
            formatted.append(
                {
                    "id": payload.get("id") or it.get("event_id") or str(it.get("id")),
                    "area": area_val,
                    "timestamp": iso,
                    "content_full": content,
                    "knowledge_source": False,
                    "source_file": meta.get("source_file", ""),
                    "file_type": meta.get("file_type", ""),
                    "consolidation_action": meta.get("consolidation_action", ""),
                    "tags": meta.get("tags", []),
                    "metadata": payload,
                }
            )

        return {
            "success": True,
            "memories": formatted,
            "total_count": len(formatted),
            "total_db_count": len(formatted),
            "knowledge_count": sum(1 for m in formatted if m["knowledge_source"]),
            "conversation_count": sum(1 for m in formatted if not m["knowledge_source"]),
            "search_query": q,
            "area_filter": area,
            "memory_subdir": input.get("memory_subdir", "default"),
        }

    async def _gateway_delete(self, input: dict) -> dict:
        mem_id = input.get("memory_id")
        if not mem_id:
            return {"success": False, "error": "Memory ID is required for deletion"}
        base = self._gateway_base()
        url = f"{base}/v1/memory/{mem_id}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.delete(url, headers=self._auth_headers())
        if resp.status_code >= 300:
            return {"success": False, "error": f"delete failed: {resp.text}"}
        return {"success": True, "message": f"Memory {mem_id} deleted via Gateway"}

    async def _gateway_bulk_delete(self, input: dict) -> dict:
        ids = input.get("memory_ids") or []
        if not isinstance(ids, list) or not ids:
            return {"success": False, "error": "No memory IDs provided for bulk deletion"}
        ok = 0
        for mem_id in ids:
            res = await self._gateway_delete({"memory_id": mem_id})
            if res.get("success"):
                ok += 1
        if ok == len(ids):
            return {"success": True, "message": f"Successfully deleted {ok} memories"}
        if ok > 0:
            return {"success": True, "message": f"Deleted {ok} memories; {len(ids)-ok} failed"}
        return {"success": False, "error": "Failed to delete any memories"}

    async def _delete_memory(self, input: dict) -> dict:
        """Delete a memory by ID from the specified subdirectory."""
        try:
            memory_subdir = input.get("memory_subdir", "default")
            memory_id = input.get("memory_id")

            if not memory_id:
                return {"success": False, "error": "Memory ID is required for deletion"}

            memory = await Memory.get_by_subdir(memory_subdir, preload_knowledge=False)

            rem = await memory.delete_documents_by_ids([memory_id])

            if len(rem) == 0:
                return {
                    "success": False,
                    "error": f"Memory with ID '{memory_id}' not found",
                }
            else:
                return {
                    "success": True,
                    "message": f"Memory {memory_id} deleted successfully",
                }

        except Exception as e:
            return {"success": False, "error": f"Failed to delete memory: {str(e)}"}

    async def _bulk_delete_memories(self, input: dict) -> dict:
        """Delete multiple memories by IDs from the specified subdirectory."""
        try:
            memory_subdir = input.get("memory_subdir", "default")
            memory_ids = input.get("memory_ids", [])

            if not memory_ids:
                return {
                    "success": False,
                    "error": "No memory IDs provided for bulk deletion",
                }

            if not isinstance(memory_ids, list):
                return {
                    "success": False,
                    "error": "Memory IDs must be provided as a list",
                }

            # delete
            memory = await Memory.get_by_subdir(memory_subdir, preload_knowledge=False)
            rem = await memory.delete_documents_by_ids(memory_ids)

            if len(rem) == len(memory_ids):
                return {
                    "success": True,
                    "message": f"Successfully deleted {len(memory_ids)} memories",
                }
            elif len(rem) > 0:
                return {
                    "success": True,
                    "message": f"Successfully deleted {len(rem)} memories. {len(memory_ids) - len(rem)} failed.",
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to delete any memories.",
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to bulk delete memories: {str(e)}",
            }

    async def _get_current_memory_subdir(self, input: dict) -> dict:
        """Get the current memory subdirectory from the active context."""
        try:
            # Try to get the context from the request
            context_id = input.get("context_id", None)
            if not context_id:
                # Fallback to default if no context available
                return {"success": True, "memory_subdir": "default"}

            # Import AgentContext here to avoid circular imports
            from agent import AgentContext

            # Get the context and extract memory subdirectory
            context = AgentContext.get(context_id)
            if context and hasattr(context, "config") and hasattr(context.config, "memory_subdir"):
                memory_subdir = context.config.memory_subdir or "default"
                return {"success": True, "memory_subdir": memory_subdir}
            else:
                return {"success": True, "memory_subdir": "default"}

        except Exception:
            return {
                "success": True,  # Still success, just fallback to default
                "memory_subdir": "default",
            }

    async def _get_memory_subdirs(self) -> dict:
        """Get available memory subdirectories."""
        try:
            # Get subdirectories from memory folder
            subdirs = files.get_subdirectories("memory", exclude="embeddings")

            # Ensure 'default' is always available
            if "default" not in subdirs:
                subdirs.insert(0, "default")

            return {"success": True, "subdirs": subdirs}
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get memory subdirectories: {str(e)}",
                "subdirs": ["default"],
            }

    async def _search_memories(self, input: dict) -> dict:
        """Search memories in the specified subdirectory."""
        try:
            # Get search parameters
            memory_subdir = input.get("memory_subdir", "default")
            area_filter = input.get("area", "")  # Filter by memory area
            search_query = input.get("search", "")  # Full-text search query
            limit = input.get("limit", 100)  # Number of results to return
            threshold = input.get("threshold", 0.6)  # Similarity threshold

            memory = await Memory.get_by_subdir(memory_subdir, preload_knowledge=False)

            all_docs_map = await memory.get_all_docs()
            memories = []

            if search_query:
                docs = await memory.search_similarity_threshold(
                    query=search_query,
                    limit=limit,
                    threshold=threshold,
                    filter=f"area == '{area_filter}'" if area_filter else "",
                )
                memories = docs
            else:
                # If no search query, get all memories from specified area(s)
                for doc_id, doc in all_docs_map.items():
                    # Apply area filter if specified
                    if area_filter and doc.metadata.get("area", "") != area_filter:
                        continue
                    memories.append(doc)

                # sort by timestamp
                def get_sort_key(m):
                    timestamp = m.metadata.get("timestamp", "0000-00-00 00:00:00")
                    return timestamp

                memories.sort(key=get_sort_key, reverse=True)

                # Apply limit AFTER sorting to get the newest entries
                if limit and len(memories) > limit:
                    memories = memories[:limit]

            # Format memories for the dashboard
            formatted_memories = [self._format_memory_for_dashboard(m) for m in memories]

            # Get summary statistics
            total_memories = len(formatted_memories)
            knowledge_count = sum(1 for m in formatted_memories if m["knowledge_source"])
            conversation_count = total_memories - knowledge_count

            # Get total count of all memories in database (unfiltered)
            total_db_count = len(all_docs_map)

            return {
                "success": True,
                "memories": formatted_memories,
                "total_count": total_memories,
                "total_db_count": total_db_count,
                "knowledge_count": knowledge_count,
                "conversation_count": conversation_count,
                "search_query": search_query,
                "area_filter": area_filter,
                "memory_subdir": memory_subdir,
            }

        except Exception as e:
            return {"success": False, "error": str(e), "memories": [], "total_count": 0}

    def _format_memory_for_dashboard(self, m: Document) -> dict:
        """Format a memory document for the dashboard."""
        metadata = m.metadata
        return {
            "id": metadata.get("id", "unknown"),
            "area": metadata.get("area", "unknown"),
            "timestamp": metadata.get("timestamp", "unknown"),
            # "content_preview": m.page_content[:200]
            # + ("..." if len(m.page_content) > 200 else ""),
            "content_full": m.page_content,
            "knowledge_source": metadata.get("knowledge_source", False),
            "source_file": metadata.get("source_file", ""),
            "file_type": metadata.get("file_type", ""),
            "consolidation_action": metadata.get("consolidation_action", ""),
            "tags": metadata.get("tags", []),
            "metadata": metadata,  # Include full metadata for advanced users
        }

    async def _update_memory(self, input: dict) -> dict:
        try:
            memory_subdir = input.get("memory_subdir")
            original = input.get("original")
            edited = input.get("edited")

            if not memory_subdir or not original or not edited:
                return {"success": False, "error": "Missing required parameters"}

            doc = Document(
                page_content=edited["content_full"],
                metadata=edited["metadata"],
            )

            memory = await Memory.get_by_subdir(memory_subdir, preload_knowledge=False)
            id = (await memory.update_documents([doc]))[0]
            doc = memory.get_document_by_id(id)
            formatted_doc = self._format_memory_for_dashboard(doc) if doc else None

            return {"success": formatted_doc is not None, "memory": formatted_doc}
        except Exception as e:
            return {"success": False, "error": str(e), "memory": None}


def _iso_utc(ts: Optional[float]) -> str:
    try:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(float(ts)))
    except Exception:
        return "unknown"
