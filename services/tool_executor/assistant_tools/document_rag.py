"""Document RAG via MemoryGateway only — T-1 (TOOLS-001 §5.9).

A0 clones FAISS + local parsers. Soma does not: index/query go through
``MemoryGateway`` → SomaBrain. No SFM client, no second embedder, no local
vector store in the agent process.

Journey (Operator PDF example):
  upload → filesv2 bytes → document_ingest extract → index chunks
  (remember_text) → later document_query (recall) → answer.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from services.common.memory_contract import MemoryRecallUnavailable
from services.tool_executor.assistant_tools.base import (
    SomaAssistantTool,
    tool_error,
)

LOGGER = logging.getLogger(__name__)

# A0 document_query defaults (chunk_size 1000 / overlap 100) — config-shaped
# constants for chunking only; not topology or secrets.
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 100
DEFAULT_QUERY_K = 8
MAX_QUERY_K = 50
MAX_INDEX_CHUNKS = 1200


def _memory_gateway():
    from admin.core.chat_orchestrator import _require_memory_gateway

    return _require_memory_gateway()


def require_tenant(args: Dict[str, Any]) -> str:
    """Fail-closed tenant — same rules as memory tools."""
    tenant = args.get("tenant_id") or args.get("tenant") or ""
    if not isinstance(tenant, str) or not tenant.strip():
        raise tool_error("tenant_id is required for document memory tools")
    t = tenant.strip()
    if t.lower() in {"default", "standalone", "none", "null", "public"}:
        raise tool_error(
            "tenant_id must be the real capsule tenant (not a placeholder)"
        )
    return t


def split_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    max_chunks: int = MAX_INDEX_CHUNKS,
) -> List[str]:
    """Split text into overlapping chunks (A0-compatible sizing)."""
    body = (text or "").strip()
    if not body:
        return []
    size = max(200, int(chunk_size))
    overlap = max(0, min(int(chunk_overlap), size - 1))
    if len(body) <= size:
        chunks = [body]
    else:
        step = size - overlap
        chunks = []
        start = 0
        while start < len(body) and len(chunks) < max_chunks:
            end = min(len(body), start + size)
            chunks.append(body[start:end].strip())
            if end >= len(body):
                break
            start += step
    return [c for c in chunks if c]


def chunk_label(attachment_id: str, index: int) -> str:
    return f"[doc:{attachment_id} #{index}] "


def is_chunk_for_document(text: str, attachment_id: str) -> bool:
    prefix = f"[doc:{attachment_id} "
    return bool(text) and str(text).startswith(prefix)


async def index_document_text(
    text: str,
    *,
    tenant_id: str,
    attachment_id: str,
    session_id: Optional[str] = None,
    source: Optional[str] = None,
    gateway: Any = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> Dict[str, Any]:
    """Index extracted text as semantic memories via MemoryGateway only.

    Each chunk: ``remember_text`` → T-6 WAL → POST /memory/remember.
    """
    doc_source = source or f"document:{attachment_id}"
    chunks = split_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    if not chunks:
        return {
            "attachment_id": attachment_id,
            "indexed": 0,
            "failed": 0,
            "coords": [],
            "error": "no text to index",
        }

    gw = gateway if gateway is not None else _memory_gateway()
    coords: List[str] = []
    failed = 0
    errors: List[str] = []
    for i, chunk in enumerate(chunks):
        labeled = f"{chunk_label(attachment_id, i)}{chunk}"
        try:
            acks = await gw.remember_text(
                labeled,
                tenant_id=tenant_id,
                kind="semantic",
                session_id=session_id,
                source=doc_source,
                salience=0.6,
            )
            ack = acks[0] if acks else None
            ok = bool(getattr(ack, "ok", False))
            coord = getattr(ack, "coord", None) if ack else None
            if ok and coord:
                coords.append(str(coord))
            else:
                failed += 1
                err = getattr(ack, "error", None) if ack else "no ack"
                if err and len(errors) < 3:
                    errors.append(str(err))
        except Exception as exc:  # noqa: BLE001 — surface per-chunk, fail closed overall
            failed += 1
            if len(errors) < 3:
                errors.append(str(exc))
            LOGGER.warning(
                "document index chunk failed attachment=%s chunk=%s: %s",
                attachment_id,
                i,
                exc,
            )

    return {
        "attachment_id": attachment_id,
        "chunks_total": len(chunks),
        "indexed": len(coords),
        "failed": failed,
        "coords": coords[:50],
        "source": doc_source,
        "error": (
            None
            if failed == 0 and coords
            else (
                "all chunks failed to index via SomaBrain"
                if not coords
                else (
                    f"partial index: {len(coords)}/{len(chunks)} ok"
                    if failed
                    else None
                )
            )
        ),
        "detail": errors or None,
    }


async def query_document(
    query: str,
    *,
    tenant_id: str,
    attachment_id: Optional[str] = None,
    k: int = DEFAULT_QUERY_K,
    gateway: Any = None,
) -> Dict[str, Any]:
    """Query indexed document chunks via MemoryGateway.recall only."""
    probe = (query or "").strip()
    if not probe:
        return {
            "query": "",
            "count": 0,
            "digest": [],
            "error": "query is required",
        }

    top_k = max(1, min(int(k or DEFAULT_QUERY_K), MAX_QUERY_K))
    # Pull extra when filtering by document so post-filter still has hits.
    fetch_k = min(MAX_QUERY_K, top_k * 4) if attachment_id else top_k

    gw = gateway if gateway is not None else _memory_gateway()
    try:
        hits = await gw.recall(probe, fetch_k, tenant_id)
    except MemoryRecallUnavailable as exc:
        raise tool_error(f"document_query: memory unavailable — {exc}") from exc
    except Exception as exc:  # noqa: BLE001
        raise tool_error(f"document_query failed: {exc}") from exc

    digested: List[Dict[str, Any]] = []
    for h in hits or []:
        text = str(getattr(h, "text", "") or "")
        if attachment_id and not is_chunk_for_document(text, attachment_id):
            continue
        # Strip the [doc:… #n] label for the model-facing summary.
        body = text
        if body.startswith("[doc:"):
            close = body.find("] ")
            if close != -1:
                body = body[close + 2 :]
        digested.append(
            {
                "summary": body if len(body) <= 400 else body[:399] + "…",
                "coord": getattr(h, "coord", None),
                "score": getattr(h, "score", None),
                "kind": getattr(h, "kind", None),
                "store": getattr(h, "store", None),
            }
        )
        if len(digested) >= top_k:
            break

    return {
        "query": probe,
        "attachment_id": attachment_id,
        "count": len(digested),
        "digest": digested,
        "error": (
            None
            if digested
            else (
                "no indexed chunks for this document — run document_ingest "
                "or document_index first"
                if attachment_id
                else "no matching memories for this query"
            )
        ),
    }


class DocumentIndexTool(SomaAssistantTool):
    """Index extracted document text into SomaBrain via MemoryGateway."""

    name = "document_index"
    description = (
        "Index document text into SomaBrain long-term memory as semantic "
        "chunks (source=document:<attachment_id>). Use after extraction or "
        "with attachment_id to index an uploaded file. Requires approval. "
        "Never talks to SFM directly."
    )
    tier = 2
    needs_workroot = False
    needs_egress = False

    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "attachment_id": {
                    "type": "string",
                    "description": "filesv2 / chat attachment id (document identity).",
                },
                "text": {
                    "type": "string",
                    "description": "Optional pre-extracted text. If omitted, attachment_id must be fetchable by document_ingest.",
                },
                "tenant_id": {"type": "string"},
                "session_id": {"type": ["string", "null"]},
            },
            "required": ["attachment_id", "tenant_id"],
            "additionalProperties": False,
        }

    async def run(
        self,
        args: Dict[str, Any],
        *,
        guard: Optional[Any] = None,
        ctx: Optional[Any] = None,
    ) -> Dict[str, Any]:
        data = args or {}
        attachment_id = str(data.get("attachment_id") or "").strip()
        if not attachment_id:
            raise tool_error("attachment_id is required")
        tenant_id = require_tenant(data)
        session_id = data.get("session_id")
        text = data.get("text")
        if not isinstance(text, str) or not text.strip():
            # Extract via the live ingest tool (same path as document_ingest).
            from services.tool_executor.tools import IngestDocumentTool

            extracted = await IngestDocumentTool().run(
                {
                    "attachment_id": attachment_id,
                    "tenant_id": tenant_id,
                    "session_id": session_id,
                }
            )
            text = str(extracted.get("text") or "")
        if not text.strip():
            raise tool_error("no extractable text to index")
        return await index_document_text(
            text,
            tenant_id=tenant_id,
            attachment_id=attachment_id,
            session_id=str(session_id) if session_id else None,
        )


class DocumentQueryTool(SomaAssistantTool):
    """Ask questions over document chunks already indexed in SomaBrain."""

    name = "document_query"
    description = (
        "Search and answer from documents previously indexed into SomaBrain "
        "(via document_ingest / document_index). Pass attachment_id to scope "
        "to one document. Uses memory recall only — not a direct store client."
    )
    tier = 2
    needs_workroot = False
    needs_egress = False

    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Question or search text about the document content.",
                },
                "attachment_id": {
                    "type": ["string", "null"],
                    "description": "Optional document id to scope results.",
                },
                "k": {"type": "integer", "description": "Max hits (default 8)."},
                "tenant_id": {"type": "string"},
            },
            "required": ["query", "tenant_id"],
            "additionalProperties": False,
        }

    async def run(
        self,
        args: Dict[str, Any],
        *,
        guard: Optional[Any] = None,
        ctx: Optional[Any] = None,
    ) -> Dict[str, Any]:
        data = args or {}
        tenant_id = require_tenant(data)
        attachment_id = data.get("attachment_id")
        attachment_id = str(attachment_id).strip() if attachment_id else None
        try:
            k = int(data.get("k") or DEFAULT_QUERY_K)
        except (TypeError, ValueError):
            k = DEFAULT_QUERY_K
        return await query_document(
            str(data.get("query") or ""),
            tenant_id=tenant_id,
            attachment_id=attachment_id or None,
            k=k,
        )


DOCUMENT_ASSISTANT_TOOLS: List[SomaAssistantTool] = [
    DocumentIndexTool(),
    DocumentQueryTool(),
]
