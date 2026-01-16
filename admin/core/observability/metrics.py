"""Prometheus Metrics for SomaAgent01.

Split into modules for 650-line compliance:
- metrics_definitions.py: Metric declarations
- metrics.py: Collector class and helpers (this file)
"""

import asyncio
import time
from functools import wraps
from typing import Any, Callable, Dict

from prometheus_client import generate_latest

# Import all metrics from definitions
from admin.core.observability.metrics_definitions import (
    auth_duration,
    auth_requests,
    circuit_breaker_state,
    context_builder_prompt_total,
    context_prompt_tokens,
    context_tokens_after_budget,
    context_tokens_after_redaction,
    context_tokens_before_budget,
    Counter,
    db_connections,
    db_query_duration,
    errors_total,
    event_publish_failure_total,
    event_publish_latency_seconds,
    event_published_total,
    feature_profile_info,
    feature_state_info,
    gateway_request_duration,
    gateway_requests,
    Gauge,
    Histogram,
    kafka_message_duration,
    kafka_messages,
    llm_call_latency_seconds,
    llm_calls_total,
    llm_input_tokens_total,
    llm_output_tokens_total,
    memory_persistence_sla,
    memory_policy_decisions,
    memory_retry_attempts,
    memory_wal_lag_seconds,
    registry,
    runtime_config_info,
    runtime_config_last_applied_ts,
    runtime_config_layer_total,
    runtime_config_updates_total,
    settings_read_total,
    settings_write_latency_seconds,
    settings_write_total,
    singleton_health,
    somabrain_errors_total,
    somabrain_latency_seconds,
    somabrain_memory_operations_total,
    somabrain_requests_total,
    sse_connections,
    sse_message_duration,
    sse_messages_sent,
    system_cpu_usage,
    system_health_gauge,
    system_memory_usage,
    system_uptime_seconds,
    thinking_prompt_seconds,
    thinking_ranking_seconds,
    thinking_redaction_seconds,
    thinking_retrieval_seconds,
    thinking_salience_seconds,
    thinking_tokenisation_seconds,
    thinking_total_seconds,
    tokens_received_total,
    tool_calls,
    tool_duration,
)


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

    def _safe_total(counter) -> float:
        try:
            return float(sum(s.samples[0].value for s in counter.collect()))
        except Exception:
            return 0.0

    def _safe_gauge(g) -> float:
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


class MetricsCollector:
    """Collect and expose common observability actions."""

    def __init__(self) -> None:
        self._initialized = True

    def track_error(self, error_type: str = "", component: str = "", location: str = "") -> None:
        try:
            loc = location or component
            errors_total.labels(error_type=error_type, location=loc).inc()
        except Exception:
            pass

    def track_singleton_health(self, name: str, healthy: bool) -> None:
        try:
            singleton_health.labels(integration_name=name).set(1 if healthy else 0)
        except Exception:
            pass

    def update_feature_metrics(self) -> None:
        from services.common.features import build_default_registry

        reg = build_default_registry()
        feature_profile_info.labels(profile=reg.profile).set(1)
        for desc in reg.describe():
            state = reg.state(desc.key)
            for candidate in ("on", "degraded", "disabled"):
                feature_state_info.labels(feature=desc.key, state=candidate).set(
                    1 if candidate == state else 0
                )

    def track_auth_result(self, result: str, source: str) -> None:
        try:
            auth_requests.labels(result=result, source=source).inc()
        except Exception:
            pass

    def track_circuit_state(self, name: str, state_value: int) -> None:
        try:
            circuit_breaker_state.labels(circuit_name=name).set(state_value)
        except Exception:
            pass

    def __repr__(self) -> str:
        return f"<MetricsCollector initialized={self._initialized}>"


metrics_collector = MetricsCollector()


class ContextBuilderMetrics:
    """Wrapper for context builder metrics."""

    @staticmethod
    def record_prompt() -> None:
        try:
            context_builder_prompt_total.inc()
        except Exception:
            pass

    @staticmethod
    def record_tokens_before_budget(count: int) -> None:
        try:
            context_tokens_before_budget.set(count)
        except Exception:
            pass

    @staticmethod
    def record_tokens_after_budget(count: int) -> None:
        try:
            context_tokens_after_budget.set(count)
        except Exception:
            pass

    @staticmethod
    def record_tokens_after_redaction(count: int) -> None:
        try:
            context_tokens_after_redaction.set(count)
        except Exception:
            pass

    @staticmethod
    def record_prompt_tokens(count: int) -> None:
        try:
            context_prompt_tokens.set(count)
        except Exception:
            pass

    @staticmethod
    def record_snippets(stage: str, count: int) -> None:
        try:
            context_builder_snippets_total.labels(stage=stage).inc(count)
        except Exception:
            pass


# Re-export all for backward compatibility
__all__ = [
    "Counter",
    "Gauge",
    "Histogram",
    "registry",
    "measure_duration",
    "get_metrics_snapshot",
    "MetricsCollector",
    "metrics_collector",
    "ContextBuilderMetrics",
    # All metrics
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
