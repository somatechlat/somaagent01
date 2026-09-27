"""SFM adapter — talks to the real SomaFractalMemory HTTP API.

Live endpoints (somafractalmemory/api/core.py:135-138 mounts both routers at
``/memories``):
    POST   {SFM_URL}/memories            store  (routers/memory.py:40)
    GET    {SFM_URL}/memories/{coord}    fetch  (routers/memory.py:61)
    DELETE {SFM_URL}/memories/{coord}    delete (routers/memory.py:78)
    POST   {SFM_URL}/memories/search     search (routers/search.py:75)

The ``/api/v1/store|search`` dialect exists ONLY in
``infra/mocks/somafractalmemory/main.py`` and must never be used.

URL resolution is fail-closed (VIBE Rule 91): env ``SFM_URL`` (contract name,
alias ``SOMAFRACTALMEMORY_URL``) with no localhost fallback.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote

import httpx

from services.common.memory_contract import (
    MemoryAck,
    MemoryConfigurationError,
    MemoryHit,
    MemoryWrite,
    embed_text,
    get_memory_setting,
)

LOGGER = logging.getLogger(__name__)

# MemoryWrite.kind -> MemoryStoreRequest.memory_type.
# The live schema accepts all three verbatim (api/schemas.py:33), so this is a
# pass-through table, not a downgrade map. It exists to fail loudly if a new
# kind is added to the contract without updating SFM in the same change.
_SFM_MEMORY_TYPE = {"episodic": "episodic", "semantic": "semantic", "belief": "belief"}


def _resolve_base_url(explicit: str | None) -> str:
    """Resolve the SFM base URL or fail closed.

    Resolution goes through ``get_memory_setting`` so ``config/settings.py``
    stays the one authority (VIBE §4 — no second lookup path).
    """

    base = (
        explicit
        or get_memory_setting("SOMAFRACTALMEMORY_URL")
        or get_memory_setting("SFM_URL")
        or ""
    )
    base = str(base).strip()
    if not base:
        raise MemoryConfigurationError(
            "SFM store URL is not configured. Set SOMAFRACTALMEMORY_URL in "
            "config/settings.py (env alias SFM_URL) to the SomaFractalMemory "
            "base URL. No localhost fallback is permitted (VIBE Rule 91)."
        )
    return base.rstrip("/")


class SFMAdapter:
    """HTTP adapter for SomaFractalMemory's real ``/memories*`` API."""

    def __init__(
        self,
        base_url: str | None = None,
        *,
        token: str | None = None,
        timeout: float | None = None,
        namespace: str | None = None,
    ) -> None:
        """Initialize the adapter. Raises if the store URL is unset."""

        self._base_url = _resolve_base_url(base_url)
        self._token = (
            token
            if token is not None
            else str(get_memory_setting("SOMA_API_TOKEN", "") or "")
        )
        self._timeout = float(
            timeout if timeout is not None else get_memory_setting("MEM_HTTP_TIMEOUT", 5.0)
        )
        # Informational only: SFM's live store() uses the server-side namespace
        # (api/core.py:67), the client cannot select it per request.
        self._namespace = namespace or str(
            get_memory_setting("SFM_NAMESPACE", "api_ns") or "api_ns"
        )
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout,
            headers=self._headers(),
        )

    def _headers(self, tenant_id: str | None = None) -> dict[str, str]:
        """Build request headers; bearer token plus tenant hint."""

        headers: dict[str, str] = {"Accept": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        if tenant_id:
            # Scoping hint for get_tenant_from_request (api/utils.py:36);
            # standalone auth currently pins the row tenant to "standalone".
            headers["X-Soma-Tenant"] = tenant_id
        return headers

    async def remember(self, w: MemoryWrite) -> MemoryAck:
        """Store one memory via POST /memories. Returns a failed ack, never raises."""

        memory_type = _SFM_MEMORY_TYPE.get(w.kind, "episodic")
        # ``payload`` is SFM's free-form JSON dict (MemoryStoreRequest.payload),
        # not a string. Text and the metadata that has no first-class column
        # live inside it.
        payload: dict[str, Any] = {
            "text": w.text,
            "kind": w.kind,
            "source": w.source,
            "salience": w.salience,
            # Search results do not carry created_at (services.py search), so
            # it rides in the payload for MemoryHit reconstruction.
            "created_at": datetime.now(UTC).isoformat(),
        }
        if w.session_id is not None:
            payload["session_id"] = w.session_id

        # MemoryStoreRequest fields, verbatim (somafractalmemory/api/schemas.py:22).
        # ``embedding`` is a FIRST-CLASS field: sent here it is written verbatim
        # to Milvus (embedding_source="precomputed"). Nesting it in ``payload``
        # silently loses it — SFM then falls back to its hash embedder and the
        # record is ranked x0.25, which is why recall used to return noise.
        body = {
            "coord": w.coord,
            "payload": payload,
            "memory_type": memory_type,
            "embedding": w.embedding,
            "tenant_id": w.tenant_id,
        }
        try:
            response = await self._client.post(
                "/memories", json=body, headers=self._headers(w.tenant_id)
            )
            response.raise_for_status()
            return MemoryAck(coord=w.coord, store="somafractalmemory", ok=True)
        except Exception as exc:
            LOGGER.warning("SFM remember failed: %s", exc)
            return MemoryAck(
                coord=w.coord, store="somafractalmemory", ok=False, error=str(exc)
            )

    async def recall(self, query: str, k: int, tenant_id: str) -> list[MemoryHit]:
        """Search via POST /memories/search. Store outage surfaces as an error log + empty list.

        The query embedding is sent precomputed, from the SAME embedder the
        write path used (ARCHITECTURE-INVARIANTS §2). Omitting it makes SFM
        embed the query with its own ``HashEmbedder`` — a different algorithm
        — so the query vector and the stored vector are in incompatible spaces
        and every hit scores 0.0. That failure is silent: the store returns
        200 and an empty or noise list.
        """

        body = {
            "query": query,
            "top_k": max(1, int(k)),
            "offset": 0,
            "tenant_id": tenant_id,
            "embedding": embed_text(query),
        }
        try:
            response = await self._client.post(
                "/memories/search", json=body, headers=self._headers(tenant_id)
            )
            response.raise_for_status()
            data = response.json() or {}
        except Exception as exc:
            LOGGER.warning("SFM recall failed: %s", exc)
            return []

        hits: list[MemoryHit] = []
        for item in data.get("memories") or []:
            hit = self._to_hit(item)
            if hit is not None:
                hits.append(hit)
        return hits

    async def forget(self, coord: str, tenant_id: str) -> bool:
        """Delete via DELETE /memories/{coord}. Returns False when unsupported."""

        try:
            response = await self._client.delete(
                f"/memories/{quote(coord, safe=',')}",
                headers=self._headers(tenant_id),
            )
            if response.status_code == 404:
                return False
            response.raise_for_status()
            data = response.json() or {}
            return bool(data.get("deleted"))
        except Exception as exc:
            LOGGER.warning("SFM forget failed: %s", exc)
            return False

    @staticmethod
    def _to_hit(item: dict[str, Any]) -> MemoryHit | None:
        """Map one SFM search row to MemoryHit."""

        if not isinstance(item, dict):
            return None
        payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
        text = payload.get("text") or payload.get("content") or payload.get("summary")
        if not isinstance(text, str) or not text:
            return None
        coord = payload.get("coord")
        if not isinstance(coord, str) or not coord:
            raw = item.get("coordinate")
            if isinstance(raw, (list, tuple)) and raw:
                coord = ",".join(str(c) for c in raw)
            else:
                return None
        score = item.get("score")
        created = payload.get("created_at")
        return MemoryHit(
            text=text,
            coord=coord,
            score=float(score) if isinstance(score, (int, float)) else 0.0,
            store="somafractalmemory",
            created_at=str(created) if created else "",
        )

    async def close(self) -> None:
        """Close the HTTP client."""

        await self._client.aclose()


__all__ = ["SFMAdapter"]
