⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data.

# Sprint C: Observability & Monitoring
**Duration**: 2 weeks (parallel with Sprints A, B, D)  
**Goal**: Implement comprehensive observability with Prometheus, OpenTelemetry tracing, dashboards, and alerting

---

## 🎯 OBJECTIVES

1. Deploy Prometheus monitoring stack with alerting
2. Implement OpenTelemetry distributed tracing
3. Add comprehensive metrics to all services
4. Create alerting rules for SLO violations
5. Implement Dead Letter Queue (DLQ) for failed events
6. Build log aggregation and structured logging

---

## 📦 DELIVERABLES

### 1. Prometheus Configuration

#### 1.1 Prometheus Config
**File**: `infra/observability/prometheus.yml`
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'somaagent01'
    environment: 'production'

# Alertmanager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093

# Load rules
rule_files:
  - 'alerts.yml'
  - 'recording_rules.yml'

# Scrape configurations
scrape_configs:
  - job_name: 'gateway'
    static_configs:
      - targets: ['gateway:8010']
    metrics_path: '/metrics'
    
  - job_name: 'conversation-worker'
    static_configs:
      - targets: ['conversation-worker:8011']
        
  - job_name: 'tool-executor'
    static_configs:
      - targets: ['tool-executor:8012']
        
  - job_name: 'router'
    static_configs:
      - targets: ['router:8013']
        
  - job_name: 'canvas-service'
    static_configs:
      - targets: ['canvas-service:8014']
        
  - job_name: 'delegation-gateway'
    static_configs:
      - targets: ['delegation-gateway:8015']
        
  - job_name: 'kafka'
    static_configs:
      - targets: ['kafka:9092']
    metrics_path: '/metrics'
    
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
        
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
```

#### 1.2 Alert Rules
**File**: `infra/observability/alerts.yml`
```yaml
groups:
  - name: somaagent_slos
    interval: 30s
    rules:
      # Gateway SLOs
      - alert: HighGatewayLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job="gateway"}[5m])) > 2.5
        for: 5m
        labels:
          severity: warning
          service: gateway
        annotations:
          summary: "Gateway p95 latency > 2.5s"
          description: "p95 latency is {{ $value }}s for {{ $labels.instance }}"
          
      - alert: HighGatewayErrorRate
        expr: rate(http_requests_total{job="gateway",status=~"5.."}[5m]) / rate(http_requests_total{job="gateway"}[5m]) > 0.01
        for: 2m
        labels:
          severity: critical
          service: gateway
        annotations:
          summary: "Gateway error rate > 1%"
          description: "Error rate is {{ $value | humanizePercentage }} for {{ $labels.instance }}"
          
      # Conversation Worker SLOs
      - alert: SlowConversationProcessing
        expr: histogram_quantile(0.95, rate(conversation_processing_duration_seconds_bucket[5m])) > 5.0
        for: 5m
        labels:
          severity: warning
          service: conversation-worker
        annotations:
          summary: "Conversation processing p95 > 5s"
          description: "Processing time is {{ $value }}s"
          
      - alert: HighConversationFailureRate
        expr: rate(conversation_errors_total[5m]) / rate(conversation_requests_total[5m]) > 0.05
        for: 2m
        labels:
          severity: critical
          service: conversation-worker
        annotations:
          summary: "Conversation failure rate > 5%"
          
      # Budget alerts
      - alert: TenantBudgetExhausted
        expr: increase(budget_limit_reached_total[5m]) > 10
        for: 1m
        labels:
          severity: warning
          service: budget-manager
        annotations:
          summary: "Tenant {{ $labels.tenant }} hitting budget limits"
          
      # Tool Executor
      - alert: HighToolExecutionFailures
        expr: rate(tool_execution_failures_total[5m]) / rate(tool_execution_total[5m]) > 0.10
        for: 3m
        labels:
          severity: warning
          service: tool-executor
        annotations:
          summary: "Tool execution failure rate > 10%"
          
      # Policy violations
      - alert: HighPolicyBlockRate
        expr: rate(policy_blocked_total[5m]) > 10
        for: 2m
        labels:
          severity: warning
          service: policy
        annotations:
          summary: "High rate of policy blocks"
          description: "{{ $value }} blocks/sec on {{ $labels.instance }}"
          
      # Kafka lag
      - alert: HighKafkaConsumerLag
        expr: kafka_consumer_lag > 1000
        for: 5m
        labels:
          severity: critical
          service: kafka
        annotations:
          summary: "Kafka consumer lag > 1000"
          description: "Consumer {{ $labels.group }} has lag {{ $value }}"
          
      # Infrastructure
      - alert: RedisDown
        expr: up{job="redis"} == 0
        for: 1m
        labels:
          severity: critical
          service: redis
        annotations:
          summary: "Redis is down"
          
      - alert: PostgresDown
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
          service: postgres
        annotations:
          summary: "Postgres is down"
          
      - alert: KafkaDown
        expr: up{job="kafka"} == 0
        for: 1m
        labels:
          severity: critical
          service: kafka
        annotations:
          summary: "Kafka is down"
