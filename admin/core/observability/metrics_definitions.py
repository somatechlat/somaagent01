"""Prometheus Metric Definitions for SomaAgent01.

Split from metrics.py for 650-line compliance. Contains all metric declarations.
"""

from prometheus_client import (
    Counter as _BaseCounter,
    Gauge as _BaseGauge,
    Histogram as _BaseHistogram,
    Info,
    REGISTRY,
)

_metric_cache: dict[str, object] = {}


def _ensure_metric(metric_cls, name: str, *args, **kwargs):
    """Return an existing collector or create a new one."""
    existing = getattr(REGISTRY, "_names_to_collectors", {}).get(name)
    if existing is not None:
        return existing
    metric = metric_cls(name, *args, **kwargs)
    _metric_cache[name] = metric
    return metric


def Counter(name: str, *args, **kwargs):
    return _ensure_metric(_BaseCounter, name, *args, **kwargs)


def Gauge(name: str, *args, **kwargs):
    return _ensure_metric(_BaseGauge, name, *args, **kwargs)


def Histogram(name: str, *args, **kwargs):
    return _ensure_metric(_BaseHistogram, name, *args, **kwargs)


registry = REGISTRY

# Core app info
app_info = Info("somaagent01_app_info", "Application information", registry=registry)
app_info.info(
    {"version": "canonical-0.1.0", "architecture": "sse-only", "singleton_registry": "enabled"}
)

