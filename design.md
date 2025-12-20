# SomaAgent01 — Architectural Design

**Document ID:** SA01-DESIGN-2025-12  
**Version:** 3.0  
**Date:** 2025-12-16  
**Status:** VERIFIED + MULTIMODAL EXTENSION PLANNED

---

## Overview

This document provides the high-level architectural design for SomaAgent01, covering system components, data flows, integration points, and the multimodal capabilities extension.

**Full Design:** See [`docs/architecture/MULTIMODAL_DESIGN.md`](docs/architecture/MULTIMODAL_DESIGN.md) for complete multimodal design (500+ lines).

---

## System Architecture

### High-Level Component Diagram

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

---

## Data Flow Architecture

### Message Processing Pipeline

```
User Message
    ↓
Gateway (/v1/llm/invoke)
    ↓
Kafka (conversation.inbound)
    ↓
ConversationWorker.ProcessMessageUseCase
    ├─ MessageAnalyzer → Intent/sentiment/tags
    ├─ PolicyEnforcer → OPA authorization
    ├─ SessionRepository → Store user message (PostgreSQL)
    ├─ SomaClient.remember() → Store to SomaBrain
    ├─ ContextBuilder → Build LLM context
    ├─ GenerateResponseUseCase → LLM invoke (stream)
    ├─ SessionRepository → Store assistant message
    ├─ SomaClient.remember() → Store response to SomaBrain
    └─ Kafka (conversation.outbound) → Publish response
    ↓
Gateway (SSE stream)
    ↓
Client (UI renders response)
```

### Tool Execution Flow

```
Tool Request
    ↓
ToolExecutor.RequestHandler
    ├─ Validate request
    ├─ Audit start
    ├─ OPA policy check
    ├─ ToolRegistry lookup
    ├─ Publish tool.start event
    ├─ ExecutionEngine.execute()
    ├─ ResultPublisher
    │   ├─ Validate result
    │   ├─ Store to session
    │   ├─ Publish to Kafka (tool.results)
    │   ├─ Emit telemetry
    │   ├─ SomaClient.context_feedback()
    │   └─ SomaClient.remember() (if policy allows)
    └─ Audit finish
```

---

## Multimodal Extension Architecture

**Feature Flag:** `SA01_ENABLE_multimodal_capabilities` (default: false)

### Multimodal Flow (End-to-End)

```
User: "Generate SRS with architecture diagrams"
    ↓
Gateway → ConversationWorker
    ↓
ContextBuilder (multimodal-aware)
    ↓
LLM Plan Extraction → Task DSL JSON
    {
      "tasks": [
        {"task_id": "step_00", "step_type": "generate_diagram", ...},
        {"task_id": "step_01", "step_type": "compose_srs", ...}
      ]
    }
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
    │   └─ [Optional] AssetCritic (C) → Quality evaluation → Pass/Rework/Fail
    └─ SomaClient.context_feedback() → Record outcome
    ↓
All steps complete
    ↓
SRSComposer → Markdown + Assets + Provenance
    ↓
Response to user
```

### Component Details

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
  2. Critic evaluates against rubric (vision model for images, heuristics for diagrams)
  3. Pass → Store asset
  4. Fail → Re-prompt with feedback (bounded: MAX_REWORK=2)
  5. Exhausted → Fail with a surfaced error
- **Vision Model:** Single configured vision model per task

#### D — Task DSL & Compiler
- **JSON Schema v1.0:**
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
- **Compiler Output:** Executable DAG with topological ordering

#### E — Capability Registry
- **Registration:**
  ```python
  registry.register(
      tool_id="dalle3_image_gen",
      provider="openai",
      modalities=["image"],
      constraints={"max_resolution": 1792},
      cost_tier="high"
  )
  ```
- **Health Checks:** Periodic (60s cron) + circuit breaker triggers

---

## Data Model

### Core PostgreSQL Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| session_envelopes | Session metadata | session_id, tenant, created_at |
| session_events | Event timeline | session_id, event_type, occurred_at |
| dlq_messages | Dead letter queue | topic, event, error |
| attachments | File storage | id, filename, sha256, content |
| audit_events | Audit log | action, tenant, session_id, timestamp |

### Multimodal Tables (NEW)

