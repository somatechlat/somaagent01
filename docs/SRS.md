# Software Requirements Specification (SRS)
## SomaAgent01 - Enterprise AI Agent Framework
### Version 3.0 | December 2025

---

## Document Control

| Item | Value |
|------|-------|
| Document ID | SA01-SRS-2025-12 |
| Version | 3.0 |
| Status | VERIFIED + MULTIMODAL EXTENSION PLANNED |
| Classification | Internal |
| Compliance | ISO/IEC/IEEE 29148:2018 |

---

## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification (SRS) documents the complete architecture, data flows, and system requirements for SomaAgent01 - an enterprise-grade AI agent framework. This document serves as the authoritative reference for:

- System architecture and component interactions
- Data flow patterns and messaging protocols
- Integration points with external services
- Correctness properties and verification criteria

### 1.2 Scope

SomaAgent01 is a distributed microservices system comprising:

- **Gateway Service**: FastAPI HTTP gateway (port 8010)
- **Conversation Worker**: Kafka consumer for message processing
- **Tool Executor**: Sandboxed tool execution service
- **SomaBrain Integration**: Cognitive memory and neuromodulation
- **Celery Task System**: Async task processing via Redis

### 1.3 Definitions and Acronyms

| Term | Definition |
|------|------------|
| FSM | Finite State Machine - Agent lifecycle orchestration |
| SomaBrain | External cognitive memory service (port 9696) |
| DLQ | Dead Letter Queue - Failed message storage |
| OPA | Open Policy Agent - Authorization service |
| VIBE | Verification, Implementation, Behavior, Execution coding rules |
| Use Case | Clean Architecture business operation encapsulation |

---

## 2. System Architecture Overview

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Web UI    │  │   CLI       │  │   A2A       │  │   MCP       │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
└─────────┼────────────────┼────────────────┼────────────────┼────────────────┘
          │                │                │                │
          ▼                ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           GATEWAY SERVICE (8010)                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  FastAPI Application                                                 │   │
