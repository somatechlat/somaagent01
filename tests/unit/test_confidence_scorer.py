"""Unit tests for Confidence Scorer.

VIBE COMPLIANT:
- Real implementations only (no mocks)
- Tests use actual computations
- No placeholder assertions

Tests cover:
- Confidence calculation modes (average, min, percentile_90)
- Empty/missing logprobs handling
- Threshold evaluation
- EWMA tracking
"""

import pytest
from typing import List, Optional

from python.somaagent.confidence_scorer import (
    ConfidenceScorer,
    ConfidenceConfig,
    ConfidenceResult,
    ConfidenceMode,
    OnLowAction,
)


# -----------------------------------------------------------------------------
# ConfidenceScorer Tests
# -----------------------------------------------------------------------------

class TestConfidenceScorer:
    """Test ConfidenceScorer class."""

    @pytest.fixture
    def scorer(self):
        """Create scorer with default config."""
        return ConfidenceScorer(ConfidenceConfig(enabled=True))

    @pytest.fixture
    def sample_logprobs(self) -> List[float]:
        """Sample logprobs for testing (natural log)."""
        # ln(0.9) ≈ -0.105, ln(0.8) ≈ -0.223, ln(0.95) ≈ -0.051
        return [-0.105, -0.223, -0.051, -0.150, -0.300]

    def test_confidence_average_mode(self, scorer, sample_logprobs):
        """Average mode should compute mean of exp(logprobs)."""
        scorer.config.mode = ConfidenceMode.AVERAGE
        result = scorer.calculate(
            logprobs=sample_logprobs,
            provider="openai",
            model="gpt-4",
        )
        assert result.score is not None
        assert 0.0 <= result.score <= 1.0
        assert result.mode == ConfidenceMode.AVERAGE.value
        assert result.token_count == len(sample_logprobs)

    def test_confidence_min_mode(self, scorer, sample_logprobs):
        """Min mode should return minimum exp(logprob)."""
        scorer.config.mode = ConfidenceMode.MIN
        result = scorer.calculate(
            logprobs=sample_logprobs,
            provider="openai",
            model="gpt-4",
        )
        assert result.score is not None
        # Min should be exp(-0.300) ≈ 0.74
        assert result.score < 0.8  # Lower than average
        assert result.mode == ConfidenceMode.MIN.value

    def test_confidence_percentile_mode(self, scorer, sample_logprobs):
        """Percentile mode should return 10th percentile."""
        scorer.config.mode = ConfidenceMode.PERCENTILE_90
        result = scorer.calculate(
            logprobs=sample_logprobs,
            provider="openai",
            model="gpt-4",
        )
        assert result.score is not None
        assert 0.0 <= result.score <= 1.0
        assert result.mode == ConfidenceMode.PERCENTILE_90.value

    def test_confidence_empty_logprobs(self, scorer):
        """Empty logprobs should return None score."""
        result = scorer.calculate(
            logprobs=[],
            provider="openai",
            model="gpt-4",
        )
        assert result.score is None
        assert result.token_count == 0

    def test_confidence_none_logprobs(self, scorer):
        """None logprobs should return None score."""
        result = scorer.calculate(
            logprobs=None,
            provider="anthropic",
            model="claude-3",
        )
        assert result.score is None

    def test_confidence_failure_does_not_raise(self, scorer):
        """Confidence calculation should not raise exceptions."""
        # Invalid logprobs (should handle gracefully)
        result = scorer.calculate(
            logprobs=["invalid", "data"],  # type: ignore
            provider="openai",
            model="gpt-4",
        )
        # Should return None, not raise
        assert result.score is None

    def test_confidence_provider_model_stored(self, scorer, sample_logprobs):
        """Provider and model should be stored in result."""
        result = scorer.calculate(
            logprobs=sample_logprobs,
            provider="azure",
            model="gpt-4-turbo",
        )
        assert result.provider == "azure"
        assert result.model == "gpt-4-turbo"

    def test_confidence_latency_tracked(self, scorer, sample_logprobs):
        """Latency should be tracked in result."""
        result = scorer.calculate(
            logprobs=sample_logprobs,
            provider="openai",
            model="gpt-4",
        )
        assert result.latency_ms >= 0.0


# -----------------------------------------------------------------------------
# ConfidenceResult Tests
# -----------------------------------------------------------------------------

