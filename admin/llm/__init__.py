"""LLM app - Django-compliant LLM wrappers and services.

Migrated from root models.py per
Uses lazy imports for Django models to avoid AppRegistryNotReady errors.
"""

from __future__ import annotations


def _get_model_type():
    """Lazy import ModelType to avoid circular imports."""
    from admin.llm.models import ModelType

    return ModelType


def _get_model_config():
    """Lazy import LLMModelConfig to avoid circular imports."""
    from admin.llm.models import LLMModelConfig

    return LLMModelConfig


# Lazy service imports
def get_litellm_chat_wrapper():
    """Lazy import LiteLLMChatWrapper."""
    from admin.llm.services.litellm_client import LiteLLMChatWrapper

    return LiteLLMChatWrapper


def get_browser_compatible_chat_wrapper():
    """Lazy import BrowserCompatibleChatWrapper."""
    from admin.llm.services.litellm_client import BrowserCompatibleChatWrapper

    return BrowserCompatibleChatWrapper


def get_chat_generation_result():
    """Lazy import ChatGenerationResult."""
    from admin.llm.services.litellm_client import ChatGenerationResult

    return ChatGenerationResult


def get_chat_chunk():
    """Lazy import ChatChunk."""
    from admin.llm.services.litellm_client import ChatChunk

    return ChatChunk


def get_api_key(service: str) -> str:
    """Lazy import and call get_api_key."""
    from admin.llm.services.litellm_client import get_api_key as _get_api_key

    return _get_api_key(service)


def get_rate_limiter(provider: str, name: str, requests: int, input: int, output: int):
    """Lazy import and call get_rate_limiter."""
    from admin.llm.services.litellm_client import get_rate_limiter as _get_rate_limiter

    return _get_rate_limiter(provider, name, requests, input, output)


def turn_off_logging():
    """Lazy import and call turn_off_logging."""
    from admin.llm.services.litellm_client import turn_off_logging as _turn_off_logging

    return _turn_off_logging()


# Exception import (safe - no Django model registration)
from admin.llm.exceptions import LLMNotConfiguredError


# Lazy property accessors for Django models
class _LazyModelAccessor:
    """Provides lazy access to Django models to avoid registry issues."""

    @property
    def ModelType(self):
        """Execute ModelType."""

        return _get_model_type()

    @property
    def ModelConfig(self):
        """Execute ModelConfig."""

        return _get_model_config()

    @property
    def LLMModelConfig(self):
        """Execute LLMModelConfig."""

        return _get_model_config()


_lazy = _LazyModelAccessor()

__all__ = [
    # Models (lazy loaded via functions)
    "_get_model_type",
    "_get_model_config",
    # Exceptions
    "LLMNotConfiguredError",
    # Services (lazy loaded via functions)
    "get_litellm_chat_wrapper",
    "get_browser_compatible_chat_wrapper",
    "get_chat_generation_result",
    "get_chat_chunk",
    "get_api_key",
    "get_rate_limiter",
    "turn_off_logging",
]