```

#### 1.3 Recording Rules
**File**: `infra/observability/recording_rules.yml`
```yaml
groups:
  - name: somaagent_aggregations
    interval: 30s
    rules:
      # Gateway aggregations
      - record: job:http_requests:rate5m
        expr: sum(rate(http_requests_total[5m])) by (job, status)
        
      - record: job:http_request_duration:p95
        expr: histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (job, le))
        
      - record: job:http_request_duration:p99
        expr: histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (job, le))
        
      # Token usage aggregations
      - record: tenant:tokens:rate1h
        expr: sum(rate(budget_tokens_consumed_total[1h])) by (tenant)
        
      - record: persona:tokens:rate1h
        expr: sum(rate(budget_tokens_consumed_total[1h])) by (tenant, persona_id)
        
      # Model usage aggregations
      - record: model:invocations:rate5m
        expr: sum(rate(slm_requests_total[5m])) by (model)
        
      - record: model:latency:p95
        expr: histogram_quantile(0.95, sum(rate(slm_latency_seconds_bucket[5m])) by (model, le))
```

### 2. Metrics Implementation

#### 2.1 Gateway Metrics
**File**: `services/gateway/metrics.py`
```python
"""Prometheus metrics for gateway service"""
from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
)

websocket_connections_active = Gauge(
    'websocket_connections_active',
    'Active WebSocket connections'
)

# Session metrics
sessions_created_total = Counter(
    'sessions_created_total',
    'Total sessions created'
)

# Auth metrics
auth_attempts_total = Counter(
    'auth_attempts_total',
    'Authentication attempts',
    ['result']  # success, failure, missing
)

# Policy metrics
policy_evaluations_total = Counter(
    'policy_evaluations_total',
    'OPA policy evaluations',
    ['result']  # allow, deny, error
)

