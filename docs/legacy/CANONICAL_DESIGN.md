?
# SomaAgent01 — Canonical Design Specification

**Document ID:** SA01-DESIGN-CANONICAL-2025-12  
**Version:** 4.0  
**Date:** 2025-12-21  
**Status:** CANONICAL — Single Source of Truth

---

## 1. Introduction

This document defines the unified architectural design for SomaAgent01. It enforces Clean Architecture (DDD), specifies integration of security components (OPA, TUS, ClamAV), details the modern Web UI implementation, and covers multimodal capabilities.

---

## 2. High-Level Architecture

### 2.1 System Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│  CLIENT LAYER (Web UI, CLI, A2A, MCP)                           │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP/WebSocket
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  GATEWAY SERVICE (Port 8010)                                    │
│  - FastAPI routing                                              │
│  - Auth, rate limiting, circuit breakers                        │
│  - Session management, uploads, admin endpoints                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Kafka: conversation.inbound
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  CONVERSATION WORKER                                            │
│  - ProcessMessageUseCase (orchestration)                        │
│  - GenerateResponseUseCase (LLM invoke)                         │
│  - StoreMemoryUseCase (SomaBrain integration)                   │
│  - BuildContextUseCase (context assembly)                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Kafka: tool.requests
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  TOOL EXECUTOR                                                  │
│  - Sandboxed execution                                          │
│  - Policy enforcement (OPA)                                     │
│  - Result publishing                                            │
│  - Memory capture                                               │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  SOMABRAIN SERVICE (Port 9696)                                  │
│  - Memory storage/recall                                        │
│  - Neuromodulation state                                        │
│  - Adaptation weights                                           │
│  - Sleep cycle (consolidation)                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Layered Architecture (Clean Architecture)

The system obeys the Dependency Rule: *Source code dependencies can only point inwards.*

```mermaid
graph TD
    subgraph Infrastructure ["Infrastructure (Outer)"]
        Web[FastAPI Controllers]
        DB[Postgres/Chroma Adapter]
        Bus[Kafka Adapter]
        Ext[SomaBrain/OPA Client]
    end

    subgraph Application ["Application (Middle)"]
        UC[Use Cases / Interactors]
        Services[Domain Services]
    end

    subgraph Domain ["Domain (Inner)"]
        Entities[Entities & Aggregates]
        VO[Value Objects]
        Ports[Repository Interfaces]
    end

    Web --> UC
    UC --> Ports
    UC --> Entities
    Infrastructure -.-> Ports : implements
```

### 2.3 Directory Structure

```
src/
├── core/
│   ├── domain/               # Pure business logic
│   │   ├── entities/
│   │   ├── value_objects/
│   │   ├── ports/            # Interfaces for repos/gateways
│   │   └── exceptions.py
│   ├── application/          # Use Cases
│   │   ├── use_cases/
│   │   └── dtos/
│   ├── infrastructure/       # Implementations
│   │   ├── persistence/
│   │   ├── adapters/         # OPA, SomaBrain, FileSystem adapters
│   │   └── config/           # ConfigFacade
│   └── main.py              # App Assembly
├── services/                 # Microservices/Modules
│   ├── gateway/              # API Gateway
│   ├── conversation_worker/  # Message Processor
│   ├── tool_executor/        # Tool Execution
│   ├── multimodal/           # Multimodal Providers
│   └── common/               # Shared utilities
```

---

## 3. Component Design

### 3.1 Configuration System

**Pattern:** Singleton Facade
- **Class:** `ConfigFacade`
- **Responsibility:** Aggregates environment variables (`SA01_` prefix), CLI args, and Secrets (Vault)
- **Usage:** `cfg.env("KEY")` everywhere. No direct `os.getenv`

### 3.2 Security Subsystems

#### A. Authorization (OPA)

- **Integration:** `OPAPolicyAdapter` implements `PolicyPort`
- **Flow:**
  1. Agent attempts tool execution
  2. `ToolExecutor` calls `PolicyPort.evaluate(action, resource, context)`
  3. Adapter queries OPA Service via HTTP
  4. If `allow: false`, execution halts

