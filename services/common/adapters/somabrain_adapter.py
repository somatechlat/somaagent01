"""SomaBrain adapter — talks to the real SomaBrain memory HTTP API.

Live endpoints (Django Ninja routers mounted at ``/memory/`` in
somabrain/api/v1.py:96,104; Django serves them both with and without the
``/api`` prefix — somabrain/config/urls.py:479,482):
    POST {SOMABRAIN_URL}/memory/remember   (endpoints/memory_remember.py:102)
    POST {SOMABRAIN_URL}/memory/recall     (endpoints/memory.py:73)
    POST {SOMABRAIN_URL}/memory/forget     (endpoints/memory.py:291)
    POST {SOMABRAIN_URL}/memory/remember/batch

The ``/api/remember`` and ``/api/recall`` dialect (agent BrainBridge,
aaas/brain.py:162,218) has NO route in somabrain and is not used here.

Forget speaks the brain's ``ForgetRequest`` / ``ForgetResponse`` contract
(somabrain.api.memory.models:454-471): ``POST /memory/forget`` with
``{coord, tenant, tenant_id}`` and a response of
``{ok, coord, store, tenant, error}``.

URL resolution is fail-closed (VIBE Rule 91): env ``SOMABRAIN_URL``, no
localhost fallback.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, Union

import httpx
from pydantic import BaseModel, Field

from services.common.memory_contract import (
    MemoryAck,
    MemoryConfigurationError,
    MemoryHit,
    MemoryRecallUnavailable,
    MemoryWrite,
    get_memory_setting,
)

LOGGER = logging.getLogger(__name__)

# Logical namespace sent with writes; recall must use the same one.
DEFAULT_NAMESPACE = "default"


class ForgetRequest(BaseModel):
    """Wire DTO for ``POST /memory/forget`` — mirrors somabrain's ForgetRequest.

    ``coord`` accepts the seam comma-separated float string or a float list;
    ``tenant`` (rich name) and ``tenant_id`` (seam name) are both optional
    there, but this adapter always sends the seam ``tenant_id`` in both slots
    so either resolver on the brain side lands on the same tenant.
    """

    coord: Union[str, list[float]] = Field(
        ..., description="Coordinate identity: 'x,y,z' or [x,y,z]"
    )
    tenant: str | None = Field(None, description="Tenant identifier (rich name)")
    tenant_id: str | None = Field(None, description="Tenant identifier (seam name)")


class ForgetResponse(BaseModel):
    """Wire DTO for ``POST /memory/forget`` — mirrors somabrain's ForgetResponse.

    ``ok`` is True only when the backend deleted the record. ``ok: false`` with
    ``error: "not found"`` means the coordinate was not present — the brain
    fails closed with an HTTP error on backend outage, never a silent success.
    """

    ok: bool
    coord: str
    store: str = "somafractalmemory"
    tenant: str = ""
    error: str | None = None


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
    """HTTP adapter for SomaBrain's real ``/memory/remember|recall|forget`` API."""

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
        # Production low-latency write: WM + durable outbox ack, LTM async (T-6).
        headers["X-Soma-Fast-Ack"] = "true"
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
            data = response.json() or {}
            # Prefer the backend's stored coordinate so get/forget use the real key.
            stored = data.get("coord") or data.get("coordinate")
            if isinstance(stored, (list, tuple)) and stored:
                stored_coord = ",".join(str(x) for x in stored)
            elif isinstance(stored, str) and stored.strip():
                stored_coord = stored.strip()
            else:
                stored_coord = w.coord
            return MemoryAck(coord=stored_coord, store="somabrain", ok=True)
        except Exception as exc:
            LOGGER.warning("SomaBrain remember failed: %s", exc)
            return MemoryAck(coord=w.coord, store="somabrain", ok=False, error=str(exc))

    async def recall(self, query: str, k: int, tenant_id: str) -> list[MemoryHit]:
        """Search via POST /memory/recall.

        Fail-closed (R-05 / F-10): a transport or store failure raises
        ``MemoryRecallUnavailable`` — it is never reported as an empty list,
        which would be indistinguishable from "the user has no history".
        """

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
            raise MemoryRecallUnavailable(
                f"SomaBrain recall failed for tenant={tenant_id!r}: {exc}"
            ) from exc

        hits: list[MemoryHit] = []
        for item in data.get("results") or []:
            hit = self._to_hit(item)
            if hit is not None:
                hits.append(hit)
        return hits

    async def forget(self, coord: str, tenant_id: str) -> bool:
        """Delete via POST /memory/forget. True only when the brain reports ``ok: true``.

        Request/response are the brain's ``ForgetRequest`` / ``ForgetResponse``
        (somabrain.api.memory.models:454-471). ``ok: false`` with
        ``error: "not found"`` is a real answer — the coordinate was not
        present — and returns False. A transport or backend failure is logged
        and also returns False; it is never a silent skip of the call.
        """

        body = ForgetRequest(coord=coord, tenant=tenant_id, tenant_id=tenant_id)
        try:
            response = await self._client.post(
                "/memory/forget",
                json=body.model_dump(exclude_none=True),
                headers=self._headers(tenant_id),
            )
            response.raise_for_status()
            payload = ForgetResponse.model_validate(response.json() or {})
        except Exception as exc:
            LOGGER.warning("SomaBrain forget failed for coord=%s: %s", coord, exc)
            return False
        if not payload.ok:
            LOGGER.info(
                "SomaBrain forget: coord=%s not deleted (%s)", coord, payload.error
            )
        return bool(payload.ok)

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


__all__ = ["ForgetRequest", "ForgetResponse", "SomaBrainAdapter"]
