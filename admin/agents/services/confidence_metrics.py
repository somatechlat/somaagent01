"""Prometheus Metrics for Confidence Scoring.

Per Confidence Score Spec T5 (REQ-CONF-008)


- Real Prometheus metrics (no stubs)
- All metrics have tenant, model, endpoint labels
- Integrates with existing observability infrastructure

Exported metrics:
- llm_confidence_histogram: Distribution of confidence scores
- llm_confidence_average: Gauge for average confidence
- llm_confidence_missing_total: Counter for missing logprobs
- llm_confidence_rejected_total: Counter for rejections
"""

import logging
from typing import Optional

from prometheus_client import Counter, Gauge, Histogram

LOGGER = logging.getLogger(__name__)

# Label names for all confidence metrics
CONFIDENCE_LABELS = ("tenant", "model", "endpoint")

# -----------------------------------------------------------------------------
# Histogram: Confidence Score Distribution
# -----------------------------------------------------------------------------

from prometheus_client import REGISTRY


def _get_or_create_metric(cls, name, documentation, **kwargs):
    """Get existing metric from registry or create new one."""
    # Check if metric already exists in registry
    if name in REGISTRY._names_to_collectors:
        return REGISTRY._names_to_collectors[name]

    # Check for Counter suffixes if applicable
    if cls == Counter:
        if f"{name}_total" in REGISTRY._names_to_collectors:
            return REGISTRY._names_to_collectors[f"{name}_total"]

    # If explicit registry was passed (rare), use it, otherwise default
    registry = kwargs.pop("registry", REGISTRY)
    try:
        return cls(name, documentation, registry=registry, **kwargs)
    except ValueError:
        # Race condition or other duplicate error, try to find it again
        if name in registry._names_to_collectors:
            return registry._names_to_collectors[name]
        if cls == Counter and f"{name}_total" in registry._names_to_collectors:
            return registry._names_to_collectors[f"{name}_total"]
        raise


# -----------------------------------------------------------------------------
# Histogram: Confidence Score Distribution
# -----------------------------------------------------------------------------

LLM_CONFIDENCE_HISTOGRAM = _get_or_create_metric(
    Histogram,
    "llm_confidence_histogram",
    "Distribution of LLM confidence scores",
    labelnames=CONFIDENCE_LABELS,
    buckets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
)

# -----------------------------------------------------------------------------
# Gauge: Average Confidence (for dashboards)
# -----------------------------------------------------------------------------

LLM_CONFIDENCE_AVERAGE = _get_or_create_metric(
    Gauge,
    "llm_confidence_average",
    "Average LLM confidence score (sliding window)",
    labelnames=CONFIDENCE_LABELS,
)

# -----------------------------------------------------------------------------
# Counter: Missing Logprobs
# -----------------------------------------------------------------------------

LLM_CONFIDENCE_MISSING_TOTAL = _get_or_create_metric(
    Counter,
    "llm_confidence_missing_total",
    "Total count of LLM responses with missing logprobs",
    labelnames=CONFIDENCE_LABELS,
)

# -----------------------------------------------------------------------------
# Counter: Rejected Responses
# -----------------------------------------------------------------------------

LLM_CONFIDENCE_REJECTED_TOTAL = _get_or_create_metric(
    Counter,
    "llm_confidence_rejected_total",
    "Total count of LLM responses rejected due to low confidence",
    labelnames=CONFIDENCE_LABELS,
)

# -----------------------------------------------------------------------------
# Counter: Flagged Responses
# -----------------------------------------------------------------------------

LLM_CONFIDENCE_FLAGGED_TOTAL = _get_or_create_metric(
    Counter,
    "llm_confidence_flagged_total",
    "Total count of LLM responses flagged with LOW_CONFIDENCE",
    labelnames=CONFIDENCE_LABELS,
)

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------


def record_confidence(
    confidence: Optional[float],
    tenant: str,
    model: str,
    endpoint: str,
) -> None:
    """
    Record a confidence score in metrics.

    Args:
        confidence: Confidence score 0.0-1.0 or None
        tenant: Tenant ID
        model: Model name
        endpoint: API endpoint
    """
    labels = {"tenant": tenant, "model": model, "endpoint": endpoint}

    if confidence is None:
        LLM_CONFIDENCE_MISSING_TOTAL.labels(**labels).inc()
    else:
        # Validate range
        if not 0.0 <= confidence <= 1.0:
            LOGGER.warning(f"Invalid confidence {confidence}, clamping to [0, 1]")
            confidence = max(0.0, min(1.0, confidence))

        LLM_CONFIDENCE_HISTOGRAM.labels(**labels).observe(confidence)
        LLM_CONFIDENCE_AVERAGE.labels(**labels).set(confidence)


def record_missing(
    tenant: str,
    model: str,
    endpoint: str,
) -> None:
    """Record a missing logprobs event."""
    LLM_CONFIDENCE_MISSING_TOTAL.labels(
        tenant=tenant,
        model=model,
        endpoint=endpoint,
    ).inc()


def record_rejection(
    confidence: Optional[float],
    tenant: str,
    model: str,
    endpoint: str,
) -> None:
    """
    Record a confidence rejection.

    Args:
        confidence: The rejected confidence score
        tenant: Tenant ID
        model: Model name
        endpoint: API endpoint
    """
    LLM_CONFIDENCE_REJECTED_TOTAL.labels(
        tenant=tenant,
        model=model,
        endpoint=endpoint,
    ).inc()

    LOGGER.info(
        "Confidence rejected",
        extra={
            "confidence": confidence,
            "tenant": tenant,
            "model": model,
            "endpoint": endpoint,
        },
    )


def record_flag(
    confidence: Optional[float],
    tenant: str,
    model: str,
    endpoint: str,
) -> None:
    """
    Record a confidence flag event.

    Args:
        confidence: The flagged confidence score
        tenant: Tenant ID
        model: Model name
        endpoint: API endpoint
    """
    LLM_CONFIDENCE_FLAGGED_TOTAL.labels(
        tenant=tenant,
        model=model,
        endpoint=endpoint,
    ).inc()