# SRS: Metrics & Dashboard Architecture

**Document ID:** SA01-SRS-METRICS-DASHBOARDS-2025-12
**Purpose:** Catalog ALL Prometheus metrics and define dashboard UI for consuming them
**Status:** CANONICAL REFERENCE

---

## 1. Metrics Infrastructure Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        OBSERVABILITY STACK                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                     │
│  │  Services   │───▶│ Prometheus  │───▶│  Grafana    │                     │
│  │  (metrics)  │    │  (scrape)   │    │ (visualize) │                     │
│  └─────────────┘    └─────────────┘    └─────────────┘                     │
│        │                  │                   │                             │
│        │                  │                   │                             │
│        ▼                  ▼                   ▼                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     CUSTOM DASHBOARD UI                             │   │
│  │                     (Lit Components)                                │   │
│  │                                                                     │   │
│  │  Route: /platform/metrics                                           │   │
│  │  Route: /admin/metrics                                              │   │
│  │  Route: /metrics (Agent view)                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Port: 20090 (Prometheus)                                                   │
│  Port: 20030 (Grafana)                                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Complete Metrics Catalog (60+ Metrics)

### 2.1 Application Info

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `somaagent01_app_info` | Info | version, architecture | App metadata |
| `deployment_mode_info` | Info | mode | LOCAL or PROD |
| `runtime_config_info` | Info | - | Current runtime config |

### 2.2 SSE Streaming Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `sse_active_connections` | Gauge | session_id | Active SSE connections |
| `sse_messages_sent_total` | Counter | message_type, session_id | Total SSE messages |
| `sse_message_duration_seconds` | Histogram | message_type | SSE message latency |

### 2.3 Gateway Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `gateway_requests_total` | Counter | method, endpoint, status_code | Total requests |
| `gateway_request_duration_seconds` | Histogram | method, endpoint | Request latency |

### 2.4 Database Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `database_connections_active` | Gauge | - | Active DB connections |
| `database_query_duration_seconds` | Histogram | operation | Query latency |

### 2.5 Kafka Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `kafka_messages_total` | Counter | topic, operation | Messages processed |
| `kafka_message_duration_seconds` | Histogram | topic, operation | Processing latency |

### 2.6 Authorization Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `auth_requests_total` | Counter | result, source | Auth requests |
| `auth_duration_seconds` | Histogram | source | Auth check latency |

### 2.7 Tool Execution Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `tool_calls_total` | Counter | tool_name, result | Tool invocations |
| `tool_duration_seconds` | Histogram | tool_name | Tool execution latency |
| `tool_executor_requests_total` | Counter | tool, outcome | Tool executor requests |
| `tool_executor_feedback_total` | Counter | status | Feedback delivery |
| `tool_executor_policy_decisions_total` | Counter | tool, decision | Policy evaluations |
| `tool_executor_execution_seconds` | Histogram | tool | Execution latency |
| `tool_executor_inflight` | Gauge | tool | In-flight executions |
| `tool_executor_requeue_total` | Counter | tool, reason | Requeue events |

### 2.8 LLM Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `conversation_worker_llm_calls_total` | Counter | model, result | LLM call outcomes |
| `conversation_worker_llm_latency_seconds` | Histogram | model | LLM call latency |
| `conversation_worker_llm_input_tokens_total` | Counter | model | Input tokens sent |
| `conversation_worker_llm_output_tokens_total` | Counter | model | Output tokens received |
| `conversation_worker_tokens_received_total` | Counter | - | Raw tokens from users |

### 2.9 SomaBrain Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `somabrain_requests_total` | Counter | agent | SomaBrain requests |
| `somabrain_latency_seconds` | Histogram | agent, operation | SomaBrain latency |
| `somabrain_errors_total` | Counter | agent, operation, error_type | SomaBrain errors |
| `somabrain_memory_operations_total` | Counter | agent, operation, status | Memory operations |

