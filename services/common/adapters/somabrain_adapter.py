"""SomaBrain adapter — talks to the real SomaBrain memory HTTP API.

Live endpoints (Django Ninja routers mounted at ``/memory/`` in
somabrain/api/v1.py:96,104; Django serves them both with and without the
``/api`` prefix — somabrain/config/urls.py:479,482):
    POST {SOMABRAIN_URL}/memory/remember   (endpoints/memory_remember.py:102)
    POST {SOMABRAIN_URL}/memory/recall     (endpoints/memory.py:73)
    POST {SOMABRAIN_URL}/memory/remember/batch

The ``/api/remember`` and ``/api/recall`` dialect (agent BrainBridge,
aaas/brain.py:162,218) has NO route in somabrain and is not used here.
There is no memory delete route on the brain, so ``forget`` reports False.

URL resolution is fail-closed (VIBE Rule 91): env ``SOMABRAIN_URL``, no
localhost fallback.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import httpx

from services.common.memory_contract import (
    MemoryAck,
    MemoryConfigurationError,
    MemoryHit,
    MemoryWrite,
    get_memory_setting,
)

LOGGER = logging.getLogger(__name__)

# Logical namespace sent with writes; recall must use the same one.
DEFAULT_NAMESPACE = "default"


def _resolve_base_url(explicit: str | None) -> str:
    """Resolve the SomaBrain base URL or fail closed.

    Resolution goes through ``get_memory_setting`` so ``config/settings.py``
    stays the one authority (VIBE §4 — no second lookup path).
    """

    base = str(explicit or get_memory_setting("SOMABRAIN_URL") or "").strip()
    if not base:
        raise MemoryConfigurationError(
            "SomaBrain store URL is not configured. Set SOMABRAIN_URL in "
            "config/settings.py to the SomaBrain base URL. No localhost "
            "fallback is permitted (VIBE Rule 91)."
        )
    return base.rstrip("/")


class SomaBrainAdapter:
    """HTTP adapter for SomaBrain's real ``/memory/remember|recall`` API."""

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
            else str(get_memory_setting("SOMABRAIN_MEMORY_HTTP_TOKEN", "") or "")
        )
        self._timeout = float(
            timeout if timeout is not None else get_memory_setting("MEM_HTTP_TIMEOUT", 5.0)
        )
        self._namespace = namespace or str(
            get_memory_setting("SOMABRAIN_NAMESPACE", DEFAULT_NAMESPACE) or DEFAULT_NAMESPACE
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
            headers["X-Tenant-ID"] = tenant_id
        return headers

    async def remember(self, w: MemoryWrite, *, key_material: str | None = None) -> MemoryAck:
        """Store one memory via POST /memory/remember. Returns a failed ack, never raises.

        ``key_material`` (from ``memory_contract.coord_key_material``) makes the
        brain derive the seam coordinate for its own placement — its write path
        computes ``_stable_coord(f"{universe}::{key}")``
        (somabrain/memory/client/write.py:21). Without it the coord string is
        used as the key and the brain places the record at its own derived
        point; the seam coord still travels in the payload for cross-store
        identity.
        """

        key = key_material or w.coord
        value: dict[str, Any] = {
            "text": w.text,
            "kind": w.kind,
            "coord": w.coord,
            "source": w.source,
            "salience": w.salience,
            "created_at": datetime.now(UTC).isoformat(),
        }
        if w.session_id is not None:
            value["session_id"] = w.session_id
        if w.embedding is not None:
            # Precomputed vector (PLAN §1 rule 2); the brain composes its own
            # payload today (api/memory/helpers.py _compose_memory_payload) and
            # has no first-class embedding field yet.
            value["embedding"] = w.embedding

        body: dict[str, Any] = {
            "tenant": w.tenant_id,
            "namespace": self._namespace,
            "key": key,
            "value": value,
            "meta": {"coord": w.coord, "kind": w.kind, "source": w.source},
            "importance": w.salience,
            "tags": [w.kind, w.source],
        }
        try:
            response = await self._client.post(
                "/memory/remember", json=body, headers=self._headers(w.tenant_id)
            )
            response.raise_for_status()
            return MemoryAck(coord=w.coord, store="somabrain", ok=True)
        except Exception as exc:
            LOGGER.warning("SomaBrain remember failed: %s", exc)
            return MemoryAck(coord=w.coord, store="somabrain", ok=False, error=str(exc))

    async def recall(self, query: str, k: int, tenant_id: str) -> list[MemoryHit]:
        """Search via POST /memory/recall. Store outage surfaces as an error log + empty list."""

        body = {
            "query": query,
            "top_k": max(1, int(k)),
            "layer": "both",
            "tenant": tenant_id,
            "namespace": self._namespace,
        }
        try:
            response = await self._client.post(
                "/memory/recall", json=body, headers=self._headers(tenant_id)
            )
            response.raise_for_status()
            data = response.json() or {}
        except Exception as exc:
            LOGGER.warning("SomaBrain recall failed: %s", exc)
            return []

        hits: list[MemoryHit] = []
        for item in data.get("results") or []:
            hit = self._to_hit(item)
            if hit is not None:
                hits.append(hit)
        return hits

    async def forget(self, coord: str, tenant_id: str) -> bool:
        """Forget a memory. The brain exposes no memory delete route today."""

        LOGGER.info(
            "SomaBrain forget skipped: no delete route on the brain API (coord=%s)",
            coord,
        )
        return False

    @staticmethod
    def _to_hit(item: Any) -> MemoryHit | None:
        """Map one brain recall result to MemoryHit."""

        if not isinstance(item, dict):
            return None
        content = item.get("content")
        payload = content if isinstance(content, dict) else {}
        text = payload.get("text") or payload.get("content")
        if not isinstance(text, str) or not text:
            if isinstance(content, str) and content:
                text = content
            else:
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
            store="somabrain",
            created_at=str(created) if created else "",
        )

    async def close(self) -> None:
        """Close the HTTP client."""

        await self._client.aclose()


__all__ = ["SomaBrainAdapter"]
