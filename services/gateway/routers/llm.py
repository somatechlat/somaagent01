"""LLM invoke endpoints - VIBE COMPLIANT.

Gets model configuration from AgentSettingsStore (PostgreSQL).
Gets API keys from UnifiedSecretManager (Vault).
Uses FastAPI dependency injection - NO circular imports.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from services.common.agent_settings_store import get_agent_settings_store
from services.common.unified_secret_manager import get_secret_manager
from services.gateway.providers import get_slm_client

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


async def _get_model_config() -> Dict[str, Any]:
    """Get model configuration from AgentSettingsStore.
    
    Returns model provider, name, and base_url from UI settings.
    """
    store = get_agent_settings_store()
    settings = await store.get_settings()
    
    # Extract model configuration from settings
    # UI stores these as chat-model-provider, chat-model-name
    return {
        "provider": settings.get("chat-model-provider", "openai"),
        "model": settings.get("chat-model-name", "gpt-4o-mini"),
        "base_url": settings.get("chat-model-base-url"),
        "temperature": settings.get("chat-model-temperature"),
    }


async def _get_api_key(provider: str) -> Optional[str]:
    """Get API key for provider from UnifiedSecretManager (Vault)."""
    secrets = get_secret_manager()
    return secrets.get_provider_key(provider)


@router.post("/invoke")
async def invoke(
    req: LlmInvokeRequest,
    slm_client=Depends(get_slm_client),
) -> dict:
    """Invoke LLM with the given prompt or messages.
    
    Model configuration comes from AgentSettingsStore (UI settings).
    API keys come from UnifiedSecretManager (Vault).
    """
    if not req.prompt and not req.messages:
        raise HTTPException(status_code=400, detail="prompt_or_messages_required")
    
    # Get model config from AgentSettingsStore
    model_config = await _get_model_config()
    
    # Allow request overrides to take precedence
    provider = req.overrides.get("provider", model_config["provider"]) if req.overrides else model_config["provider"]
    model = req.overrides.get("model", model_config["model"]) if req.overrides else model_config["model"]
    base_url = req.overrides.get("base_url", model_config["base_url"]) if req.overrides else model_config["base_url"]
    temperature = req.overrides.get("temperature", model_config["temperature"]) if req.overrides else model_config["temperature"]
    
    # Get API key from Vault
    api_key = await _get_api_key(provider)
    if api_key:
        slm_client.api_key = api_key
    
    # Set default base_url based on provider if not specified
    if not base_url:
        provider_urls = {
            "openai": "https://api.openai.com/v1",
            "groq": "https://api.groq.com/openai/v1",
            "anthropic": "https://api.anthropic.com/v1",
            "fireworks": "https://api.fireworks.ai/inference/v1",
        }
        base_url = provider_urls.get(provider, "https://api.openai.com/v1")
    
    # Prepare messages
    messages = req.messages or [{"role": "user", "content": req.prompt}]
    if messages and isinstance(messages[0], ChatMessage):
        messages = [{"role": m.role, "content": m.content} for m in messages]
    
    # Call the LLM
    content, usage = await slm_client.chat(
        messages=messages,
        model=model,
        base_url=base_url,
        temperature=temperature,
        **(req.overrides.get("kwargs", {}) if req.overrides else {})
    )
    
    return {
        "content": content,
        "usage": usage,
        "metadata": req.metadata or {},
        "model_used": model,
        "provider_used": provider,
    }


@router.post("/invoke/stream")
async def invoke_stream(
    req: LlmInvokeRequest,
    slm_client=Depends(get_slm_client),
) -> dict:
    """Invoke LLM with streaming response.
    
    Model configuration comes from AgentSettingsStore (UI settings).
    API keys come from UnifiedSecretManager (Vault).
    """
    if not req.prompt and not req.messages:
        raise HTTPException(status_code=400, detail="prompt_or_messages_required")
    
    # Get model config from AgentSettingsStore
    model_config = await _get_model_config()
    
    # Allow request overrides to take precedence
    provider = req.overrides.get("provider", model_config["provider"]) if req.overrides else model_config["provider"]
    model = req.overrides.get("model", model_config["model"]) if req.overrides else model_config["model"]
    base_url = req.overrides.get("base_url", model_config["base_url"]) if req.overrides else model_config["base_url"]
    temperature = req.overrides.get("temperature", model_config["temperature"]) if req.overrides else model_config["temperature"]
    
    # Get API key from Vault
    api_key = await _get_api_key(provider)
    if api_key:
        slm_client.api_key = api_key
    
    # Set default base_url based on provider if not specified
    if not base_url:
        provider_urls = {
            "openai": "https://api.openai.com/v1",
            "groq": "https://api.groq.com/openai/v1",
            "anthropic": "https://api.anthropic.com/v1",
            "fireworks": "https://api.fireworks.ai/inference/v1",
        }
        base_url = provider_urls.get(provider, "https://api.openai.com/v1")
    
    # Prepare messages
    messages = req.messages or [{"role": "user", "content": req.prompt}]
    if messages and isinstance(messages[0], ChatMessage):
        messages = [{"role": m.role, "content": m.content} for m in messages]
    
    # Call the LLM for streaming
    content, usage = await slm_client.chat(
        messages=messages,
        model=model,
        base_url=base_url,
        temperature=temperature,
        **(req.overrides.get("kwargs", {}) if req.overrides else {})
    )
    
    return {
        "stream": [content],
        "usage": usage,
        "metadata": req.metadata or {},
        "model_used": model,
        "provider_used": provider,
    }