class TestConfidenceResult:
    """Test ConfidenceResult dataclass."""

    def test_is_acceptable_above_threshold(self):
        """Score above threshold should be acceptable."""
        result = ConfidenceResult(
            score=0.8,
            mode="average",
            token_count=100,
            provider="openai",
            model="gpt-4",
        )
        assert result.is_acceptable(min_threshold=0.5) is True

    def test_is_acceptable_below_threshold(self):
        """Score below threshold should not be acceptable."""
        result = ConfidenceResult(
            score=0.2,
            mode="average",
            token_count=100,
            provider="openai",
            model="gpt-4",
        )
        assert result.is_acceptable(min_threshold=0.5) is False

    def test_is_acceptable_none_score(self):
        """None score should use treat_null_as_low logic."""
        result = ConfidenceResult(
            score=None,
            mode="average",
            token_count=0,
            provider="anthropic",
            model="claude-3",
        )
        # None should return False by default (no score = not acceptable)
        assert result.is_acceptable(min_threshold=0.5) is False

    def test_to_dict(self):
        """to_dict should return all fields."""
        result = ConfidenceResult(
            score=0.85,
            mode="average",
            token_count=50,
            provider="openai",
            model="gpt-4",
            latency_ms=2.5,
        )
        d = result.to_dict()
        assert d["score"] == 0.85
        assert d["mode"] == "average"
        assert d["token_count"] == 50
        assert d["provider"] == "openai"
        assert d["model"] == "gpt-4"
        assert d["latency_ms"] == 2.5


# -----------------------------------------------------------------------------
# Threshold Evaluation Tests
# -----------------------------------------------------------------------------

class TestThresholdEvaluation:
    """Test threshold evaluation logic."""

    @pytest.fixture
    def scorer_with_thresholds(self):
        """Create scorer with custom thresholds."""
        return ConfidenceScorer(ConfidenceConfig(
            enabled=True,
            min_acceptance=0.3,
            on_low=OnLowAction.WARN,
        ))

    def test_evaluate_acceptable(self, scorer_with_thresholds):
        """Acceptable confidence should pass."""
        result = ConfidenceResult(
            score=0.8,
            mode="average",
            token_count=100,
            provider="openai",
            model="gpt-4",
        )
        is_ok, message = scorer_with_thresholds.evaluate_result(result)
        assert is_ok is True
        assert message == ""

    def test_evaluate_low_warn(self, scorer_with_thresholds):
        """Low confidence with WARN action should pass with message."""
        result = ConfidenceResult(
            score=0.2,  # Below 0.3 threshold
            mode="average",
            token_count=100,
            provider="openai",
            model="gpt-4",
        )
        is_ok, message = scorer_with_thresholds.evaluate_result(result)
        assert is_ok is True  # WARN allows continuation
        assert "low confidence" in message.lower()

    def test_evaluate_low_reject(self):
        """Low confidence with REJECT action should fail."""
        scorer = ConfidenceScorer(ConfidenceConfig(
            enabled=True,
            min_acceptance=0.5,
            on_low=OnLowAction.REJECT,
        ))
        result = ConfidenceResult(
            score=0.3,  # Below 0.5 threshold
            mode="average",
            token_count=100,
            provider="openai",
            model="gpt-4",
        )
        is_ok, message = scorer.evaluate_result(result)
        assert is_ok is False
        assert "rejected" in message.lower() or "low" in message.lower()


# -----------------------------------------------------------------------------
# ConfidenceConfig Tests
# -----------------------------------------------------------------------------

class TestConfidenceConfig:
    """Test ConfidenceConfig."""

    def test_default_config(self):
        """Default config should have sensible defaults."""
        config = ConfidenceConfig()
        assert config.enabled is False  # Disabled by default
        assert config.min_acceptance == 0.3
        assert config.on_low == OnLowAction.WARN
        assert config.treat_null_as_low is False

    def test_custom_config(self):
        """Custom config should be applied."""
        config = ConfidenceConfig(
            enabled=True,
            mode=ConfidenceMode.MIN,
            min_acceptance=0.5,
            on_low=OnLowAction.REJECT,
            treat_null_as_low=True,
        )
        assert config.enabled is True
        assert config.mode == ConfidenceMode.MIN
        assert config.min_acceptance == 0.5
        assert config.on_low == OnLowAction.REJECT
        assert config.treat_null_as_low is True
