"""Lightweight async client to the Gateway service for UI proxy usage."""

from __future__ import annotations

import os
from typing import Any, Dict, List

import httpx


class GatewayClient:
	def __init__(self, base_url: str | None = None, *, timeout: float = 10.0) -> None:
		self.base_url = (base_url or os.getenv("GATEWAY_BASE_URL") or "http://gateway:8010").rstrip("/")
		self.timeout = timeout
		self._client = httpx.AsyncClient(timeout=timeout)

	async def aclose(self) -> None:
		await self._client.aclose()

	async def post_message(self, payload: Dict[str, Any]) -> httpx.Response:
		url = f"{self.base_url}/v1/session/message"
		return await self._client.post(url, json=payload)

	async def get_contexts(self) -> List[Dict[str, Any]] | Dict[str, Any]:
		url = f"{self.base_url}/v1/sessions"
		resp = await self._client.get(url)
		resp.raise_for_status()
		return resp.json()

	async def list_events(self, session_id: str, *, limit: int = 200) -> Dict[str, Any]:
		url = f"{self.base_url}/v1/sessions/{session_id}/events"
		resp = await self._client.get(url, params={"limit": str(limit)})
		resp.raise_for_status()
		return resp.json()
