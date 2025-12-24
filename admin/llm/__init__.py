"""LLM app - Django-compliant LLM wrappers and services.

Migrated from root models.py per VIBE Rule 8 (Django capabilities ONLY).
Uses lazy imports for Django models to avoid AppRegistryNotReady errors.
"""


def _get_model_type():
    """Lazy import ModelType to avoid circular imports."""
    from admin.llm.models import ModelType
    return ModelType


def _get_model_config():
    """Lazy import LLMModelConfig to avoid circular imports."""
    from admin.llm.models import LLMModelConfig
    return LLMModelConfig


# Import non-model items directly (safe - no Django model registration)
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


# Lazy property accessors for Django models
class _LazyModelAccessor:
    """Provides lazy access to Django models to avoid registry issues."""
    
    @property
    def ModelType(self):
        return _get_model_type()
    
    @property
    def ModelConfig(self):
        return _get_model_config()
    
    @property  
    def LLMModelConfig(self):
        return _get_model_config()


_lazy = _LazyModelAccessor()

# Re-export for backward compatibility
ModelType = property(fget=lambda self: _get_model_type())
ModelConfig = property(fget=lambda self: _get_model_config())

__all__ = [
    # Models (lazy loaded)
    "ModelType",
    "ModelConfig", 
    "LLMModelConfig",
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