│  │  ├── /v1/sessions/*     Session management                          │   │
│  │  ├── /v1/llm/invoke     LLM invocation (stream/non-stream)          │   │
│  │  ├── /v1/uploads        File upload processing                      │   │
│  │  ├── /v1/admin/*        Admin endpoints (audit, DLQ, requeue)       │   │
│  │  └── /v1/health         Health checks                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ AuthMiddle  │  │ RateLimit   │  │ CircuitBrkr │  │ DegradMon   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          │ Kafka: conversation.inbound
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CONVERSATION WORKER                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Clean Architecture Use Cases                                        │   │
│  │  ├── ProcessMessageUseCase    Main orchestration (453 lines)        │   │
│  │  ├── GenerateResponseUseCase  LLM response generation (285 lines)   │   │
│  │  ├── StoreMemoryUseCase       Memory operations (203 lines)         │   │
│  │  └── BuildContextUseCase      Context building (114 lines)          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ MsgAnalyzer │  │ PolicyEnf   │  │ CtxBuilder  │  │ ToolOrch    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          │ Kafka: tool.requests
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          TOOL EXECUTOR (147 lines)                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Thin Orchestrator Pattern                                           │   │
│  │  ├── RequestHandler      Policy check, tool dispatch                │   │
│  │  ├── ResultPublisher     Result publishing, feedback, memory        │   │
│  │  ├── ExecutionEngine     Sandboxed execution                        │   │
│  │  └── ToolRegistry        Tool discovery and schema                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          │ HTTP: /remember, /recall, /neuromodulators, /sleep/run
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SOMABRAIN SERVICE (9696)                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Cognitive Memory Service                                            │   │
│  │  ├── /remember, /recall       Memory storage and retrieval          │   │
│  │  ├── /neuromodulators         Neuromodulation state (global)        │   │
│  │  ├── /context/adaptation/state Adaptation weights                   │   │
│  │  ├── /sleep/run               Memory consolidation                  │   │
│  │  └── /persona/{pid}           Persona management                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Summary

| Component | Location | Lines | Responsibility |
|-----------|----------|-------|----------------|
| Gateway | `services/gateway/main.py` | 97 | HTTP routing, auth, rate limiting |
| ConversationWorker | `services/conversation_worker/main.py` | 178 | Message processing orchestration |
| ToolExecutor | `services/tool_executor/main.py` | 147 | Tool execution, policy, audit |
| Agent | `agent.py` | 400 | FSM orchestration, cognitive processing |
| SomaClient | `python/integrations/soma_client.py` | 909 | SomaBrain HTTP client |

---

## 3. Conversation Flow Architecture

### 3.1 Message Processing Pipeline

```
User Message → Gateway → Kafka → ConversationWorker → Use Cases → Response
```

#### 3.1.1 ProcessMessageUseCase Pipeline

1. **Message Analysis** - Intent, sentiment, tag detection
2. **Policy Check** - OPA authorization via `ConversationPolicyEnforcer`
3. **User Message Storage** - PostgreSQL via `SessionRepository`
4. **Memory Storage** - SomaBrain via `remember()` endpoint
5. **Context Building** - `ContextBuilder.build_for_turn()`
6. **Response Generation** - `GenerateResponseUseCase` with streaming
7. **Assistant Storage** - PostgreSQL + SomaBrain
8. **Response Publishing** - Kafka `conversation.outbound`

#### 3.1.2 Message Analysis (MessageAnalyzer)

```python
# Intent Detection
- "question" → starts with how/what/why/when/where/who or ends with ?
- "action_request" → contains create/build/implement/write
- "problem_report" → contains fix/bug/issue/error
- "statement" → default

# Tag Detection
- "code" → code/python/function/class
- "infrastructure" → deploy/docker/kubernetes/infra
- "testing" → test/validate/qa

# Sentiment Detection
- "negative" → fail/broken/crash/error/issue
- "positive" → great/thanks/awesome/good
- "neutral" → default
```

### 3.2 Data Flow Verification

| Step | Source | Destination | Protocol | Verified |
|------|--------|-------------|----------|----------|
| 1 | Client | Gateway | HTTP/SSE | ✅ |
| 2 | Gateway | Kafka | conversation.inbound | ✅ |
| 3 | Kafka | ConversationWorker | Consumer | ✅ |
| 4 | Worker | PostgreSQL | asyncpg | ✅ |
| 5 | Worker | SomaBrain | HTTP | ✅ |
| 6 | Worker | Gateway | HTTP (LLM invoke) | ✅ |
| 7 | Worker | Kafka | conversation.outbound | ✅ |

---

## 4. Upload Processing Architecture

### 4.1 Upload Flow

```
File Upload → Gateway → AttachmentsStore → Kafka → Processing
```

#### 4.1.1 Implementation Details (`uploads_full.py`)

```python
# Upload Processing Steps:
1. Authorization via authorize_request()
2. File reading and SHA256 hashing
3. Storage via AttachmentsStore.create()
4. Descriptor generation with metadata
5. Response with file paths

# Storage Fields:
- id: UUID
- filename: sanitized name
- mime: content type
- size: bytes
- sha256: hash
- status: "clean" (post-scan)
- path: /v1/attachments/{id}
```

#### 4.1.2 Dependencies

| Component | Implementation | VIBE Status |
|-----------|----------------|-------------|
| AttachmentsStore | PostgreSQL-backed | ✅ Real |
| DurablePublisher | Kafka + Outbox | ✅ Real |
| SessionCache | Redis | ✅ Real |
| SessionStore | PostgreSQL | ✅ Real |

---

## 5. Tool Execution Architecture

### 5.1 Tool Executor Flow

```
Tool Request → Policy Check → Execution → Result Publishing → Memory Capture
```

#### 5.1.1 RequestHandler Pipeline

1. **Validation** - `validate_tool_request()`
2. **Audit Start** - `log_tool_event(action="tool.execute.start")`
3. **Policy Check** - OPA `tool.execute` action
4. **Tool Lookup** - `ToolRegistry.get(tool_name)`
5. **UI Event** - Publish `tool.start` to `conversation.outbound`
6. **Execution** - `ExecutionEngine.execute(tool, args, limits)`
7. **Result Publishing** - `ResultPublisher.publish()`
8. **Audit Finish** - `log_tool_event(action="tool.execute.finish")`

#### 5.1.2 ResultPublisher Pipeline

1. **Validation** - `validate_tool_result()`
2. **Session Storage** - `store.append_event()`
3. **Kafka Publishing** - `publisher.publish(streams["results"])`
4. **UI Event** - Publish to `conversation.outbound`
5. **Telemetry** - `telemetry.emit_tool_execution()`
6. **Feedback** - `soma.context_feedback()`
7. **Memory Capture** - `soma.remember()` (policy-gated)

#### 5.1.3 Memory Capture Policy

```python
# Policy Check for Memory Write
allow_memory = await policy.evaluate(PolicyRequest(
    tenant=tenant,
    persona_id=persona_id,
    action="memory.write",
    resource="somabrain",
    context={
        "payload_type": "tool_result",
        "tool_name": tool_name,
        "session_id": session_id,
    }
))
```

### 5.2 Tool Metrics

| Metric | Type | Labels |
|--------|------|--------|
| `TOOL_REQUEST_COUNTER` | Counter | tool_name, result |
| `TOOL_EXECUTION_LATENCY` | Histogram | tool_name |
| `TOOL_INFLIGHT` | Gauge | tool_name |
| `POLICY_DECISIONS` | Counter | tool_name, decision |
| `REQUEUE_EVENTS` | Counter | tool_name, reason |
| `TOOL_FEEDBACK_TOTAL` | Counter | status |

---

## 6. Celery Tasks Architecture

### 6.1 Task Organization

| Module | Tasks | Responsibility |
|--------|-------|----------------|
| `core_tasks.py` | Infrastructure | SafeTask base, shared resources |
| `conversation_tasks.py` | delegate, build_context, store_interaction, feedback_loop | Conversation domain |
| `memory_tasks.py` | rebuild_index, evaluate_policy | Memory/index domain |
| `maintenance_tasks.py` | publish_metrics, cleanup_sessions, dead_letter | System maintenance |

### 6.2 SafeTask Base Class

```python
class SafeTask(Task):
    """Base task providing metrics and robust error recording."""
    
    def __call__(self, *args, **kwargs):
        # 1. Record start time
        # 2. Execute task
        # 3. Record metrics (success/error)
        # 4. Send feedback to SomaBrain
        # 5. On error: enqueue to DLQ
```

### 6.3 Task Configuration

| Task | Max Retries | Soft Limit | Hard Limit | Rate Limit |
|------|-------------|------------|------------|------------|
| delegate | 3 | 45s | 60s | 60/m |
| build_context | 2 | 30s | 45s | - |
| store_interaction | 2 | 30s | 45s | - |
| feedback_loop | 2 | 30s | 45s | - |
| rebuild_index | 1 | 60s | 90s | - |
| evaluate_policy | 2 | 20s | 30s | - |
| publish_metrics | 1 | 15s | 20s | - |
| cleanup_sessions | 1 | 90s | 120s | - |
| dead_letter | 0 | - | - | 120/m |

### 6.4 Saga Pattern Integration

```python
# Delegate task with saga management
saga_id = await saga_manager.start("delegate", step="authorize", data={...})

# On policy denial
await saga_manager.fail(saga_id, "policy_denied")
await run_compensation("delegate", saga_id, {"reason": "policy_denied"})

# On success
await saga_manager.update(saga_id, step="recorded", status="accepted", data={...})
```

---

## 7. SomaBrain Integration Architecture

### 7.1 API Endpoints (Verified from OpenAPI)

| Endpoint | Method | Purpose | Parameters |
|----------|--------|---------|------------|
| `/remember` | POST | Store memory | payload, coord, universe |
| `/recall` | POST | Recall memories | query, top_k, universe |
| `/neuromodulators` | GET | Get neuromod state | (none - global) |
| `/neuromodulators` | POST | Update neuromod state | dopamine, serotonin, noradrenaline, acetylcholine |
| `/context/adaptation/state` | GET | Get adaptation weights | tenant_id (optional) |
| `/sleep/run` | POST | Trigger sleep cycle | nrem, rem |
| `/persona/{pid}` | PUT/GET/DELETE | Persona management | persona_id |
| `/context/feedback` | POST | Submit feedback | task_name, success, latency_ms |

### 7.2 SomaClient Implementation

```python
class SomaClient:
    """Singleton HTTP client for SomaBrain endpoints."""
    
    # Circuit breaker configuration
    _CB_THRESHOLD: int = 3
    _CB_COOLDOWN_SEC: float = 15.0
    
    # Retry configuration
    _max_retries: int = 2
    _retry_base_ms: int = 150
    
    # Key methods:
    async def remember(payload, *, coord, universe, tenant, namespace, ...)
    async def recall(query, *, top_k, universe, tenant, namespace, ...)
    async def get_neuromodulators(*, tenant_id, persona_id)  # params ignored
    async def update_neuromodulators(*, tenant_id, persona_id, neuromodulators)
    async def get_adaptation_state(*, tenant_id, persona_id)  # persona_id ignored
    async def sleep_cycle(*, tenant_id, persona_id, duration_minutes, nrem, rem)
```

### 7.3 Cognitive Processing Integration

```python
# cognitive.py - Neuromodulation Application
async def apply_neuromodulation(agent):
    neuromods = agent.data.get("neuromodulators", {})
    dopamine = neuromods.get("dopamine", 0.4)
    serotonin = neuromods.get("serotonin", 0.5)
    noradrenaline = neuromods.get("noradrenaline", 0.0)
    
    cognitive_params = agent.data.setdefault("cognitive_params", {})
    cognitive_params["exploration_factor"] = 0.5 + (dopamine * 0.5)
    cognitive_params["creativity_boost"] = dopamine > 0.6
    cognitive_params["patience_factor"] = 0.5 + (serotonin * 0.5)
    cognitive_params["empathy_boost"] = serotonin > 0.6
    cognitive_params["focus_factor"] = 0.5 + (noradrenaline * 0.5)
    cognitive_params["alertness_boost"] = noradrenaline > 0.3
    
    # Natural decay
    if dopamine > 0.4:
        neuromods["dopamine"] = max(0.4, dopamine - 0.05)
```

### 7.4 Sleep Cycle Triggering

```python
# Triggered when cognitive_load > 0.8
async def consider_sleep_cycle(agent):
    cognitive_load = agent.data.get("cognitive_load", 0.5)
    if cognitive_load > 0.8:
        sleep_result = await agent.soma_client.sleep_cycle(
            tenant_id=agent.tenant_id,
            persona_id=agent.persona_id,
            duration_minutes=5,  # Ignored by SomaBrain
            nrem=True,
            rem=True,
        )
        # Post-sleep optimization
        await optimize_cognitive_parameters(agent, sleep_result)
```

---

## 8. Degraded Mode Architecture

### 8.1 DegradationMonitor

```python
class DegradationMonitor:
    """Production-ready degradation monitoring system."""
    
    # Monitored components
    core_components = [
        "somabrain", "database", "kafka", "redis",
        "gateway", "auth_service", "tool_executor"
    ]
    
    # Degradation thresholds
    _degradation_thresholds = {
        "response_time": 5.0,      # seconds
        "error_rate": 0.1,         # 10%
        "circuit_failure_rate": 0.3  # 30%
    }
```

### 8.2 Degradation Levels

| Level | Criteria | Actions |
|-------|----------|---------|
| NONE | All healthy | Normal operation |
| MINOR | response_time > 5s OR error_rate > 10% | Continue monitoring |
| MODERATE | response_time > 10s OR error_rate > 20% | Increase monitoring, prepare scaling |
| SEVERE | response_time > 15s OR unhealthy | Activate circuit breakers |
| CRITICAL | Circuit OPEN | Emergency procedures, failover |

### 8.3 Circuit Breaker Integration

```python
# Critical components with circuit breakers
critical_components = ["somabrain", "database", "kafka"]

# Circuit breaker configuration
CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,  # 1 minute
    expected_exception=Exception
)
```

### 8.4 Health Check Methods

| Component | Check Method | Implementation |
|-----------|--------------|----------------|
| somabrain | `_check_somabrain_health` | `SomaClient.health()` |
| database | `_check_database_health` | Connection test |
| kafka | `_check_kafka_health` | Broker connectivity |
| redis | `_check_redis_health` | PING command |
| generic | `_check_generic_component` | Assume healthy |

---

## 9. A2A (Agent-to-Agent) Architecture

### 9.1 A2A Protocol

```python
# A2A Communication via FastA2A
# Server: DynamicA2AProxy ASGI application
# Client: a2a_chat tool for outbound calls

# Skills advertised:
- code_execution
- file_management
- web_browsing
```

### 9.2 A2A Integration Points

| Component | Role | Implementation |
|-----------|------|----------------|
| Gateway | A2A Server | Token-authenticated endpoints |
| Agent | A2A Client | `a2a_chat` tool |
| Context | Isolation | Temporary context per conversation |

---

## 10. Data Storage Architecture

### 10.1 PostgreSQL Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| session_envelopes | Session metadata | session_id, tenant, created_at |
| session_events | Event timeline | session_id, event_type, occurred_at |
| dlq_messages | Dead letter queue | topic, event, error, created_at |
| attachments | File storage | id, filename, sha256, content |
| audit_events | Audit log | action, tenant, session_id, timestamp |
| outbox | Transactional outbox | topic, payload, status |
| memory_write_outbox | Memory retry queue | payload, tenant, status |

### 10.2 Redis Usage

| Key Pattern | Purpose | TTL |
|-------------|---------|-----|
| `session:{id}` | Session cache | Configurable |
| `policy:requeue:{id}` | Blocked events | 3600s |
| `dedupe:{key}` | Idempotency | 3600s |
| `rate_limit:{tenant}` | Rate limiting | Window-based |

### 10.3 Kafka Topics

| Topic | Producer | Consumer | Purpose |
|-------|----------|----------|---------|
| conversation.inbound | Gateway | ConversationWorker | User messages |
| conversation.outbound | Worker | Gateway (SSE) | Responses |
| tool.requests | Worker | ToolExecutor | Tool execution |
| tool.results | ToolExecutor | Worker | Tool results |
| audit.events | All services | AuditWorker | Audit trail |
| dlq.events | SafeTask | Admin | Failed tasks |
| memory.wal | All services | MemorySync | Memory WAL |
| task.feedback.dlq | Tasks | Admin | Failed feedback |

---

## 11. Security Architecture

### 11.1 Authentication

| Layer | Mechanism | Implementation |
|-------|-----------|----------------|
| External | Bearer Token / API Key | `services/gateway/auth.py` |
| Internal | X-Internal-Token | Service-to-service |
| OPA | Policy evaluation | `services/common/policy_client.py` |

### 11.2 Authorization Actions

| Action | Resource | Enforced By |
|--------|----------|-------------|
| conversation.send | message | ConversationPolicyEnforcer |
| tool.execute | tool_name | ToolExecutor |
| memory.write | somabrain | ResultPublisher |
| delegate.task | target | Celery delegate task |
| admin.* | endpoint | Gateway admin routes |

### 11.3 Secrets Management

| Secret | Storage | Access |
|--------|---------|--------|
| API Keys | Redis (encrypted) | `SA01_CRYPTO_FERNET_KEY` |
| Provider Credentials | Web UI Settings | Runtime injection |
| Internal Tokens | Environment | `SA01_AUTH_INTERNAL_TOKEN` |

### 11.4 Security & Transmission Hardening

- **Transport**: TLS 1.3 only; disable TLS 1.2/weak ciphers; enforce HSTS and OCSP stapling; no plaintext fallbacks.
- **Mutual TLS**: All service-to-service calls (Agent ↔ Hub ↔ Providers) use mTLS with short-lived client certificates from an internal CA; pin server certificates in the agent to prevent MITM.
- **Request Signing**: Every API request is JWS-signed (with `kid`, nonce, timestamp). Enforce tight replay window; validate both TLS client identity and signature.
- **Capsule Supply Chain**: Require SHA-256 checksum and detached signature (cosign/sigstore) before install/upgrade/rollback; optional transparency log; reject unsigned or incompatible capsules in Production.
- **Payload Encryption**: For sensitive bodies, support envelope encryption (per-request data keys from KMS) layered on top of TLS.
- **Mode-Aware Policy**: Dev/Test may allow unsigned dev capsules; Prod/Training must enforce signatures, allow/deny lists, and classification/retention rules. Modes gate tool/capsule execution and adaptive learning.
- **Authorization**: Fine-grained allow/deny by capsule id/version, tool, tenant, environment; link to manifest policy.
- **Audit & Telemetry**: Immutable, structured logs for install/enable/disable/rollback/API calls/workflows, tagged with capsule id/version, user, client cert fingerprint, nonce. Alert on replay or failed signature attempts.
- **Background Tasks**: Celery tasks include capsule id/version; emit audit + metrics; respect classification/retention when handling data.
- **Network Posture**: Least-privilege firewall rules; disable compression on sensitive endpoints (mitigate CRIME/BREACH); DDoS/abuse throttles; circuit breakers and exponential backoff around provider calls.
- **Key Hygiene**: Rotate TLS, JWS, and signing keys regularly; short TTL tokens; support key revocation; store keys in HSM/KMS; zeroize secrets on shutdown.
- **Export/Import**: Capsule export supports signing and optional encryption; verify signatures and policy on import. Data exports honor classification and retention timers.

---

## 12. Observability Architecture

### 12.1 Prometheus Metrics

| Metric | Type | Labels | Source |
|--------|------|--------|--------|
| `somabrain_http_requests_total` | Counter | method, path, status | SomaClient |
| `somabrain_request_seconds` | Histogram | method, path, status | SomaClient |
| `conversation_worker_messages_total` | Counter | result | MessageProcessor |
| `conversation_worker_processing_seconds` | Histogram | path | MessageProcessor |
| `sa01_core_tasks_total` | Counter | task, result | SafeTask |
| `sa01_core_task_latency_seconds` | Histogram | task | SafeTask |
| `gateway_sse_connections` | Gauge | - | Gateway |
| `fsm_transition_total` | Counter | from_state, to_state | Agent |

### 12.2 OpenTelemetry Tracing

```python
# Trace propagation
from opentelemetry.propagate import inject
inject(request_headers)  # Propagate trace context

# Span creation
tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span("somabrain.remember"):
    response = await self._request(...)
```

---

## 13. Architecture Improvements & Recommendations

### 13.1 Identified Issues

| Issue | Severity | Location | Recommendation |
|-------|----------|----------|----------------|
| Neuromodulators global | Medium | SomaBrain API | Consider tenant-scoped neuromodulation |
| Health checks simplified | Low | DegradationMonitor | Implement real DB/Kafka/Redis checks |
| A2A documentation sparse | Low | - | Document A2A protocol fully |
| Memory namespace confusion | Medium | SomaClient | Clarify universe vs namespace |

### 13.2 Recommended Refactors

1. **Tenant-Scoped Neuromodulation**: Current SomaBrain `/neuromodulators` is global. Consider extending API for per-tenant state.

2. **Real Health Checks**: `DegradationMonitor` health checks for database/kafka/redis are placeholders. Implement actual connectivity tests.

3. **Memory Namespace Clarity**: `SomaClient` has both `namespace` (memory sub-namespace like "wm") and `universe` (logical context). Document distinction clearly.

4. **Circuit Breaker Metrics**: Add Prometheus metrics for circuit breaker state transitions.

### 13.3 Correctness Properties (Verified)

| Property | Status | Evidence |
|----------|--------|----------|
| File Size Limits | ✅ | All files within tracked baselines |
| Repository Pattern | ✅ | All data access via ports/adapters |
| Use Case Isolation | ✅ | 4 Use Cases with DI |
| Config Single Source | ✅ | All imports from `src.core.config` |
| No VIBE Violations | ✅ | 20/20 requirements complete |

---

## 14. Capsule Domain Integration (SomaAgentHub)

### 14.1 Domain Model Alignment

**CapsuleDefinition** (Hub) ↔ Capsule manifest header:
- Keys: `id`, `tenant_id`, `name`, `version`, `status`, `description`, `default_persona_ref_id`, `role_overrides`, `allowed_tools`, `prohibited_tools`, `allowed_mcp_servers`, `tool_risk_profile`, `max_wall_clock_seconds`, `max_concurrent_nodes`, `allowed_runtimes`, `resource_profile`, `allowed_domains`, `blocked_domains`, `egress_mode`, `opa_policy_packages`, `guardrail_profiles`, `default_hitl_mode`, `risk_thresholds`, `max_pending_hitl`, `rl_export_allowed`, `rl_export_scope`, `rl_excluded_fields`, `example_store_policy`, `data_classification`, `retention_policy_days`, timestamps.
- Action: extend our capsule manifest `policy` block to carry all above; persist in DB as canonical CapsuleDefinition.

**CapsuleInstance** (Hub) ↔ runtime activation record:
- Keys: `id`, `tenant_id`, `capsule_definition_id`, `capsule_definition_version`, `scope`, `scope_reference`, `start_time`, `end_time`, `effective_config`, `derived_from_id`, timestamps.
- Action: create CapsuleInstance rows on every run/enablement; include in audit and task tagging.

### 14.2 Service & Data Flow Integration
- Source of truth: Task Capsule Repo ingests manifest → normalized CapsuleDefinition (Postgres). Orchestrator `/capsules` serves that data; deprecate duplicate CapsuleModel.
- Run flow: Client → Orchestrator `/workflows/...` creates CapsuleInstance → WorkflowEngine executes → results posted to `memory-gateway /v1/capsule/results` (object store + optional vector index/Qdrant) with capsule_instance metadata.
- Manifest storage: keep both raw `manifest_yaml` and normalized spec for drift detection.

### 14.3 API Contracts (to converge)
- `POST /capsules` (CapsuleSpec) → create CapsuleDefinition (uniqueness on tenant_id, name, version).
- `POST /v1/capsules` (manifest upload) → ingest + normalize → CapsuleDefinition.
- `POST /workflows/{id}/run` with capsule reference → create CapsuleInstance, enforce policy/HITL/limits.
- `POST /v1/capsule/results` (file, metadata) → store artifact; upsert vector if provided; apply classification/retention.

### 14.4 Enforcement & Policy (gaps to close)
- Enforce egress/domain allow/deny and allowed MCP servers at gateway/tool executor.
- Apply `max_wall_clock_seconds`, `max_concurrent_nodes`, `risk_thresholds`, `default_hitl_mode`, `max_pending_hitl` inside workflow engine/orchestrator dispatch.
- Respect `rl_export_allowed` / `rl_excluded_fields` on export endpoints; block export in Prod if disallowed.
- Classification/retention applied to artifacts and vector entries; purge jobs scheduled per `retention_policy_days`.
- All runs/results audited with `capsule_definition_id/version` and `capsule_instance_id`.

### 14.5 Integrity/Alignment Actions
1) Pick single capsule authority (Task Capsule Repo + normalized CapsuleDefinition); map orchestrator API to it.
2) Add migrations for CapsuleDefinition/CapsuleInstance with FK constraints and uniqueness (tenant_id, name, version).
3) Wire manifest ingestion pipeline to populate policy/risk/HITL fields and reject incompatible capsules by mode.
4) Implement enforcement hooks in gateway/tool executor/workflow engine (egress, time, concurrency, HITL, risk thresholds).
5) Publish OpenAPI for capsule endpoints and DDL snapshot; add tests for policy enforcement and retention purges.

### 14.6 Capsule Creator (Admin UI & Pipeline)
- **Goal**: Let admins build, validate, sign, and export capsules inside the Agent, without CLI tooling; output must be install-ready and policy-compliant.
- **UI Workflow**:
  - Create new capsule → choose template (skin, UI module, provider adapter, data, persona, workflow) → fill manifest fields (id/name/version/tenant, compatibility, policy, classification/retention, HITL, risk thresholds, egress/domain/MCP/tool allow/deny, resource_profile, runtimes).
  - Add assets: upload skin tokens/layouts, UI module bundles, adapter code, data payloads (KB/memories), workflows/temporal jobs, persona overlays.
  - Settings schema builder: form designer to define `settingsSchema` entries (type, required, secret, enum, default).
  - Policy presets: Prod/Training/Test/Dev profiles toggle signature requirement, allowUnsigned, egress rules, RL export flags.
  - Validation step: schema/compatibility check, dependency scan, signature readiness, size limits, checksum preview.
  - Signing: integrate cosign/sigstore via backend; store public keys; present detached signature + checksum.
  - Export: generate `.tgz` + `.sig`; optional encryption for data capsules; store draft history; version bump helper.
  - Drafts & versioning: save WIP capsules in Postgres; promote to published; duplicate existing capsule as baseline.
- **Backend pipeline**:
  - POST `/v1/capsules/build` receives spec + assets; runs validation; produces build artifact; persists draft CapsuleDefinition (status=draft).
  - POST `/v1/capsules/sign` signs artifact with org key; records signature provenance.
  - POST `/v1/capsules/publish` marks definition as published and registers in CapsuleDefinition table; optional auto-install flag.
  - GET `/v1/capsules/drafts` list drafts; GET `/v1/capsules/{id}/history` show versions and signatures.
- **Enforcement**:
  - Drafts cannot be installed until published and signature verified (except Dev mode with allowUnsigned).
  - Classification/retention applied to stored draft payloads; secrets stripped from exports.
  - HITL/risk/egress constraints must pass validation before publish in Prod/Training modes.
- **Acceptance Criteria**:
  - Admin can create a capsule with skin + UI module + adapter + settings schema, validate, sign, export `.tgz/.sig`, and install it via the existing install path without editing files manually.
  - Build logs and audit entries include capsule id/version and user; draft history preserved.
  - Validation blocks publish if required fields or policy gates are unmet; Dev override is explicit and logged.

### 14.7 Marketplace & Versioned Capsule Model (Hub + Agent)
- **Shared domain types**:
  - `Capsule` (id, name, description, owner_vendor_id, tags/category, latest_version)
  - `CapsuleVersion` (capsule_id, semver version, manifest YAML/JSON, input_schema, output_schema, runtime_engine=orchestrator|local|external, status=draft|published|deprecated)
  - `CapsuleManifest` (steps graph, resources: tools/models/secrets, policies: limits/egress/HITL, dependencies)
  - `CapsuleRun` (run_id, capsule_version_id, status, input, result_ref)
- **Hub services**:
  - **Capsule Registry (task_capsule_repo)**: source of truth for Capsule + CapsuleVersion; endpoints GET/POST capsules, versions, publish.
  - **Marketplace Manager (new)**: maps Capsule ↔ Mercur product/price; manages licenses/entitlements and agent installations; generates signed artifact URLs; hides Mercur from agents.
    - Entities: `CapsulePlan`, `License`, `AgentInstallation`.
    - API to Agent: `GET /marketplace/capsules`, `GET /marketplace/capsules/{id}`, `POST /marketplace/install`, `GET /marketplace/updates`, `POST /marketplace/telemetry`.
  - **Orchestrator**: Temporal workflows for `CapsuleRun`; fetches CapsuleVersion, validates input, executes steps, stores results, updates status.
  - **Agent Runtime**: executes steps when orchestrator delegates; unaware of marketplace/licensing.
- **Agent modules**:
  - `MarketplaceClient` (talks only to Hub Marketplace Manager): list/get/install/check_updates/send_telemetry.
  - `CapsuleInstaller`: consumes install payload (capsule_id, version, artifact_url, manifest); downloads, verifies, registers LocalCapsule.
  - Local registry: tracks installed versions/status; reconciles with Hub `AgentInstallation`.
  - GUI: Marketplace tab (browse/install/update), Installed tab (local state), Run action chooses Hub-orchestrated path (preferred for long jobs) or local quick-run for small manifests.
- **Flows**:
  - Browse/Install: Agent GUI → Hub list → POST install → Hub handles license/entitlement → returns artifact_url + manifest → Agent installs → reports status.
  - Run (recommended): Agent → Hub `/v1/capsules/{id}/runs` → Orchestrator → Agent Runtime/tools/object store → Agent polls run status.
  - Run (local fast path): allowed for short/simple capsules; honor runtime_engine flag and policy limits.
- **Policy/Licensing**:
  - Entitlement check before install/update/run; license state stored via Marketplace Manager.
  - Telemetry from Agent to Hub for usage/billing.
  - Artifact retrieval always checksum/signature verified on Agent side.
- **SRS Actions**:
  - Split data model: add `Capsule` + `CapsuleVersion` tables and APIs mirroring Hub; keep `CapsuleInstance` as runtime record mapped to `CapsuleRun`.
  - Document Marketplace Manager module, its API, and Agent integration components.
  - Add `runtime_engine` and entitlement/telemetry requirements to manifest and installer flow.

## 15. Appendices

### Appendix A: File Size Summary (Post-Refactor)

| Module | Before | After | Reduction |
|--------|--------|-------|-----------|
| ConversationWorker | 3022 | 178 | 94% |
| Agent | 4092 | 400 | 90% |
| ToolExecutor | 748 | 147 | 80% |
| TaskScheduler | 1276 | 284 | 78% |
| Gateway | 438 | 97 | 78% |
| CoreTasks | 764 | 215 | 72% |
| MCPHandler | 1087 | 319 | 71% |
| Memory | 1010 | 348 | 66% |
| Settings | 1793 | 610 | 66% |
| **TOTAL** | **14,230** | **2,598** | **82%** |

### Appendix B: SomaBrain API Reference

See `.kiro/steering/somabrain-api.md` for complete API documentation.

### Appendix C: Environment Variables

See `.kiro/steering/tech.md` for complete environment variable reference.

---

## 16. Multimodal Capabilities Extension (SRS‑MMX‑2025‑12‑16)

### 16.1 Overview

**Document ID:** SRS‑MMX‑2025‑12‑16  
**Version:** 1.0  
**Status:** PLANNED  
**Feature Flag:** `SA01_ENABLE_multimodal_capabilities` (default: false)

This section extends SomaAgent01 with **multimodal generation and consumption capabilities** (images, diagrams, screenshots, video) while preserving existing provider integrations and operational guarantees.

**Multimodal Scope**:
- **Asset Creation**: Images, diagrams, annotated screenshots, short videos (provider-dependent)
- **Asset Consumption**: Attaching and referencing images/video frames as context (vision models)
- **SRS Authoring**: Generating ISO 29148-style documents with embedded/linked assets

**Architecture Components** (A–E):
- **A — Policy Graph Router**: Deterministic routing + fallback ladders (always-on)
- **E — Capability Registry**: Tool/model discovery substrate (always-on)
- **C — Producer + Critic**: Quality gating loop (policy-gated, off by default)
- **D — Task DSL + Compiler**: Structured job plan format + compilation (always-on)
- **B — Portfolio Selector**: Ranking optimizer using SomaBrain outcomes (shadow mode → opt-in)

### 16.2 Component Architecture

```
User Request → Context Builder (multimodal-aware) → LLM Plan Extraction → Task DSL JSON
   ↓
Plan Compiler (D) → Executable DAG → For each step:
   ↓
Capability Registry (E).find_candidates(modality, constraints)
   ↓
Policy Graph Router (A): OPA filter + budget + fallback ladder
   ↓
Portfolio Ranker (B): SomaBrain outcomes → ranked list (shadow/active)
   ↓
ToolExecutor.multimodal_dispatch(): Execute with fallback
   ↓
Asset Created → AssetStore → Provenance Recorded
   ↓
[Optional] Asset Critic (C): Quality evaluation → Pass/Rework/Fail
   ↓
Outcome Feedback → SomaBrain
   ↓
All Steps Complete → SRS Composer → Document + Asset Bundle + Provenance
```

### 16.3 Data Model

#### 16.3.1 New Database Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `multimodal_assets` | Asset storage (image/video/diagram) | id, tenant_id, asset_type, format, storage_path, content (bytea), checksum, metadata |
| `multimodal_capabilities` | Tool/model registry | id, tool_id, provider, modalities[], input_schema, output_schema, constraints, cost_tier, health_status |
| `multimodal_job_plans` | Task DSL storage | id, tenant_id, plan_json, status, created_at |
| `multimodal_executions` | Execution history | id, plan_id, step_index, tool_id, provider, status, asset_id, latency_ms, cost_estimate, quality_score |
| `asset_provenance` | Audit trail | asset_id, request_id, execution_id, prompt_summary, generation_params, user_id |

#### 16.3.2 Storage Strategy

- **Primary**: S3-compatible object storage (scalable, cost-effective)
- **Fallback**: PostgreSQL `bytea` column (MVP/dev environments)
- **Deduplication**: SHA256 checksums prevent duplicate storage
- **Versioning**: Same content = same hash; regenerations create new versions

### 16.4 Component A: Policy Graph Router

**Deterministic Fallback Ladders** per modality + task type:

| Ladder Key | Primary | Fallback 1 | Fallback 2 | Fallback 3 | Terminal |
|-----------|---------|------------|------------|------------|----------|
| `image_diagram` | `mermaid_svg` | `plantuml_png` | `matplotlib_png` | `dalle_raster` | controlled_failure |
| `image_photo` | `dalle3` | `dalle2` | `stable_diffusion` | — | controlled_failure |
| `screenshot` | `playwright_capture` | `selenium_screenshot` | user_upload | — | controlled_failure |
| `video_short` | `runway_gen2` | `pika_labs` | `storyboard_frames` | — | controlled_failure |

**OPA Integration**:
- Action: `multimodal.tool.execute`
- Filters: Provider allowlists, budget constraints, data classification
- Enforcement: Pre-execution + per-fallback-attempt

### 16.5 Component B: Portfolio Selector (Learning)

**Ranking Algorithm**:
1. Query SomaBrain for historical outcomes (`task_type`, `modality`)
2. Compute metrics: `success_rate`, `avg_latency`, `avg_quality`, `avg_cost`
3. Weighted score:
   ```
   score = 0.4·success_rate + 0.2·(1-norm_latency) + 0.3·quality + 0.1·(1-norm_cost)
   ```
4. Sort candidates by score (descending)

**Modes**:
- **Shadow Mode** (default): Ranks but doesn't decide; logs divergence
- **Active Mode** (opt-in): Ranking used as tie-breaker within policy-allowed set

**Safety**: B never overrides hard constraints (A's OPA/budgets/health).

### 16.6 Component C: Producer + Critic (Quality Gating)

**Quality Evaluation Flow**:
1. **Producer** generates asset (image/diagram/video)
2. **Critic** evaluates against rubric (vision model for images, heuristics for diagrams)
3. **Pass** → Store asset, continue
4. **Fail** → Re-prompt with feedback (bounded attempts: MAX_REWORK=2)
5. **Exhausted** → Advance to fallback ladder

**Vision Model Integration**:
- Primary: GPT-4 Vision
- Fallback: Claude 3 Opus (vision)
- Fallback: Heuristics (resolution, file size, metadata)

**Rubric Schema**:
```json
{
  "criteria": [
    {"dimension": "clarity", "weight": 0.4, "threshold": 0.7},
    {"dimension": "relevance", "weight": 0.3, "threshold": 0.6},
    {"dimension": "aesthetic", "weight": 0.3, "threshold": 0.5}
  ],
  "min_overall_score": 0.65
}
```

### 16.7 Component D: Task DSL & Compiler

**Task DSL v1.0 JSON Schema** (simplified):
```json
{
  "version": "1.0",
  "tasks": [
    {
      "task_id": "step_00",
      "step_type": "generate_diagram",
      "modality": "image",
      "depends_on": [],
      "description": "System architecture diagram",
      "constraints": {"max_resolution": 1920, "format": "svg"},
      "quality_gate": {"enabled": true, "rubric": {...}},
      "user_defaults": {"provider": "mermaid"}
    }
  ],
  "budget": {"max_cost_cents": 500, "max_duration_sec": 300}
}
```

**Compiler Output**: Executable DAG with topological ordering of steps.

**Validation**:
- No circular dependencies
- All `depends_on` references exist
- Modality + step_type compatibility
- Positive budgets

### 16.8 Component E: Capability Registry

**Registration Example**:
```python
await registry.register(
    tool_id="dalle3_image_gen",
    provider="openai",
    modalities=["image"],
    input_schema={"type": "object", "required": ["prompt"], ...},
    output_schema={"type": "object", "properties": {"format": "png", ...}},
    constraints={"max_resolution": 1792, "supported_formats": ["png"]},
    cost_tier="high"
)
```

**Health Checks**: Periodic (60s cron) + on-demand + circuit breaker triggers.

### 16.9 Integration with Existing Architecture

#### 16.9.1 Gateway Service Extensions

**New Routes** (`services/gateway/main.py`):
- `GET /v1/multimodal/capabilities` → List tools/models by modality
- `POST /v1/multimodal/jobs` → Submit job plan
- `GET /v1/multimodal/jobs/{id}` → Job status
- `GET /v1/multimodal/assets/{id}` → Download asset
- `GET /v1/multimodal/provenance/{asset_id}` → Audit trail

#### 16.9.2 ToolExecutor Extensions

**New Method**: `multimodal_dispatch(tool_name, args, tenant_id, session_id, execution_id)`
- Routes to image_gen, diagram_gen, screenshot, video tools
- Integrates PolicyGraphRouter for fallbacks
- Records executions to `multimodal_executions` table
- Triggers AssetCritic if quality gates enabled

#### 16.9.3 Provider Cards UI Extensions

**Existing `ui_settings` Extended**:
```json
{
  "provider_id": "openai",
  "modalities": ["text", "image"],
  "recommended_for": ["diagrams", "photorealistic images"],
  "multimodal_models": {
    "image": ["dall-e-3", "dall-e-2"],
    "vision": ["gpt-4-vision-preview"]
  }
}
```

### 16.10 Security & Governance

#### 16.10.1 OPA Policies

**File**: `policy/multimodal.rego`
```rego
package multimodal

allow_multimodal {
    input.tenant_plan in ["enterprise", "pro"]
}

allow_provider {
    input.modality == "image"
    input.provider in ["openai", "stability"]
}

allow_provider {
    input.modality == "video"
    input.provider in ["runway", "pika"]
    input.tenant_plan == "enterprise"  # Video enterprise-only
}

within_budget {
    input.cost_tier in ["free", "low"]
}
```

#### 16.10.2 Asset Encryption (Optional)

**Envelope Encryption**:
1. Generate Data Key (DEK) via KMS
2. Encrypt asset: `AES-256-GCM(content, DEK)`
3. Encrypt DEK: `KMS.encrypt(DEK, tenant_key_id)`
4. Store: `encrypted_content` + `encrypted_dek` in metadata

**Policy-Gated**: Enabled for data classification = "sensitive" or "confidential".

#### 16.10.3 Provenance Redaction

- **Full Prompts**: Redacted if policy denies `provenance.store_full_prompt`
- **Sensitive Params**: API keys, internal model IDs stripped
- **User Context**: PII scrubbed per GDPR/compliance rules

### 16.11 Observability & Metrics

#### 16.11.1 Prometheus Metrics

| Metric | Type | Labels | Purpose |
|--------|------|--------|---------|
| `multimodal_capability_selection_total` | Counter | modality, tool_id, provider, decision_source | Track tool selection |
| `multimodal_execution_latency_seconds` | Histogram | modality, tool_id, provider, status | Execution duration |
| `multimodal_execution_cost_estimate_cents` | Histogram | modality, tool_id, provider | Cost tracking |
| `multimodal_fallback_total` | Counter | modality, tool_id, fallback_reason | Fallback frequency |
| `multimodal_quality_score` | Histogram | modality, tool_id | Critic scores |
| `multimodal_rework_attempts_total` | Counter | modality, reason | Quality rework |
| `portfolio_ranker_shadow_divergence_total` | Counter | modality, task_type | Shadow mode deviation |

#### 16.11.2 OpenTelemetry Traces

**Span Structure**:
```
multimodal_job (root)
├── plan_extraction
│   └── llm_invoke
├── plan_compilation
├── step_00_generate_diagram
│   ├── capability_discovery
│   ├── policy_routing
│   ├── portfolio_ranking (optional)
│   ├── execution_attempt_0
│   │   ├── provider_api_call
│   │   └── asset_store_create
│   ├── provenance_record
│   └── quality_evaluation (optional)
└── srs_composition
```

### 16.12 Verification & Testing

#### 16.12.1 Unit Tests

- `test_capability_registry.py`: Modality matching, constraint filtering
- `test_policy_graph_router.py`: Fallback ladder construction, OPA integration
- `test_asset_store.py`: S3 + PostgreSQL hybrid storage
- `test_asset_critic.py`: Vision model evaluation, rubric scoring
- `test_portfolio_ranker.py`: SomaBrain outcomes ranking

#### 16.12.2 Integration Tests

- `test_multimodal_providers.py`: OpenAI DALL-E, Stability, Mermaid adapters
- `test_multimodal_job.py`: End-to-end job execution with assets
- `test_soma_outcomes.py`: Feedback loop to SomaBrain

#### 16.12.3 E2E Golden Tests

1. **"Generate SRS with Diagrams"**
   - Input: "Create ISO SRS with 2 architecture diagrams"
   - Verify: Plan extracted, diagrams generated, SRS markdown with embedded SVGs

2. **"Provider Failure → Fallback"**
   - Setup: Mock DALL-E 503 error
   - Verify: Fallback to Stability AI, success, fallback metric incremented

3. **"Quality Gate Rework"**
   - Setup: Mock Critic fails first attempt
   - Verify: Re-prompt, second attempt passes, rework metric = 1

#### 16.12.4 Chaos Tests

- **Circuit Breaker**: Repeated failures open circuit, skip primary provider
- **Partial Resume**: Kill process mid-job, resume from checkpoint

### 16.13 Performance Budgets

| Operation | P95 Target | P99 Max | Notes |
|-----------|------------|---------|-------|
| Capability Discovery | 50ms | 100ms | DB query |
| Policy Routing | 100ms | 200ms | Includes OPA |
| Portfolio Ranking | 200ms | 400ms | SomaBrain recall |
| Image Generation (DALL-E) | 15s | 30s | Provider latency |
| Diagram Rendering (Mermaid) | 2s | 5s | Local rendering |
| Quality Evaluation | 5s | 10s | Vision LLM call |
| SRS Composition (5 assets) | 3s | 7s | Asset retrieval + markdown |

### 16.14 Rollout Plan

1. **v1.0-alpha** (Dev/Test only)
   - Feature flag: `SA01_ENABLE_multimodal_capabilities=true` (default: false)
   - Components: A, D, E (Foundation, execution, registry)
   - Quality gates disabled

2. **v1.1-beta** (Single tenant pilot)
   - Enable for 1 enterprise pilot tenant
   - Add Component C (Quality Gates)
   - Portfolio Ranker (B) in shadow mode

3. **v1.2-rc** (Multi-tenant staging)
   - Enable for all test/staging tenants
   - Portfolio Ranker → active mode (opt-in)
   - Full SRS generation operational

4. **v2.0-prod** (General availability)
   - Gradual rollout: 10% → 50% → 100% production tenants
   - Monitor error rates, fallback counts, costs
   - Feature flag remains (per-tenant disable supported)

### 16.15 Dependencies & Prerequisites

- **PostgreSQL 14+**: For new tables (5 tables, 8 indexes)
- **S3-Compatible Storage**: MinIO/AWS S3 for asset storage (optional, PostgreSQL fallback)
- **Provider API Keys**: OpenAI (DALL-E, GPT-4V), Stability AI, Runway/Pika (video, optional)
- **OPA 0.40+**: For multimodal policy enforcement
- **SomaBrain v2.0+**: For outcome feedback and ranking
- **Existing Services**: Gateway, ToolExecutor, ConversationWorker (extended, not replaced)

### 16.16 Cost & Resource Implications

> [!WARNING]
> **Provider API Costs**: Image/video generation significantly higher than text.
> - DALL-E 3: $0.04-0.12 per image
> - Runway Gen-2: $0.05 per second of video
> - Per-tenant budgets enforced via OPA policies

**Object Storage**: Estimate 5-50 MB per job (images), 100-500 MB (videos).  
**Recommended**: S3 lifecycle policies (archive after 90 days, delete after 365 days).

### 16.17 Open Items (v1.0 Out of Scope)

- **Real-time Streaming Video**: Not supported (only short clips)
- **Arbitrary Long-Form Video Editing**: Out of scope
- **GPU-Heavy Local Rendering**: Requires deployment infrastructure changes
- **Multi-Asset Composition**: No inter-asset dependencies (e.g., overlay screenshot on diagram)

### 16.18 Acceptance Criteria

- [ ] All 5 database tables created with migrations
- [ ] CapabilityRegistry discovers tools by modality and constraints
- [ ] PolicyGraphRouter routes with fallback ladders (tested with chaos scenarios)
- [ ] AssetStore creates/retrieves assets from S3 or PostgreSQL
- [ ] Provenance recorded for every generated asset
- [ ] At least 3 provider adapters implemented (OpenAI DALL-E, Stability, Mermaid)
- [ ] Quality Critic evaluates image quality with vision model
- [ ] Portfolio Ranker queries SomaBrain outcomes (shadow mode functional)
- [ ] SRSComposer generates markdown with embedded images
- [ ] All API endpoints functional and tested
- [ ] OPA policies enforce modality permissions
- [ ] Unit tests: 90%+ coverage for new modules
- [ ] E2E golden test: "Generate SRS with diagrams" succeeds
- [ ] Chaos test: circuit breaker prevents cascade failures
- [ ] Zero VIBE violations (no TODO/stub/placeholder keywords)

### 16.19 Related Documents

- [MULTIMODAL_DESIGN.md](file:///Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgent01/docs/architecture/MULTIMODAL_DESIGN.md) — Detailed design
- [Implementation Plan](file:///Users/macbookpro201916i964gb1tb/.gemini/antigravity/brain/7ffdc83a-c828-4d31-afa5-ce22734eb669/implementation_plan.md) — Phased rollout plan
- [Task Breakdown](file:///Users/macbookpro201916i964gb1tb/.gemini/antigravity/brain/7ffdc83a-c828-4d31-afa5-ce22734eb669/task.md) — 12-phase implementation tasks

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Nov 2025 | System | Initial architecture documentation |
| 2.0 | Dec 2025 | Kiro | Complete architecture analysis, VIBE compliance verification |

---

*End of Document*
# Settings Persistence Requirements

## REQ-PERSIST-001: Feature Flags Database Persistence
**Priority:** HIGH  
**Status:** NOT IMPLEMENTED  
**Category:** Configuration Management

### Problem Statement
Currently, 14 feature flags are read-only from environment variables (`SA01_FEATURE_PROFILE`, `SA01_ENABLE_*`). These cannot be changed via UI and require container restart.

### Current State
```bash
# Environment variables only:
SA01_FEATURE_PROFILE=enhanced
SA01_ENABLE_sse_enabled=true
SA01_ENABLE_semantic_recall=true
SA01_ENABLE_browser_support=true
# ... 11 more flags
```

**Storage:** Environment variables only (not persisted)  
**Impact:** No UI control, requires restart, not tenant-specific

### Required Implementation

#### 1. Database Schema
```sql
CREATE TABLE feature_flags (
    id SERIAL PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT false,
    profile_override TEXT CHECK (profile_override IN ('minimal', 'standard', 'enhanced', 'max')),
    tenant TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_feature_flags_tenant ON feature_flags(tenant, key);
```

#### 2. Store Implementation
**File:** `services/common/feature_flags_store.py`
```python
class FeatureFlagsStore:
    async def get_flags(self, tenant: str) -> dict:
        """Get all feature flags for tenant."""
        pass
    
    async def set_flag(self, tenant: str, key: str, enabled: bool) -> bool:
        """Set feature flag."""
        pass
    
    async def get_profile(self, tenant: str) -> str:
        """Get feature profile (minimal/standard/enhanced/max)."""
        pass
```

#### 3. UI Integration
Add new section to `ui_settings`:
```json
{
  "id": "feature_flags",
  "tab": "system",
  "title": "Feature Flags",
  "description": "Enable/disable system features",
  "fields": [
    {"id": "profile", "title": "Feature Profile", "type": "select", 
     "options": ["minimal", "standard", "enhanced", "max"]},
    {"id": "sse_enabled", "title": "Server-Sent Events", "type": "toggle"},
    {"id": "semantic_recall", "title": "Semantic Memory Recall", "type": "toggle"},
    {"id": "browser_support", "title": "Browser Automation", "type": "toggle"}
    // ... 11 more flags
  ]
}
```

#### 4. Agent Reload Trigger
```python
# On flag change:
await agent_manager.reload_agent(tenant_id)
```

### Acceptance Criteria
- [ ] `feature_flags` table created and accessible
- [ ] UI exposes all 14 feature flags
- [ ] Changes persist to PostgreSQL
- [ ] Environment variables override database values
- [ ] Agent reloads on flag change (< 5s)
- [ ] Multi-tenant support (flags per tenant)

---

## REQ-PERSIST-002: AgentConfig UI Exposure
**Priority:** MEDIUM  
**Status:** NOT IMPLEMENTED  
**Category:** Configuration Management

### Problem Statement
5 AgentConfig settings are currently code-level only (`profile`, `knowledge_subdirs`, `memory_subdir`, `code_exec_ssh_*`, `additional`). These cannot be changed without modifying code.

### Current State
```python
# AgentConfig (code-level only):
@dataclass
class AgentConfig:
    profile: str = "enhanced"
    memory_subdir: str = ""
    knowledge_subdirs: list[str] = ["default", "custom"]
    code_exec_ssh_enabled: bool = True
    code_exec_ssh_addr: str = "localhost"
    code_exec_ssh_port: int = 55022
    code_exec_ssh_user: str = "root"
    # ... ssh_pass already in Vault
```

**Storage:** Python dataclass (not persisted)  
**Impact:** No UI control, hardcoded defaults

### Required Implementation

#### 1. Add to ui_settings
Extend `ui_settings` JSONB with new section:
```json
{
  "id": "agent_config",
  "tab": "system",
  "title": "Agent Configuration",
  "description": "Core agent behavior settings",
  "fields": [
    {"id": "profile", "title": "Agent Profile", "type": "select",
     "options": ["minimal", "standard", "enhanced", "max"], 
     "value": "enhanced"},
    {"id": "knowledge_subdirs", "title": "Knowledge Directories", 
     "type": "json", "value": ["default", "custom"]},
    {"id": "memory_subdir", "title": "Memory Subdirectory", 
     "type": "text", "value": ""},
    {"id": "code_exec_ssh_enabled", "title": "SSH Code Execution", 
     "type": "toggle", "value": true},
    {"id": "code_exec_ssh_addr", "title": "SSH Host", 
     "type": "text", "value": "localhost"},
    {"id": "code_exec_ssh_port", "title": "SSH Port", 
     "type": "number", "value": 55022},
    {"id": "code_exec_ssh_user", "title": "SSH User", 
     "type": "text", "value": "root"}
  ]
}
```

#### 2. AgentConfig Loader
```python
# Load from PostgreSQL instead of defaults:
async def load_agent_config(tenant: str) -> AgentConfig:
    settings = await ui_settings_store.get("global")
    agent_config_section = find_section(settings, "agent_config")
    
    return AgentConfig(
        profile=get_field(agent_config_section, "profile", "enhanced"),
        knowledge_subdirs=get_field(agent_config_section, "knowledge_subdirs", ["default"]),
        memory_subdir=get_field(agent_config_section, "memory_subdir", ""),
        code_exec_ssh_enabled=get_field(agent_config_section, "code_exec_ssh_enabled", True),
        # ...
    )
```

#### 3. Validation
```python
# Validate knowledge subdirectories exist:
async def validate_knowledge_subdirs(subdirs: list[str]) -> bool:
    for subdir in subdirs:
        path = Path(f"/knowledge/{subdir}")
        if not path.exists():
            raise ValueError(f"Knowledge subdirectory '{subdir}' does not exist")
    return True
```

### Acceptance Criteria
- [ ] UI exposes AgentConfig section with 7 fields
- [ ] Settings persist to `ui_settings` JSONB
- [ ] Agent initialization reads from database
- [ ] Directory path validation implemented
- [ ] Changes require agent reload
- [ ] Backward compatible with existing agents

---

## Implementation Summary

### Settings Persistence Status
**Total Settings:** 100+  
**Currently Persisted:** 80 (80%)  
**Remaining:** 20 (20%)

| Storage | Settings | Status |
|---------|----------|--------|
| PostgreSQL `ui_settings` | 60 | ✅ ACTIVE |
| Vault | 10 | ✅ ACTIVE |
| Environment (read-only) | 14 | ⚠️ REQ-PERSIST-001 |
| Code-level (no persistence) | 5 | ⚠️ REQ-PERSIST-002 |

### Dependencies
- REQ-PERSIST-001 depends on: PostgreSQL, Agent reload mechanism
- REQ-PERSIST-002 depends on: `ui_settings_store.py` extension

### Related Documents
- `COMPLETE_AGENT_SETTINGS_CATALOG.md` - Full settings list
- `services/common/ui_settings_store.py` - Current implementation
- `services/common/unified_secret_manager.py` - Vault integration


---
---

# APPENDIX D: SETTINGS PERSISTENCE REQUIREMENTS


# Settings Persistence Requirements

## REQ-PERSIST-001: Feature Flags Database Persistence
**Priority:** HIGH  
**Status:** NOT IMPLEMENTED  
**Category:** Configuration Management

### Problem Statement
Currently, 14 feature flags are read-only from environment variables (`SA01_FEATURE_PROFILE`, `SA01_ENABLE_*`). These cannot be changed via UI and require container restart.

### Current State
```bash
# Environment variables only:
SA01_FEATURE_PROFILE=enhanced
SA01_ENABLE_sse_enabled=true
SA01_ENABLE_semantic_recall=true
SA01_ENABLE_browser_support=true
# ... 11 more flags
```

**Storage:** Environment variables only (not persisted)  
**Impact:** No UI control, requires restart, not tenant-specific

### Required Implementation

#### 1. Database Schema
```sql
CREATE TABLE feature_flags (
    id SERIAL PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT false,
    profile_override TEXT CHECK (profile_override IN ('minimal', 'standard', 'enhanced', 'max')),
    tenant TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_feature_flags_tenant ON feature_flags(tenant, key);
```

#### 2. Store Implementation
**File:** `services/common/feature_flags_store.py`
```python
class FeatureFlagsStore:
    async def get_flags(self, tenant: str) -> dict:
        """Get all feature flags for tenant."""
        pass
    
    async def set_flag(self, tenant: str, key: str, enabled: bool) -> bool:
        """Set feature flag."""
        pass
    
    async def get_profile(self, tenant: str) -> str:
        """Get feature profile (minimal/standard/enhanced/max)."""
        pass
```

#### 3. UI Integration
Add new section to `ui_settings`:
```json
{
  "id": "feature_flags",
  "tab": "system",
  "title": "Feature Flags",
  "description": "Enable/disable system features",
  "fields": [
    {"id": "profile", "title": "Feature Profile", "type": "select", 
     "options": ["minimal", "standard", "enhanced", "max"]},
    {"id": "sse_enabled", "title": "Server-Sent Events", "type": "toggle"},
    {"id": "semantic_recall", "title": "Semantic Memory Recall", "type": "toggle"},
    {"id": "browser_support", "title": "Browser Automation", "type": "toggle"}
    // ... 11 more flags
  ]
}
```

#### 4. Agent Reload Trigger
```python
# On flag change:
await agent_manager.reload_agent(tenant_id)
```

### Acceptance Criteria
- [ ] `feature_flags` table created and accessible
- [ ] UI exposes all 14 feature flags
- [ ] Changes persist to PostgreSQL
- [ ] Environment variables override database values
- [ ] Agent reloads on flag change (< 5s)
- [ ] Multi-tenant support (flags per tenant)

---

## REQ-PERSIST-002: AgentConfig UI Exposure
**Priority:** MEDIUM  
**Status:** NOT IMPLEMENTED  
**Category:** Configuration Management

### Problem Statement
5 AgentConfig settings are currently code-level only (`profile`, `knowledge_subdirs`, `memory_subdir`, `code_exec_ssh_*`, `additional`). These cannot be changed without modifying code.

### Current State
```python
# AgentConfig (code-level only):
@dataclass
class AgentConfig:
    profile: str = "enhanced"
    memory_subdir: str = ""
    knowledge_subdirs: list[str] = ["default", "custom"]
    code_exec_ssh_enabled: bool = True
    code_exec_ssh_addr: str = "localhost"
    code_exec_ssh_port: int = 55022
    code_exec_ssh_user: str = "root"
    # ... ssh_pass already in Vault
```

**Storage:** Python dataclass (not persisted)  
**Impact:** No UI control, hardcoded defaults

### Required Implementation

#### 1. Add to ui_settings
Extend `ui_settings` JSONB with new section:
```json
{
  "id": "agent_config",
  "tab": "system",
  "title": "Agent Configuration",
  "description": "Core agent behavior settings",
  "fields": [
    {"id": "profile", "title": "Agent Profile", "type": "select",
     "options": ["minimal", "standard", "enhanced", "max"], 
     "value": "enhanced"},
    {"id": "knowledge_subdirs", "title": "Knowledge Directories", 
     "type": "json", "value": ["default", "custom"]},
    {"id": "memory_subdir", "title": "Memory Subdirectory", 
     "type": "text", "value": ""},
    {"id": "code_exec_ssh_enabled", "title": "SSH Code Execution", 
     "type": "toggle", "value": true},
    {"id": "code_exec_ssh_addr", "title": "SSH Host", 
     "type": "text", "value": "localhost"},
    {"id": "code_exec_ssh_port", "title": "SSH Port", 
     "type": "number", "value": 55022},
    {"id": "code_exec_ssh_user", "title": "SSH User", 
     "type": "text", "value": "root"}
  ]
}
```

#### 2. AgentConfig Loader
```python
# Load from PostgreSQL instead of defaults:
async def load_agent_config(tenant: str) -> AgentConfig:
    settings = await ui_settings_store.get("global")
    agent_config_section = find_section(settings, "agent_config")
    
    return AgentConfig(
        profile=get_field(agent_config_section, "profile", "enhanced"),
        knowledge_subdirs=get_field(agent_config_section, "knowledge_subdirs", ["default"]),
        memory_subdir=get_field(agent_config_section, "memory_subdir", ""),
        code_exec_ssh_enabled=get_field(agent_config_section, "code_exec_ssh_enabled", True),
        # ...
    )
```

#### 3. Validation
```python
# Validate knowledge subdirectories exist:
async def validate_knowledge_subdirs(subdirs: list[str]) -> bool:
    for subdir in subdirs:
        path = Path(f"/knowledge/{subdir}")
        if not path.exists():
            raise ValueError(f"Knowledge subdirectory '{subdir}' does not exist")
    return True
```

### Acceptance Criteria
- [ ] UI exposes AgentConfig section with 7 fields
- [ ] Settings persist to `ui_settings` JSONB
- [ ] Agent initialization reads from database
- [ ] Directory path validation implemented
- [ ] Changes require agent reload
- [ ] Backward compatible with existing agents

---

## Implementation Summary

### Settings Persistence Status
**Total Settings:** 100+  
**Currently Persisted:** 80 (80%)  
**Remaining:** 20 (20%)

| Storage | Settings | Status |
|---------|----------|--------|
| PostgreSQL `ui_settings` | 60 | ✅ ACTIVE |
| Vault | 10 | ✅ ACTIVE |
| Environment (read-only) | 14 | ⚠️ REQ-PERSIST-001 |
| Code-level (no persistence) | 5 | ⚠️ REQ-PERSIST-002 |

### Dependencies
- REQ-PERSIST-001 depends on: PostgreSQL, Agent reload mechanism
- REQ-PERSIST-002 depends on: `ui_settings_store.py` extension

### Related Documents
- `COMPLETE_AGENT_SETTINGS_CATALOG.md` - Full settings list
- `services/common/ui_settings_store.py` - Current implementation
- `services/common/unified_secret_manager.py` - Vault integration
