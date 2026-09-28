"""Completions API - OpenAI-compatible chat completions.


Chat completions with streaming support.

- ML Eng: LLM inference
- PhD Dev: Completion parameters
- DevOps: Streaming, rate limits
"""

from __future__ import annotations

import logging
from typing import Optional

from ninja import Router
from ninja.errors import HttpError
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
    raise HttpError(
        501,
        "Chat completion is not implemented on this endpoint. "
        "Use the V3 chat orchestrator / WS chat path for real LLM inference.",
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
    raise HttpError(
        501,
        "Text completion is not implemented on this endpoint. "
        "Use the V3 chat orchestrator / WS chat path for real LLM inference.",
    )


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
    raise HttpError(
        501,
        "Function-calling completion is not implemented on this endpoint. "
        "Use the V3 chat orchestrator tool path.",
    )


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
    raise HttpError(
        501,
        "JSON-mode completion is not implemented on this endpoint. "
        "Use the V3 chat orchestrator / WS chat path for real LLM inference.",
    )


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
    # Real empty state: no completion usage store is wired to this endpoint.
    return {
        "total_completions": 0,
        "total_tokens": 0,
        "total_cost": 0.0,
        "avg_latency_ms": 0,
    }
