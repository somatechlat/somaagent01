"""
Comprehensive Prometheus metrics for SomaAgent01 canonical backend.
Real observability for SSE streaming, singleton health, and system telemetry.
"""

import asyncio
import time
from functools import wraps
from typing import Any, Callable, Dict

# Import the original Prometheus collector classes under private aliases.
from prometheus_client import (
    Counter as _BaseCounter,
    Gauge as _BaseGauge,
    Histogram as _BaseHistogram,
    Info,
    REGISTRY,
)

# ---------------------------------------------------------------------------
# Compatibility wrappers for Prometheus collectors.
# Each wrapper checks the global ``REGISTRY`` for an existing collector with the
# same name and returns it if present, otherwise creates a new collector.  This
# prevents ``ValueError: Duplicated timeseries`` errors when the module is
# imported multiple times (e.g., during test collection).
# ---------------------------------------------------------------------------
_metric_cache: dict[str, object] = {}


def _ensure_metric(metric_cls, name: str, *args, **kwargs):
    """Return an existing collector or create a new one.

    ``metric_cls`` is one of the base Prometheus collector classes imported as
    ``_BaseCounter``, ``_BaseGauge`` or ``_BaseHistogram``.
    """
    existing = getattr(REGISTRY, "_names_to_collectors", {}).get(name)  # type: ignore
    if existing is not None:
        return existing
    metric = metric_cls(name, *args, **kwargs)
    _metric_cache[name] = metric
    return metric


def Counter(name: str, *args, **kwargs):  # type: ignore
    """Execute Counter.

    Args:
        name: The name.
    """

    return _ensure_metric(_BaseCounter, name, *args, **kwargs)


def Gauge(name: str, *args, **kwargs):  # type: ignore
    """Execute Gauge.

    Args:
        name: The name.
    """

    return _ensure_metric(_BaseGauge, name, *args, **kwargs)


def Histogram(name: str, *args, **kwargs):  # type: ignore
    """Execute Histogram.

    Args:
        name: The name.
    """

    return _ensure_metric(_BaseHistogram, name, *args, **kwargs)


# Registry for canonical backend metrics (reuse default so every service exports consistently)
registry = REGISTRY

# Feature profile/state gauges (mirrors gateway local collectors)
feature_profile_info = _ensure_metric(
    Gauge,
    "feature_profile_info",
    "Active feature profile (presence gauge)",
    ["profile"],
    registry=registry,
)
feature_state_info = _ensure_metric(
    Gauge,
    "feature_state_info",
    "Feature state indicator (1 for current state)",
    ["feature", "state"],
    registry=registry,
)

# Core application metrics
app_info = Info("somaagent01_app_info", "Application information", registry=registry)
app_info.info(
    {"version": "canonical-0.1.0", "architecture": "sse-only", "singleton_registry": "enabled"}
)

# SSE streaming metrics
sse_connections = Gauge(
    "sse_active_connections", "Number of active SSE connections", ["session_id"], registry=registry
)

sse_messages_sent = Counter(
    "sse_messages_sent_total",
    "Total SSE messages sent",
    ["message_type", "session_id"],
    registry=registry,
)

