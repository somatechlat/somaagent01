"""AgentIQ Prometheus Metrics - Observability for Governor and Confidence Scoring.

Production-grade metrics for AIQ scores, lane utilization, degradation levels,
and LLM confidence tracking.


- Real Prometheus metrics (no mocks)
- Uses existing observability/metrics.py wrappers
- Consistent labeling with rest of system
"""

from __future__ import annotations

from admin.core.observability.metrics import Counter, Gauge, Histogram, registry

# -----------------------------------------------------------------------------
# AgentIQ Governor Metrics
# -----------------------------------------------------------------------------

# AIQ Score Histograms
AGENTIQ_AIQ_PRED = Histogram(
    "agentiq_aiq_pred",
    "Predicted AIQ score distribution (0-100)",
    labelnames=("tenant_id",),
    buckets=[10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
    registry=registry,
)

AGENTIQ_AIQ_OBS = Histogram(
    "agentiq_aiq_obs",
    "Observed AIQ score distribution (0-100)",
    labelnames=("tenant_id",),
    buckets=[10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
    registry=registry,
)

# Governor Latency
AGENTIQ_GOVERNOR_LATENCY = Histogram(
    "agentiq_governor_latency_seconds",
    "Governor computation latency in seconds",
    labelnames=("tenant_id",),
    buckets=[0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1],
    registry=registry,
)

# Degradation Level Gauge
AGENTIQ_DEGRADATION_LEVEL = Gauge(
    "agentiq_degradation_level",
    "Current degradation level (0=none, 1=minor, 2=moderate, 3=severe, 4=critical)",
    labelnames=("tenant_id",),
    registry=registry,
)

# Path Mode Counter
AGENTIQ_PATH_MODE = Counter(
    "agentiq_path_mode_total",
    "Path mode selections",
    labelnames=("mode", "tenant_id"),
    registry=registry,
)

# Lane Utilization Gauges
AGENTIQ_LANE_BUDGET = Gauge(
    "agentiq_lane_budget_tokens",
    "Token budget allocated per lane",
    labelnames=("lane", "tenant_id"),
    registry=registry,
)

AGENTIQ_LANE_ACTUAL = Gauge(
    "agentiq_lane_actual_tokens",
    "Actual tokens used per lane",
    labelnames=("lane", "tenant_id"),
    registry=registry,
)

AGENTIQ_LANE_UTILIZATION = Gauge(
    "agentiq_lane_utilization_ratio",
    "Lane token utilization ratio (actual/budget)",
    labelnames=("lane", "tenant_id"),
    registry=registry,
)

# Tool Selection
AGENTIQ_TOOL_K = Gauge(
    "agentiq_tool_k",
    "Number of tools allowed for current turn",
    labelnames=("tenant_id",),
    registry=registry,
)

# Governor Decisions Counter
AGENTIQ_DECISIONS_TOTAL = Counter(
    "agentiq_decisions_total",
    "Total governor decisions made",
    labelnames=("tenant_id", "path_mode", "degradation_level"),
    registry=registry,
)

# Governor Errors
AGENTIQ_ERRORS_TOTAL = Counter(
    "agentiq_errors_total",
    "Total governor errors",
    labelnames=("tenant_id", "error_type"),
    registry=registry,
)


# -----------------------------------------------------------------------------
# Confidence Scoring Metrics
# -----------------------------------------------------------------------------

# Confidence Score Histogram
LLM_CONFIDENCE_SCORE = Histogram(
    "llm_confidence_score",
    "LLM response confidence scores (0.0-1.0)",
    labelnames=("provider", "model"),
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
    registry=registry,
)

# Missing Confidence Counter
LLM_CONFIDENCE_MISSING = Counter(
    "llm_confidence_missing_total",
    "Count of responses without confidence (logprobs unavailable)",
    labelnames=("provider", "model"),
    registry=registry,
)

# Low Confidence Counter
LLM_CONFIDENCE_LOW = Counter(
    "llm_confidence_low_total",
    "Count of responses with confidence below threshold",
    labelnames=("provider", "model"),
    registry=registry,
)

# Rejected Responses Counter
LLM_CONFIDENCE_REJECTED = Counter(
    "llm_confidence_rejected_total",
    "Count of responses rejected for low confidence",
    labelnames=("provider", "model"),
    registry=registry,
)

# EWMA Gauge
LLM_CONFIDENCE_EWMA = Gauge(
    "llm_confidence_ewma",
    "Exponentially weighted moving average of confidence",
    labelnames=("provider", "model"),
    registry=registry,
)

# Confidence Calculation Latency
LLM_CONFIDENCE_LATENCY = Histogram(
    "llm_confidence_latency_seconds",
    "Confidence calculation latency in seconds",
    labelnames=("provider", "model"),
    buckets=[0.0001, 0.0005, 0.001, 0.002, 0.005, 0.01],
    registry=registry,
)


# -----------------------------------------------------------------------------
# RunReceipt Metrics
# -----------------------------------------------------------------------------

# Receipt Persistence
RUNRECEIPT_PERSISTED_TOTAL = Counter(
    "runreceipt_persisted_total",
    "Total run receipts persisted",
    labelnames=("tenant_id",),
    registry=registry,
)

RUNRECEIPT_PERSIST_ERRORS = Counter(
    "runreceipt_persist_errors_total",
    "Total run receipt persistence errors",
    labelnames=("tenant_id", "error_type"),
    registry=registry,
)

RUNRECEIPT_PERSIST_LATENCY = Histogram(
    "runreceipt_persist_latency_seconds",
    "Run receipt persistence latency in seconds",
    labelnames=("tenant_id",),
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0],
    registry=registry,
)


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------


def record_governor_decision(
    tenant_id: str,
    aiq_pred: float,
    degradation_level: str,
    path_mode: str,
    tool_k: int,
    latency_ms: float,
    lane_budgets: dict,
) -> None:
    """Record metrics for a governor decision.

    Args:
        tenant_id: Tenant identifier
        aiq_pred: Predicted AIQ score (0-100)
        degradation_level: Degradation level string
        path_mode: Path mode (fast/rescue)
        tool_k: Number of tools allowed
        latency_ms: Governor latency in milliseconds
        lane_budgets: Token budget per lane
    """
    # AIQ prediction
    AGENTIQ_AIQ_PRED.labels(tenant_id=tenant_id).observe(aiq_pred)

    # Latency (convert ms to seconds)
    AGENTIQ_GOVERNOR_LATENCY.labels(tenant_id=tenant_id).observe(latency_ms / 1000.0)

    # Degradation level (convert to int)
    level_map = {"none": 0, "minor": 1, "moderate": 2, "severe": 3, "critical": 4}
    level_int = level_map.get(degradation_level.lower(), 0)
    AGENTIQ_DEGRADATION_LEVEL.labels(tenant_id=tenant_id).set(level_int)

    # Path mode
    AGENTIQ_PATH_MODE.labels(mode=path_mode, tenant_id=tenant_id).inc()

    # Tool K
    AGENTIQ_TOOL_K.labels(tenant_id=tenant_id).set(tool_k)

    # Lane budgets
    for lane, tokens in lane_budgets.items():
        AGENTIQ_LANE_BUDGET.labels(lane=lane, tenant_id=tenant_id).set(tokens)

    # Decision counter
    AGENTIQ_DECISIONS_TOTAL.labels(
        tenant_id=tenant_id,
        path_mode=path_mode,
        degradation_level=degradation_level,
    ).inc()


def record_lane_actual(tenant_id: str, lane_actual: dict, lane_budgets: dict) -> None:
    """Record actual lane token usage.

    Args:
        tenant_id: Tenant identifier
        lane_actual: Actual tokens used per lane
        lane_budgets: Token budget per lane (for utilization ratio)
    """
    for lane, actual in lane_actual.items():
        AGENTIQ_LANE_ACTUAL.labels(lane=lane, tenant_id=tenant_id).set(actual)

        # Calculate utilization ratio
        budget = lane_budgets.get(lane, 0)
        if budget > 0:
            ratio = actual / budget
            AGENTIQ_LANE_UTILIZATION.labels(lane=lane, tenant_id=tenant_id).set(ratio)


def record_aiq_observed(tenant_id: str, aiq_obs: float) -> None:
    """Record observed AIQ score.

    Args:
        tenant_id: Tenant identifier
        aiq_obs: Observed AIQ score (0-100)
    """
    AGENTIQ_AIQ_OBS.labels(tenant_id=tenant_id).observe(aiq_obs)


def record_governor_error(tenant_id: str, error_type: str) -> None:
    """Record a governor error.

    Args:
        tenant_id: Tenant identifier
        error_type: Type of error (e.g., "budget_exhausted", "capsule_not_found")
    """
    AGENTIQ_ERRORS_TOTAL.labels(tenant_id=tenant_id, error_type=error_type).inc()


def record_confidence(
    provider: str,
    model: str,
    score: float | None,
    latency_ms: float,
    is_low: bool = False,
    is_rejected: bool = False,
) -> None:
    """Record confidence scoring metrics.

    Args:
        provider: LLM provider name
        model: Model name
        score: Confidence score (0.0-1.0) or None if unavailable
        latency_ms: Calculation latency in milliseconds
        is_low: Whether score was below threshold
        is_rejected: Whether response was rejected
    """
    # Latency
    LLM_CONFIDENCE_LATENCY.labels(provider=provider, model=model).observe(latency_ms / 1000.0)

    if score is None:
        LLM_CONFIDENCE_MISSING.labels(provider=provider, model=model).inc()
        return

    # Score histogram
    LLM_CONFIDENCE_SCORE.labels(provider=provider, model=model).observe(score)

    if is_low:
        LLM_CONFIDENCE_LOW.labels(provider=provider, model=model).inc()

    if is_rejected:
        LLM_CONFIDENCE_REJECTED.labels(provider=provider, model=model).inc()


def update_confidence_ewma(provider: str, model: str, ewma_value: float) -> None:
    """Update confidence EWMA gauge.

    Args:
        provider: LLM provider name
        model: Model name
        ewma_value: Current EWMA value
    """
    LLM_CONFIDENCE_EWMA.labels(provider=provider, model=model).set(ewma_value)


def record_receipt_persisted(tenant_id: str, latency_ms: float) -> None:
    """Record successful receipt persistence.

    Args:
        tenant_id: Tenant identifier
        latency_ms: Persistence latency in milliseconds
    """
    RUNRECEIPT_PERSISTED_TOTAL.labels(tenant_id=tenant_id).inc()
    RUNRECEIPT_PERSIST_LATENCY.labels(tenant_id=tenant_id).observe(latency_ms / 1000.0)


def record_receipt_error(tenant_id: str, error_type: str) -> None:
    """Record receipt persistence error.

    Args:
        tenant_id: Tenant identifier
        error_type: Type of error
    """
    RUNRECEIPT_PERSIST_ERRORS.labels(tenant_id=tenant_id, error_type=error_type).inc()


__all__ = [
    # Governor metrics
    "AGENTIQ_AIQ_PRED",
    "AGENTIQ_AIQ_OBS",
    "AGENTIQ_GOVERNOR_LATENCY",
    "AGENTIQ_DEGRADATION_LEVEL",
    "AGENTIQ_PATH_MODE",
    "AGENTIQ_LANE_BUDGET",
    "AGENTIQ_LANE_ACTUAL",
    "AGENTIQ_LANE_UTILIZATION",
    "AGENTIQ_TOOL_K",
    "AGENTIQ_DECISIONS_TOTAL",
    "AGENTIQ_ERRORS_TOTAL",
    # Confidence metrics
    "LLM_CONFIDENCE_SCORE",
    "LLM_CONFIDENCE_MISSING",
    "LLM_CONFIDENCE_LOW",
    "LLM_CONFIDENCE_REJECTED",
    "LLM_CONFIDENCE_EWMA",
    "LLM_CONFIDENCE_LATENCY",
    # Receipt metrics
    "RUNRECEIPT_PERSISTED_TOTAL",
    "RUNRECEIPT_PERSIST_ERRORS",
    "RUNRECEIPT_PERSIST_LATENCY",
    # Helper functions
    "record_governor_decision",
    "record_lane_actual",
    "record_aiq_observed",
    "record_governor_error",
    "record_confidence",
    "update_confidence_ewma",
    "record_receipt_persisted",
    "record_receipt_error",
]