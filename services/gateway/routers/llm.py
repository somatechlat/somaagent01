"""LLM invoke endpoints extracted from gateway monolith (minimal functional)."""

from __future__ import annotations

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from integrations.repositories import get_audit_store
from src.core.config import cfg

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
    multimodal: bool = False


def _multimodal_instructions() -> str:
    return (
        "MULTIMODAL CAPABILITIES:\n"
        "If the user asks for images, diagrams, screenshots, or other visuals, "
        "output a JSON block at the END of your response containing a "
        "`multimodal_plan` that follows Task DSL v1.0. Example:\n\n"
        "{\n"
        '  "multimodal_plan": {\n'
        '    "version": "1.0",\n'
        '    "tasks": [\n'
        "      {\n"
        '        "task_id": "step_00",\n'
        '        "step_type": "generate_image",\n'
        '        "modality": "image",\n'
        '        "depends_on": [],\n'
        '        "params": {\n'
        '          "prompt": "Describe the image",\n'
        '          "format": "png",\n'
        '          "dimensions": {"width": 1920, "height": 1080}\n'
        "        },\n"
        '        "constraints": {"max_cost_cents": 50},\n'
        '        "quality_gate": {"enabled": true, "min_score": 0.7, "max_reworks": 2}\n'
        "      }\n"
        "    ],\n"
        '    "budget": {"max_cost_cents": 500}\n'
        "  }\n"
        "}\n\n"
        "Supported step_types: generate_image, generate_diagram, capture_screenshot.\n"
        "Do NOT ask for confirmation. Return the JSON block after your text."
    )


@router.post("/invoke")
async def invoke(req: LlmInvokeRequest) -> dict:
    # Support both prompt and messages format for backward compatibility
    if not req.prompt and not req.messages:
        raise HTTPException(status_code=400, detail="prompt_or_messages_required")

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

    messages = req.messages or [{"role": "user", "content": req.prompt}]
    if req.multimodal and cfg.env("SA01_ENABLE_MULTIMODAL_CAPABILITIES", "false").lower() == "true":
        messages = [{"role": "system", "content": _multimodal_instructions()}] + messages

    try:
        request_logprobs = cfg.env("CONFIDENCE_ENABLED", "false").lower() == "true"
        aggregation = cfg.env("CONFIDENCE_AGGREGATION", "average")
        content, usage, confidence = await slm_client.chat(
            messages=messages,
            model=model,
            base_url=base_url,
            temperature=temperature,
            request_logprobs=request_logprobs,
            confidence_aggregation=aggregation,
            **(req.overrides.get("kwargs", {}) if req.overrides else {})
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"llm_provider_error: {exc}")

    # Audit log real event
    try:
        await get_audit_store().log(
            request_id=None,
            trace_id=None,
            session_id=req.session_id,
            tenant=req.tenant,
            subject=None,
            action="llm.invoke",
            resource="llm.invoke",
            target_id=None,
            details={
                "status": "ok",
                "provider": provider,
                "model": model,
                "base_url": base_url,
                "usage": usage,
            },
            diff=None,
            ip=None,
            user_agent=None,
        )
    except Exception:
        # Audit errors must not break the endpoint; log at debug level.
        import logging

        logging.getLogger(__name__).debug("audit log failed for llm.invoke", exc_info=True)

    return {
        "content": content,
        "usage": usage,
        "metadata": req.metadata or {},
        "confidence": confidence if request_logprobs else None,
    }


@router.post("/invoke/stream")
async def invoke_stream(req: LlmInvokeRequest) -> dict:
    if not req.prompt and not req.messages:
        raise HTTPException(status_code=400, detail="prompt_or_messages_required")

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

    messages = req.messages or [{"role": "user", "content": req.prompt}]
    if req.multimodal and cfg.env("SA01_ENABLE_MULTIMODAL_CAPABILITIES", "false").lower() == "true":
        messages = [{"role": "system", "content": _multimodal_instructions()}] + messages

    try:
        request_logprobs = cfg.env("CONFIDENCE_ENABLED", "false").lower() == "true"
        aggregation = cfg.env("CONFIDENCE_AGGREGATION", "average")
        content, usage, confidence = await slm_client.chat(
            messages=messages,
            model=model,
            base_url=base_url,
            temperature=temperature,
            request_logprobs=request_logprobs,
            confidence_aggregation=aggregation,
            **(req.overrides.get("kwargs", {}) if req.overrides else {})
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"llm_provider_error: {exc}")

    return {
        "stream": [content],
        "usage": usage,
        "metadata": req.metadata or {},
        "confidence": confidence if request_logprobs else None,
    }
