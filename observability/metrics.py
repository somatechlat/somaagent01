"""
Comprehensive Prometheus metrics for SomaAgent01 canonical backend.
Real observability for SSE streaming, singleton health, and system telemetry.
"""
import time
from functools import wraps
from typing import Callable, Any, Dict
import asyncio
from prometheus_client import Counter, Histogram, Gauge, Info, start_http_server
from prometheus_client.core import CollectorRegistry

# Registry for canonical backend metrics
registry = CollectorRegistry()

# Core application metrics
app_info = Info('somaagent01_app_info', 'Application information', registry=registry)
app_info.info({
    'version': 'canonical-0.1.0',
    'architecture': 'sse-only',
    'singleton_registry': 'enabled'
})

# SSE streaming metrics
sse_connections = Gauge(
    'sse_active_connections',
    'Number of active SSE connections',
    ['session_id'],
    registry=registry
)

sse_messages_sent = Counter(
    'sse_messages_sent_total',
    'Total SSE messages sent',
    ['message_type', 'session_id'],
    registry=registry
)

sse_message_duration = Histogram(
    'sse_message_duration_seconds',
    'Duration of SSE message processing',
    ['message_type'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
    registry=registry
)

# Gateway metrics
gateway_requests = Counter(
    'gateway_requests_total',
    'Total gateway requests',
    ['method', 'endpoint', 'status_code'],
    registry=registry
)

gateway_request_duration = Histogram(
    'gateway_request_duration_seconds',
    'Duration of gateway requests',
    ['method', 'endpoint'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
    registry=registry
)

# Singleton health metrics
singleton_health = Gauge(
    'singleton_health_status',
    'Health status of singleton integrations (1=healthy, 0=unhealthy)',
    ['integration_name'],
    registry=registry
)

# Database metrics
db_connections = Gauge(
    'database_connections_active',
    'Number of active database connections',
    registry=registry
)

db_query_duration = Histogram(
    'database_query_duration_seconds',
    'Duration of database queries',
    ['operation'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
    registry=registry
)

# Kafka metrics
kafka_messages = Counter(
    'kafka_messages_total',
    'Total Kafka messages processed',
    ['topic', 'operation'],
    registry=registry
)

kafka_message_duration = Histogram(
    'kafka_message_duration_seconds',
    'Duration of Kafka message processing',
    ['topic', 'operation'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
    registry=registry
)

# Authorization metrics
auth_requests = Counter(
    'auth_requests_total',
    'Total authorization requests',
    ['result', 'source'],
    registry=registry
)

auth_duration = Histogram(
    'auth_duration_seconds',
    'Duration of authorization checks',
    ['source'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0],
    registry=registry
)

# Tool catalog metrics
tool_calls = Counter(
    'tool_calls_total',
    'Total tool catalog calls',
    ['tool_name', 'result'],
    registry=registry
)

tool_duration = Histogram(
    'tool_duration_seconds',
    'Duration of tool execution',
    ['tool_name'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
    registry=registry
)

# Error metrics
errors_total = Counter(
    'errors_total',
    'Total errors by type',
    ['error_type', 'location'],
    registry=registry
)

# System metrics
system_memory_usage = Gauge(
    'system_memory_usage_bytes',
    'System memory usage in bytes',
    registry=registry
)

system_cpu_usage = Gauge(
    'system_cpu_usage_percent',
    'System CPU usage percentage',
    registry=registry
)


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
        tool_calls.labels(tool_name=tool_name, result='success' if success else 'error').inc()


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
                if metric_name == 'sse_message':
                    sse_message_duration.labels(message_type=func.__name__).observe(duration)
                elif metric_name == 'gateway_request':
                    gateway_request_duration.labels(method='GET', endpoint=func.__name__).observe(duration)
                elif metric_name == 'database_query':
                    db_query_duration.labels(operation=func.__name__).observe(duration)
                elif metric_name == 'auth_check':
                    auth_duration.labels(source=func.__name__).observe(duration)
                elif metric_name == 'tool_execution':
                    tool_duration.labels(tool_name=func.__name__).observe(duration)

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if metric_name == 'sse_message':
                    sse_message_duration.labels(message_type=func.__name__).observe(duration)
                elif metric_name == 'gateway_request':
                    gateway_request_duration.labels(method='GET', endpoint=func.__name__).observe(duration)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


def get_metrics_snapshot() -> Dict[str, Any]:
    """Get current metrics snapshot for health checks."""
    from prometheus_client import generate_latest
    
    return {
        'metrics_endpoint': '/metrics',
        'port': 9090,
        'active_connections': float(sse_connections._value.get()),
        'total_messages_sent': float(sse_messages_sent._value.get()),
        'singleton_health': {
            name: float(gauge._value.get()) 
            for name, gauge in singleton_health._metrics.items()
        },
        'raw_metrics': generate_latest(registry).decode('utf-8')
    }