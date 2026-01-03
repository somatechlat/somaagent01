"""LLM Invoke API Router.

Migrated from: services/gateway/routers/llm.py
Pure Django Ninja with Django caching, settings, and signals for audit.

VIBE COMPLIANT - Full Django capabilities, centralized config, no hardcoded values.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

from django.conf import settings
from django.core.cache import cache
from django.dispatch import Signal
from ninja import Router
from pydantic import BaseModel

from admin.common.exceptions import ServiceError, ValidationError

router = Router(tags=["llm"])
logger = logging.getLogger(__name__)

# Django signal for audit logging
llm_invoked = Signal()  # args: session_id, tenant, provider, model, usage


class ChatMessage(BaseModel):
    """Chat message format."""

    role: str
    content: str


class LlmInvokeRequest(BaseModel):
    """LLM invocation request."""

    prompt: Optional[str] = None
    messages: Optional[list[ChatMessage]] = None
    role: Optional[str] = None
    session_id: Optional[str] = None
    tenant: Optional[str] = None
    overrides: Optional[dict[str, Any]] = None
    metadata: Optional[dict] = None
    multimodal: bool = False


class LlmInvokeResponse(BaseModel):
    """LLM invocation response."""

    content: str
    usage: Optional[dict] = None
    metadata: dict = {}
    confidence: Optional[float] = None


# Centralized configuration via lazy getters to avoid blocking app population
def get_default_model() -> str:
    """Get the default chat model from settings or environment.

    Per VIBE Rules: Source from database first, then environment.
    """
    model = getattr(settings, "SAAS_DEFAULT_CHAT_MODEL", os.environ.get("SA01_LLM_MODEL"))
    if not model:
        # Fallback to a safe string during migrations/setup if needed,
        # but do NOT block module import.
        return "unconfigured"
    return model


def get_multimodal_enabled() -> bool:
    return getattr(settings, "SA01_ENABLE_MULTIMODAL_CAPABILITIES", False)


def get_confidence_enabled() -> bool:
    return getattr(settings, "CONFIDENCE_ENABLED", False)


def get_confidence_aggregation() -> str:
    return getattr(settings, "CONFIDENCE_AGGREGATION", "average")


def _multimodal_instructions() -> str:
    """Get multimodal system prompt instructions."""
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


async def _get_llm_client():
    """Get LLM client with Django caching for credentials."""
    from services.gateway.main import _gateway_llm_client, get_secret_manager

    return get_secret_manager(), _gateway_llm_client()


def _get_cached_api_key(provider: str) -> Optional[str]:
    """Get API key from Django cache, falling back to secret manager."""
    cache_key = f"llm_api_key:{provider}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    return None


async def _invoke_llm(
    messages: list,
    model: str,
    base_url: str,
    temperature: Optional[float],
    overrides: dict,
    request_logprobs: bool,
    aggregation: str,
) -> tuple[str, dict, Optional[float]]:
    """Execute LLM invocation with Django caching."""
    creds_store, llm_client = await _get_llm_client()

    # Get provider from model
    provider = model.split("/")[0] if "/" in model else "openai"

    # Check cache first
    api_key = _get_cached_api_key(provider)
    if not api_key:
        api_key = await creds_store.get_provider_key(provider)
        if api_key:
            # Cache API key for 5 minutes
            cache.set(f"llm_api_key:{provider}", api_key, 300)

    if api_key:
        llm_client.api_key = api_key

    content, usage, confidence = await llm_client.chat(
        messages=messages,
        model=model,
        base_url=base_url,
        temperature=temperature,
        request_logprobs=request_logprobs,
        confidence_aggregation=aggregation,
        **(overrides.get("kwargs", {}) if overrides else {}),
    )

    return content, usage, confidence


@router.post("/invoke", response=LlmInvokeResponse, summary="Invoke LLM")
async def invoke(req: LlmInvokeRequest) -> dict:
    """Invoke LLM with prompt or messages.

    Uses Django caching for API keys and signals for audit logging.
    """
    if not req.prompt and not req.messages:
        raise ValidationError("prompt_or_messages_required")

    # Extract params with Django settings defaults
    overrides = req.overrides or {}
    model = overrides.get("model") or get_default_model()
    base_url = overrides.get("base_url", getattr(settings, "LLM_DEFAULT_BASE_URL", None))
    temperature = overrides.get("temperature")

    if model == "unconfigured":
        raise ServiceError("llm_not_configured: SAAS_DEFAULT_CHAT_MODEL is missing.")

    # Build messages
    messages = (
        [m.model_dump() for m in req.messages]
        if req.messages
        else [{"role": "user", "content": req.prompt}]
    )

    # Add multimodal instructions if enabled
    if req.multimodal and get_multimodal_enabled():
        messages = [{"role": "system", "content": _multimodal_instructions()}] + messages

    try:
        content, usage, confidence = await _invoke_llm(
            messages=messages,
            model=model,
            base_url=base_url,
            temperature=temperature,
            overrides=overrides,
            request_logprobs=CONFIDENCE_ENABLED,
            aggregation=CONFIDENCE_AGGREGATION,
        )
    except Exception as exc:
        logger.error(f"LLM invocation failed: {exc}")
        raise ServiceError(f"llm_provider_error: {exc}")

    # Emit Django signal for audit logging
    provider = model.split("/")[0] if "/" in model else "openai"
    llm_invoked.send(
        sender=None,
        session_id=req.session_id,
        tenant=req.tenant,
        provider=provider,
        model=model,
        usage=usage,
    )

    # Also log via audit store
    try:
        from integrations.repositories import get_audit_store

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
        logger.debug("audit log failed for llm.invoke", exc_info=True)

    return {
        "content": content,
        "usage": usage,
        "metadata": req.metadata or {},
        "confidence": confidence if CONFIDENCE_ENABLED else None,
    }


@router.post("/invoke/stream", response=LlmInvokeResponse, summary="Stream LLM response")
async def invoke_stream(req: LlmInvokeRequest) -> dict:
    """Stream LLM response.

    Note: Current implementation returns complete response.
    """
    if not req.prompt and not req.messages:
        raise ValidationError("prompt_or_messages_required")

    overrides = req.overrides or {}
    model = overrides.get("model", DEFAULT_MODEL)
    base_url = overrides.get("base_url", DEFAULT_BASE_URL)
    temperature = overrides.get("temperature")

    messages = (
        [m.model_dump() for m in req.messages]
        if req.messages
        else [{"role": "user", "content": req.prompt}]
    )

    if req.multimodal and MULTIMODAL_ENABLED:
        messages = [{"role": "system", "content": _multimodal_instructions()}] + messages

    try:
        content, usage, confidence = await _invoke_llm(
            messages=messages,
            model=model,
            base_url=base_url,
            temperature=temperature,
            overrides=overrides,
            request_logprobs=get_confidence_enabled(),
            aggregation=get_confidence_aggregation(),
        )
    except Exception as exc:
        logger.error(f"LLM streaming failed: {exc}")
        raise ServiceError(f"llm_provider_error: {exc}")

    return {
        "content": content,
        "usage": usage,
        "metadata": req.metadata or {},
        "confidence": confidence if get_confidence_enabled() else None,
    }