#### B. File Security (Uploads)

- **Protocol:** TUS (Resumable Uploads)
- **Storage:** `UploadsRepository` (Metadata in DB, content in implementation-specific store)
- **Scanning Pipeline:**
  1. User Uploads → `temp_storage`
  2. `ClamAVScanner` scans stream
  3. If Clean → Move to `permanent_storage`
  4. If Malware → Quarantine & Alert

### 3.3 Web UI Architecture

#### A. Frontend Stack

- **Framework:** Vanilla JS + Alpine.js (Reactive State)
- **Design System:** CSS Variables (Glassmorphism theme)
- **Build:** Vite (optional, mostly ESM)

#### B. State Management (Store Pattern)

- Each feature (Chat, Settings, Memory) has a `store.js`
- **Pattern:** `createStore(initialState, actions)`
- **Reactivity:** Alpine.js `x-data="$store.feature"`

#### C. Communication

- **REST:** Standard JSON APIs for CRUD
- **SSE:** `/v1/sessions/{id}/events` for chat streaming and live updates

---

## 4. SomaBrain Integration Architecture

### 4.1 Integration Layer

```
┌─────────────────────────────────────────────────────────────────────┐
│                         SomaAgent01                                  │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌──────────────────────┐                    │
│  │   agent.py      │───▶│  cognitive.py        │                    │
│  │   (Main Agent)  │    │  (Neuromodulation)   │                    │
│  └────────┬────────┘    └──────────┬───────────┘                    │
│           │                        │                                 │
│           ▼                        ▼                                 │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │              somabrain_integration.py                           ││
│  │  (store_memory, recall_memories, get_adaptation_state,          ││
│  │   get_neuromodulators, update_neuromodulators, etc.)            ││
│  └────────────────────────────┬────────────────────────────────────┘│
│                               │                                      │
│                               ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    soma_client.py                               ││
│  │  (SomaClient singleton with circuit breaker, retry, metrics)    ││
│  └────────────────────────────┬────────────────────────────────────┘│
└───────────────────────────────┼─────────────────────────────────────┘
                                │ HTTP/HTTPS
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         SomaBrain (Port 9696)                        │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ Memory API   │  │ Context API  │  │ Cognitive    │               │
│  │ /memory/*    │  │ /context/*   │  │ /plan, /act  │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ Neuromod API │  │ Sleep API    │  │ Admin API    │               │
│  │ /neuromod*   │  │ /sleep/*     │  │ /admin/*     │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 SomaClient Design Principles

1. **Single Responsibility**: Each method wraps exactly one SomaBrain endpoint
2. **Fail-Fast**: Circuit breaker opens after 3 consecutive failures, 15s cooldown
3. **Observability**: All requests emit Prometheus metrics and propagate OpenTelemetry traces
4. **Type Safety**: All methods return `Mapping[str, Any]` with full type hints
5. **VIBE Compliance**: No mocks, no placeholders, real implementations only

### 4.3 New SomaClient Methods

#### Adaptation Reset

```python
async def adaptation_reset(
    self,
    *,
    tenant_id: Optional[str] = None,
    base_lr: float = 0.01,
    reset_history: bool = True,
) -> Mapping[str, Any]:
    """Reset adaptation engine to defaults."""
    body: Dict[str, Any] = {
        "base_lr": base_lr,
        "reset_history": reset_history,
    }
    if tenant_id:
        body["tenant_id"] = tenant_id
    return await self._request("POST", "/context/adaptation/reset", json=body)
```

#### Action Execution

```python
async def act(
    self,
    *,
    task_key: str,
    context: Optional[Mapping[str, Any]] = None,
    max_steps: int = 5,
    tenant_id: Optional[str] = None,
) -> Mapping[str, Any]:
    """Execute an action/task with salience scoring."""
    body: Dict[str, Any] = {
        "task_key": task_key,
        "max_steps": max_steps,
    }
    if context:
        body["context"] = dict(context)
    if tenant_id:
        body["tenant_id"] = tenant_id
    return await self._request("POST", "/act", json=body)
