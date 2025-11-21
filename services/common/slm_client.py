"""Async client for OpenAI-compatible chat endpoints (restored from stable gateway logic)."""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, Optional, Sequence, Tuple

import httpx

LOGGER = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    role: str
    content: str


class SLMClient:
    def __init__(self, base_url: str | None = None, model: str | None = None) -> None:
        self.base_url = base_url or os.getenv("SLM_BASE_URL", "https://slm.somaagent01.dev/v1")
        self.default_model = model or os.getenv("SLM_MODEL", "meta-llama/Meta-Llama-3.1-8B-Instruct")
        self.api_key = os.getenv("SLM_API_KEY")
        self._client = httpx.AsyncClient(timeout=30.0)

    async def chat(
        self,
        messages: Sequence[ChatMessage],
        *,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        api_path: Optional[str] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> Tuple[str, dict[str, int]]:
        if not (self.base_url and (model or self.default_model)):
            raise RuntimeError("SLM misconfigured: base_url or model missing")
        if not self.api_key:
            raise RuntimeError("SLM_API_KEY missing: no LLM calls will succeed")
        chosen_model = model or self.default_model
        path = api_path or kwargs.get("api_path") or "/v1/chat/completions"
        url = f"{(base_url or self.base_url).rstrip('/')}{path}"
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
        if response.is_error:
            try:
                body = response.text
                LOGGER.error("SLM error response", extra={"status": response.status_code, "body": body[:800]})
            except Exception:
                pass
            response.raise_for_status()

        data: dict[str, Any] = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            usage_dict = {
                "input_tokens": int(usage.get("prompt_tokens", 0)),
                "output_tokens": int(usage.get("completion_tokens", 0)),
            }
            return content, usage_dict
        except (KeyError, IndexError) as exc:
            LOGGER.error("Unexpected response from SLM", extra={"data": data})
            raise RuntimeError("Invalid response from SLM") from exc

    async def chat_stream(
        self,
        messages: Sequence[ChatMessage],
        *,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        api_path: Optional[str] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> AsyncIterator[Dict[str, Any]]:
        if not (self.base_url and (model or self.default_model)):
            raise RuntimeError("SLM misconfigured: base_url or model missing")
        if not self.api_key:
            raise RuntimeError("SLM_API_KEY missing: no LLM calls will succeed")
        chosen_model = model or self.default_model
        path = api_path or kwargs.get("api_path") or "/v1/chat/completions"
        url = f"{(base_url or self.base_url).rstrip('/')}{path}"
        payload = {
            "model": chosen_model,
            "messages": [message.__dict__ for message in messages],
            "temperature": temperature if temperature is not None else float(os.getenv("SLM_TEMPERATURE", "0.2")),
            "stream": True,
        }
        if kwargs:
            payload.update(kwargs)
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        async with self._client.stream("POST", url, json=payload, headers=headers) as response:
            if response.is_error:
                try:
                    body = await response.aread()
                    LOGGER.error(
                        "SLM stream error response",
                        extra={"status": response.status_code, "body": body.decode("utf-8", errors="ignore")[:800]},
                    )
                except Exception:
                    pass
                response.raise_for_status()
            async for line in response.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                data_str = line[5:].strip()
                if data_str == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                except json.JSONDecodeError:
                    LOGGER.warning("Skipping malformed stream chunk", extra={"chunk": data_str})
                    continue
                yield data

    async def close(self) -> None:
        await self._client.aclose()
