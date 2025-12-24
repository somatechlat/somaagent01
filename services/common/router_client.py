"""Client for the dynamic router service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import httpx

import os


@dataclass
class RouteDecision:
    model: str
    score: float


class RouterClient:
    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = base_url or os.environ.get("ROUTER_URL")
        self._client = httpx.AsyncClient(timeout=5.0) if self.base_url else None

    async def route(
        self,
        *,
        role: str,
        deployment_mode: str,
        candidates: list[str],
    ) -> Optional[RouteDecision]:
        if not self._client or not self.base_url:
            return None
        response = await self._client.post(
            f"{self.base_url.rstrip('/')}/v1/route",
            json={
                "role": role,
                "deployment_mode": deployment_mode,
                "candidates": candidates,
            },
        )
        response.raise_for_status()
        data = response.json()
        return RouteDecision(model=data["model"], score=float(data.get("score", 0.0)))

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()


# ---------------------------------------------------------------------------
# Helper / factory function
# ---------------------------------------------------------------------------
# The codebase historically imported a ``get_router_client`` function from this
# module.  The original implementation was removed during refactoring, which now
# causes an ``ImportError`` when modules such as ``services.gateway.routers.
# uploads_full`` attempt to import it.  To preserve backwards compatibility while
# keeping a single source of truth, we expose a lightweight factory that returns a
# shared ``RouterClient`` instance.  The instance is cached at module level so
# repeated calls are inexpensive and behave like a singleton.

_router_client: RouterClient | None = None


def get_router_client() -> RouterClient:
    """Return a shared :class:`RouterClient` instance.

    The function lazily creates a ``RouterClient`` on first call and re‑uses the
    same object for subsequent calls.  This mirrors the behaviour expected by
    legacy callers that relied on a module‑level singleton.
    """
    global _router_client
    if _router_client is None:
        _router_client = RouterClient()
    return _router_client


__all__ = [
    "RouterClient",
    "RouteDecision",
    "get_router_client",
]
