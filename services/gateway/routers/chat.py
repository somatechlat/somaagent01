"""Gateway chat completions endpoint (restored functional path)."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, validator

from services.common.slm_client import SLMClient, ChatMessage
from services.common.llm_credentials_store import LlmCredentialsStore

router = APIRouter(prefix="/v1/chat", tags=["chat"])


class ChatCompletionMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    messages: List[ChatCompletionMessage]
    model: Optional[str] = None
    base_url: Optional[str] = None
    api_path: Optional[str] = None
    temperature: Optional[float] = Field(default=None, ge=0, le=2)
    kwargs: Optional[Dict[str, Any]] = None

    @validator("messages")
    def _non_empty_messages(cls, v):
        if not v:
            raise ValueError("messages cannot be empty")
        return v


def _normalize_llm_base_url(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return s
    s = s.rstrip("/")
    if s.endswith("/chat/completions"):
        s = s[: -len("/chat/completions")].rstrip("/")
    if s.endswith("/v1"):
        s = s[: -len("/v1")].rstrip("/")
    return s


def _detect_provider_from_base(base_url: str) -> str:
    host = base_url.lower()
    try:
        from urllib.parse import urlparse
        netloc = (urlparse(base_url).netloc or "").lower()
        if netloc:
            host = netloc
    except Exception:
        pass
    if "groq" in host:
        return "groq"
    if "openrouter" in host:
        return "openrouter"
    if "openai" in host:
        return "openai"
    return "other"


async def _resolve_credentials(base_url: str) -> str:
    provider = _detect_provider_from_base(base_url)
    store = LlmCredentialsStore()
    if hasattr(store, "get"):
        secret = await store.get(provider)
    else:
        secret = await store.get_provider_key(provider)
    if not secret:
        raise HTTPException(status_code=404, detail=f"credentials not found for provider: {provider}")
    return secret


@router.post("/completions")
async def chat_completions(payload: ChatCompletionRequest):
    model = (payload.model or os.getenv("SLM_MODEL", "")).strip()
    base_url_raw = payload.base_url or os.getenv("SLM_BASE_URL", "")
    base_url = _normalize_llm_base_url(base_url_raw)
    if not model or not base_url:
        raise HTTPException(status_code=400, detail="model and base_url are required")

    secret = await _resolve_credentials(base_url)

    messages = [ChatMessage(role=m.role, content=m.content) for m in payload.messages]

    client = SLMClient(base_url=base_url, model=model)
    client.api_key = secret

    try:
        content, usage = await client.chat(
            messages,
            model=model,
            base_url=base_url,
            api_path=payload.api_path,
            temperature=payload.temperature,
            **(payload.kwargs or {}),
        )
        return {"content": content, "usage": usage, "model": model, "base_url": base_url}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"provider error: {exc}")
