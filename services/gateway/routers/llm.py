"""LLM invoke endpoints – real OpenAI-compatible proxy used by the worker."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from services.common.slm_client import SLMClient, ChatMessage
from services.gateway.routers.chat import (
    _normalize_llm_base_url,
    _detect_provider_from_base,
    _resolve_credentials,
    _load_llm_settings,
)

router = APIRouter(prefix="/v1/llm", tags=["llm"])


class InvokePayload(BaseModel):
    role: Optional[str] = None
    session_id: Optional[str] = None
    persona_id: Optional[str] = None
    tenant: Optional[str] = None
    messages: List[Dict[str, Any]]
    overrides: Optional[Dict[str, Any]] = None


async def _extract_overrides(payload: InvokePayload) -> tuple[str, str, float | None, dict]:
    ov = payload.overrides or {}
    model = (ov.get("model") or "").strip()
    base_url = _normalize_llm_base_url((ov.get("base_url") or "").strip())
    temperature = ov.get("temperature") if ov.get("temperature") is not None else None
    kwargs = ov.get("kwargs") or {}
    # Centralized fallback
    if not model or not base_url:
        settings = await _load_llm_settings()  # type: ignore
        model = settings["model"]
        base_url = settings["base_url"]
        if temperature is None:
            temperature = settings.get("temperature")
    return model, base_url, temperature, kwargs


async def _resolve_client(model: str, base_url: str) -> SLMClient:
    if not model:
        raise HTTPException(status_code=400, detail="model_required")
    if not base_url:
        raise HTTPException(status_code=400, detail="base_url_required")
    secret = await _resolve_credentials(base_url)
    client = SLMClient(base_url=base_url, model=model)
    client.api_key = secret
    return client


def _to_messages(raw_messages: List[Dict[str, Any]]) -> List[ChatMessage]:
    msgs: List[ChatMessage] = []
    for m in raw_messages:
        role = m.get("role") or "user"
        content = m.get("content") or ""
        msgs.append(ChatMessage(role=role, content=content))
    return msgs


@router.post("/invoke")
async def invoke(req: InvokePayload) -> dict:
    if not req.messages:
        raise HTTPException(status_code=400, detail="messages_required")

    model, base_url, temperature, kwargs = await _extract_overrides(req)
    client = await _resolve_client(model, base_url)
    messages = _to_messages(req.messages)

    content, usage = await client.chat(
        messages,
        model=model,
        base_url=base_url,
        temperature=temperature,
        **kwargs,
    )
    return {
        "content": content,
        "usage": usage,
        "model": model,
        "base_url": base_url,
    }


@router.post("/invoke/stream")
async def invoke_stream(req: InvokePayload):
    if not req.messages:
        raise HTTPException(status_code=400, detail="messages_required")

    model, base_url, temperature, kwargs = await _extract_overrides(req)
    client = await _resolve_client(model, base_url)
    messages = _to_messages(req.messages)

    async def _event_stream():
        try:
            async for chunk in client.chat_stream(
                messages,
                model=model,
                base_url=base_url,
                temperature=temperature,
                **kwargs,
            ):
                yield f"data: {json.dumps(chunk)}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(_event_stream(), media_type="text/event-stream")