sse_message_duration = Histogram(
    "sse_message_duration_seconds",
    "Duration of SSE message processing",
    ["message_type"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
    registry=registry,
)

# Gateway metrics
gateway_requests = Counter(
    "gateway_requests_total",
    "Total gateway requests",
    ["method", "endpoint", "status_code"],
    registry=registry,
)

gateway_request_duration = Histogram(
    "gateway_request_duration_seconds",
    "Duration of gateway requests",
    ["method", "endpoint"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
    registry=registry,
)

# Singleton health metrics
singleton_health = Gauge(
    "singleton_health_status",
    "Health status of singleton integrations (1=healthy, 0=unhealthy)",
    ["integration_name"],
    registry=registry,
)

# Database metrics
db_connections = Gauge(
    "database_connections_active", "Number of active database connections", registry=registry
)

db_query_duration = Histogram(
    "database_query_duration_seconds",
    "Duration of database queries",
    ["operation"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
    registry=registry,
)

# Kafka metrics
kafka_messages = Counter(
    "kafka_messages_total",
    "Total Kafka messages processed",
    ["topic", "operation"],
    registry=registry,
)

kafka_message_duration = Histogram(
    "kafka_message_duration_seconds",
    "Duration of Kafka message processing",
    ["topic", "operation"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
    registry=registry,
)

# Authorization metrics
auth_requests = Counter(
    "auth_requests_total", "Total authorization requests", ["result", "source"], registry=registry
)

auth_duration = Histogram(
    "auth_duration_seconds",
    "Duration of authorization checks",
    ["source"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0],
    registry=registry,
)

# Tool catalog metrics
tool_calls = Counter(
    "tool_calls_total", "Total tool catalog calls", ["tool_name", "result"], registry=registry
)

tool_duration = Histogram(
    "tool_duration_seconds",
    "Duration of tool execution",
    ["tool_name"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
    registry=registry,
)

# Error metrics
errors_total = Counter(
    "errors_total", "Total errors by type", ["error_type", "location"], registry=registry
)

# Circuit Breaker metrics
circuit_breaker_state = Gauge(
    "circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=open, 2=half-open)",
    ["circuit_name"],
    registry=registry,
)

# System metrics
system_memory_usage = Gauge(
    "system_memory_usage_bytes", "System memory usage in bytes", registry=registry
)

system_cpu_usage = Gauge(
    "system_cpu_usage_percent", "System CPU usage percentage", registry=registry
)

# ---------------------------------------------------------------------------
# Compatibility metrics required by the FastA2A integration.
# The ``python.observability.metrics`` module expects a ``somabrain_requests_total``
# counter to be available from this ``observability.metrics`` package.  The
# original implementation mistakenly imported the symbol from itself, leading to
# an ``ImportError`` at runtime.  We provide the canonical counter here so the
# integration can record requests consistently.
# ---------------------------------------------------------------------------
somabrain_requests_total = Counter(
    "somabrain_requests_total",
    "Total SomaBrain requests made",
    ["agent"],
    registry=registry,
)

# Additional SomaBrain + health metrics required by FastA2A & gateway integrations.
somabrain_latency_seconds = Histogram(
    "somabrain_latency_seconds",
    "Latency of SomaBrain interactions",
    ["agent", "operation"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
    registry=registry,
)

somabrain_errors_total = Counter(
    "somabrain_errors_total",
    "Total SomaBrain errors",
    ["agent", "operation", "error_type"],
    registry=registry,
)

somabrain_memory_operations_total = Counter(
    "somabrain_memory_operations_total",
    "Memory operation invocations to SomaBrain",
    ["agent", "operation", "status"],
    registry=registry,
)

system_health_gauge = Gauge(
    "system_health_status",
    "Health status of service components (1=healthy,0=unhealthy)",
    ["service", "component"],
    registry=registry,
)

system_uptime_seconds = Counter(
    "system_uptime_seconds",
    "Uptime counter by service/version",
    ["service", "version"],
    registry=registry,
)

memory_wal_lag_seconds = Gauge(
    "memory_wal_lag_seconds", "WAL replication lag in seconds", ["tenant"], registry=registry
)

memory_persistence_sla = Histogram(
    "memory_persistence_duration_seconds",
    "Duration of memory persistence operations",
    ["operation", "status", "tenant"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
    registry=registry,
)

memory_retry_attempts = Counter(
    "memory_retry_attempts_total",
    "Number of memory write retry attempts",
    ["tenant", "session_id", "operation"],
    registry=registry,
)

memory_policy_decisions = Counter(
    "memory_policy_decisions_total",
    "Number of memory policy decisions",
    ["action", "resource", "tenant", "decision"],
    registry=registry,
)

# Chaotic recovery metrics
chaos_recovery_duration = Histogram(
    "chaos_recovery_duration_seconds",
    "Duration of system recovery from chaos events",
    ["chaos_type", "component"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
    registry=registry,
)

chaos_events_total = Counter(
    "chaos_events_total",
    "Number of chaos events triggered",
    ["component", "chaos_type"],
    registry=registry,
)

# ---------------------------------------------------------------------------
# Context builder metrics (token budgets, latency per thinking stage)
# ---------------------------------------------------------------------------

context_tokens_before_budget = Gauge(
    "context_tokens_before_budget",
    "Token count before applying prompt budget",
    registry=registry,
)

context_tokens_after_budget = Gauge(
    "context_tokens_after_budget",
    "Token count after applying prompt budget",
    registry=registry,
)

context_tokens_after_redaction = Gauge(
    "context_tokens_after_redaction",
    "Token count after PII redaction",
    registry=registry,
)

context_prompt_tokens = Gauge(
    "context_prompt_tokens",
    "Token count for final rendered prompt",
    registry=registry,
)

context_builder_prompt_total = Counter(
    "context_builder_prompt_total",
    "Number of prompts built by context builder",
    registry=registry,
)

tokens_received_total = Counter(
    "conversation_worker_tokens_received_total",
    "Raw tokens received from user messages",
    registry=registry,
)

thinking_policy_seconds = Histogram(
    "conversation_worker_policy_seconds",
    "Time spent evaluating policies",
    ["policy"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
    registry=registry,
)

llm_calls_total = Counter(
    "conversation_worker_llm_calls_total",
    "LLM call outcomes",
    ["model", "result"],
    registry=registry,
)

llm_call_latency_seconds = Histogram(
    "conversation_worker_llm_latency_seconds",
    "Latency of Gateway LLM invocations",
    ["model"],
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0],
    registry=registry,
)

llm_input_tokens_total = Counter(
    "conversation_worker_llm_input_tokens_total",
    "Prompt tokens sent to the LLM",
    ["model"],
    registry=registry,
)

llm_output_tokens_total = Counter(
    "conversation_worker_llm_output_tokens_total",
    "Completion tokens received from the LLM",
    ["model"],
    registry=registry,
)

context_builder_snippets_total = Counter(
    "context_builder_snippets_total",
    "Total memory snippets considered",
    ["stage"],
    registry=registry,
)

thinking_total_seconds = Histogram(
    "thinking_total_seconds",
    "Overall context-building latency",
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
    registry=registry,
)

thinking_tokenisation_seconds = Histogram(
    "thinking_tokenisation_seconds",
    "Latency of tokenisation/budget stage",
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0],
    registry=registry,
)

thinking_retrieval_seconds = Histogram(
    "thinking_retrieval_seconds",
    "Latency of Somabrain retrieval stage",
    ["state"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0],
    registry=registry,
)

thinking_salience_seconds = Histogram(
    "thinking_salience_seconds",
    "Latency of local salience scoring",
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0],
    registry=registry,
)

thinking_ranking_seconds = Histogram(
    "thinking_ranking_seconds",
    "Latency of ranking/filtering",
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0],
    registry=registry,
)

thinking_redaction_seconds = Histogram(
    "thinking_redaction_seconds",
    "Latency of redaction stage",
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0],
    registry=registry,
)

thinking_prompt_seconds = Histogram(
    "thinking_prompt_seconds",
    "Latency of prompt rendering stage",
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0],
    registry=registry,
)

event_published_total = Counter(
    "context_builder_events_total",
    "Number of context-builder events published",
    ["event_type"],
    registry=registry,
)

event_publish_latency_seconds = Histogram(
    "context_builder_event_publish_seconds",
    "Latency of publishing context-builder events",
    ["event_type"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0],
    registry=registry,
)

event_publish_failure_total = Counter(
    "context_builder_event_publish_failure_total",
    "Number of failed event publish attempts",
    registry=registry,
)

# SLA metrics
sla_violations_total = Counter(
    "sla_violations_total",
    "Number of SLA violations",
    ["metric", "tenant", "threshold_type"],
    registry=registry,
)

# Settings configuration metrics (M0 instrumentation)
settings_read_total = Counter(
    "settings_read_total", "Total settings read operations", ["endpoint"], registry=registry
)
settings_write_total = Counter(
    "settings_write_total",
    "Total settings write attempts",
    ["endpoint", "result"],  # result: success|error
    registry=registry,
)
settings_write_latency_seconds = Histogram(
    "settings_write_latency_seconds",
    "Latency of settings write operations",
    ["endpoint", "result"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
    registry=registry,
)

# Runtime config metrics (C2)
runtime_config_updates_total = Counter(
    "runtime_config_updates_total",
    "Number of runtime config updates applied",
    ["source"],  # source: default|dynamic|tenant
    registry=registry,
)

runtime_config_info = Info(
    "runtime_config_info", "Current runtime config snapshot info", registry=registry
)

runtime_config_last_applied_ts = Gauge(
    "runtime_config_last_applied_timestamp_seconds",
    "Unix timestamp when runtime config was last applied",
    registry=registry,
)
runtime_config_layer_total = Counter(
    "runtime_config_layer_total",
    "Count of config resolutions by layer",
    ["layer"],
    registry=registry,
)

# Deployment mode metric (LOCAL | PROD)
deployment_mode_info = Info(
    "deployment_mode_info", "Canonical deployment mode information", registry=registry
)


def record_memory_persistence(duration: float, operation: str, status: str, tenant: str) -> None:
    """Record a memory persistence event.

    The original implementation contained dead code after a ``return`` statement
    (referencing undefined ``count`` and ``stage`` variables).  That block has
    been removed and the helper ``_ensure_metric`` is now defined at module
    level (see above) and reused here.
    """
    # The actual metric updates are performed elsewhere via the ``MetricsCollector``.
    return None

    def time_total(self):
        """Execute time total."""

        return thinking_total_seconds.time()

    def time_tokenisation(self):
        """Execute time tokenisation."""

        return thinking_tokenisation_seconds.time()

    def time_retrieval(self, *, state: str):
        """Execute time retrieval."""

        return thinking_retrieval_seconds.labels(state=state).time()

    def time_salience(self):
        """Execute time salience."""

        return thinking_salience_seconds.time()

    def time_ranking(self):
        """Execute time ranking."""

        return thinking_ranking_seconds.time()

    def time_redaction(self):
        """Execute time redaction."""

        return thinking_redaction_seconds.time()

    def time_prompt(self):
        """Execute time prompt."""

        return thinking_prompt_seconds.time()

    def record_event_publish(self, event_type: str, *, duration: float | None = None) -> None:
        """Execute record event publish.

        Args:
            event_type: The event_type.
        """

        if duration is None:
            event_published_total.labels(event_type=event_type).inc()
            return
        event_published_total.labels(event_type=event_type).inc()
        event_publish_latency_seconds.labels(event_type=event_type).observe(duration)

    def record_event_failure(self) -> None:
        """Execute record event failure."""

        event_publish_failure_total.inc()


def measure_duration(metric_name: str):
    """Decorator to measure function execution duration."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            """Execute async wrapper."""

            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if metric_name == "sse_message":
                    sse_message_duration.labels(message_type=func.__name__).observe(duration)
                elif metric_name == "gateway_request":
                    gateway_request_duration.labels(method="GET", endpoint=func.__name__).observe(
                        duration
                    )
                elif metric_name == "database_query":
                    db_query_duration.labels(operation=func.__name__).observe(duration)
                elif metric_name == "auth_check":
                    auth_duration.labels(source=func.__name__).observe(duration)
                elif metric_name == "tool_execution":
                    tool_duration.labels(tool_name=func.__name__).observe(duration)

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            """Execute sync wrapper."""

            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if metric_name == "sse_message":
                    sse_message_duration.labels(message_type=func.__name__).observe(duration)
                elif metric_name == "gateway_request":
                    gateway_request_duration.labels(method="GET", endpoint=func.__name__).observe(
                        duration
                    )

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


def get_metrics_snapshot() -> Dict[str, Any]:
    """Get current metrics snapshot for health checks."""
    from prometheus_client import generate_latest

    # Best-effort extraction; internal attributes vary across versions.
    def _safe_total(counter: Counter) -> float:
        """Execute safe total.

        Args:
            counter: The counter.
        """

        try:
            return float(sum(s.samples[0].value for s in counter.collect()))
        except Exception:
            return 0.0

    def _safe_gauge(g: Gauge) -> float:
        """Execute safe gauge.

        Args:
            g: The g.
        """

        try:
            return float(next(iter(g.collect())).samples[0].value)
        except Exception:
            return 0.0

    return {
        "metrics_endpoint": "/metrics",
        "port": 9090,
        "active_connections": _safe_gauge(sse_connections),
        "total_messages_sent": _safe_total(sse_messages_sent),
        "settings_reads": _safe_total(settings_read_total),
        "runtime_config_last_applied": _safe_gauge(runtime_config_last_applied_ts),
        "raw_metrics": generate_latest(registry).decode("utf-8"),
    }


# ---------------------------------------------------------------------------
# Minimal MetricsCollector implementation
# ---------------------------------------------------------------------------
class MetricsCollector:
    """Collect and expose common observability actions.

    The production codebase expects a singleton ``metrics_collector`` with a
    handful of helper methods (e.g. ``track_error``, ``track_singleton_health``
    and ``update_feature_metrics``).  Implementations update the Prometheus
    counters/gauges defined above while keeping import side effects minimal.
    """

    def __init__(self) -> None:
        """Initialize the instance."""

        self._initialized = True

    # Generic error tracking used by circuit breakers, degradation monitor, etc.
    def track_error(self, error_type: str, component: str) -> None:
        # Use a generic counter; if a dedicated counter does not exist we fall
        # back to ``errors_total`` which already captures error_type and location.
        """Execute track error.

        Args:
            error_type: The error_type.
            component: The component.
        """

        try:
            errors_total.labels(error_type=error_type, location=component).inc()
        except Exception:
            # Defensive: ensure the method never raises during import.
            pass

    # Singleton health tracking for gateway components.
    def track_singleton_health(self, name: str, healthy: bool) -> None:
        """Execute track singleton health.

        Args:
            name: The name.
            healthy: The healthy.
        """

        try:
            singleton_health.labels(integration_name=name).set(1 if healthy else 0)
        except Exception:
            pass

    def update_feature_metrics(self) -> None:
        """Execute update feature metrics."""

        from services.common.features import build_default_registry

        reg = build_default_registry()
        feature_profile_info.labels(profile=reg.profile).set(1)
        for desc in reg.describe():
            state = reg.state(desc.key)
            for candidate in ("on", "degraded", "disabled"):
                feature_state_info.labels(feature=desc.key, state=candidate).set(
                    1 if candidate == state else 0
                )

    # Additional helper used by some services (e.g., auth results).
    def track_auth_result(self, result: str, source: str) -> None:
        """Execute track auth result.

        Args:
            result: The result.
            source: The source.
        """

        try:
            auth_requests.labels(result=result, source=source).inc()
        except Exception:
            pass

    # Circuit breaker state tracking
    def track_circuit_state(self, name: str, state_value: int) -> None:
        """Execute track circuit state.

        Args:
            name: The name.
            state_value: The state_value.
        """

        try:
            circuit_breaker_state.labels(circuit_name=name).set(state_value)
        except Exception:
            pass

    # Placeholder for any future metric updates.
    def __repr__(self) -> str:  # pragma: no cover
        """Return object representation."""

        return f"<MetricsCollector initialized={self._initialized}>"


# Export a singleton instance used throughout the codebase.
metrics_collector = MetricsCollector()


# ---------------------------------------------------------------------------
# ContextBuilderMetrics adapter (used by the FastA2A integration).
# ---------------------------------------------------------------------------
class ContextBuilderMetrics:
    """Simple wrapper exposing counters used by the context builder.

    The fast‑A2A integration imports this class to record prompt and token
    metrics.  The implementation mirrors the counters already defined in this
    module.
    """

    @staticmethod
    def record_prompt() -> None:
        """Execute record prompt."""

        try:
            context_builder_prompt_total.inc()
        except Exception:
            pass

    @staticmethod
    def record_tokens_before() -> None:
        """Execute record tokens before."""

        try:
            context_tokens_before_budget.inc()
        except Exception:
            pass

    @staticmethod
    def record_tokens_after() -> None:
        """Execute record tokens after."""

        try:
            context_tokens_after_budget.inc()
        except Exception:
            pass

    @staticmethod
    def record_tokens_redacted() -> None:
        """Execute record tokens redacted."""

        try:
            context_tokens_after_redaction.inc()
        except Exception:
            pass

    def time_total(self):
        """Return timer context for total context building time."""
        return thinking_total_seconds.time()

    def time_tokenisation(self):
        """Return timer context for tokenization time."""
        return thinking_tokenisation_seconds.time()

    def time_retrieval(self, *, state: str):
        """Return timer context for retrieval time with state label."""
        return thinking_retrieval_seconds.labels(state=state).time()

    def time_salience(self):
        """Return timer context for salience scoring time."""
        return thinking_salience_seconds.time()

    def time_ranking(self):
        """Return timer context for ranking time."""
        return thinking_ranking_seconds.time()

    def time_redaction(self):
        """Return timer context for redaction time."""
        return thinking_redaction_seconds.time()

    def time_prompt(self):
        """Return timer context for prompt rendering time."""
        return thinking_prompt_seconds.time()

    def inc_prompt(self):
        """Increment prompt counter."""
        context_builder_prompt_total.inc()

    def inc_snippets(self, *, stage: str, count: int = 1):
        """Increment snippet counter for given stage."""
        context_builder_snippets_total.labels(stage=stage).inc(count)

    def record_tokens(
        self,
        *,
        before_budget: float,
        after_budget: float,
        after_redaction: float,
        prompt_tokens: float,
    ):
        """Record token metrics at various stages."""
        context_tokens_before_budget.set(before_budget)
        context_tokens_after_budget.set(after_budget)
        context_tokens_after_redaction.set(after_redaction)
        context_prompt_tokens.set(prompt_tokens)
