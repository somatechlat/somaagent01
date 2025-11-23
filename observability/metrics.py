"""
Comprehensive Prometheus metrics for SomaAgent01 canonical backend.
Real observability for SSE streaming, singleton health, and system telemetry.
"""

import asyncio
import time
from functools import wraps
from typing import Any, Callable, Dict

from prometheus_client import Counter, Gauge, Histogram, Info, start_http_server, REGISTRY, CollectorRegistry

# Use a fresh CollectorRegistry for this module to avoid duplicate metric registration
# when the module is imported multiple times during testing. Each import will get its own
# isolated registry, preventing "Duplicated timeseries" errors while preserving the
# metric objects for internal use.
registry = CollectorRegistry()

# Feature profile/state gauges (mirrors gateway local collectors)
feature_profile_info = Gauge(
    "feature_profile_info",
    "Active feature profile (presence gauge)",
    ["profile"],
    registry=registry,
)
feature_state_info = Gauge(
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

# ---------------------------------------------------------------------------
# Degraded‑sync metrics (buffer processing)
# ---------------------------------------------------------------------------
degraded_sync_success_total = Counter(
    "degraded_sync_success_total",
    "Number of buffered events successfully enriched and published",
    ["service"],
    registry=registry,
)

degraded_sync_failure_total = Counter(
    "degraded_sync_failure_total",
    "Number of buffered events that failed enrichment",
    ["service", "error_type"],
    registry=registry,
)

degraded_sync_backlog = Gauge(
    "degraded_sync_backlog",
    "Current number of events waiting in the degraded buffer",
    ["service"],
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
# an ``ImportError`` at runtime.  We provide a minimal placeholder counter that
# satisfies the import without altering behaviour – the FastA2A code only
# increments this counter, so a simple ``Counter`` with a generic ``agent``
# label is sufficient.
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

# Phase 3: Memory Guarantees & WAL Lag Metrics
memory_write_outbox_pending = Gauge(
    "memory_write_outbox_pending_total",
    "Number of pending memory writes in outbox",
    ["tenant", "session_id"],
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

# Outbox processing metrics
outbox_processing_duration = Histogram(
    "outbox_processing_duration_seconds",
    "Duration of outbox message processing",
    ["status", "operation"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
    registry=registry,
)

outbox_batch_size = Gauge(
    "outbox_batch_size",
    "Number of messages in outbox processing batch",
    ["operation"],
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

# Deployment mode metric (LOCAL | PROD)
deployment_mode_info = Info(
    "deployment_mode_info", "Canonical deployment mode information", registry=registry
)


def record_memory_persistence(duration: float, operation: str, status: str, tenant: str) -> None:
    """Record memory persistence duration for SLA tracking."""
    memory_persistence_sla.observe(
        duration, {"operation": operation, "status": status, "tenant": tenant}
    )

    # Check SLA violations
    if operation == "write" and status == "success" and duration > 5.0:
        sla_violations_total.labels(
            metric="memory_persistence", tenant=tenant, threshold_type="p95_5s"
        ).inc()


def record_wal_lag(lag_seconds: float, tenant: str) -> None:
    """Record WAL lag for monitoring."""
    memory_wal_lag_seconds.set(lag_seconds, {"tenant": tenant})

    # Check SLA violations
    if lag_seconds > 30.0:
        sla_violations_total.labels(metric="wal_lag", tenant=tenant, threshold_type="max_30s").inc()


def record_policy_decision(action: str, resource: str, tenant: str, decision: str) -> None:
    """Record policy enforcement decisions."""
    memory_policy_decisions.labels(
        action=action, resource=resource, tenant=tenant, decision=decision
    ).inc()


class MetricsCollector:
    """Centralized metrics collection for SomaAgent01."""

    def __init__(self, port: int = 9090):
        self.port = port
        self._initialized = False

    def start_server(self) -> None:
        """Start Prometheus metrics server."""
        if not self._initialized:
            start_http_server(self.port, registry=registry)
            self._initialized = True

    def track_sse_connection(self, session_id: str) -> None:
        """Track active SSE connection."""
        sse_connections.labels(session_id=session_id).inc()

    def track_sse_disconnection(self, session_id: str) -> None:
        """Track SSE connection closure."""
        sse_connections.labels(session_id=session_id).dec()

    def track_sse_message(self, message_type: str, session_id: str) -> None:
        """Track SSE message sent."""
        sse_messages_sent.labels(message_type=message_type, session_id=session_id).inc()

    def track_gateway_request(self, method: str, endpoint: str, status_code: int) -> None:
        """Track gateway request."""
        gateway_requests.labels(method=method, endpoint=endpoint, status_code=status_code).inc()

    def track_singleton_health(self, integration_name: str, is_healthy: bool) -> None:
        """Track singleton integration health."""
        singleton_health.labels(integration_name=integration_name).set(1 if is_healthy else 0)

    def track_db_connection_count(self, count: int) -> None:
        """Track active database connections."""
        db_connections.set(count)

    def track_error(self, error_type: str, location: str) -> None:
        """Track error occurrence."""
        errors_total.labels(error_type=error_type, location=location).inc()

    def track_auth_result(self, result: str, source: str) -> None:
        """Track authorization result."""
        auth_requests.labels(result=result, source=source).inc()

    def track_tool_call(self, tool_name: str, success: bool) -> None:
        """Track tool catalog call."""
        tool_calls.labels(tool_name=tool_name, result="success" if success else "error").inc()

    def track_settings_read(self, endpoint: str) -> None:
        """Track a settings read operation."""
        settings_read_total.labels(endpoint=endpoint).inc()

    def track_settings_write(self, endpoint: str, result: str, duration: float) -> None:
        """Track a settings write operation with result and latency."""
        settings_write_total.labels(endpoint=endpoint, result=result).inc()
        settings_write_latency_seconds.labels(endpoint=endpoint, result=result).observe(duration)

    def update_feature_metrics(self) -> None:
        """Refresh feature profile/state metrics via FeatureRegistry."""
        try:
            from services.common.features import build_default_registry

            reg = build_default_registry()
            feature_profile_info.labels(reg.profile).set(1)
            for d in reg.describe():
                feature_state_info.labels(d.key, reg.state(d.key)).set(1)
        except Exception:
            pass

    def record_deployment_mode(self, mode: str) -> None:
        """Record current canonical deployment mode (LOCAL | PROD)."""
        try:
            deployment_mode_info.info({"mode": mode})
        except Exception:
            pass


# Global metrics collector
metrics_collector = MetricsCollector()


class ContextBuilderMetrics:
    """Helper for recording context-builder metrics consistently."""

    def record_tokens(
        self,
        *,
        before_budget: int | None = None,
        after_budget: int | None = None,
        after_redaction: int | None = None,
        prompt_tokens: int | None = None,
    ) -> None:
        if before_budget is not None:
            context_tokens_before_budget.set(before_budget)
        if after_budget is not None:
            context_tokens_after_budget.set(after_budget)
        if after_redaction is not None:
            context_tokens_after_redaction.set(after_redaction)
        if prompt_tokens is not None:
            context_prompt_tokens.set(prompt_tokens)

    def inc_prompt(self) -> None:
        context_builder_prompt_total.inc()

    def inc_snippets(self, *, stage: str, count: int) -> None:
        if count <= 0:
            return
        context_builder_snippets_total.labels(stage=stage).inc(count)

    def time_total(self):
        return thinking_total_seconds.time()

    def time_tokenisation(self):
        return thinking_tokenisation_seconds.time()

    def time_retrieval(self, *, state: str):
        return thinking_retrieval_seconds.labels(state=state).time()

    def time_salience(self):
        return thinking_salience_seconds.time()

    def time_ranking(self):
        return thinking_ranking_seconds.time()

    def time_redaction(self):
        return thinking_redaction_seconds.time()

    def time_prompt(self):
        return thinking_prompt_seconds.time()

    def record_event_publish(self, event_type: str, *, duration: float | None = None) -> None:
        if duration is None:
            event_published_total.labels(event_type=event_type).inc()
            return
        event_published_total.labels(event_type=event_type).inc()
        event_publish_latency_seconds.labels(event_type=event_type).observe(duration)

    def record_event_failure(self) -> None:
        event_publish_failure_total.inc()


def measure_duration(metric_name: str):
    """Decorator to measure function execution duration."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
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
        try:
            return float(sum(s.samples[0].value for s in counter.collect()))
        except Exception:
            return 0.0

    def _safe_gauge(g: Gauge) -> float:
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
        "raw_metrics": generate_latest(registry).decode("utf-8"),
    }
