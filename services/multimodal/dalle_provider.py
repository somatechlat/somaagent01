"""OpenAI DALL-E image generation provider.

Generates images using OpenAI's DALL-E 3 API with support for
various sizes, quality presets, and style options.

SRS Reference: Section 16.6.1 (Image Providers)
Feature Flag: SA01_ENABLE_multimodal_capabilities
"""

from __future__ import annotations

import logging
import os
import time
from typing import Dict, List, Optional

import httpx

from services.multimodal.base_provider import (
    GenerationRequest,
    GenerationResult,
    MultimodalProvider,
    ProviderCapability,
    QuotaExceededError,
    RateLimitError,
)

__all__ = ["DalleProvider"]

logger = logging.getLogger(__name__)


class DalleProvider(MultimodalProvider):
    """Provider for OpenAI DALL-E image generation.

    Uses the OpenAI Images API to generate images from text prompts.
    Supports DALL-E 3 with various size and quality options.

    Environment:
        OPENAI_API_KEY: Required API key

    Usage:
        provider = DalleProvider()
        result = await provider.generate(GenerationRequest(
            tenant_id="acme",
            session_id="s1",
            modality="image_photo",
            prompt="A serene mountain landscape at sunset",
            parameters={"size": "1024x1024", "quality": "hd"},
        ))
    """

    # DALL-E 3 supported sizes
    SIZES = ["1024x1024", "1792x1024", "1024x1792"]

    # Quality options
    QUALITIES = ["standard", "hd"]

    # Style options
    STYLES = ["vivid", "natural"]

    # Cost estimates in cents (approximate)
    COST_PER_IMAGE = {
        ("standard", "1024x1024"): 4,  # $0.04
        ("standard", "1792x1024"): 8,  # $0.08
        ("standard", "1024x1792"): 8,  # $0.08
        ("hd", "1024x1024"): 8,  # $0.08
        ("hd", "1792x1024"): 12,  # $0.12
        ("hd", "1024x1792"): 12,  # $0.12
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "dall-e-3",
        timeout_seconds: int = 60,
    ) -> None:
        """Initialize DALL-E provider.

        Args:
            api_key: OpenAI API key. Uses env var if not provided.
            model: Model to use (dall-e-3 or dall-e-2).
            timeout_seconds: Request timeout.
        """
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._model = model
        self._timeout = timeout_seconds
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def name(self) -> str:
        """Execute name."""

        return "dalle3_image_gen"

    @property
    def provider_id(self) -> str:
        """Execute provider id."""

        return "openai"

    @property
    def capabilities(self) -> List[ProviderCapability]:
        """Execute capabilities."""

        return [ProviderCapability.IMAGE]

    @property
    def supported_formats(self) -> List[str]:
        """Execute supported formats."""

        return ["png"]

    @property
    def max_dimensions(self) -> Optional[Dict[str, int]]:
        """Execute max dimensions."""

        return {"width": 1792, "height": 1792}

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate an image using DALL-E.

        Args:
            request: Generation request with prompt

        Returns:
            GenerationResult with PNG image data
        """
        start_time = time.time()

        # Check API key
        if not self._api_key:
            return GenerationResult(
                success=False,
                error_code="NO_API_KEY",
                error_message="OPENAI_API_KEY not configured",
                provider=self.provider_id,
            )

        # Validate first
        errors = self.validate(request)
        if errors:
            return GenerationResult(
                success=False,
                error_code="VALIDATION_ERROR",
                error_message="; ".join(errors),
                provider=self.provider_id,
            )

        # Extract parameters
        size = request.parameters.get("size", "1024x1024")
        quality = request.parameters.get("quality", "standard")
        style = request.parameters.get("style", "vivid")

        try:
            client = await self._get_client()

            payload = {
                "model": self._model,
                "prompt": request.prompt,
                "n": 1,
                "size": size,
                "quality": quality,
                "style": style,
                "response_format": "b64_json",
            }

            logger.info(
                "Calling DALL-E API: model=%s, size=%s, quality=%s", self._model, size, quality
            )

            response = await client.post(
                "https://api.openai.com/v1/images/generations",
                json=payload,
            )

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                raise RateLimitError(
                    "DALL-E rate limit exceeded",
                    self.provider_id,
                    retry_after_seconds=int(retry_after) if retry_after else 60,
                )

            if response.status_code == 402 or "insufficient_quota" in response.text:
                raise QuotaExceededError(
                    "OpenAI quota exceeded",
                    self.provider_id,
                )

            if response.status_code != 200:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("error", {}).get("message", response.text)
                return GenerationResult(
                    success=False,
                    error_code=f"API_ERROR_{response.status_code}",
                    error_message=error_msg,
                    provider=self.provider_id,
                )

            # Parse response
            data = response.json()
            image_data = data["data"][0]

            # Decode base64 image
            import base64

            content = base64.b64decode(image_data["b64_json"])

            latency_ms = int((time.time() - start_time) * 1000)
            cost_cents = self.COST_PER_IMAGE.get((quality, size), 8)

            # Extract dimensions from size
            width, height = map(int, size.split("x"))

            logger.info(
                "Generated DALL-E image: %d bytes, %dms, %d cents",
                len(content),
                latency_ms,
                cost_cents,
            )

            return GenerationResult(
                success=True,
                content=content,
                content_type="image/png",
                format="png",
                dimensions={"width": width, "height": height},
                latency_ms=latency_ms,
                cost_cents=cost_cents,
                provider=self.provider_id,
                model_version=self._model,
                quality_hints={
                    "revised_prompt": image_data.get("revised_prompt"),
                    "quality": quality,
                    "style": style,
                },
            )

        except (RateLimitError, QuotaExceededError):
            raise
        except httpx.TimeoutException:
            return GenerationResult(
                success=False,
                error_code="TIMEOUT",
                error_message=f"DALL-E request timed out after {self._timeout}s",
                provider=self.provider_id,
            )
        except Exception as exc:
            logger.exception("DALL-E generation failed: %s", exc)
            return GenerationResult(
                success=False,
                error_code="INTERNAL_ERROR",
                error_message=str(exc),
                provider=self.provider_id,
            )

    def validate(self, request: GenerationRequest) -> List[str]:
        """Validate DALL-E generation request."""
        errors: List[str] = []

        if not request.prompt:
            errors.append("Prompt is required")
            return errors

        if len(request.prompt) > 4000:
            errors.append("Prompt exceeds maximum length of 4000 characters")

        # Validate size
        size = request.parameters.get("size", "1024x1024")
        if size not in self.SIZES:
            errors.append(f"Invalid size: {size}. Supported: {self.SIZES}")

        # Validate quality
        quality = request.parameters.get("quality", "standard")
        if quality not in self.QUALITIES:
            errors.append(f"Invalid quality: {quality}. Supported: {self.QUALITIES}")

        # Validate style
        style = request.parameters.get("style", "vivid")
        if style not in self.STYLES:
            errors.append(f"Invalid style: {style}. Supported: {self.STYLES}")

        return errors

    def estimate_cost(self, request: GenerationRequest) -> int:
        """Estimate cost in cents for DALL-E generation."""
        size = request.parameters.get("size", "1024x1024")
        quality = request.parameters.get("quality", "standard")
        return self.COST_PER_IMAGE.get((quality, size), 8)

    async def health_check(self) -> bool:
        """Check if OpenAI API is accessible."""
        if not self._api_key:
            return False

        try:
            client = await self._get_client()
            response = await client.get(
                "https://api.openai.com/v1/models",
                timeout=5.0,
            )
            return response.status_code == 200
        except Exception:
            return False

    def get_model_version(self) -> Optional[str]:
        """Get current model version."""
        return self._model

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
