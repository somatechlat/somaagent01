"""Multimodal provider adapters.

This package contains provider implementations for various multimodal
generation capabilities including images, diagrams, screenshots, and video.

Usage:
    from services.multimodal import (
        MermaidProvider,
        DalleProvider,
        PlaywrightProvider,
    )

    # Diagram generation
    provider = MermaidProvider()
    result = await provider.generate(request)

    # Image generation — the provider key comes from the agent's model
    # administration (Vault secret/agent/api_keys/openai_api_key). No env var.
    provider = DalleProvider()
    result = await provider.generate(request)

SRS Reference: Section 16.6 (Execution Engine)
Feature Flag: SA01_ENABLE_multimodal_capabilities
"""

from services.multimodal.base_provider import (
    GenerationRequest,
    GenerationResult,
    MultimodalProvider,
    ProviderCapability,
    ProviderError,
    QuotaExceededError,
    RateLimitError,
    ValidationError,
)
from services.multimodal.dalle_provider import DalleProvider
from services.multimodal.mermaid_provider import MermaidProvider
from services.multimodal.playwright_provider import PlaywrightProvider

__all__ = [
    # Base classes
    "MultimodalProvider",
    "GenerationRequest",
    "GenerationResult",
    "ProviderCapability",
    # Exceptions
    "ProviderError",
    "ValidationError",
    "RateLimitError",
    "QuotaExceededError",
    # Providers
    "MermaidProvider",
    "DalleProvider",
    "PlaywrightProvider",
]
