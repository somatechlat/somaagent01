"""Agent memory tools — recall / save / forget / proximity via SomaBrain.

All tools go through the agent SomaBrain connector (one write/read lane).
No mocks. Fail-closed on missing tenant.

Proximity = vector + coordinate search through SomaBrain recall (Brain
algorithm: WM/LTM + scoring), not a local fake.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from services.common.memory_contract import get_memory_setting
from services.tool_executor.tools import BaseTool, ToolExecutionError

LOGGER = logging.getLogger(__name__)


def _require_tenant(args: Dict[str, Any]) -> str:
    """Fail-closed tenant. Never accepts 'default' / empty (T-5)."""
    tenant = (
        args.get("tenant_id")
        or args.get("tenant")
        or args.get("tenantId")
        or ""
    )
    if not isinstance(tenant, str) or not tenant.strip():
        raise ToolExecutionError("tenant_id is required for memory tools")
    t = tenant.strip()
    if t.lower() in {"default", "standalone", "none", "null", "public"}:
        raise ToolExecutionError(
            "tenant_id must be the real capsule tenant (not a placeholder)"
        )
    return t


def _memory_gateway():
    from admin.core.chat_orchestrator import _require_memory_gateway

    return _require_memory_gateway()


def _hit_to_dict(hit: Any) -> Dict[str, Any]:
    """Normalize MemoryHit / brain result to a tool-safe dict."""
    if isinstance(hit, dict):
        text = hit.get("text") or hit.get("content") or ""
        if isinstance(text, dict):
            text = text.get("text") or text.get("content") or str(text)
        return {
            "text": str(text)[:2000],
            "coord": hit.get("coord") or hit.get("coordinate") or hit.get("coordinate_key"),
            "score": hit.get("score"),
            "store": hit.get("store"),
            "kind": hit.get("kind") or hit.get("memory_type"),
            "created_at": hit.get("created_at"),
        }
    text = getattr(hit, "text", None) or getattr(hit, "content", "") or ""
    if isinstance(text, dict):
        text = text.get("text") or text.get("content") or str(text)
    payload = getattr(hit, "payload", None)
    if not text and isinstance(payload, dict):
        text = payload.get("text") or payload.get("content") or ""
    return {
        "text": str(text)[:2000],
        "coord": getattr(hit, "coordinate", None)
        or (payload.get("coord") if isinstance(payload, dict) else None),
        "score": getattr(hit, "score", None),
        "store": getattr(hit, "store", None),
        "kind": getattr(hit, "kind", None)
        or (payload.get("kind") if isinstance(payload, dict) else None),
        "created_at": (payload.get("created_at") if isinstance(payload, dict) else None)
        or getattr(hit, "created_at", None),
    }


class MemoryRecallTool(BaseTool):
    """Semantic recall from SomaBrain (proximity + keyword)."""

    name = "memory_recall"

    async def run(self, args: Dict[str, Any]) -> Dict[str, Any]:
        query = args.get("query") or args.get("text") or ""
        if not isinstance(query, str) or not query.strip():
            raise ToolExecutionError("query is required for memory_recall")
        tenant_id = _require_tenant(args)
        try:
            top_k = int(
                args.get("top_k")
                or args.get("limit")
                or get_memory_setting("MEM_RECALL_TOP_K", 8)
            )
        except (TypeError, ValueError):
            top_k = int(get_memory_setting("MEM_RECALL_TOP_K", 8))
        top_k = max(1, min(top_k, 50))

        gateway = _memory_gateway()
        try:
            hits = await gateway.recall(query.strip(), top_k, tenant_id)
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("memory_recall failed")
            raise ToolExecutionError(f"memory_recall failed: {exc}") from exc

        results = [_hit_to_dict(h) for h in (hits or [])]
        return {
            "query": query,
            "tenant_id": tenant_id,
            "count": len(results),
            "memories": results,
        }

    def input_schema(self) -> Dict[str, Any] | None:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Natural language query"},
                "top_k": {"type": "integer", "minimum": 1, "maximum": 50},
                "tenant_id": {"type": "string"},
            },
            "required": ["query", "tenant_id"],
            "additionalProperties": True,
        }


class MemorySaveTool(BaseTool):
    """Persist a fact to SomaBrain + SFM (learning path)."""

    name = "memory_save"

    async def run(self, args: Dict[str, Any]) -> Dict[str, Any]:
        from services.common.memory_contract import MemoryWrite

        text = args.get("text") or args.get("content") or ""
        if not isinstance(text, str) or not text.strip():
            raise ToolExecutionError("text is required for memory_save")
        tenant_id = _require_tenant(args)
        kind = str(
            args.get("kind")
            or args.get("memory_type")
            or get_memory_setting("MEM_DEFAULT_KIND", "episodic")
        )
        salience = args.get("salience")
        if salience is None:
            salience_f = float(get_memory_setting("MEM_DEFAULT_SALIENCE", 0.5))
        else:
            try:
                salience_f = float(salience)
            except (TypeError, ValueError):
                raise ToolExecutionError("salience must be a number") from None
            if not (0.0 <= salience_f <= 1.0):
                raise ToolExecutionError("salience must be between 0 and 1")

        gateway = _memory_gateway()
        try:
            acks = await gateway.remember_text(
                text.strip(),
                tenant_id=tenant_id,
                kind=kind,
                salience=salience_f,
            )
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("memory_save failed")
            raise ToolExecutionError(f"memory_save failed: {exc}") from exc

        acks = acks or []
        # Unique memory id = seam coordinate (ARCHITECTURE-INVARIANTS §1).
        memory_id = next(
            (str(getattr(a, "coord", "") or "") for a in acks if getattr(a, "coord", None)),
            "",
        )
        return {
            "saved": any(bool(getattr(a, "ok", False)) for a in acks),
            "memory_id": memory_id,
            "tenant_id": tenant_id,
            "kind": kind,
            "salience": salience_f,
            "acks": [
                {
                    "ok": bool(getattr(a, "ok", False)),
                    "store": getattr(a, "store", None),
                    "coord": getattr(a, "coord", None),
                    "error": getattr(a, "error", None),
                }
                for a in acks
            ],
        }

    def input_schema(self) -> Dict[str, Any] | None:
        return {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Fact or episode to remember"},
                "kind": {"type": "string", "enum": ["episodic", "semantic", "belief"]},
                "salience": {"type": "number", "minimum": 0, "maximum": 1},
                "tenant_id": {"type": "string"},
            },
            "required": ["text", "tenant_id"],
            "additionalProperties": True,
        }


class MemoryForgetTool(BaseTool):
    """Delete a memory by coord (erasure primitive)."""

    name = "memory_forget"

    async def run(self, args: Dict[str, Any]) -> Dict[str, Any]:
        coord = args.get("coord") or args.get("coordinate") or ""
        if not isinstance(coord, str) or not coord.strip():
            raise ToolExecutionError("coord is required for memory_forget")
        tenant_id = _require_tenant(args)

        gateway = _memory_gateway()
        try:
            ok = await gateway.forget(coord.strip(), tenant_id)
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("memory_forget failed")
            raise ToolExecutionError(f"memory_forget failed: {exc}") from exc

        return {"forgotten": bool(ok), "coord": coord, "tenant_id": tenant_id}

    def input_schema(self) -> Dict[str, Any] | None:
        return {
            "type": "object",
            "properties": {
                "coord": {"type": "string", "description": "Memory coordinate string"},
                "tenant_id": {"type": "string"},
            },
            "required": ["coord", "tenant_id"],
            "additionalProperties": True,
        }


class MemoryProximityTool(BaseTool):
    """Find memories nearest to a reference (query or coord) — Brain scoring."""

    name = "memory_proximity"

    async def run(self, args: Dict[str, Any]) -> Dict[str, Any]:
        query = args.get("query") or args.get("text") or ""
        coord = args.get("coord") or args.get("coordinate") or ""
        if not query and not coord:
            raise ToolExecutionError("query or coord is required for memory_proximity")
        tenant_id = _require_tenant(args)
        try:
            top_k = int(
                args.get("top_k")
                or args.get("limit")
                or get_memory_setting("MEM_PROXIMITY_TOP_K", 10)
            )
        except (TypeError, ValueError):
            top_k = int(get_memory_setting("MEM_PROXIMITY_TOP_K", 10))
        top_k = max(1, min(top_k, 50))

        # Coord proximity is expressed as a recall query including the coord
        # material so Brain's scorer can rank nearby rows.
        probe = (query or "").strip() or f"coord:{coord}"
        gateway = _memory_gateway()
        try:
            hits = await gateway.recall(probe, top_k, tenant_id)
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("memory_proximity failed")
            raise ToolExecutionError(f"memory_proximity failed: {exc}") from exc

        results = [_hit_to_dict(h) for h in (hits or [])]
        # Stable sort by score desc when present
        results.sort(key=lambda r: (r.get("score") is not None, r.get("score") or 0.0), reverse=True)
        return {
            "probe": probe,
            "coord": coord or None,
            "tenant_id": tenant_id,
            "count": len(results),
            "neighbors": results,
        }

    def input_schema(self) -> Dict[str, Any] | None:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "coord": {"type": "string"},
                "top_k": {"type": "integer", "minimum": 1, "maximum": 50},
                "tenant_id": {"type": "string"},
            },
            "required": ["tenant_id"],
            "additionalProperties": True,
        }


class MemoryGetTool(BaseTool):
    """Fetch a memory by coordinate via SomaBrain (T-1: Brain is the only bridge).

    Never calls somafractalmemory directly — SFM is store-only behind SomaBrain.
    """

    name = "memory_get"

    async def run(self, args: Dict[str, Any]) -> Dict[str, Any]:
        coord = args.get("coord") or args.get("coordinate") or ""
        if not isinstance(coord, str) or not coord.strip():
            raise ToolExecutionError("coord is required for memory_get")
        tenant_id = _require_tenant(args)

        # SomaBrain recall with the coordinate as probe — one lane (Brain).
        gateway = _memory_gateway()
        try:
            hits = await gateway.recall(f"coord:{coord.strip()}", 8, tenant_id)
        except Exception as exc:  # noqa: BLE001
            raise ToolExecutionError(f"memory_get failed: {exc}") from exc

        wanted = coord.strip()
        for h in hits or []:
            d = _hit_to_dict(h)
            c = d.get("coord")
            if isinstance(c, list):
                c = ",".join(str(x) for x in c)
            if c and wanted in str(c):
                return {"found": True, "memory": d}
        return {
            "found": False,
            "coord": wanted,
            "hint": "Use memory_recall / memory_proximity to search SomaBrain",
        }

    def input_schema(self) -> Dict[str, Any] | None:
        return {
            "type": "object",
            "properties": {
                "coord": {"type": "string"},
                "tenant_id": {"type": "string"},
            },
            "required": ["coord", "tenant_id"],
            "additionalProperties": True,
        }
