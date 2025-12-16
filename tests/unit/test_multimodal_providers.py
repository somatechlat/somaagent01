"""Unit tests for multimodal providers (no external calls required).

Tests verify provider interface implementation, validation logic,
cost estimation, and dataclass behavior without external API calls.

Pattern Reference: test_capability_registry.py
"""

import pytest
from uuid import uuid4

from services.multimodal.base_provider import (
    MultimodalProvider,
    GenerationRequest,
    GenerationResult,
    ProviderCapability,
    ProviderError,
    ValidationError,
    RateLimitError,
)
from services.multimodal.mermaid_provider import MermaidProvider
from services.multimodal.dalle_provider import DalleProvider
from services.multimodal.playwright_provider import PlaywrightProvider


def make_request(**kwargs) -> GenerationRequest:
    """Create a test GenerationRequest with defaults."""
    defaults = {
        "tenant_id": "test-tenant",
        "session_id": "session-123",
        "modality": "image",
        "prompt": "Test prompt",
        "format": "png",
    }
    defaults.update(kwargs)
    return GenerationRequest(**defaults)


class TestGenerationRequest:
    """Tests for GenerationRequest dataclass."""

    def test_create_minimal(self):
        req = GenerationRequest(
            tenant_id="test",
            session_id="s1",
            modality="image",
            prompt="A blue sky",
        )
        assert req.tenant_id == "test"
        assert req.prompt == "A blue sky"
        assert req.format == "png"
        assert req.timeout_ms == 60000

    def test_create_full(self):
        req = make_request(
            prompt="Generate a diagram",
            format="svg",
            dimensions={"width": 1024, "height": 768},
            parameters={"style": "vivid"},
        )
        assert req.dimensions["width"] == 1024
        assert req.parameters["style"] == "vivid"


class TestGenerationResult:
    """Tests for GenerationResult dataclass."""

    def test_create_success(self):
        result = GenerationResult(
            success=True,
            content=b"image data",
            content_type="image/png",
            format="png",
            latency_ms=1500,
            cost_cents=50,
            provider="openai",
        )
        assert result.success is True
        assert result.content == b"image data"
        assert result.cost_cents == 50

    def test_create_failure(self):
        result = GenerationResult(
            success=False,
            error_code="TIMEOUT",
            error_message="Request timed out",
            provider="openai",
        )
        assert result.success is False
        assert result.is_retryable is True

    def test_retryable_codes(self):
        retryable = GenerationResult(
            success=False,
            error_code="RATE_LIMIT",
            provider="test",
        )
        assert retryable.is_retryable is True
        
        not_retryable = GenerationResult(
            success=False,
            error_code="VALIDATION_ERROR",
            provider="test",
        )
        assert not_retryable.is_retryable is False


class TestProviderCapability:
    """Tests for ProviderCapability enum."""

    def test_capability_values(self):
        assert ProviderCapability.IMAGE.value == "image"
        assert ProviderCapability.DIAGRAM.value == "diagram"
        assert ProviderCapability.SCREENSHOT.value == "screenshot"
        assert ProviderCapability.VIDEO.value == "video"
        assert ProviderCapability.DOCUMENT.value == "document"


class TestProviderExceptions:
    """Tests for provider exception hierarchy."""

    def test_provider_error(self):
        error = ProviderError("Test error", "openai", "TEST_ERROR", retryable=True)
        assert error.message == "Test error"
        assert error.provider == "openai"
        assert error.error_code == "TEST_ERROR"
        assert error.retryable is True

    def test_validation_error(self):
        error = ValidationError("Invalid size", "openai")
        assert isinstance(error, ProviderError)

    def test_rate_limit_error(self):
        error = RateLimitError("Rate limited", "openai", retry_after_seconds=60)
        assert error.retryable is True
        assert error.retry_after_seconds == 60


