"""Policy enforcement via OPA/OpenFGA."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Optional

import httpx

LOGGER = logging.getLogger(__name__)


@dataclass
class PolicyRequest:
    tenant: str
    persona_id: Optional[str]
    action: str
    resource: str
    context: dict[str, Any]


class PolicyClient:
    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = base_url or os.getenv("POLICY_BASE_URL", "http://opa:8181")
        self.data_path = os.getenv("POLICY_DATA_PATH", "/v1/data/soma/allow")
        self._client = httpx.AsyncClient(timeout=10.0)

    async def evaluate(self, request: PolicyRequest) -> bool:
        payload = {
            "input": {
                "tenant": request.tenant,
                "persona_id": request.persona_id,
                "action": request.action,
                "resource": request.resource,
                "context": request.context,
            }
        }
        url = f"{self.base_url.rstrip('/')}{self.data_path}"
        response = await self._client.post(url, json=payload)
        if response.status_code != 200:
            LOGGER.error(
                "OPA request failed", extra={"status": response.status_code, "body": response.text}
            )
            response.raise_for_status()
        data: dict[str, Any] = response.json()
        return bool(data.get("result"))

    async def close(self) -> None:
        await self._client.aclose()
