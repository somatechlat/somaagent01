"""Agent memory tools — recall / save / forget / proximity via SomaBrain.

All tools go through the agent SomaBrain connector (one write/read lane).
No mocks. Fail-closed on missing tenant.

Proximity = vector + coordinate search through SomaBrain recall (Brain
algorithm: WM/LTM + scoring), not a local fake.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List

from services.common.memory_contract import get_memory_setting
from services.tool_executor.tools import BaseTool, ToolExecutionError

LOGGER = logging.getLogger(__name__)


#: Characters per hit summary. Eight summaries stay well inside the tool-message
#: cap, so the model never sees truncated JSON and re-queries.
_SUMMARY_CHARS = 240


def _fact_boost(text: str) -> float:
    """Prefer durable facts over raw dialog transcripts and questions.

    Chat turns are also stored (chat_history). When the user asks for a
    name/codeword the fact row must outrank "User: ...\\nAssistant: ...".
    Questions ("What is my name?") are what the user asked, not what they
    said — they must never outrank the fact that answers them.
    """
    t = (text or "").strip()
    if not t:
        return -1.0
    # Dialog / Q&A transcripts — chat turns, not facts.
    if t.startswith("User:") or "\nAssistant:" in t or t.startswith("Assistant:"):
        return -0.50
    # Questions are not facts.
    if t.endswith("?") or t.lower().startswith(
        ("what ", "how ", "why ", "is ", "can ", "do ", "does ",
         "where ", "when ", "who ", "which ", "remind ", "whast ")
    ):
        return -0.40
    # Short factual statements.
    if len(t) <= 180 and "User:" not in t:
        return 0.30
    return 0.0


def _keyword_boost(text: str, query: str) -> float:
    """Boost hits that share distinctive query terms (exact word overlap).

    The hash embedder produces low-discriminative cosine scores, so a fact
    that contains the user's own words can rank below unrelated chat echoes.
    A per-term bonus makes lexical evidence count alongside the vector score.
    """
    if not query or not text:
        return 0.0
    text_lower = text.lower()
    terms = {t for t in re.findall(r"[a-z0-9]{3,}", query.lower()) if t}
    if not terms:
        return 0.0
    matched = sum(1 for t in terms if t in text_lower)
    return matched * 0.08


def _is_fact(text: str) -> bool:
    """True when the row is a durable fact (not a question or chat transcript)."""
    return _fact_boost(text) > 0


def _digest(hits: List[Dict[str, Any]], query: str = "") -> List[Dict[str, Any]]:
    """Shape hits into a ranked digest the model can answer from.

    Ranking is tiered: facts always outrank questions and chat transcripts,
    and within each tier the newest created_at wins.  This is what makes
    "My name is Daniel" beat "What is my name?" and stale "My name is Marco"
    even when the raw cosine score favours the wrong row.

    Raw payloads invite re-query: they overflow the tool-message cap, the
    model sees incomplete JSON, and asks again. A summary per hit keeps the
    whole result readable in one round.
    """
    scored: List[Dict[str, Any]] = []
    for h in hits:
        text = str(h.get("text") or "").strip()
        base = h.get("score")
        try:
            base_f = float(base) if base is not None else 0.0
        except (TypeError, ValueError):
            base_f = 0.0
        tier = 1 if _is_fact(text) else 0
        created = str(h.get("created_at") or "")
        scored.append({
            **h,
            "_tier": tier,
            "_created": created,
            "_rank_score": base_f + _fact_boost(text) + _keyword_boost(text, query),
        })
    # Tier (facts first) → newest → score.  Reverse sorts each key descending.
    scored.sort(
        key=lambda x: (x["_tier"], x["_created"], x.get("_rank_score") or 0.0),
        reverse=True,
    )

    out: List[Dict[str, Any]] = []
    for i, h in enumerate(scored, start=1):
        text = str(h.get("text") or "").strip()
        summary = text if len(text) <= _SUMMARY_CHARS else text[: _SUMMARY_CHARS - 1] + "…"
        out.append(
            {
                "rank": i,
                "summary": summary,
                "coord": h.get("coord") or h.get("coordinate"),
                "score": h.get("score"),
                "kind": h.get("kind"),
                "store": h.get("store"),
                "created_at": h.get("created_at"),
            }
        )
    return out


def _require_tenant(args: Dict[str, Any]) -> str:
    """Fail-closed tenant. Never accepts 'default' / empty (T-5)."""
    tenant = args.get("tenant_id") or args.get("tenant") or args.get("tenantId") or ""
    if not isinstance(tenant, str) or not tenant.strip():
        raise ToolExecutionError("tenant_id is required for memory tools")
    t = tenant.strip()
    if t.lower() in {"default", "standalone", "none", "null", "public"}:
        raise ToolExecutionError("tenant_id must be the real capsule tenant (not a placeholder)")
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
        # MemoryHit.coord is the seam coordinate (memory_contract.MemoryHit).
        # Do not look for `.coordinate` — that attribute does not exist and
        # made every tool hit coord:null (agent could never show a memory id).
        "coord": getattr(hit, "coord", None)
        or getattr(hit, "coordinate", None)
        or (payload.get("coord") if isinstance(payload, dict) else None)
        or (payload.get("coordinate") if isinstance(payload, dict) else None),
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
    description = (
        "Search long-term memory (SomaBrain). Use a specific question or name/codeword, "
        "not the word 'memory'. Each hit has a coord (memory_id). When the user asks "
        "where a memory is stored or for its id, print that coord. "
        "Prefer tool results over guessing."
    )

    async def run(self, args: Dict[str, Any]) -> Dict[str, Any]:
        query = args.get("query") or args.get("text") or ""
        tenant_id = _require_tenant(args)
        try:
            top_k = int(
                args.get("top_k") or args.get("limit") or get_memory_setting("MEM_RECALL_TOP_K")
            )
        except (TypeError, ValueError):
            top_k = int(get_memory_setting("MEM_RECALL_TOP_K"))
        top_k = max(1, min(top_k, 50))
        # An empty query is a refusal, not a wildcard dump. Listing a tenant's
        # whole memory overflows the tool message, the model sees truncated
        # JSON, and asks again - that is the runaway.
        probe = query.strip()
        if not probe:
            return {
                "query": "",
                "tenant_id": tenant_id,
                "count": 0,
                "enough": False,
                "digest": [],
                "error": "A specific question is required. Answer from the memory "
                "already in the prompt, or ask the user for more detail.",
            }

        gateway = _memory_gateway()
        # Over-fetch + multi-query: the hash embedder's cosine scores are
        # low-discriminative, so "My name is Daniel" can sit outside the
        # top_k for "What is my name?".  We widen the fetch, add a
        # keyword-focused second query that matches fact phrasing, merge by
        # coord, then re-rank with tier + keyword + fact boosts.
        # SomaBrain's recall endpoint 422s above top_k=40 — hard cap there.
        fetch_k = min(max(top_k * 3, 20), 40)
        try:
            hits = await gateway.recall(probe, fetch_k, tenant_id)
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("memory_recall failed")
            raise ToolExecutionError(f"memory_recall failed: {exc}") from exc

        results = [_hit_to_dict(h) for h in (hits or [])]

        # Second pass: keyword-focused query.  "What is my name?" rarely
        # surfaces "My name is Daniel" in the vector store, but "name" or
        # "my name" does.  Extract the distinctive terms and try once more.
        terms = [t for t in re.findall(r"[a-z0-9]{3,}", probe.lower()) if t]
        if len(terms) >= 1:
            kw_query = " ".join(terms[:4])
            if kw_query.lower() != probe.lower():
                try:
                    kw_hits = await gateway.recall(kw_query, fetch_k, tenant_id)
                    seen = {r.get("coord") for r in results}
                    for h in kw_hits or []:
                        d = _hit_to_dict(h)
                        if d.get("coord") not in seen:
                            results.append(d)
                            seen.add(d.get("coord"))
                except Exception:  # noqa: BLE001
                    LOGGER.debug("keyword recall pass failed (non-fatal)", exc_info=True)

        digest = _digest(results, query=probe)[:top_k]
        return {
            "query": probe,
            "tenant_id": tenant_id,
            "count": len(digest),
            # True when these hits are enough to answer. The model should
            # answer from them rather than call again.
            "enough": bool(digest),
            "digest": digest,
            "instruction": "Answer from digest summaries when they contain the fact. "
            "When facts conflict, prefer the one with the latest created_at. "
            "Print coord as memory_id if the user asks where a memory is stored. "
            "Never invent a fact that is not in the digest.",
        }

    def input_schema(self) -> Dict[str, Any] | None:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Natural language query"},
                "top_k": {"type": "integer", "minimum": 1, "maximum": 50},
                "tenant_id": {"type": "string"},
            },
            "required": ["tenant_id"],
            "additionalProperties": True,
        }


class MemorySaveTool(BaseTool):
    """Persist a fact to SomaBrain + SFM (learning path)."""

    name = "memory_save"

    async def run(self, args: Dict[str, Any]) -> Dict[str, Any]:

        text = args.get("text") or args.get("content") or ""
        if not isinstance(text, str) or not text.strip():
            raise ToolExecutionError("text is required for memory_save")
        tenant_id = _require_tenant(args)
        kind = str(
            args.get("kind")
            or args.get("memory_type")
            or get_memory_setting("MEM_DEFAULT_KIND")
        )
        salience = args.get("salience")
        if salience is None:
            salience_f = float(get_memory_setting("MEM_DEFAULT_SALIENCE"))
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
            "note": "memory_id is the seam coordinate. Show it to the user when they ask where a memory is stored.",
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
    """Delete memories by coord, or all matches for an explicit erase query.

    Single ``coord`` is the precision primitive (approval_required by default).
    ``query`` is the product path for "delete my name from long-term memory":
    it recalls matching rows (fact **and** chat echoes like "Your name is Zoe")
    and forgets every coord whose text contains a distinctive match. One coord
    is never enough when the same fact was stored as a fact + transcript.
    """

    name = "memory_forget"

    async def run(self, args: Dict[str, Any]) -> Dict[str, Any]:
        coord = args.get("coord") or args.get("coordinate") or ""
        query = args.get("query") or args.get("text") or args.get("match") or ""
        tenant_id = _require_tenant(args)

        if isinstance(coord, str) and coord.strip():
            gateway = _memory_gateway()
            try:
                ok = await gateway.forget(coord.strip(), tenant_id)
            except Exception as exc:  # noqa: BLE001
                LOGGER.exception("memory_forget failed")
                raise ToolExecutionError(f"memory_forget failed: {exc}") from exc

            return {
                "forgotten": bool(ok),
                "mode": "coord",
                "coord": coord,
                "deleted": 1 if ok else 0,
                "tenant_id": tenant_id,
                "instruction": (
                    "Only tell the user a fact was deleted if THEY explicitly asked "
                    "to erase this memory. Do not claim names or preferences were "
                    "removed after ordinary chat. If forgotten is false, the memory "
                    "was not deleted — do not pretend otherwise. If the same fact "
                    "also lives in chat-echo rows, use query= mode to erase all copies."
                ),
            }

        probe = str(query).strip()
        if not probe:
            raise ToolExecutionError(
                "memory_forget requires coord or query "
                "(query matches fact rows AND chat echoes of that fact)"
            )

        # Distinctive tokens the model must have pulled from the user request
        # or a prior recall — not the generic word "name" alone.
        tokens = [t for t in re.split(r"[^a-z0-9]+", probe.lower()) if len(t) >= 3]
        stop = {
            "the",
            "and",
            "for",
            "you",
            "your",
            "memory",
            "memories",
            "from",
            "long",
            "term",
            "please",
            "delete",
            "remove",
            "forget",
            "erase",
            "name",
            "about",
            "that",
            "this",
            "with",
            "all",
            "any",
        }
        distinctive = [t for t in tokens if t not in stop]
        if not distinctive:
            # Fall back to full probe if it is already distinctive (e.g. a name).
            distinctive = [probe.lower()] if len(probe) >= 3 else []

        gateway = _memory_gateway()
        try:
            hits = await gateway.recall(probe, 50, tenant_id)
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("memory_forget query recall failed")
            raise ToolExecutionError(f"memory_forget query failed: {exc}") from exc

        deleted_coords: List[str] = []
        failed: List[str] = []
        matched_preview: List[str] = []
        for h in hits or []:
            text = str(getattr(h, "text", "") or "")
            low = text.lower()
            if distinctive and not any(t in low for t in distinctive):
                continue
            # Require a real content hit, not a bare "?" or empty stub.
            if len(text.strip()) < 4:
                continue
            c = str(getattr(h, "coord", "") or "").strip()
            if not c or c in deleted_coords:
                continue
            try:
                ok = await gateway.forget(c, tenant_id)
            except Exception as exc:  # noqa: BLE001
                failed.append(f"{c}: {exc}")
                continue
            if ok:
                deleted_coords.append(c)
                if len(matched_preview) < 5:
                    matched_preview.append(text[:160].replace("\n", " "))
            else:
                failed.append(f"{c}: not deleted")

        return {
            "forgotten": bool(deleted_coords),
            "mode": "query",
            "query": probe,
            "deleted": len(deleted_coords),
            "failed": len(failed),
            "coords": deleted_coords[:25],
            "matched": matched_preview,
            "tenant_id": tenant_id,
            "instruction": (
                f"Erased {len(deleted_coords)} matching memor(ies) for this explicit "
                "user request. Tell the user it is deleted only if deleted>=1. "
                "If deleted is 0, the fact was not found or not deleted — say so. "
                "Do not invent a second erase without another user request."
            ),
        }

    def input_schema(self) -> Dict[str, Any] | None:
        return {
            "type": "object",
            "properties": {
                "coord": {
                    "type": "string",
                    "description": "Exact memory coordinate to delete (one row).",
                },
                "query": {
                    "type": "string",
                    "description": (
                        "When the user explicitly asks to erase a fact (e.g. "
                        "'delete my name'), pass a distinctive query such as the "
                        "stored value 'Zoe' or 'name is Zoe'. Deletes every matching "
                        "fact and chat-echo row."
                    ),
                },
                "tenant_id": {"type": "string"},
            },
            "required": ["tenant_id"],
            "additionalProperties": True,
        }


class MemoryProximityTool(BaseTool):
    """Find memories nearest to a reference (query or coord) — Brain scoring."""

    name = "memory_proximity"

    async def run(self, args: Dict[str, Any]) -> Dict[str, Any]:
        query = args.get("query") or args.get("text") or ""
        coord = args.get("coord") or args.get("coordinate") or ""
        tenant_id = _require_tenant(args)
        try:
            top_k = int(
                args.get("top_k")
                or args.get("limit")
                or get_memory_setting("MEM_PROXIMITY_TOP_K")
            )
        except (TypeError, ValueError):
            top_k = int(get_memory_setting("MEM_PROXIMITY_TOP_K"))
        top_k = max(1, min(top_k, 50))

        # Coord proximity is expressed as a recall query including the coord
        # material so Brain's scorer can rank nearby rows.
        # Empty probe = list this tenant's memories (SomaBrain ranked); not an error.
        if query.strip():
            probe = query.strip()
        elif coord.strip():
            probe = f"coord:{coord.strip()}"
        else:
            return {
                "probe": "",
                "coord": coord,
                "tenant_id": tenant_id,
                "count": 0,
                "neighbors": [],
                "error": "A probe string or a coord is required. A wildcard dump "
                "is not offered: it overflows the tool message and invites a "
                "second call.",
            }

        gateway = _memory_gateway()
        try:
            hits = await gateway.recall(probe, top_k, tenant_id)
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("memory_proximity failed")
            raise ToolExecutionError(f"memory_proximity failed: {exc}") from exc

        results = [_hit_to_dict(h) for h in (hits or [])]
        # Stable sort by score desc when present
        results.sort(
            key=lambda r: (r.get("score") is not None, r.get("score") or 0.0), reverse=True
        )
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

        # Exact coordinate fetch through SomaBrain (T-1). Outage raises;
        # absent is found:false — never a semantic-search guess.
        gateway = _memory_gateway()
        try:
            mem = await gateway.get(coord.strip(), tenant_id)
        except Exception as exc:  # noqa: BLE001
            raise ToolExecutionError(f"memory_get failed: {exc}") from exc

        if mem is not None:
            return {"found": True, "memory": mem}
        return {
            "found": False,
            "coord": coord.strip(),
            "hint": "Not found. Answer from what you already have, or tell the user you do not know.",
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