def track_request(method: str, endpoint: str):
    """Decorator to track HTTP request metrics"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            status = 500
            try:
                result = await func(*args, **kwargs)
                status = result.status_code if hasattr(result, 'status_code') else 200
                return result
            finally:
                duration = time.time() - start
                http_requests_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status=str(status)
                ).inc()
                http_request_duration_seconds.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)
        return wrapper
    return decorator
```

#### 2.2 Conversation Worker Metrics
**File**: `services/conversation_worker/metrics.py`
```python
"""Prometheus metrics for conversation worker"""
from prometheus_client import Counter, Histogram, Gauge

# Processing metrics
conversation_requests_total = Counter(
    'conversation_requests_total',
    'Total conversation requests processed'
)

conversation_processing_duration_seconds = Histogram(
    'conversation_processing_duration_seconds',
    'Conversation processing duration',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

conversation_errors_total = Counter(
    'conversation_errors_total',
    'Conversation processing errors',
    ['error_type']
)

# SLM metrics
slm_requests_total = Counter(
    'slm_requests_total',
    'SLM API requests',
    ['model']
)

slm_latency_seconds = Histogram(
    'slm_latency_seconds',
    'SLM API latency',
    ['model'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

slm_tokens_total = Counter(
    'slm_tokens_total',
    'Total tokens processed',
    ['model', 'type']  # input, output
)

# Budget metrics
budget_tokens_consumed_total = Counter(
    'budget_tokens_consumed_total',
    'Total tokens consumed',
    ['tenant', 'persona_id']
)

budget_limit_reached_total = Counter(
    'budget_limit_reached_total',
    'Budget limit violations',
    ['tenant', 'persona_id']
)

# Preprocessing metrics
intent_classification_total = Counter(
    'intent_classification_total',
    'Intent classifications',
    ['intent']
)
```

#### 2.3 Tool Executor Metrics
**File**: `services/tool_executor/metrics.py`
```python
"""Prometheus metrics for tool executor"""
from prometheus_client import Counter, Histogram, Gauge

tool_execution_total = Counter(
    'tool_execution_total',
    'Total tool executions',
    ['tool_name', 'status']
)

tool_execution_duration_seconds = Histogram(
    'tool_execution_duration_seconds',
    'Tool execution duration',
    ['tool_name'],
    buckets=[0.01, 0.1, 0.5, 1.0, 5.0, 10.0, 30.0]
)

tool_execution_failures_total = Counter(
    'tool_execution_failures_total',
    'Tool execution failures',
    ['tool_name', 'error_type']
)

policy_blocked_total = Counter(
    'policy_blocked_total',
    'Policy-blocked tool executions',
    ['tool_name', 'tenant']
)

sandbox_active_executions = Gauge(
    'sandbox_active_executions',
    'Currently executing tools in sandbox'
)

resource_usage_cpu_seconds = Counter(
    'resource_usage_cpu_seconds',
    'CPU seconds consumed by tools',
    ['tool_name']
)

resource_usage_memory_bytes = Histogram(
    'resource_usage_memory_bytes',
    'Memory usage by tools',
    ['tool_name'],
    buckets=[1e6, 10e6, 50e6, 100e6, 500e6, 1e9]
)
```

### 3. OpenTelemetry Tracing

#### 3.1 Tracing Configuration
**File**: `services/common/tracing.py`
```python
"""OpenTelemetry distributed tracing setup"""
import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor

def setup_tracing(service_name: str):
    """Initialize OpenTelemetry tracing"""
    resource = Resource(attributes={
        SERVICE_NAME: service_name,
        "deployment.environment": os.getenv("SOMA_AGENT_MODE", "LOCAL"),
    })
    
    provider = TracerProvider(resource=resource)
    
    # Export to OTLP collector
    otlp_exporter = OTLPSpanExporter(
        endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317"),
        insecure=True
    )
    
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    trace.set_tracer_provider(provider)
    
    # Auto-instrument libraries
    FastAPIInstrumentor().instrument()
    HTTPXClientInstrumentor().instrument()
    AsyncPGInstrumentor().instrument()
    RedisInstrumentor().instrument()
    
    return trace.get_tracer(service_name)

# Usage in services
tracer = setup_tracing("gateway")

# Manual span creation
async def my_function():
    with tracer.start_as_current_span("my_operation") as span:
        span.set_attribute("custom.attribute", "value")
        # Do work
        pass
```

#### 3.2 Trace Context Propagation
**File**: `services/common/trace_context.py`
```python
"""Trace context propagation across Kafka"""
from opentelemetry import trace
from opentelemetry.propagate import inject, extract
from typing import Dict, Any

def inject_trace_context(event: Dict[str, Any]) -> Dict[str, Any]:
    """Inject trace context into Kafka event"""
    carrier = {}
    inject(carrier)
    event.setdefault("trace_context", {}).update(carrier)
    return event

def extract_trace_context(event: Dict[str, Any]) -> None:
    """Extract trace context from Kafka event"""
    carrier = event.get("trace_context", {})
    ctx = extract(carrier)
    return ctx
```

### 4. Dead Letter Queue (DLQ)

#### 4.1 DLQ Implementation
**File**: `services/common/dlq.py`
```python
"""Dead Letter Queue for failed events"""
import logging
from typing import Any, Dict
from services.common.event_bus import KafkaEventBus

LOGGER = logging.getLogger(__name__)

class DeadLetterQueue:
    def __init__(self, source_topic: str):
        self.source_topic = source_topic
        self.dlq_topic = f"{source_topic}.dlq"
        self.bus = KafkaEventBus()
        
    async def send_to_dlq(
        self,
        event: Dict[str, Any],
        error: Exception,
        retry_count: int = 0
    ):
        """Send failed event to DLQ"""
        dlq_event = {
            "original_event": event,
            "source_topic": self.source_topic,
            "error_message": str(error),
            "error_type": type(error).__name__,
            "retry_count": retry_count,
            "timestamp": time.time()
        }
        
        try:
            await self.bus.publish(self.dlq_topic, dlq_event)
            LOGGER.warning(
                "Sent event to DLQ",
                extra={
                    "source_topic": self.source_topic,
                    "dlq_topic": self.dlq_topic,
                    "error": str(error)
                }
            )
        except Exception as dlq_error:
            LOGGER.error(
                "Failed to send to DLQ",
                extra={"error": str(dlq_error)}
            )
```

### 5. Structured Logging

#### 5.1 JSON Logging Configuration
**File**: `services/common/logging_config.py`
```python
"""Structured JSON logging configuration"""
import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict

class JSONFormatter(logging.Formatter):
    """Format logs as JSON"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields
        if hasattr(record, "extra"):
            log_data.update(record.extra)
            
        # Add exception info
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_data)

def setup_logging():
    """Configure structured logging"""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)
```

---

## 🔧 IMPLEMENTATION TASKS

### Week 1
- [ ] Setup Prometheus with scrape configs
- [ ] Add recording rules for key SLOs
- [ ] Add metrics to gateway service
- [ ] Add metrics to conversation worker
- [ ] Add metrics to tool executor
- [ ] Implement alert rules

### Week 2
- [ ] Implement OpenTelemetry tracing
- [ ] Add trace context propagation
- [ ] Implement DLQ for all topics
- [ ] Setup structured JSON logging
- [ ] Deploy OTEL collector
- [ ] Create runbook for common alerts

---

## ✅ ACCEPTANCE CRITERIA

1. ✅ All services expose /metrics endpoint
2. ✅ Prometheus scrapes all services successfully
3. ✅ Recording rules cover key SLOs and KPIs
4. ✅ Alert rules fire correctly in test scenarios
5. ✅ Distributed traces span gateway → worker → executor
6. ✅ DLQ captures and stores failed events
7. ✅ Logs are structured JSON with trace IDs
8. ✅ Runbook documents alert response procedures

---

## 📊 SUCCESS METRICS

- **Metric Coverage**: 100% of services expose key metrics
- **Alert Coverage**: All SLOs have alerts
- **Trace Sampling**: 10% of requests traced
- **MTTR**: < 15 minutes with observability tools

---

## 🚀 NEXT STEPS

After Sprint C completion:
1. Add custom metrics for business KPIs
2. Implement SLA reports
3. Add anomaly detection
4. Integrate with PagerDuty/Opsgenie