class TestMermaidProvider:
    """Tests for MermaidProvider."""

    def test_provider_properties(self):
        provider = MermaidProvider()
        assert provider.name == "mermaid_diagram"
        assert provider.provider_id == "local"
        assert ProviderCapability.DIAGRAM in provider.capabilities
        assert "svg" in provider.supported_formats
        assert "png" in provider.supported_formats

    def test_validate_valid_request(self):
        provider = MermaidProvider()
        request = make_request(
            modality="diagram",
            prompt="graph TD\n  A-->B",
            format="svg",
        )
        errors = provider.validate(request)
        assert errors == []

    def test_validate_empty_prompt(self):
        provider = MermaidProvider()
        request = make_request(prompt="", modality="diagram")
        errors = provider.validate(request)
        assert any("required" in e.lower() for e in errors)

    def test_validate_unsupported_format(self):
        provider = MermaidProvider()
        request = make_request(
            prompt="graph TD\n  A-->B",
            format="gif",  # Unsupported
        )
        errors = provider.validate(request)
        assert any("unsupported" in e.lower() for e in errors)

    def test_estimate_cost_always_free(self):
        provider = MermaidProvider()
        request = make_request(prompt="graph TD\n  A-->B")
        cost = provider.estimate_cost(request)
        assert cost == 0

    def test_detect_diagram_type(self):
        provider = MermaidProvider()
        assert provider._detect_diagram_type("flowchart TD") == "flowchart"
        assert provider._detect_diagram_type("sequenceDiagram") == "sequence"
        assert provider._detect_diagram_type("classDiagram") == "class"
        assert provider._detect_diagram_type("random text") == "unknown"


class TestDalleProvider:
    """Tests for DalleProvider."""

    def test_provider_properties(self):
        provider = DalleProvider()
        assert provider.name == "dalle3_image_gen"
        assert provider.provider_id == "openai"
        assert ProviderCapability.IMAGE in provider.capabilities
        assert "png" in provider.supported_formats

    def test_validate_valid_request(self):
        provider = DalleProvider()
        request = make_request(
            modality="image_photo",
            prompt="A beautiful sunset",
            parameters={"size": "1024x1024", "quality": "standard"},
        )
        errors = provider.validate(request)
        assert errors == []

    def test_validate_invalid_size(self):
        provider = DalleProvider()
        request = make_request(
            prompt="Test",
            parameters={"size": "500x500"},  # Invalid
        )
        errors = provider.validate(request)
        assert any("size" in e.lower() for e in errors)

    def test_validate_invalid_quality(self):
        provider = DalleProvider()
        request = make_request(
            prompt="Test",
            parameters={"quality": "ultra"},  # Invalid
        )
        errors = provider.validate(request)
        assert any("quality" in e.lower() for e in errors)

    def test_validate_prompt_too_long(self):
        provider = DalleProvider()
        request = make_request(prompt="x" * 5000)  # Too long
        errors = provider.validate(request)
        assert any("length" in e.lower() for e in errors)

    def test_estimate_cost_standard(self):
        provider = DalleProvider()
        request = make_request(
            prompt="Test",
            parameters={"size": "1024x1024", "quality": "standard"},
        )
        cost = provider.estimate_cost(request)
        assert cost == 4  # $0.04

    def test_estimate_cost_hd_large(self):
        provider = DalleProvider()
        request = make_request(
            prompt="Test",
            parameters={"size": "1792x1024", "quality": "hd"},
        )
        cost = provider.estimate_cost(request)
        assert cost == 12  # $0.12


class TestPlaywrightProvider:
    """Tests for PlaywrightProvider."""

    def test_provider_properties(self):
        provider = PlaywrightProvider()
        assert provider.name == "playwright_screenshot"
        assert provider.provider_id == "local"
        assert ProviderCapability.SCREENSHOT in provider.capabilities
        assert "png" in provider.supported_formats
        assert "jpeg" in provider.supported_formats

    def test_validate_valid_request(self):
        provider = PlaywrightProvider()
        request = make_request(
            modality="screenshot",
            prompt="https://example.com",
            format="png",
        )
        errors = provider.validate(request)
        assert errors == []

    def test_validate_invalid_url(self):
        provider = PlaywrightProvider()
        request = make_request(
            prompt="not-a-url",
        )
        errors = provider.validate(request)
        assert any("http" in e.lower() for e in errors)

    def test_validate_unsupported_format(self):
        provider = PlaywrightProvider()
        request = make_request(
            prompt="https://example.com",
            format="gif",
        )
        errors = provider.validate(request)
        assert any("unsupported" in e.lower() for e in errors)

    def test_estimate_cost_always_free(self):
        provider = PlaywrightProvider()
        request = make_request(prompt="https://example.com")
        cost = provider.estimate_cost(request)
        assert cost == 0

    def test_model_version(self):
        provider = PlaywrightProvider(browser_type="firefox")
        version = provider.get_model_version()
        assert version == "playwright-firefox"


class TestProviderRepr:
    """Tests for provider string representation."""

    def test_mermaid_repr(self):
        provider = MermaidProvider()
        assert "MermaidProvider" in repr(provider)
        assert "mermaid_diagram" in repr(provider)

    def test_dalle_repr(self):
        provider = DalleProvider()
        assert "DalleProvider" in repr(provider)
        assert "dalle3_image_gen" in repr(provider)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
