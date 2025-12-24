"""Confidence Scorer - LLM response confidence calculation from logprobs.

Production-grade confidence scoring with multiple calculation modes.
Target latency: ≤5ms. Failure does NOT abort response.

VIBE COMPLIANT:
- Real implementations only (no mocks, no placeholders)
- Graceful degradation on missing logprobs
- Safe calculation that never raises
"""

from __future__ import annotations

import logging
import math
import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

LOGGER = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Feature Flag Helper
# -----------------------------------------------------------------------------

def is_confidence_enabled() -> bool:
    """Check if Confidence Scoring is enabled via feature flag.
    
    Checks SA01_ENABLE_CONFIDENCE_SCORING environment variable.
    Default: disabled (False).
    """
    val = os.environ.get("SA01_ENABLE_CONFIDENCE_SCORING", "false")
    return val.lower() in ("true", "1", "yes", "on")


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

class ConfidenceMode(str, Enum):
    """Confidence calculation mode."""
    AVERAGE = "average"
    MIN = "min"
    PERCENTILE_90 = "percentile_90"


class OnLowAction(str, Enum):
    """Action to take when confidence is below threshold."""
    WARN = "warn"
    RETRY = "retry"
    REJECT = "reject"


class ConfidenceConfig(BaseModel):
    """Configuration for confidence scoring."""
    enabled: bool = Field(default=False, description="Feature flag for confidence scoring")
    mode: ConfidenceMode = Field(default=ConfidenceMode.AVERAGE, description="Calculation mode")
    min_acceptance: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Minimum acceptable confidence score",
    )
    on_low: OnLowAction = Field(
        default=OnLowAction.WARN,
        description="Action when confidence is below min_acceptance",
    )
    treat_null_as_low: bool = Field(
        default=False,
        description="Treat missing logprobs as low confidence",
    )


# -----------------------------------------------------------------------------
# Data Classes
# -----------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class ConfidenceResult:
    """Result of confidence calculation.
    
    Attributes:
        score: Confidence score 0.0-1.0, or None if unavailable
        mode: Calculation mode used
        token_count: Number of tokens with logprobs
        provider: LLM provider name
        model: Model name
        latency_ms: Calculation latency in milliseconds
    """
    score: Optional[float]
    mode: ConfidenceMode
    token_count: int
    provider: str
    model: str
    latency_ms: float = 0.0

    def is_acceptable(self, min_threshold: float) -> bool:
        """Check if confidence meets minimum threshold."""
        if self.score is None:
            return True  # Missing confidence is acceptable by default
        return self.score >= min_threshold

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "score": self.score,
            "mode": self.mode.value,
            "token_count": self.token_count,
            "provider": self.provider,
            "model": self.model,
            "latency_ms": self.latency_ms,
        }


# -----------------------------------------------------------------------------
# Confidence Scorer
# -----------------------------------------------------------------------------