```

#### Admin Service Management (ADMIN MODE ONLY)

```python
async def list_services(self) -> Mapping[str, Any]:
    """List all cognitive services (ADMIN mode only)."""
    return await self._request("GET", "/admin/services")

async def start_service(self, name: str) -> Mapping[str, Any]:
    """Start a cognitive service (ADMIN mode only)."""
    return await self._request("POST", f"/admin/services/{name}/start")

async def stop_service(self, name: str) -> Mapping[str, Any]:
    """Stop a cognitive service (ADMIN mode only)."""
    return await self._request("POST", f"/admin/services/{name}/stop")
```

#### Sleep State Transitions

```python
async def brain_sleep_mode(
    self,
    *,
    target_state: str,
    ttl_seconds: Optional[int] = None,
    async_mode: bool = False,
    trace_id: Optional[str] = None,
) -> Mapping[str, Any]:
    """Transition cognitive sleep state."""
    body: Dict[str, Any] = {
        "target_state": target_state,
        "async_mode": async_mode,
    }
    if ttl_seconds is not None:
        body["ttl_seconds"] = ttl_seconds
    if trace_id:
        body["trace_id"] = trace_id
    return await self._request("POST", "/api/brain/sleep_mode", json=body)
```

---

## 5. Multimodal Extension Architecture

**Feature Flag:** `SA01_ENABLE_multimodal_capabilities` (default: false)

### 5.1 Multimodal Flow (End-to-End)

```
User: "Generate SRS with architecture diagrams"
    ↓
Gateway → ConversationWorker
    ↓
ContextBuilder (multimodal-aware)
    ↓
LLM Plan Extraction → Task DSL JSON
    ↓
Plan Compiler (D) → Executable DAG
    ↓
For each step:
    ├─ Capability Registry (E).find_candidates(modality, constraints)
    ├─ Policy Graph Router (A): OPA filter + budget + deterministic selection
    ├─ Portfolio Ranker (B): SomaBrain outcomes → ranked list (shadow/active)
    ├─ ToolExecutor.multimodal_dispatch()
    │   ├─ Execute selected provider
    │   ├─ AssetStore.create() → S3/PostgreSQL
    │   ├─ ProvenanceRecorder → Audit trail
    │   └─ [Optional] AssetCritic (C) → Quality evaluation
    └─ SomaClient.context_feedback() → Record outcome
    ↓
SRSComposer → Markdown + Assets + Provenance
    ↓
