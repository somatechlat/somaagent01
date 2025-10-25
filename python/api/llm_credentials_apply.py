import os
from typing import Any, Dict

import httpx

from python.helpers.api import ApiHandler, Request, Response


class LlmCredentialsApply(ApiHandler):
    """Proxy endpoint to store provider LLM credentials in Gateway.

    Request JSON:
      {"provider": "groq", "secret": "..."}
    Forwards to: {UI_GATEWAY_BASE}/v1/llm/credentials (POST)
    """

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]

    def _gateway_base(self) -> str:
        return os.getenv("UI_GATEWAY_BASE", os.getenv("GATEWAY_BASE_URL", "http://localhost:20016")).rstrip("/")

    async def process(self, input: Dict[str, Any], request: Request) -> Dict[str, Any] | Response:
        provider = (input.get("provider") or "").strip().lower()
        secret = (input.get("secret") or "").strip()
        if not provider or not secret:
            return {"ok": False, "error": "provider and secret are required"}
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if (bearer := os.getenv("UI_GATEWAY_BEARER")):
            headers["Authorization"] = f"Bearer {bearer}"
        url = f"{self._gateway_base()}/v1/llm/credentials"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json={"provider": provider, "secret": secret}, headers=headers)
        if resp.status_code >= 300:
            return {"ok": False, "error": f"gateway store failed: {resp.status_code} {resp.text}"}
        return {"ok": True}

