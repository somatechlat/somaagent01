import os
from typing import Any, Dict

import httpx

from python.helpers.api import ApiHandler, Request, Response


class LlmProfileApply(ApiHandler):
    """Proxy endpoint to apply the dialogue model profile to Gateway.

    Expects a JSON body with the following optional fields (string/number):
      - model: str
      - base_url: str
      - temperature: float
      - kwargs: dict (optional extra provider params)

    This handler forwards a PUT to:
      {UI_GATEWAY_BASE}/v1/model-profiles/dialogue/{DEPLOYMENT_MODE}

    DEPLOYMENT_MODE is read from UI_DEPLOYMENT_MODE (default: DEV).
    If UI_GATEWAY_BEARER is set, it is sent as Authorization: Bearer <token>.
    """

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]

    def _gateway_base(self) -> str:
        return os.getenv("UI_GATEWAY_BASE", os.getenv("GATEWAY_BASE_URL", "http://localhost:20016")).rstrip("/")

    def _deployment_mode(self) -> str:
        # Align with SA01Settings defaults; DEV is the common local mode
        return os.getenv("UI_DEPLOYMENT_MODE", os.getenv("SA01_DEPLOYMENT_MODE", "DEV")).upper()

    async def process(self, input: Dict[str, Any], request: Request) -> Dict[str, Any] | Response:
        model = (input.get("model") or "").strip()
        base_url = (input.get("base_url") or "").strip()
        kwargs = input.get("kwargs") or {}
        try:
            temperature = float(input.get("temperature")) if input.get("temperature") is not None else 0.2
        except (ValueError, TypeError):
            temperature = 0.2

        if not model:
            return {"ok": False, "error": "model is required"}

        payload = {
            "role": "dialogue",
            "deployment_mode": self._deployment_mode(),
            "model": model,
            "base_url": base_url,
            "temperature": temperature,
            "kwargs": kwargs if isinstance(kwargs, dict) else {},
        }

        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if (bearer := os.getenv("UI_GATEWAY_BEARER")):
            headers["Authorization"] = f"Bearer {bearer}"

        url = f"{self._gateway_base()}/v1/model-profiles/dialogue/{self._deployment_mode()}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.put(url, json=payload, headers=headers)
        if resp.status_code >= 300:
            return {"ok": False, "error": f"gateway update failed: {resp.status_code} {resp.text}"}
        return {"ok": True}