### 2.10 Memory Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `memory_wal_lag_seconds` | Gauge | tenant | WAL replication lag |
| `memory_persistence_duration_seconds` | Histogram | operation, status, tenant | Persistence latency |
| `memory_retry_attempts_total` | Counter | tenant, session_id, operation | Retry attempts |
| `memory_policy_decisions_total` | Counter | action, resource, tenant, decision | Policy decisions |

### 2.11 Context Builder Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `context_tokens_before_budget` | Gauge | - | Tokens before budget |
| `context_tokens_after_budget` | Gauge | - | Tokens after budget |
| `context_tokens_after_redaction` | Gauge | - | Tokens after redaction |
| `context_prompt_tokens` | Gauge | - | Final prompt tokens |
| `context_builder_prompt_total` | Counter | - | Prompts built |
| `context_builder_snippets_total` | Counter | stage | Memory snippets |
| `context_builder_events_total` | Counter | event_type | Events published |
| `context_builder_event_publish_seconds` | Histogram | event_type | Event publish latency |
| `context_builder_event_publish_failure_total` | Counter | - | Failed publishes |

### 2.12 Thinking Stage Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `thinking_total_seconds` | Histogram | - | Total context building |
| `thinking_tokenisation_seconds` | Histogram | - | Tokenization stage |
| `thinking_retrieval_seconds` | Histogram | state | Retrieval stage |
| `thinking_salience_seconds` | Histogram | - | Salience scoring |
| `thinking_ranking_seconds` | Histogram | - | Ranking/filtering |
| `thinking_redaction_seconds` | Histogram | - | Redaction stage |
| `thinking_prompt_seconds` | Histogram | - | Prompt rendering |
| `conversation_worker_policy_seconds` | Histogram | policy | Policy evaluation |

### 2.13 System Health Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `singleton_health_status` | Gauge | integration_name | Singleton health |
| `system_health_status` | Gauge | service, component | Component health |
| `system_uptime_seconds` | Counter | service, version | Uptime counter |
| `system_memory_usage_bytes` | Gauge | - | Memory usage |
| `system_cpu_usage_percent` | Gauge | - | CPU usage |

### 2.14 Circuit Breaker Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `circuit_breaker_state` | Gauge | circuit_name | 0=closed, 1=open, 2=half |
| `errors_total` | Counter | error_type, location | Error counts |

### 2.15 Chaos Recovery Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `chaos_recovery_duration_seconds` | Histogram | chaos_type, component | Recovery latency |
| `chaos_events_total` | Counter | component, chaos_type | Chaos events |

### 2.16 SLA Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `sla_violations_total` | Counter | metric, tenant, threshold_type | SLA violations |

### 2.17 Settings/Config Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `settings_read_total` | Counter | endpoint | Settings reads |
| `settings_write_total` | Counter | endpoint, result | Settings writes |
| `settings_write_latency_seconds` | Histogram | endpoint, result | Write latency |
| `runtime_config_updates_total` | Counter | source | Config updates |
| `runtime_config_last_applied_timestamp_seconds` | Gauge | - | Last config update |
| `runtime_config_layer_total` | Counter | layer | Config resolutions |

### 2.18 Feature Flag Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `feature_profile_info` | Gauge | profile | Active profile |
| `feature_state_info` | Gauge | feature, state | Feature states |

---

## 3. Dashboard Screens

### 3.1 Platform Admin Dashboard

