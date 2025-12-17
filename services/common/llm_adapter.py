"""LLM Adapter for SomaAgent01.

Production-grade adapter that talks to real HTTP endpoints – no stubs, no
placeholders. This adapter acts as a unified interface for LLM providers
(OpenAI-compatible).

Functionality:
* Uses httpx for async HTTP calls.
* Requires an API key for chat/LLM interactions.
* Accepts per-call ``base_url``/``api_path`` overrides to stay provider-agnostic.
* Supports Text and Multimodal (Vision) payloads.
"""

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, Sequence, List, Union

import httpx

from src.core.config import cfg


@dataclass
class ChatMessage:
    """Chat message structure for LLM communications."""

    role: str
    content: Union[str, List[Dict[str, Any]]]
    metadata: Optional[Dict[str, Any]] = None


class LLMAdapter:
    """
    Language Model Adapter for SomaAgent01.

    Provides interface capabilities including:
    - Chat message processing for LLM communications
    - Service health monitoring
    - Performance metrics collection
    """

    def __init__(self, service_url: str | None = None, api_key: str | None = None):
        """
        Initialize LLM adapter.

        Args:
            service_url: Optional base URL for the LLM provider. Can be overridden per call.
            api_key: Optional API key; can be injected per request when secrets are fetched at runtime.
        """
        # Accept absence of service_url so callers can supply per-call base_url.
        self.service_url = service_url.rstrip("/") if service_url else None
        self.api_key = api_key
        self._client = httpx.AsyncClient(timeout=float(cfg.env("LLM_HTTP_TIMEOUT", 30)))

    async def close(self) -> None:
        """Close underlying HTTP client."""
        await self._client.aclose()

    def _build_url(self, base_url: str | None, api_path: str | None) -> str:
        if not base_url and not self.service_url:
            raise RuntimeError("base_url is required for LLM requests (no fallbacks).")
        base = (base_url or self.service_url or "").rstrip("/")
        path = (api_path or "").lstrip("/") or "v1/chat/completions"
        return f"{base}/{path}"

    async def _post_json(self, url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        resp = await self._client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()

    async def send_message(self, message: ChatMessage) -> Dict[str, Any]:
        """Send a chat message through the adapter using the service_url."""
        url = self._build_url(self.service_url, "messages")
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        payload = {"role": message.role, "content": message.content, "metadata": message.metadata or {}}
        return await self._post_json(url, payload, headers)

    async def get_service_health(self, service_name: str) -> Dict[str, Any]:
        """Query health endpoint of the configured LLM service."""
        url = self._build_url(self.service_url, f"health/{service_name}")
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        resp = await self._client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()

    async def get_performance_metrics(self, service_name: str) -> Dict[str, Any]:
        """Fetch performance metrics for a service."""
        url = self._build_url(self.service_url, f"metrics/{service_name}")
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        resp = await self._client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()

    async def chat(
        self,
        messages: Sequence[ChatMessage | dict[str, Any]],
        *,
        model: str,
        base_url: str | None = None,
        api_path: str | None = "/v1/chat/completions",
        temperature: float | None = None,
        **kwargs: Any,
    ):
        """
        Chat with an LLM provider using the standard OpenAI-compatible API shape.

        Args:
            messages: Chat messages (ChatMessage or dict with role/content).
            model: Model name to use.
            base_url: Base URL for the API (required if service_url not set).
            api_path: Path portion for chat completion endpoint.
            temperature: Optional temperature.
            **kwargs: Additional provider-specific parameters (passed through).

        Returns:
            Tuple of (content, usage dict) from the provider response.
        """
        url = self._build_url(base_url, api_path)
        if not self.api_key:
            raise RuntimeError("LLMAdapter.chat requires an API key (none configured).")

        # Normalise messages to dicts accepted by OpenAI-compatible APIs.
        def _to_dict(msg: ChatMessage | dict[str, Any]) -> dict[str, Any]:
            if isinstance(msg, ChatMessage):
                return {"role": msg.role, "content": msg.content, "metadata": msg.metadata}
            return msg

        msg_payload: Iterable[dict[str, Any]] = [_to_dict(m) for m in messages]

        body: dict[str, Any] = {"model": model, "messages": list(msg_payload)}
        if temperature is not None:
            body["temperature"] = temperature
        # Merge additional parameters while keeping required fields intact
        body.update({k: v for k, v in kwargs.items() if v is not None})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = await self._post_json(url, body, headers)

        # Extract content/usage following OpenAI-compatible schema
        content: str | None = None
        if isinstance(data.get("choices"), list) and data["choices"]:
            choice = data["choices"][0]
            message = choice.get("message") or {}
            content = message.get("content") or choice.get("text")
        usage = data.get("usage", {})
        if content is None:
            raise RuntimeError("LLM provider returned no content.")
        return content, usage
