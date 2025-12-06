"""LLM invoke endpoints extracted from gateway monolith (minimal functional)."""

from __future__ import annotations

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/v1/llm", tags=["llm"])


class ChatMessage(BaseModel):
    role: str
    content: str


class LlmInvokeRequest(BaseModel):
    prompt: Optional[str] = None
    messages: Optional[List[ChatMessage]] = None
    role: Optional[str] = None
    session_id: Optional[str] = None
    tenant: Optional[str] = None
    overrides: Optional[Dict[str, Any]] = None
    metadata: dict | None = None


@router.post("/invoke")
async def invoke(req: LlmInvokeRequest) -> dict:
    # Support both prompt and messages format for backward compatibility
    if not req.prompt and not req.messages:
        raise HTTPException(status_code=400, detail="prompt_or_messages_required")
    
    # Get the actual text to process
    if req.messages:
        # Chat format - concatenate messages
        text = " ".join([msg.content for msg in req.messages])
    else:
        # Simple prompt format
        text = req.prompt
    
    # REAL IMPLEMENTATION - Use SLM client for LLM invocation
    from services.gateway.main import get_llm_credentials_store, _gateway_slm_client
    
    # Get credentials and client
    creds_store = get_llm_credentials_store()
    slm_client = _gateway_slm_client()
    
    # Get API key for the provider (default to openai)
    provider = req.overrides.get("model", "openai").split("/")[0] if req.overrides else "openai"
    api_key = await creds_store.get_provider_key(provider)
    
    if api_key:
        slm_client.api_key = api_key
    
    # Prepare parameters
    model = req.overrides.get("model", "gpt-4o-mini") if req.overrides else "gpt-4o-mini"
    base_url = req.overrides.get("base_url", "https://api.openai.com/v1") if req.overrides else "https://api.openai.com/v1"
    temperature = req.overrides.get("temperature") if req.overrides else None
    
    # Call the LLM
    content, usage = await slm_client.chat(
        messages=req.messages or [{"role": "user", "content": req.prompt}],
        model=model,
        base_url=base_url,
        temperature=temperature,
        **(req.overrides.get("kwargs", {}) if req.overrides else {})
    )
    
    return {
        "content": content,
        "usage": usage,
        "metadata": req.metadata or {}
    }


@router.post("/invoke/stream")
async def invoke_stream(req: LlmInvokeRequest) -> dict:
    if not req.prompt and not req.messages:
        raise HTTPException(status_code=400, detail="prompt_or_messages_required")
    
    # Get the actual text to process
    if req.messages:
        text = " ".join([msg.content for msg in req.messages])
    else:
        text = req.prompt
    
    # REAL IMPLEMENTATION - Use SLM client for streaming LLM invocation
    from services.gateway.main import get_llm_credentials_store, _gateway_slm_client
    
    # Get credentials and client
    creds_store = get_llm_credentials_store()
    slm_client = _gateway_slm_client()
    
    # Get API key for the provider
    provider = req.overrides.get("model", "openai").split("/")[0] if req.overrides else "openai"
    api_key = await creds_store.get_provider_key(provider)
    
    if api_key:
        slm_client.api_key = api_key
    
    # Prepare parameters
    model = req.overrides.get("model", "gpt-4o-mini") if req.overrides else "gpt-4o-mini"
    base_url = req.overrides.get("base_url", "https://api.openai.com/v1") if req.overrides else "https://api.openai.com/v1"
    temperature = req.overrides.get("temperature") if req.overrides else None
    
    # Call the LLM for streaming
    content, usage = await slm_client.chat(
        messages=req.messages or [{"role": "user", "content": req.prompt}],
        model=model,
        base_url=base_url,
        temperature=temperature,
        **(req.overrides.get("kwargs", {}) if req.overrides else {})
    )
    
    return {
        "stream": [content],
        "usage": usage,
        "metadata": req.metadata or {}
    }
