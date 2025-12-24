"""LLM app - Django-compliant LLM wrappers and services.

Migrated from root models.py per VIBE Rule 8 (Django capabilities ONLY).
"""

from admin.llm.models import ModelType, ModelConfig
from admin.llm.exceptions import LLMNotConfiguredError
from admin.llm.services import (
    LiteLLMChatWrapper,
    BrowserCompatibleChatWrapper,
    ChatGenerationResult,
    ChatChunk,
    get_api_key,
    get_rate_limiter,
    apply_rate_limiter,
    apply_rate_limiter_sync,
    turn_off_logging,
)

__all__ = [
    # Models
    "ModelType",
    "ModelConfig",
    # Exceptions
    "LLMNotConfiguredError",
    # Services
    "LiteLLMChatWrapper",
    "BrowserCompatibleChatWrapper",
    "ChatGenerationResult",
    "ChatChunk",
    "get_api_key",
    "get_rate_limiter",
    "apply_rate_limiter",
    "apply_rate_limiter_sync",
    "turn_off_logging",
]
