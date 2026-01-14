"""Completions API - OpenAI-compatible chat completions.


Chat completions with streaming support.

- ML Eng: LLM inference
- PhD Dev: Completion parameters
- DevOps: Streaming, rate limits
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import uuid4

from django.utils import timezone
from ninja import Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer

router = Router(tags=["completions"])
logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS
# =============================================================================


class Message(BaseModel):
    """Chat message."""

    role: str  # system, user, assistant, tool
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None


class CompletionRequest(BaseModel):
    """Chat completion request."""

    model: str
    messages: list[Message]
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: Optional[list[str]] = None
    stream: bool = False


class CompletionChoice(BaseModel):
    """Completion choice."""

    index: int
    message: Message
    finish_reason: str


class CompletionResponse(BaseModel):
    """Chat completion response (OpenAI-compatible)."""

    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[CompletionChoice]
    usage: dict


class UsageStats(BaseModel):
    """Token usage."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


# =============================================================================
# ENDPOINTS - Chat Completions
# =============================================================================


@router.post(
    "/chat",
    response=CompletionResponse,
    summary="Create chat completion",
    auth=AuthBearer(),
)
async def create_chat_completion(
    request,
    model: str,
    messages: list[dict],
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    stream: bool = False,
) -> CompletionResponse:
    """Create a chat completion.

    ML Eng: LLM inference.
    PhD Dev: Completion parameters.
    """
    completion_id = f"chatcmpl-{uuid4().hex[:24]}"

    # In production: call LLM provider

    logger.info(f"Completion: {completion_id}, model={model}")

    return CompletionResponse(
        id=completion_id,
        created=int(timezone.now().timestamp()),
        model=model,
        choices=[
            CompletionChoice(
                index=0,
                message=Message(
                    role="assistant",
                    content="Hello! I'm an AI assistant. How can I help you today?",
                ),
                finish_reason="stop",
            )
        ],
        usage={
            "prompt_tokens": sum(len(m.get("content", "").split()) for m in messages),
            "completion_tokens": 12,
            "total_tokens": sum(len(m.get("content", "").split()) for m in messages) + 12,
        },
    )


@router.get(
    "/chat/stream-info",
    summary="Get stream info",
    auth=AuthBearer(),
)
async def get_stream_info(request) -> dict:
    """Get streaming endpoint info.

    DevOps: SSE streaming config.
    """
    return {
        "stream_url": "/api/v2/completions/chat",
        "protocol": "sse",
        "format": "data: {json}",
    }


# =============================================================================
# ENDPOINTS - Text Completions (Legacy)
# =============================================================================


@router.post(
    "/text",
    summary="Create text completion",
    auth=AuthBearer(),
)
async def create_text_completion(
    request,
    model: str,
    prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 256,
    stop: Optional[list[str]] = None,
) -> dict:
    """Create a text completion (legacy).

    ML Eng: Legacy completion.
    """
    completion_id = f"cmpl-{uuid4().hex[:24]}"

    return {
        "id": completion_id,
        "object": "text_completion",
        "created": int(timezone.now().timestamp()),
        "model": model,
        "choices": [
            {
                "text": "Completed text response.",
                "index": 0,
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": len(prompt.split()),
            "completion_tokens": 4,
            "total_tokens": len(prompt.split()) + 4,
        },
    }


# =============================================================================
# ENDPOINTS - Function Calling
# =============================================================================


@router.post(
    "/chat/functions",
    summary="Chat with functions",
    auth=AuthBearer(),
)
async def create_chat_with_functions(
    request,
    model: str,
    messages: list[dict],
    functions: list[dict],
    function_call: str = "auto",
) -> dict:
    """Chat completion with function calling.

    PhD Dev: Tool use.
    """
    completion_id = f"chatcmpl-{uuid4().hex[:24]}"

    return {
        "id": completion_id,
        "object": "chat.completion",
        "created": int(timezone.now().timestamp()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": None,
                    "function_call": {
                        "name": functions[0]["name"] if functions else "example",
                        "arguments": "{}",
                    },
                },
                "finish_reason": "function_call",
            }
        ],
        "usage": {
            "prompt_tokens": 50,
            "completion_tokens": 10,
            "total_tokens": 60,
        },
    }


# =============================================================================
# ENDPOINTS - JSON Mode
# =============================================================================


@router.post(
    "/chat/json",
    summary="Chat with JSON mode",
    auth=AuthBearer(),
)
async def create_chat_json_mode(
    request,
    model: str,
    messages: list[dict],
    json_schema: Optional[dict] = None,
) -> dict:
    """Chat completion with JSON mode.

    PhD Dev: Structured output.
    """
    completion_id = f"chatcmpl-{uuid4().hex[:24]}"

    return {
        "id": completion_id,
        "object": "chat.completion",
        "created": int(timezone.now().timestamp()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": '{"result": "success", "data": {}}',
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 30,
            "completion_tokens": 8,
            "total_tokens": 38,
        },
    }


# =============================================================================
# ENDPOINTS - Stats
# =============================================================================


@router.get(
    "/stats",
    summary="Get completion stats",
    auth=AuthBearer(),
)
async def get_stats(
    request,
    tenant_id: Optional[str] = None,
) -> dict:
    """Get completion statistics.

    PM: Usage tracking.
    """
    return {
        "total_completions": 0,
        "total_tokens": 0,
        "total_cost": 0.0,
        "avg_latency_ms": 0,
    }
