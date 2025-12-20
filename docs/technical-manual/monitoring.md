# Monitoring & Observability

**Standards**: ISO/IEC 21500§7.5

## Metrics

### Prometheus Endpoints

| Service | Port | Endpoint |
|---------|------|----------|
| Gateway | 9600 | `/metrics` |
| Conversation Worker | 9601 | `/metrics` |
| Tool Executor | 9602 | `/metrics` |
| Memory Replicator | 9603 | `/metrics` |
| Circuit Breaker | 9610 | `/metrics` |

### Key Metrics

**Gateway**:
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request latency
- `streaming_connections_active` - Active streaming (SSE) connections
- `kafka_publish_errors_total` - Failed Kafka publishes

**Conversation Worker**:
- `messages_processed_total` - Messages processed
- `llm_call_duration_seconds` - LLM API latency
- `llm_tokens_used_total` - Token consumption
- `kafka_consumer_lag` - Consumer lag

**Tool Executor**:
- `tools_executed_total` - Tool executions
- `tool_execution_duration_seconds` - Execution time
- `tool_failures_total` - Failed executions

**Circuit Breaker**:
- `circuit_breaker_state` - Current state (0=closed, 1=open, 2=half-open)
- `circuit_breaker_open_events_total` - Times circuit opened

## Prometheus Configuration

```yaml
# infra/observability/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'gateway'
    static_configs:
      - targets: ['localhost:9600']
  
  - job_name: 'conversation-worker'
    static_configs:
      - targets: ['localhost:9601']
  
  - job_name: 'tool-executor'
    static_configs:
      - targets: ['localhost:9602']
  
  - job_name: 'circuit-breakers'
    static_configs:
      - targets: ['localhost:9610']

rule_files:
  - 'alerts.yml'

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['localhost:9093']
```

## Alerts

```yaml
# infra/observability/alerts.yml
groups:
  - name: somaagent01
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate on {{ $labels.instance }}"
      
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency on {{ $labels.instance }}"
      
      - alert: CircuitBreakerOpen
        expr: circuit_breaker_state == 1
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Circuit breaker open on {{ $labels.instance }}"
      
      - alert: KafkaConsumerLag
        expr: kafka_consumer_lag > 1000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High Kafka consumer lag: {{ $value }}"
```

## Dashboards

### Gateway Dashboard

**Panels**:
- Request rate (RPS)
- Error rate (%)
- P50/P95/P99 latency
- Active streaming (SSE) connections
- Kafka publish success rate

### Worker Dashboard

**Panels**:
- Messages processed/sec
- LLM call latency
- Token usage
- Consumer lag
- Error rate

### Infrastructure Dashboard

**Panels**:
- Kafka broker health
- PostgreSQL connections
- Redis memory usage
- Disk I/O
- Network throughput

## Logging

### Structured Logs

```python
import structlog

logger = structlog.get_logger(__name__)

logger.info(
    "message_processed",
    session_id=session_id,
    duration_ms=duration * 1000,
    tokens_used=tokens
)
```

### Log Levels

| Level | Usage |
|-------|-------|
| DEBUG | Development only |
| INFO | Normal operations |
| WARNING | Recoverable errors |
| ERROR | Failures requiring attention |
| CRITICAL | System-wide failures |

### Log Aggregation

```bash
# View all logs
docker compose logs -f

# Filter by service
docker compose logs -f gateway

# Filter by level
docker compose logs gateway | grep ERROR

# Export logs
docker compose logs > logs.txt
```

## Tracing

### OpenTelemetry

```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Setup
provider = TracerProvider()
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="localhost:4317"))
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

# Usage
tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("process_message"):
    result = await process_message(message)
```

### Trace Context

Traces propagate across services via Kafka headers:
- `traceparent` - W3C trace context
- `tracestate` - Vendor-specific data

## Health Checks

### Endpoints

```bash
# Gateway
curl http://localhost:${GATEWAY_PORT:-21016}/v1/health
# Response: {"status": "healthy", "version": "1.0.0"}

# Liveness (K8s)
curl http://localhost:${GATEWAY_PORT:-21016}/v1/health/live
# Response: 200 OK

### Prometheus Endpoints

- Gateway: `/metrics` on `GATEWAY_METRICS_PORT` (default 8000)
- Other services: `/metrics` on their `*_METRICS_PORT` env (see service code). Example defaults observed in-code:
  - Replicator: `${REPLICATOR_METRICS_PORT}` (env-driven)
  - Circuit Breakers exporter: `${CIRCUIT_BREAKER_METRICS_PORT:-9610}`
# Readiness (K8s)
curl http://localhost:${GATEWAY_PORT:-21016}/v1/health/ready
# Response: 200 OK (if Kafka/PostgreSQL accessible)
**Gateway (canonical names implemented)**:
- `gateway_requests_total{method,endpoint,status_code}` – Request counts
- `gateway_request_duration_seconds{method,endpoint}` – Request latency
- `gateway_sse_connections` – Active SSE connections
- `sse_messages_sent_total{message_type,session_id}` – SSE message counts
```bash
#!/bin/bash
# scripts/check_stack.sh

services=(
  "Kafka:20000"
  "Redis:20001"
  "PostgreSQL:20002"
  "Gateway:21016"
)

for service in "${services[@]}"; do
  name="${service%%:*}"
  port="${service##*:}"
  
  if nc -z localhost $port 2>/dev/null; then
### Health Checks

```bash
# Comprehensive health
curl http://localhost:${GATEWAY_PORT:-21016}/v1/health

# K8s style aliases exposed at root
curl http://localhost:${GATEWAY_PORT:-21016}/live     # liveness
curl http://localhost:${GATEWAY_PORT:-21016}/ready    # readiness
curl http://localhost:${GATEWAY_PORT:-21016}/healthz  # health alias
```
    echo "✅ $name: healthy"
  else
    echo "❌ $name: unhealthy"
  fi
done
```

## SLOs

### Service Level Objectives

| Metric | Target | Measurement |
|--------|--------|-------------|
| Availability | 99.9% | Uptime over 30 days |
| Latency (P95) | < 2s | Request duration |
| Error Rate | < 0.1% | 5xx responses |
| Message Processing | < 5s | End-to-end latency |

### SLO Monitoring

```promql
# Availability (30d)
avg_over_time(up{job="gateway"}[30d]) * 100

# Latency P95
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])
```

## Alertmanager

```yaml
# infra/observability/alertmanager.yml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'cluster']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'slack'

receivers:
  - name: 'slack'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}\n{{ end }}'
```

## Runbook Links

- [High Error Rate](../technical-manual/runbooks/high-error-rate.md)
- [High Latency](../technical-manual/runbooks/high-latency.md)
- [Circuit Breaker Open](../technical-manual/runbooks/circuit-breaker.md)
- [Kafka Consumer Lag](../technical-manual/runbooks/kafka-lag.md)
