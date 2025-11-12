"""
Comprehensive Prometheus metrics for SomaAgent01 canonical backend.
Real observability for SSE streaming, singleton health, and system telemetry.
"""

import asyncio
import time
from functools import wraps
from typing import Any, Callable, Dict

from prometheus_client import Counter, Gauge, Histogram, Info, start_http_server
from prometheus_client.core import CollectorRegistry

# Registry for canonical backend metrics (must be defined before metric declarations)
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

    # C2: Runtime config instrumentation helpers
    def record_runtime_config_update(self, *, version: str, checksum: str, source: str) -> None:
        try:
            runtime_config_updates_total.labels(source=source).inc()
            runtime_config_info.info({"version": version, "checksum": checksum, "source": source})
            runtime_config_last_applied_ts.set(time.time())
        except Exception:
            pass

    def record_runtime_config_layer(self, layer: str) -> None:
        try:
            runtime_config_layer_total.labels(layer=layer).inc()
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
        "runtime_config_last_applied": _safe_gauge(runtime_config_last_applied_ts),
        "raw_metrics": generate_latest(registry).decode("utf-8"),
    }
