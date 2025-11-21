"""Client for the dynamic router service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import httpx

from src.core.config import cfg

@dataclass
class RouteDecision:
    model: str
    score: float


class RouterClient:
    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = base_url or cfg.env("ROUTER_URL")
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