class ConfidenceScorer:
    """Calculates confidence scores from LLM logprobs.
    
    Supports three calculation modes:
    - average: mean(exp(logprobs)) - balanced view
    - min: min(exp(logprobs)) - most conservative
    - percentile_90: 10th percentile of exp(logprobs) - robust to outliers
    
    VIBE COMPLIANT:
    - Real implementation (no mocks)
    - Safe calculation that never raises
    - Graceful handling of missing/empty logprobs
    """

    def __init__(self, config: Optional[ConfidenceConfig] = None) -> None:
        self.config = config or ConfidenceConfig()

    def calculate(
        self,
        logprobs: Optional[List[float]],
        provider: str,
        model: str,
    ) -> ConfidenceResult:
        """Calculate confidence score from logprobs.
        
        Args:
            logprobs: List of log probabilities (natural log)
            provider: LLM provider name (e.g., "openai", "azure")
            model: Model name (e.g., "gpt-4")
            
        Returns:
            ConfidenceResult with score (0.0-1.0) or None if unavailable
            
        Note:
            This method NEVER raises exceptions. All errors are logged
            and result in None confidence score.
        """
        start_time = time.perf_counter()

        try:
            score = self._calculate_score(logprobs)
            latency_ms = (time.perf_counter() - start_time) * 1000

            return ConfidenceResult(
                score=score,
                mode=self.config.mode,
                token_count=len(logprobs) if logprobs else 0,
                provider=provider,
                model=model,
                latency_ms=latency_ms,
            )

        except Exception as e:
            LOGGER.warning(
                "Confidence calculation failed",
                extra={"error": str(e), "provider": provider, "model": model},
            )
            latency_ms = (time.perf_counter() - start_time) * 1000
            return ConfidenceResult(
                score=None,
                mode=self.config.mode,
                token_count=0,
                provider=provider,
                model=model,
                latency_ms=latency_ms,
            )

    def _calculate_score(self, logprobs: Optional[List[float]]) -> Optional[float]:
        """Internal score calculation.
        
        Converts logprobs to probabilities and applies the configured mode.
        """
        if not logprobs:
            return None

        # Convert log probabilities to probabilities
        # logprob is natural log, so exp(logprob) gives probability
        probabilities = []
        for lp in logprobs:
            if lp is None:
                continue
            try:
                # Clamp to avoid overflow/underflow
                clamped = max(-100.0, min(0.0, float(lp)))
                prob = math.exp(clamped)
                probabilities.append(prob)
            except (ValueError, OverflowError):
                continue

        if not probabilities:
            return None

        # Apply calculation mode
        if self.config.mode == ConfidenceMode.AVERAGE:
            return sum(probabilities) / len(probabilities)

        elif self.config.mode == ConfidenceMode.MIN:
            return min(probabilities)

        elif self.config.mode == ConfidenceMode.PERCENTILE_90:
            # 10th percentile (90% of values are above this)
            return self._percentile(probabilities, 10)

        return None

    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of a list of values.
        
        Args:
            values: List of numeric values
            percentile: Percentile to calculate (0-100)
            
        Returns:
            Value at the given percentile
        """
        if not values:
            return 0.0

        sorted_values = sorted(values)
        n = len(sorted_values)

        # Calculate index
        k = (percentile / 100.0) * (n - 1)
        f = math.floor(k)
        c = math.ceil(k)

        if f == c:
            return sorted_values[int(k)]

        # Linear interpolation
        d0 = sorted_values[int(f)] * (c - k)
        d1 = sorted_values[int(c)] * (k - f)
        return d0 + d1

    def evaluate_result(self, result: ConfidenceResult) -> tuple[bool, Optional[str]]:
        """Evaluate confidence result against threshold.
        
        Args:
            result: ConfidenceResult from calculate()
            
        Returns:
            Tuple of (is_acceptable, action_message)
            - is_acceptable: True if confidence meets threshold
            - action_message: Message describing action taken (if any)
        """
        # Handle missing confidence
        if result.score is None:
            if self.config.treat_null_as_low:
                return False, "Confidence unavailable, treating as low"
            return True, None

        # Check threshold
        if result.score >= self.config.min_acceptance:
            return True, None

        # Below threshold - determine action
        action = self.config.on_low

        if action == OnLowAction.WARN:
            LOGGER.warning(
                "Low confidence score",
                extra={
                    "score": result.score,
                    "threshold": self.config.min_acceptance,
                    "provider": result.provider,
                    "model": result.model,
                },
            )
            return True, f"Low confidence ({result.score:.3f}), continuing with warning"

        elif action == OnLowAction.RETRY:
            return False, f"Low confidence ({result.score:.3f}), retry recommended"

        elif action == OnLowAction.REJECT:
            return False, f"Low confidence ({result.score:.3f}), response rejected"

        return True, None


# -----------------------------------------------------------------------------
# EWMA Tracker for confidence trends
# -----------------------------------------------------------------------------

class ConfidenceEWMA:
    """Exponentially Weighted Moving Average tracker for confidence scores.
    
    Tracks confidence trends over time for alerting and monitoring.
    """

    def __init__(self, alpha: float = 0.1) -> None:
        """Initialize EWMA tracker.
        
        Args:
            alpha: Smoothing factor (0-1). Higher = more weight on recent values.
        """
        self.alpha = alpha
        self._value: Optional[float] = None
        self._count: int = 0

    def update(self, score: float) -> float:
        """Update EWMA with new score.
        
        Args:
            score: New confidence score (0.0-1.0)
            
        Returns:
            Updated EWMA value
        """
        if self._value is None:
            self._value = score
        else:
            self._value = self.alpha * score + (1 - self.alpha) * self._value

        self._count += 1
        return self._value

    @property
    def value(self) -> Optional[float]:
        """Current EWMA value."""
        return self._value

    @property
    def count(self) -> int:
        """Number of samples processed."""
        return self._count

    def reset(self) -> None:
        """Reset tracker to initial state."""
        self._value = None
        self._count = 0


# -----------------------------------------------------------------------------
# Safe wrapper for production use
# -----------------------------------------------------------------------------

def calculate_confidence_safe(
    logprobs: Optional[List[float]],
    provider: str,
    model: str,
    config: Optional[ConfidenceConfig] = None,
) -> ConfidenceResult:
    """Safe confidence calculation that never raises.
    
    This is the recommended entry point for production use.
    
    Args:
        logprobs: List of log probabilities
        provider: LLM provider name
        model: Model name
        config: Optional configuration
        
    Returns:
        ConfidenceResult (score may be None on failure)
    """
    try:
        scorer = ConfidenceScorer(config)
        return scorer.calculate(logprobs, provider, model)
    except Exception as e:
        LOGGER.warning("Confidence calculation failed completely", extra={"error": str(e)})
        return ConfidenceResult(
            score=None,
            mode=config.mode if config else ConfidenceMode.AVERAGE,
            token_count=0,
            provider=provider,
            model=model,
            latency_ms=0.0,
        )


__all__ = [
    # Configuration
    "ConfidenceConfig",
    "ConfidenceMode",
    "OnLowAction",
    # Data classes
    "ConfidenceResult",
    # Core classes
    "ConfidenceScorer",
    "ConfidenceEWMA",
    # Functions
    "calculate_confidence_safe",
]
