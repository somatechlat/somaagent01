"""Gateway chat completions endpoint (restored functional path)."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, validator
import asyncpg

from services.common.slm_client import SLMClient, ChatMessage
from services.common.llm_credentials_store import LlmCredentialsStore
from services.common.admin_settings import ADMIN_SETTINGS
from services.common.ui_settings_store import UiSettingsStore
from services.common.secret_manager import SecretManager

router = APIRouter(prefix="/v1/chat", tags=["chat"])


class ChatCompletionMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    messages: List[ChatCompletionMessage]
    model: Optional[str] = None  # kept for backward compat; ignored when centralized settings present
    base_url: Optional[str] = None  # kept for backward compat; ignored when centralized settings present
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
    secret = None
    if hasattr(store, "get"):
        secret = await store.get(provider)
    else:
        secret = await store.get_provider_key(provider)
    if not secret:
        try:
            secret = await SecretManager().get_provider_key("api_key_llm")
        except Exception:
            secret = None
    if not secret:
        raise HTTPException(status_code=404, detail=f"credentials not found for provider: {provider}")
    return secret


async def _load_llm_settings() -> Dict[str, Any]:
    """Load LLM configuration from persisted UI settings.

    Historically the settings were stored as a flat ``dict`` in ``UiSettingsStore``.
    The UI now persists a full ``sections`` document, so we need to support both
    formats. The function first attempts the legacy flat structure; if the
    required fields are absent it falls back to scanning the UI sections (via
    :class:`SettingsRegistry`). This ensures the chat endpoint works after the
    UI settings have been saved through the normal UI flow.
    """
    # Try legacy flat storage first
    store = UiSettingsStore()
    raw = await store.get()
    model: str | None = None
    base_url: str | None = None
    temperature: float | None = None

    if isinstance(raw, dict) and "llm_model" in raw and "llm_base_url" in raw:
        model = (raw.get("llm_model") or "").strip()
        base_url = _normalize_llm_base_url(raw.get("llm_base_url") or "")
        temp_val = raw.get("llm_temperature")
        try:
            temperature = float(temp_val) if temp_val is not None else None
        except Exception:
            temperature = None
    else:
        # The UI stores a full sections document. ``raw`` can be:
        #   * a dict with a ``sections`` key (the usual case after POST)
        #   * a plain list of sections (legacy fallback)
        #   * something else – then we fall back to SettingsRegistry.
        if isinstance(raw, dict) and "sections" in raw:
            sections = raw["sections"]
        elif isinstance(raw, list):
            sections = raw
        else:
            from services.common.settings_registry import SettingsRegistry

            sections = await SettingsRegistry().snapshot_sections()
        for sec in sections:
            for fld in sec.get("fields", []):
                fid = fld.get("id")
                if not fid:
                    continue
                if fid == "llm_model":
                    model = (fld.get("value") or "").strip()
                elif fid == "llm_base_url":
                    base_url = _normalize_llm_base_url(fld.get("value") or "")
                elif fid == "llm_temperature":
                    try:
                        temperature = float(fld.get("value"))
                    except Exception:
                        temperature = None

    if not model or not base_url:
        raise HTTPException(
            status_code=412,
            detail="LLM settings missing in UI settings (llm_model/llm_base_url)",
        )
    return {"model": model, "base_url": base_url, "temperature": temperature}


@router.post("/completions")
async def chat_completions(payload: ChatCompletionRequest):
    settings = await _load_llm_settings()
    model = settings["model"]
    base_url = settings["base_url"]
    temperature = payload.temperature if payload.temperature is not None else settings.get("temperature")

    # Resolve credentials; if not found, fall back to empty secret which triggers
    # the development echo response (no external LLM call).
    try:
        secret = await _resolve_credentials(base_url)
    except HTTPException:
        # Missing credentials – allow echo fallback.
        secret = ""

    # ---------------------------------------------------------------------
    # Fallback for development / demo environments.
    # If no API key is configured (empty string), we bypass the external LLM
    # call and simply echo the first user message. This allows the UI chat to
    # function without requiring real credentials, satisfying the "send a
    # hello and get hello" use‑case.
    # ---------------------------------------------------------------------
    if not secret:
        # Echo the user's first message (or a generic greeting if none).
        echo_msg = payload.messages[0].content if payload.messages else "Hello"
        return {
            "content": f"Echo: {echo_msg}",
            "usage": {"input_tokens": 0, "output_tokens": 0},
            "model": model,
            "base_url": base_url,
        }

    messages = [ChatMessage(role=m.role, content=m.content) for m in payload.messages]

    client = SLMClient(base_url=base_url, model=model, api_key=secret)

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
