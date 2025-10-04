"""Async client for OSS SLM/LLM endpoints (OpenAI-compatible)."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Sequence

import httpx

LOGGER = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    role: str
    content: str


class SLMClient:
    def __init__(self, base_url: str | None = None, model: str | None = None) -> None:
        self.base_url = base_url or os.getenv("SLM_BASE_URL", "http://vllm:8000")
        self.default_model = model or os.getenv("SLM_MODEL", "meta-llama/Meta-Llama-3.1-8B-Instruct")
        self.api_key = os.getenv("SLM_API_KEY")  # optional for authenticated gateways
        self._client = httpx.AsyncClient(timeout=30.0)

    async def chat(
        self,
        messages: Sequence[ChatMessage],
        *,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> str:
        chosen_model = model or self.default_model
        url = f"{(base_url or self.base_url).rstrip('/')}/v1/chat/completions"
        payload = {
            "model": chosen_model,
            "messages": [message.__dict__ for message in messages],
            "temperature": temperature if temperature is not None else float(os.getenv("SLM_TEMPERATURE", "0.2")),
            "stream": False,
        }
        if kwargs:
            payload.update(kwargs)
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        response = await self._client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:  # pragma: no cover - unexpected schema
            LOGGER.error("Unexpected response from SLM", extra={"data": data})
            raise RuntimeError("Invalid response from SLM") from exc

    async def close(self) -> None:
        await self._client.aclose()
