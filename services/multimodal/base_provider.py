"""Base class for multimodal providers.

Defines the abstract interface that all multimodal providers must implement,
including generation, validation, and cost estimation methods.

SRS Reference: Section 16.6 (Execution Engine)
Feature Flag: SA01_ENABLE_multimodal_capabilities
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

__all__ = [
    "MultimodalProvider",
    "GenerationRequest",
    "GenerationResult",
    "ProviderCapability",
    "ProviderError",
    "ValidationError",
    "RateLimitError",
    "QuotaExceededError",
]

logger = logging.getLogger(__name__)


class ProviderError(Exception):
    """Base exception for provider errors."""

    def __init__(
        self,
        message: str,
        provider: str,
        error_code: Optional[str] = None,
        retryable: bool = False,
    ) -> None:
        """Initialize the instance."""

        self.message = message
        self.provider = provider
        self.error_code = error_code
        self.retryable = retryable
        super().__init__(message)


class ValidationError(ProviderError):
    """Raised when request validation fails."""

    pass


class RateLimitError(ProviderError):
    """Raised when provider rate limit is hit."""

    def __init__(
        self,
        message: str,
        provider: str,
        retry_after_seconds: Optional[int] = None,
    ) -> None:
        """Initialize the instance."""

        super().__init__(message, provider, "RATE_LIMIT", retryable=True)
        self.retry_after_seconds = retry_after_seconds


class QuotaExceededError(ProviderError):
    """Raised when provider quota is exceeded."""

    pass


class ProviderCapability(str, Enum):
    """Types of content a provider can generate."""

    IMAGE = "image"
    DIAGRAM = "diagram"
    SCREENSHOT = "screenshot"
    VIDEO = "video"
    DOCUMENT = "document"


@dataclass(slots=True)
class GenerationRequest:
    """Request for multimodal generation.

    Attributes:
        tenant_id: Owning tenant
        session_id: Session context
        request_id: Correlation ID for tracing
        modality: Output type (image, diagram, etc.)
        prompt: Text prompt or code for generation
        format: Output format (png, svg, mp4, etc.)
        dimensions: Optional width/height specification
        quality: Quality preset (low, medium, high, hd)
        style: Style preset or instructions
        parameters: Provider-specific parameters
        timeout_ms: Timeout in milliseconds
        metadata: Additional metadata
    """

    tenant_id: str
    session_id: str
    modality: str
    prompt: str
    request_id: Optional[str] = None
    format: str = "png"
    dimensions: Optional[Dict[str, int]] = None
    quality: str = "medium"
    style: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    timeout_ms: int = 60000
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class GenerationResult:
    """Result of multimodal generation.

    Attributes:
        success: Whether generation succeeded
        content: Generated content bytes
        content_type: MIME type of content
        format: File format (png, svg, etc.)
        dimensions: Actual dimensions if applicable
        latency_ms: Generation latency
        cost_cents: Actual cost in cents (if known)
        provider: Provider used
        model_version: Specific model version
        quality_hints: Hints for quality evaluation
        error_code: Error code if failed
        error_message: Error message if failed
        metadata: Additional result metadata
    """

    success: bool
    content: Optional[bytes] = None
    content_type: Optional[str] = None
    format: Optional[str] = None
    dimensions: Optional[Dict[str, int]] = None
    latency_ms: Optional[int] = None
    cost_cents: Optional[int] = None
    provider: Optional[str] = None
    model_version: Optional[str] = None
    quality_hints: Dict[str, Any] = field(default_factory=dict)
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_retryable(self) -> bool:
        """Check if the error is retryable."""
        retryable_codes = {"TIMEOUT", "RATE_LIMIT", "SERVICE_UNAVAILABLE"}
        return self.error_code in retryable_codes if self.error_code else False


class MultimodalProvider(ABC):
    """Abstract base class for multimodal providers.

    All provider adapters must inherit from this class and implement
    the abstract methods.

    Example:
        class DalleProvider(MultimodalProvider):
            @property
            def name(self) -> str:
                return "dalle3_image_gen"

            @property
            def provider_id(self) -> str:
                return "openai"

            async def generate(self, request: GenerationRequest) -> GenerationResult:
                # Implementation here
                ...
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique provider name (e.g., 'dalle3_image_gen')."""
        ...

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Provider identifier (e.g., 'openai', 'stability', 'local')."""
        ...

    @property
    @abstractmethod
    def capabilities(self) -> List[ProviderCapability]:
        """List of capabilities this provider supports."""
        ...

    @property
    def supported_formats(self) -> List[str]:
        """List of output formats supported."""
        return ["png"]

    @property
    def max_dimensions(self) -> Optional[Dict[str, int]]:
        """Maximum supported dimensions."""
        return None

    @abstractmethod
    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate content from request.

        Args:
            request: Generation request with prompt and parameters

        Returns:
            GenerationResult with content or error details
        """
        ...

    @abstractmethod
    def validate(self, request: GenerationRequest) -> List[str]:
        """Validate request before generation.

        Args:
            request: Request to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        ...

    @abstractmethod
    def estimate_cost(self, request: GenerationRequest) -> int:
        """Estimate cost in cents for the request.

        Args:
            request: Request to estimate

        Returns:
            Estimated cost in cents
        """
        ...

    async def health_check(self) -> bool:
        """Check if the provider is healthy.

        Returns:
            True if provider is available and responding
        """
        return True

    def get_model_version(self) -> Optional[str]:
        """Get current model version if applicable."""
        return None

    def __repr__(self) -> str:
        """Return object representation."""

        return f"<{self.__class__.__name__} name={self.name} provider={self.provider_id}>"