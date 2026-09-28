"""SomaBrain Client - Memory operations

Production-grade HTTP client for SomaBrain memory service.
100% Django patterns - No FastAPI, No SQLAlchemy.


- Rule 1: NO BULLSHIT - Real implementation, no mocks
- Rule 4: REAL IMPLEMENTATIONS ONLY
- Rule 8: Django/Ninja ONLY
- Rule 13: CENTRALIZED SETTINGS
- Rule 32: HYBRID CONFIGURATION STANDARD
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Integration: BrainBridge (Compliant Triad Architecture)
from aaas.brain import brain as BrainBridge
from admin.core.somabrain_base import _SomaBrainBaseClient

HAS_BRIDGE = True


LOGGER = logging.getLogger(__name__)


class _SomaBrainMemoryClient(_SomaBrainBaseClient):
    """Memory operations for the SomaBrain client."""

    # =========================================================================
    # MEMORY OPERATIONS
    # =========================================================================

    async def remember(
        self,
        payload: Optional[Dict[str, Any]] = None,
        *,
        tenant: Optional[str] = None,
        namespace: str = "wm",
        content: Optional[str] = None,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        memory_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        coord: Optional[str] = None,
        universe: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Store memory in SomaBrain.

        Args:
            payload: Memory payload with value, key, tags, importance, novelty
            tenant: Tenant ID
            namespace: Memory namespace (wm=working memory)

        Returns:
            Response with coordinate of stored memory

        VIBE Rule 1: NO BULLSHIT - Real API call to somabrain /memory/remember
        """
        effective_tenant = tenant_id or tenant or "default"
        payload = payload or {}
        if content is not None:
            payload = {
                **payload,
                "content": content,
                "user_id": user_id,
                "memory_type": memory_type,
                "metadata": metadata,
            }
        # Format for SomaBrain API: key, value (not payload)
        body = {
            "key": payload.get("key")
            or f"mem_{hashlib.md5(str(payload).encode()).hexdigest()[:16]}",
            "value": payload,
            "tenant": effective_tenant,
            "namespace": namespace,
        }

        # DIRECT MODE CHECK (Triad Compliant)
        if HAS_BRIDGE and BrainBridge is not None and BrainBridge.mode == "direct":
            try:
                # Use compliant BrainBridge
                resp = await BrainBridge.remember(
                    content=payload.get("content", ""),
                    tenant=tenant or "default",
                    namespace=namespace,
                    metadata=payload.get("metadata", {}),
                )
                return {
                    "status": "success",
                    "coordinate": resp.get("coordinate"),
                    "memory_id": resp.get("id"),
                }
            except Exception as e:
                LOGGER.error("Direct remember failed, falling back to HTTP: %s", e)
                pass

        if coord is not None:
            body["coord"] = coord
        if universe is not None:
            body["universe"] = universe
        return await self._request("POST", "/memory/remember", json=body)

    async def delete(
        self,
        coordinate: Any,
        *,
        tenant: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Delete memory by coordinate (alias for forget)."""
        coord_str = coordinate if isinstance(coordinate, str) else json.dumps(coordinate)
        return await self.forget(coordinate=coord_str, tenant=tenant, tenant_id=tenant_id)

    async def migrate_export(
        self,
        include_wm: bool = False,
        wm_limit: int = 128,
    ) -> Dict[str, Any]:
        """Export memories for migration."""
        return await self._request(
            "GET",
            "/admin/migrate/export",
            params={"include_wm": str(include_wm), "wm_limit": wm_limit},
        )

    async def migrate_import(
        self,
        manifest: Dict[str, Any],
        memories: List[Dict[str, Any]],
        wm: Optional[List[Dict[str, Any]]] = None,
        replace: bool = False,
    ) -> Dict[str, Any]:
        """Import memories from migration."""
        body = {
            "manifest": manifest,
            "memories": memories,
            "wm": wm or [],
            "replace": replace,
        }
        return await self._request("POST", "/admin/migrate/import", json=body)

    async def recall(
        self,
        query: str,
        *,
        top_k: int = 10,
        tenant: Optional[str] = None,
        namespace: str = "wm",
        universe: Optional[str] = None,
        tags: Optional[List[str]] = None,
        tenant_id: Optional[str] = None,
        limit: Optional[int] = None,
        memory_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Recall memories from SomaBrain.

        Args:
            query: Search query
            top_k: Maximum results to return
            tenant: Tenant ID filter
            namespace: Memory namespace
            universe: Universe scope
            tags: Tag filters

        Returns:
            Response with memory results
        """
        effective_tenant = tenant_id or tenant
        effective_limit = limit or top_k
        body: Dict[str, Any] = {
            "query": query,
            "top_k": effective_limit,
            "namespace": namespace,
        }
        if effective_tenant:
            body["tenant"] = effective_tenant
        if universe:
            body["universe"] = universe
        if tags:
            body["tags"] = tags
        if memory_type:
            body["memory_type"] = memory_type

        # DIRECT MODE CHECK (Triad Compliant)
        if (
            HAS_BRIDGE
            and BrainBridge is not None
            and getattr(BrainBridge, "mode", None) == "direct"
        ):
            try:
                # Use compliant BrainBridge
                results = await BrainBridge.recall(query=query, top_k=top_k)

                # Transform to expected response format
                memories: List[Dict[str, Any]] = []
                for m in results:
                    memories.append(
                        {
                            "coordinate": m.get("coordinate", [0.0, 0.0, 0.0]),
                            "payload": m.get("payload", {}),
                            "score": m.get("score", 0.0),
                            "created_at": datetime.now(timezone.utc).isoformat(),  # if missing
                        }
                    )
                return memories
            except Exception as e:
                LOGGER.error("Direct recall failed, falling back to HTTP: %s", e)
                pass

        result = await self._request("POST", "/memory/recall", json=body)
        if isinstance(result, list):
            return result
        return result.get("memories", [])

    async def forget(
        self,
        coordinate: Optional[str] = None,
        *,
        tenant: Optional[str] = None,
        memory_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Delete memory by coordinate.

        Args:
            coordinate: Memory coordinate to delete
            tenant: Tenant ID

        Returns:
            Deletion confirmation
        """
        effective_coordinate = coordinate if coordinate else memory_id
        effective_tenant = tenant_id or tenant
        body = {"coordinate": effective_coordinate}
        if effective_tenant:
            body["tenant"] = effective_tenant
        return await self._request("DELETE", "/memory/forget", json=body)