**Route:** `/platform/metrics`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Platform Admin > Observability Dashboard                       🔄 Auto   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  SYSTEM HEALTH                                    Last 24h          │   │
│  ├────────────────┬────────────────┬────────────────┬──────────────────┤   │
│  │  API Requests  │   LLM Calls    │  Tool Execs    │  Errors          │   │
│  │  1.2M          │   456K         │   89K          │   0.02%          │   │
│  │  ████████████  │   ████████░░░  │   █████░░░░░░  │   ░░░░░░░░░░░░░  │   │
│  └────────────────┴────────────────┴────────────────┴──────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  LATENCY DISTRIBUTION (p50 / p95 / p99)                             │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │  Gateway        │  45ms   │  120ms  │  450ms  │  ██████████░░░░░░░  │   │
│  │  LLM Calls      │  1.2s   │  3.5s   │  8.2s   │  ████████████████░  │   │
│  │  Memory Recall  │  15ms   │  45ms   │  120ms  │  ████░░░░░░░░░░░░░  │   │
│  │  Tools          │  250ms  │  1.5s   │  5.0s   │  ██████████░░░░░░░  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  TOKEN USAGE                                                        │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │  Input Tokens:   45.2M          Output Tokens:  12.8M               │   │
│  │  Cost Estimate:  $3,245.67      Avg per Request:  2,340 tokens      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  SERVICE HEALTH                                                     │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │  ● PostgreSQL   🟢   ● Redis     🟢   ● Temporal   🟢               │   │
│  │  ● Qdrant       🟢   ● Keycloak  🟢   ● SomaBrain  🟡               │   │
│  │  ● Kafka        🟢   ● Prometheus🟢   ● Grafana    🟢               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  CIRCUIT BREAKERS                                                   │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │  somabrain_memory   🟢 CLOSED    openai_llm       🟢 CLOSED         │   │
│  │  qdrant_vectors     🟢 CLOSED    temporal_worker  🟢 CLOSED         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  SLA VIOLATIONS (Last 7 days)                                       │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │  ✓ LLM Latency < 5s:     99.8%  (Target: 99%)                       │   │
│  │  ✓ Memory Durability:    100%   (Target: 99.99%)                    │   │
│  │  ✓ API Availability:     99.95% (Target: 99.9%)                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Tenant Admin Dashboard

**Route:** `/admin/metrics`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Tenant Dashboard > Agent Metrics                    Dec 1-25, 2025        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  USAGE SUMMARY                                                      │   │
│  ├────────────────┬────────────────┬────────────────┬──────────────────┤   │
│  │  API Calls     │   LLM Tokens   │  Images        │  Voice Min       │   │
│  │  52,345/100K   │   523K/1M      │   312/500      │   245/500        │   │
│  │  ████████░░░░  │   █████░░░░░░  │   ██████░░░░░  │   █████░░░░░░░░  │   │
│  │  52%           │   52%          │   62%          │   49%            │   │
│  └────────────────┴────────────────┴────────────────┴──────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  USAGE BY AGENT                                                     │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │  AGENT              REQUESTS    TOKENS      IMAGES    VOICE         │   │
│  │  ─────────────────────────────────────────────────────────────────  │   │
│  │  Support-AI         23,456      245K        156       120 min       │   │
│  │  Sales-Bot          18,234      178K        98        80 min        │   │
│  │  Internal-AI        10,655      100K        58        45 min        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  COST BREAKDOWN (Estimated)                                         │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │  LLM Tokens:     $156.78    (GPT-4o: $120, Claude: $36.78)          │   │
│  │  Images:         $12.48     (DALLE 3 @ $0.04/image)                 │   │
│  │  Voice:          $24.50     (Whisper + Kokoro)                      │   │
│  │  ────────────────────────────────────────────────────────           │   │
│  │  TOTAL:          $193.76                                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Agent Real-Time Metrics (DEV Mode)