Response to user
```

### 5.2 Component Details

#### A — Policy Graph Router (Deterministic Selection)

- **Selection Order:** First eligible candidate by registry priority and policy constraints
- **OPA Integration:** Pre-execution policy checks for the selected provider
- **Budget Enforcement:** Cost tier filtering, quota tracking

#### B — Portfolio Selector (Learning)

- **Ranking Algorithm:**
  ```
  score = 0.4·success_rate + 0.2·(1-norm_latency) + 0.3·quality + 0.1·(1-norm_cost)
  ```
- **Modes:**
  - Shadow (default): Ranks but doesn't decide, logs divergence
  - Active (opt-in): Ranking used as tie-breaker within A's allowed set
- **Safety:** B never overrides A's hard constraints (OPA, budget, health)

#### C — Producer + Critic (Quality Gating)

- **Flow:**
  1. Producer generates asset
  2. Critic evaluates against rubric
  3. Pass → Store asset
  4. Fail → Re-prompt with feedback (MAX_REWORK=2)
  5. Exhausted → Fail with surfaced error

#### D — Task DSL & Compiler

```json
{
  "version": "1.0",
  "tasks": [
    {
      "task_id": "step_00",
      "step_type": "generate_diagram",
      "modality": "image",
      "depends_on": [],
      "constraints": {"max_resolution": 1920, "format": "svg"},
      "quality_gate": {"enabled": true, "rubric": {...}}
    }
  ]
}
```

#### E — Capability Registry

```python
registry.register(
    tool_id="dalle3_image_gen",
    provider="openai",
    modalities=["image"],
    constraints={"max_resolution": 1792},
    cost_tier="high"
)
```

---

## 6. Data Model

### 6.1 Core PostgreSQL Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| session_envelopes | Session metadata | session_id, tenant, created_at |
| session_events | Event timeline | session_id, event_type, occurred_at |
| dlq_messages | Dead letter queue | topic, event, error |
| attachments | File storage | id, filename, sha256, content |
| audit_events | Audit log | action, tenant, session_id, timestamp |

### 6.2 Multimodal Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| multimodal_assets | Asset storage | id, tenant_id, asset_type, format, storage_path, checksum |
| multimodal_capabilities | Tool/model registry | tool_id, provider, modalities[], cost_tier, health_status |
| multimodal_job_plans | Task DSL storage | id, tenant_id, plan_json, status |
| multimodal_executions | Execution history | plan_id, step_index, tool_id, status, quality_score |
| asset_provenance | Audit trail | asset_id, request_id, execution_id, prompt_summary |

### 6.3 Redis Key Patterns

| Pattern | Purpose | TTL |
|---------|---------|-----|
| `session:{id}` | Session cache | Configurable |
| `policy:requeue:{id}` | Blocked events | 3600s |
| `dedupe:{key}` | Idempotency | 3600s |
| `rate_limit:{tenant}` | Rate limiting | Window-based |

### 6.4 Kafka Topics

| Topic | Producer | Consumer | Purpose |
|-------|----------|----------|---------|
| conversation.inbound | Gateway | ConversationWorker | User messages |
| conversation.outbound | Worker | Gateway (SSE) | Responses |
| tool.requests | Worker | ToolExecutor | Tool execution |
| tool.results | ToolExecutor | Worker | Tool results |
| audit.events | All | AuditWorker | Audit trail |
| dlq.events | SafeTask | Admin | Failed tasks |

---

## 7. Security Architecture

### 7.1 Authentication Layers

- **External:** Bearer Token / API Key
- **Internal:** X-Internal-Token (service-to-service mTLS)
- **OPA:** Policy evaluation for all actions

### 7.2 Authorization Matrix

| Action | Resource | Enforced By |
|--------|----------|-------------|
| conversation.send | message | ConversationPolicyEnforcer |
| tool.execute | tool_name | ToolExecutor |
| memory.write | somabrain | ResultPublisher |
| multimodal.tool.execute | tool_id/provider | PolicyGraphRouter |
| admin.* | services | Gateway (ADMIN mode only) |

### 7.3 Hardening Measures

- TLS 1.3 only, mTLS, HSTS, OCSP stapling
- JWS request signing (kid, nonce, timestamp)
- Capsule supply chain (SHA-256, cosign/sigstore)
- Envelope encryption (per-request KMS data keys)
- Circuit breakers, exponential backoff
- Key rotation, HSM/KMS storage

---

## 8. Observability

### 8.1 Prometheus Metrics (Core)

- `somabrain_http_requests_total`, `somabrain_request_seconds`
- `conversation_worker_messages_total`, `conversation_worker_processing_seconds`
- `sa01_core_tasks_total`, `sa01_core_task_latency_seconds`
- `gateway_sse_connections`, `fsm_transition_total`

### 8.2 Prometheus Metrics (Multimodal)

- `multimodal_capability_selection_total`, `multimodal_execution_latency_seconds`
- `multimodal_execution_cost_estimate_cents`
- `multimodal_quality_score`, `multimodal_rework_attempts_total`
- `portfolio_ranker_shadow_divergence_total`, `capability_health_status`

### 8.3 OpenTelemetry Tracing

- **Span Hierarchy:** multimodal_job → plan_extraction → plan_compilation → step_NN → execution_attempt_N
- **Trace Context Propagation:** Gateway → Worker → ToolExecutor → Providers
- **Attributes:** job_id, step_id, modality, tool_id, provider, quality_score

---

## 9. Temporal Workflows & Orchestration

### 9.1 Temporal Topology

- **Namespace:** `somaagent01-dev`
- **Queues:** `conversation`, `tool-executor`, `a2a`, `maintenance`

### 9.2 Domain Workflows

| Workflow | Queue | Purpose |
|----------|-------|---------|
| ConversationWorkflow | conversation | ProcessMessageUseCase activity |
| ToolExecutorWorkflow | tool-executor | handle_tool_request activity |
| A2AWorkflow | a2a | Delegation gateway activity |
| MaintenanceWorkflow | maintenance | publish_metrics, cleanup_sessions |

### 9.3 Saga/Compensation Pattern

- Every workflow activity has a compensation step
- Compensations become child workflows/signals
- Cancellation maps to Temporal cancel + compensations

---

## 10. Transactional Integrity & Explainability

### 10.1 Patterns

- **ACID locally, Sagas globally:** Postgres mutations wrapped in transactions; cross-service flows use Temporal workflows
- **Idempotency & outbox:** Deterministic IDs; DB + Kafka publishes coupled via outbox
- **Cancellation:** User/operator cancel maps to Temporal cancel; activities heartbeat
- **Audit & explainability:** Structured audit rows per activity; gateway exposes "describe run/failure" endpoint

### 10.2 Reconciliation

- Periodic workflow compares saga records, DB state, and Kafka outbox
- Auto-heals orphaned operations
- Escalates unresolvable conflicts

---

## 11. Performance Budgets

| Operation | P95 Target | P99 Max |
|-----------|------------|---------|
| Capability Discovery | 50ms | 100ms |
| Policy Routing | 100ms | 200ms |
| Portfolio Ranking | 200ms | 400ms |
| Image Gen (DALL-E) | 15s | 30s |
| Diagram (Mermaid) | 2s | 5s |
| Quality Evaluation | 5s | 10s |
| SRS Composition (5 assets) | 3s | 7s |

---

## 12. Interfaces & Contracts

### 12.1 Domain Ports

**SessionRepositoryPort:**
```python
class SessionRepositoryPort(ABC):
    @abstractmethod
    async def get_session(self, session_id: str) -> Session: ...
    @abstractmethod
    async def save_session(self, session: Session) -> None: ...