# SSE metrics
sse_connections = Gauge(
    "sse_active_connections", "Active SSE connections", ["session_id"], registry=registry
)
sse_messages_sent = Counter(
    "sse_messages_sent_total",
    "Total SSE messages",
    ["message_type", "session_id"],
    registry=registry,
)
sse_message_duration = Histogram(
    "sse_message_duration_seconds",
    "SSE message duration",
    ["message_type"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
    registry=registry,
)

# Gateway metrics
gateway_requests = Counter(
    "gateway_requests_total",
    "Gateway requests",
    ["method", "endpoint", "status_code"],
    registry=registry,
)
gateway_request_duration = Histogram(
    "gateway_request_duration_seconds",
    "Gateway request duration",
    ["method", "endpoint"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
    registry=registry,
)

# Singleton health
singleton_health = Gauge(
    "singleton_health_status",
    "Singleton health (1=healthy)",
    ["integration_name"],
    registry=registry,
)

# Database metrics
db_connections = Gauge("database_connections_active", "Active DB connections", registry=registry)
db_query_duration = Histogram(
    "database_query_duration_seconds",
    "DB query duration",
    ["operation"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
    registry=registry,
)

# Kafka metrics
kafka_messages = Counter(
    "kafka_messages_total", "Kafka messages", ["topic", "operation"], registry=registry
)
kafka_message_duration = Histogram(
    "kafka_message_duration_seconds",
    "Kafka message duration",
    ["topic", "operation"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
    registry=registry,
)

# Auth metrics
auth_requests = Counter(
    "auth_requests_total", "Auth requests", ["result", "source"], registry=registry
)
auth_duration = Histogram(
    "auth_duration_seconds",
    "Auth check duration",
    ["source"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0],
    registry=registry,
)

# Tool metrics
tool_calls = Counter("tool_calls_total", "Tool calls", ["tool_name", "result"], registry=registry)
tool_duration = Histogram(
    "tool_duration_seconds",
    "Tool execution duration",
    ["tool_name"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
    registry=registry,
)

# Error metrics
errors_total = Counter(
    "errors_total", "Total errors", ["error_type", "location"], registry=registry
)

# Circuit breaker
circuit_breaker_state = Gauge(
    "circuit_breaker_state",
    "Circuit state (0=closed,1=open,2=half-open)",
    ["circuit_name"],
    registry=registry,
)

# System metrics
system_memory_usage = Gauge("system_memory_usage_bytes", "Memory usage", registry=registry)
system_cpu_usage = Gauge("system_cpu_usage_percent", "CPU usage", registry=registry)

# SomaBrain metrics
somabrain_requests_total = Counter(
    "somabrain_requests_total", "SomaBrain requests", ["agent"], registry=registry
)
somabrain_latency_seconds = Histogram(
    "somabrain_latency_seconds",
    "SomaBrain latency",
    ["agent", "operation"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
    registry=registry,
)
somabrain_errors_total = Counter(
    "somabrain_errors_total",
    "SomaBrain errors",
    ["agent", "operation", "error_type"],
    registry=registry,
)
somabrain_memory_operations_total = Counter(
    "somabrain_memory_operations_total",
    "Memory operations",
    ["agent", "operation", "status"],
    registry=registry,
)

# Health metrics
system_health_gauge = Gauge(
    "system_health_status", "Health status (1=healthy)", ["service", "component"], registry=registry
)
system_uptime_seconds = Counter(
    "system_uptime_seconds", "Uptime counter", ["service", "version"], registry=registry
)

# Memory metrics
memory_wal_lag_seconds = Gauge("memory_wal_lag_seconds", "WAL lag", ["tenant"], registry=registry)
memory_persistence_sla = Histogram(
    "memory_persistence_duration_seconds",
    "Memory persistence",
    ["operation", "status", "tenant"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
    registry=registry,
)
memory_retry_attempts = Counter(
    "memory_retry_attempts_total",
    "Retry attempts",
    ["tenant", "session_id", "operation"],
    registry=registry,
)
memory_policy_decisions = Counter(
    "memory_policy_decisions_total",
    "Policy decisions",
    ["action", "resource", "tenant", "decision"],
    registry=registry,
)

# Chaos metrics
chaos_recovery_duration = Histogram(
    "chaos_recovery_duration_seconds",
    "Chaos recovery",
    ["chaos_type", "component"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
    registry=registry,
)
chaos_events_total = Counter(
    "chaos_events_total", "Chaos events", ["component", "chaos_type"], registry=registry
)

# Context builder metrics
context_tokens_before_budget = Gauge(
    "context_tokens_before_budget", "Tokens before budget", registry=registry
)
context_tokens_after_budget = Gauge(
    "context_tokens_after_budget", "Tokens after budget", registry=registry
)
context_tokens_after_redaction = Gauge(
    "context_tokens_after_redaction", "Tokens after redaction", registry=registry
)
context_prompt_tokens = Gauge("context_prompt_tokens", "Prompt tokens", registry=registry)
context_builder_prompt_total = Counter(
    "context_builder_prompt_total", "Prompts built", registry=registry
)
tokens_received_total = Counter(
    "conversation_worker_tokens_received_total", "Tokens received", registry=registry
)

# Thinking metrics
thinking_policy_seconds = Histogram(
    "conversation_worker_policy_seconds",
    "Policy eval time",
    ["policy"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
    registry=registry,
)

# LLM metrics
llm_calls_total = Counter(
    "conversation_worker_llm_calls_total", "LLM calls", ["model", "result"], registry=registry
)
llm_call_latency_seconds = Histogram(
    "conversation_worker_llm_latency_seconds",
    "LLM latency",
    ["model"],
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0],
    registry=registry,
)
llm_input_tokens_total = Counter(
    "conversation_worker_llm_input_tokens_total", "LLM input tokens", ["model"], registry=registry
)
llm_output_tokens_total = Counter(
    "conversation_worker_llm_output_tokens_total", "LLM output tokens", ["model"], registry=registry
)

context_builder_snippets_total = Counter(
    "context_builder_snippets_total", "Snippets considered", ["stage"], registry=registry
)

thinking_total_seconds = Histogram(
    "thinking_total_seconds",
    "Context build latency",
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
    registry=registry,
)
thinking_tokenisation_seconds = Histogram(
    "thinking_tokenisation_seconds",
    "Tokenisation latency",
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0],
    registry=registry,
)
thinking_retrieval_seconds = Histogram(
    "thinking_retrieval_seconds",
    "Retrieval latency",
    ["state"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0],
    registry=registry,
)
thinking_salience_seconds = Histogram(
    "thinking_salience_seconds",
    "Salience latency",
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0],
    registry=registry,
)
thinking_ranking_seconds = Histogram(
    "thinking_ranking_seconds",
    "Ranking latency",
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0],
    registry=registry,
)
thinking_redaction_seconds = Histogram(
    "thinking_redaction_seconds",
    "Redaction latency",
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0],
    registry=registry,
)
thinking_prompt_seconds = Histogram(
    "thinking_prompt_seconds",
    "Prompt latency",
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0],
    registry=registry,
)

event_published_total = Counter(
    "context_builder_events_total", "Events published", ["event_type"], registry=registry
)
event_publish_latency_seconds = Histogram(
    "context_builder_event_publish_seconds",
    "Event publish latency",
    ["event_type"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0],
    registry=registry,
)
event_publish_failure_total = Counter(
    "context_builder_event_publish_failure_total", "Event failures", registry=registry
)

sla_violations_total = Counter(
    "sla_violations_total",
    "SLA violations",
    ["metric", "tenant", "threshold_type"],
    registry=registry,
)

# Settings metrics
settings_read_total = Counter(
    "settings_read_total", "Settings reads", ["endpoint"], registry=registry
)
settings_write_total = Counter(
    "settings_write_total", "Settings writes", ["endpoint", "result"], registry=registry
)
settings_write_latency_seconds = Histogram(
    "settings_write_latency_seconds",
    "Settings write latency",
    ["endpoint", "result"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
    registry=registry,
)

# Runtime config
runtime_config_updates_total = Counter(
    "runtime_config_updates_total", "Config updates", ["source"], registry=registry
)
runtime_config_info = Info("runtime_config_info", "Config info", registry=registry)
runtime_config_last_applied_ts = Gauge(
    "runtime_config_last_applied_timestamp_seconds", "Config applied timestamp", registry=registry
)
runtime_config_layer_total = Counter(
    "runtime_config_layer_total", "Config layer resolutions", ["layer"], registry=registry
)

deployment_mode_info = Info("deployment_mode_info", "Deployment mode", registry=registry)

feature_profile_info = Gauge(
    "feature_profile_info", "Feature profile", ["profile"], registry=registry
)
feature_state_info = Gauge(
    "feature_state_info", "Feature state", ["feature", "state"], registry=registry
)

__all__ = [
    "Counter",
    "Gauge",
    "Histogram",
    "registry",
    "sse_connections",
    "sse_messages_sent",
    "sse_message_duration",
    "gateway_requests",
    "gateway_request_duration",
    "singleton_health",
    "db_connections",
    "db_query_duration",
    "kafka_messages",
    "kafka_message_duration",
    "auth_requests",
    "auth_duration",
    "tool_calls",
    "tool_duration",
    "errors_total",
    "circuit_breaker_state",
    "system_memory_usage",
    "system_cpu_usage",
    "somabrain_requests_total",
    "somabrain_latency_seconds",
    "somabrain_errors_total",
    "somabrain_memory_operations_total",
    "system_health_gauge",
    "system_uptime_seconds",
    "memory_wal_lag_seconds",
    "memory_persistence_sla",
    "memory_retry_attempts",
    "memory_policy_decisions",
    "context_tokens_before_budget",
    "context_tokens_after_budget",
    "context_tokens_after_redaction",
    "context_prompt_tokens",
    "context_builder_prompt_total",
    "tokens_received_total",
    "llm_calls_total",
    "llm_call_latency_seconds",
    "llm_input_tokens_total",
    "llm_output_tokens_total",
    "thinking_total_seconds",
    "thinking_tokenisation_seconds",
    "thinking_retrieval_seconds",
    "thinking_salience_seconds",
    "thinking_ranking_seconds",
    "thinking_redaction_seconds",
    "thinking_prompt_seconds",
    "event_published_total",
    "event_publish_latency_seconds",
    "event_publish_failure_total",
    "settings_read_total",
    "settings_write_total",
    "settings_write_latency_seconds",
    "runtime_config_updates_total",
    "runtime_config_info",
    "runtime_config_last_applied_ts",
    "runtime_config_layer_total",
    "feature_profile_info",
    "feature_state_info",
]