**Route:** `/dev/metrics`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Developer Mode > Real-Time Metrics                     🔴 Live           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  THINKING PIPELINE (Last Request)                                   │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │  Stage              Duration    Tokens      Status                  │   │
│  │  ─────────────────────────────────────────────────────────────────  │   │
│  │  Tokenization       12ms        -           ✓                       │   │
│  │  Retrieval          145ms       -           ✓                       │   │
│  │  Salience           23ms        -           ✓                       │   │
│  │  Ranking            8ms         -           ✓                       │   │
│  │  Redaction          5ms         -           ✓                       │   │
│  │  Prompt Render      2ms         2,345       ✓                       │   │
│  │  ─────────────────────────────────────────────────────────────────  │   │
│  │  TOTAL              195ms       2,345                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  LLM CALL (Last Request)                                            │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │  Model:         gpt-4o                                              │   │
│  │  Input Tokens:  2,345                                               │   │
│  │  Output Tokens: 567                                                 │   │
│  │  Latency:       1.23s                                               │   │
│  │  Cost:          $0.0124                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  TOOL EXECUTIONS (Last 10)                                          │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │  09:41:23  browser_agent     SUCCESS    450ms                       │   │
│  │  09:41:18  web_search        SUCCESS    1.2s                        │   │
│  │  09:41:05  code_execution    SUCCESS    234ms                       │   │
│  │  09:40:55  image_gen         SUCCESS    3.4s                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Metrics API Endpoints

### 4.1 Raw Prometheus Metrics

| Endpoint | Port | Description |
|----------|------|-------------|
| `/metrics` | 9090 | Gateway metrics |
| `/tool_executor/metrics` | varies | Tool executor metrics |
| `/conversation_worker/metrics` | varies | Conversation worker metrics |
| `/delegation_gateway/metrics` | varies | Delegation gateway metrics |
| `http://prometheus:20090` | 20090 | Prometheus UI |

### 4.2 Dashboard API (Custom)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /api/v2/observability/snapshot` | GET | Current metrics snapshot |
| `GET /api/v2/observability/health` | GET | All service health |
| `GET /api/v2/observability/sla` | GET | SLA compliance |
| `GET /api/v2/observability/usage` | GET | Tenant usage metrics |
| `GET /api/v2/observability/costs` | GET | Cost estimates |
| `GET /api/v2/observability/latency` | GET | Latency percentiles |

---

## 5. Dashboard Views by Persona

| Route | Persona | Key Metrics Shown |
|-------|---------|-------------------|
| `/platform/metrics` | SAAS Admin | All system metrics, SLA, costs |
| `/platform/metrics/llm` | SAAS Admin | LLM token usage, latency, costs |
| `/platform/metrics/tools` | SAAS Admin | Tool execution metrics |
| `/platform/metrics/memory` | SAAS Admin | SomaBrain metrics, WAL lag |
| `/platform/metrics/sla` | SAAS Admin | SLA violations, compliance |
| `/admin/metrics` | Tenant Admin | Tenant usage, quota progress |
| `/admin/metrics/agents` | Tenant Admin | Per-agent breakdowns |
| `/admin/metrics/costs` | Tenant Admin | Cost estimates by agent |
| `/dev/metrics` | Developer | Real-time thinking metrics |
| `/dev/metrics/pipeline` | Developer | Request pipeline breakdown |

---

## 6. Alert Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| `gateway_request_duration_seconds` p99 | > 2s | > 5s | Scale gateway |
| `llm_latency_seconds` p99 | > 5s | > 10s | Check provider |
| `memory_wal_lag_seconds` | > 30s | > 60s | Investigate replication |
| `circuit_breaker_state` | = 2 (half-open) | = 1 (open) | Investigate failure |
| `errors_total` rate/min | > 10 | > 50 | Page on-call |
| `sla_violations_total` inc | > 0 | > 5 | Review SLA |

---

## 7. Implementation Priority

### Phase 1: Core Dashboards (High Priority)
1. ❌ `/platform/metrics` - System health overview
2. ❌ `/admin/metrics` - Tenant usage

### Phase 2: Detailed Views
3. ❌ `/platform/metrics/llm` - LLM deep dive
4. ❌ `/platform/metrics/sla` - SLA monitoring
5. ❌ `/dev/metrics` - Real-time dev metrics

### Phase 3: Alerting Integration
6. ❌ Alert configuration UI
7. ❌ Webhook notifications
8. ❌ PagerDuty/Slack integration