```

**PolicyAdapterPort:**
```python
class PolicyAdapterPort(ABC):
    @abstractmethod
    async def check_tool_access(self, tenant_id: str, tool_name: str) -> bool: ...
```

---

## 13. Error Handling Strategy

### 13.1 Error Categories

| Category | HTTP Status | Action |
|----------|-------------|--------|
| Client Error | 400-499 | Raise immediately |
| Server Error | 500-599 | Retry with backoff, then raise |
| Network Error | N/A | Retry with backoff, increment circuit breaker |
| Timeout | N/A | Retry with backoff, increment circuit breaker |

### 13.2 Circuit Breaker Configuration

```python
_CB_THRESHOLD: int = 3      # Failures before opening
_CB_COOLDOWN_SEC: float = 15.0  # Seconds before retry
```

---

## 14. Deployment Architecture

### 14.1 Service Topology

```
Gateway (FastAPI) ─┐
                   ├→ Kafka Cluster
ToolExecutor ──────┘   │
    │                  │
    └→ PostgreSQL      │
    └→ Redis           │
    └→ S3/MinIO        │
    └→ SomaBrain ──────┘
```

### 14.2 Horizontal Scaling

- **ToolExecutor:** Stateless replicas, scale on P95 latency
- **Bottlenecks:** Provider API limits, S3 write throughput, SomaBrain query latency
- **Mitigations:** Per-tenant quotas (OPA), async S3 upload, SomaBrain outcome caching

---

## 15. Related Documents

- **Requirements:** `CANONICAL_REQUIREMENTS.md`
- **Tasks:** `AGENT_TASKS.md`
- **VIBE Rules:** `docs/development/VIBE_CODING_RULES.md`

---

**Last Updated:** 2025-12-21  
**Maintained By:** Development Team