| Table | Purpose | Key Fields |
|-------|---------|------------|
| multimodal_assets | Asset storage | id, tenant_id, asset_type, format, storage_path, content, checksum |
| multimodal_capabilities | Tool/model registry | tool_id, provider, modalities[], cost_tier, health_status |
| multimodal_job_plans | Task DSL storage | id, tenant_id, plan_json, status |
| multimodal_executions | Execution history | plan_id, step_index, tool_id, status, asset_id, latency_ms, cost, quality_score |
| asset_provenance | Audit trail | asset_id, request_id, execution_id, prompt_summary, params, user_id |

### Redis Key Patterns

| Pattern | Purpose | TTL |
|---------|---------|-----|
| `session:{id}` | Session cache | Configurable |
| `policy:requeue:{id}` | Blocked events | 3600s |
| `dedupe:{key}` | Idempotency | 3600s |
| `rate_limit:{tenant}` | Rate limiting | Window-based |

### Kafka Topics

| Topic | Producer | Consumer | Purpose |
|-------|----------|----------|---------|
| conversation.inbound | Gateway | ConversationWorker | User messages |
| conversation.outbound | Worker | Gateway (SSE) | Responses |
| tool.requests | Worker | ToolExecutor | Tool execution |
| tool.results | ToolExecutor | Worker | Tool results |
| audit.events | All | AuditWorker | Audit trail |
| dlq.events | SafeTask | Admin | Failed tasks |

---

## Security Architecture

### Authentication Layers
- **External:** Bearer Token / API Key
- **Internal:** X-Internal-Token (service-to-service mTLS)
- **OPA:** Policy evaluation for all actions

### Authorization Matrix

| Action | Resource | Enforced By |
|--------|----------|-------------|
| conversation.send | message | ConversationPolicyEnforcer |
| tool.execute | tool_name | ToolExecutor |
| memory.write | somabrain | ResultPublisher |
| multimodal.tool.execute | tool_id/provider | PolicyGraphRouter |

### Hardening Measures
- TLS 1.3 only, mTLS, HSTS, OCSP stapling
- JWS request signing (kid, nonce, timestamp)
- Capsule supply chain (SHA-256, cosign/sigstore)
- Envelope encryption (per-request KMS data keys)
- Circuit breakers, exponential backoff
- Key rotation, HSM/KMS storage

---

## Observability

### Prometheus Metrics (Core)
- `somabrain_http_requests_total`, `somabrain_request_seconds`
- `conversation_worker_messages_total`, `conversation_worker_processing_seconds`
- `sa01_core_tasks_total`, `sa01_core_task_latency_seconds`
- `gateway_sse_connections`, `fsm_transition_total`

### Prometheus Metrics (Multimodal)
- `multimodal_capability_selection_total`, `multimodal_execution_latency_seconds`
- `multimodal_execution_cost_estimate_cents`
- `multimodal_quality_score`, `multimodal_rework_attempts_total`
- `portfolio_ranker_shadow_divergence_total`, `capability_health_status`

### OpenTelemetry Tracing
- **Span Hierarchy:** multimodal_job → plan_extraction → plan_compilation → step_NN → execution_attempt_N → quality_evaluation
- **Trace Context Propagation:** Gateway → Worker → ToolExecutor → Providers
- **Attributes:** job_id, step_id, modality, tool_id, provider, quality_score

---

## Deployment Architecture

### Service Topology
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

### Horizontal Scaling
- **ToolExecutor:** Stateless replicas, scale on `multimodal_execution_latency_seconds` P95
- **Bottlenecks:** Provider API limits, S3 write throughput, SomaBrain query latency
- **Mitigations:** Per-tenant quotas (OPA), async S3 upload, SomaBrain outcome caching (Redis, 5min TTL)

---

## Performance Budgets

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

## Related Documents

- **Requirements:** [`requirements.md`](requirements.md) - Functional and non-functional requirements
- **Tasks:** [`TASKS.md`](TASKS.md) - 250+ implementation tasks
- **Full SRS:** [`docs/SRS.md`](docs/SRS.md) - Complete specification
- **Multimodal Design:** [`docs/architecture/MULTIMODAL_DESIGN.md`](docs/architecture/MULTIMODAL_DESIGN.md) - Detailed multimodal design
- **VIBE Rules:** [`VIBE_CODING_RULES.md`](VIBE_CODING_RULES.md) - Coding standards

---

**Last Updated:** 2025-12-16  
**Maintained By:** Development Team
