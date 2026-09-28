# SOMA-01-ARCH-001 — System Architecture Document

## Document Control

| Field | Value |
|-------|-------|
| Document Title | SomaAgent01 System Architecture Document |
| Document Identifier | SOMA-01-ARCH-001 |
| Version | 2.0.0 |
| Date | 2026-06-15 |
| Status | Pre-Production |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO/IEC/IEEE 42010:2011 — Systems and Software Engineering — Architecture Description |

## Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2025-12-30 | SomaTech Engineering | Initial architecture description |
| 1.1.0 | 2026-06-01 | SomaTech Engineering | Updated deployment modes; corrected service inventory |
| 2.0.0 | 2026-06-15 | SomaTech Engineering | Code-verified deep analysis; corrected audit findings; added dual-mode architecture detail; documented integration architecture with real service clients |

---

## 1. Purpose and Scope

### 1.1 Purpose

This document provides an ISO/IEC/IEEE 42010-compliant architecture description for the SomaAgent01 enterprise multi-agent cognitive platform. It defines the system's architectural views, deployment modes, service components, integration points, data models, and security architecture.

### 1.2 Scope

This document covers:
- System overview and technology stack
- Dual-mode deployment architecture (Standalone and AAAS)
- Logical, process, and physical architecture views
- Service component inventory
- Integration architecture with external systems
- Core and AAAS data models
- Security architecture
- Known architectural debt

This document does not cover:
- Detailed API specifications (see `docs/requirements/`)
- Operational runbooks (see `docs/operations/`)
- Quality management processes (see SOMA-01-QMS-001)

### 1.3 Intended Audience

- Software architects
- Platform engineers
- Security engineers
- Technical project managers
- AI software engineering agents

### 1.4 Normative References

| Document | Identifier | Location |
|----------|------------|----------|
| System Overview | SOMA-DOC-001 | `README.md` |
| Agent Knowledge Base | SOMA-DOC-002 | `AGENT.md` |
| Comprehensive Audit Report | SOMA-AUDIT-001 | `docs/archive/SOMA-OLD-AUDIT-001.md` |
| VIBE Coding Rules | SOMA-STD-001 | `docs/standards/SOMA-STD-CODING-001.md` |
| Deployment Modes | SOMA-DEP-001 | `docs/operations/SOMA-OPS-SOFTMODES-001.md` |

---

## 2. System Overview

### 2.1 System Description

SomaAgent01 is an enterprise multi-agent cognitive platform that provides AI agent orchestration, multi-tenant management, real-time chat, and cognitive memory integration. The system operates in two deployment modes: **Standalone** (agent-only) and **AAAS** (Agent As A Service) with full cognitive triad integration.

### 2.2 Technology Stack

| Layer | Technology | Constraint |
|-------|------------|------------|
| API Framework | Django 5.1 + Django Ninja 1.3 | FastAPI prohibited |
| ORM | Django ORM | SQLAlchemy prohibited; raw SQL only in helper modules |
| Frontend | Lit 3.x Web Components | React and Alpine.js prohibited |
| Database | PostgreSQL 16 | SQLite prohibited in production |
| Cache | Redis 7 | — |
| Message Broker | Kafka 3.7 (KRaft mode) | Optional in Standalone mode |
| Vector Database | Milvus 2.3 | Qdrant prohibited |
| Identity Provider | Keycloak 24 | OIDC protocol |
| Authorization | SpiceDB 1.29 | Zanzibar-style; `UnifiedGate` makes real gRPC calls |
| Policy Engine | OPA | `PolicyClient` makes real HTTP calls |
| Observability | Prometheus + Grafana + OpenTelemetry | Partially wired |
| Cognitive Runtime | SomaBrain | AAAS mode only (port 63996) |
| Memory Storage | SomaFractalMemory | AAAS mode only (port 63901) |

### 2.3 System Maturity

The system is classified as **Pre-Production**. System maturity score: approximately 45% (D+ overall per audit SOMA-01-AUDIT-002). Critical gaps must be resolved before production deployment.

---

## 3. Deployment Modes

SomaAgent01 operates in two distinct modes controlled by the `SA01_DEPLOYMENT_MODE` environment variable. The canonical dispatch occurs in `config/settings_registry.py`, which selects `StandaloneSettings` or `AAASSettings` accordingly.

### 3.1 Standalone Mode

Agent-only deployment without SomaBrain or SomaFractalMemory dependencies. Suitable for development, testing, and agent-only production scenarios.

| Service | Port | Required |
|---------|------|----------|
| SomaAgent API | 20020 | Yes |
| PostgreSQL | 20432 | Yes |
| Redis | 20379 | Yes |
| Keycloak | 20880 | Yes |
| Vault | 20882 | Optional |

**Environment Variables:**

| Variable | Value | Description |
|----------|-------|-------------|
| `SA01_DEPLOYMENT_MODE` | `STANDALONE` | Mode selector |
| `SOMA_AAAS_MODE` | `false` | AAAS feature flag |
| `SA01_DB_DSN` | `postgresql://...` | Database connection |
| `SA01_REDIS_URL` | `redis://...` | Redis connection |
| `KEYCLOAK_URL` | `http://somaagent_keycloak:8080` | Identity provider |

**Required Services:** PostgreSQL 16, Redis 7, Keycloak 24

### 3.2 AAAS Mode (Agent As A Service)

Full cognitive triad deployment: Agent + SomaBrain + SomaFractalMemory. Requires sibling repositories (`../somabrain`, `../somafractalmemory`).

| Service | Port | Required |
|---------|------|----------|
| SomaAgent API | 63900 | Yes |
| PostgreSQL | 63932 | Yes |
| Redis | 63979 | Yes |
| Keycloak | 63980 | Yes |
| SomaBrain | 63996 | Yes |
| SomaFractalMemory | 63901 | Yes |

**Environment Variables:**

| Variable | Value | Description |
|----------|-------|-------------|
| `SA01_DEPLOYMENT_MODE` | `AAAS` | Mode selector |
| `SOMA_AAAS_MODE` | `true` | AAAS feature flag |
| `SA01_DB_DSN` | `postgresql://...` | Database connection |
| `SA01_REDIS_URL` | `redis://...` | Redis connection |
| `KEYCLOAK_URL` | `http://somaagent_keycloak:8080` | Identity provider |
| `SOMABRAIN_URL` | `http://localhost:63996` | Cognitive runtime |
| `SOMAFRACTALMEMORY_URL` | `http://localhost:63901` | Memory storage |

**Required Services:** PostgreSQL 16, Redis 7, Keycloak 24, SomaBrain, SomaFractalMemory

### 3.3 Mode Comparison

| Feature | Standalone | AAAS |
|---------|-----------|------|
| Port Namespace | 20xxx | 63xxx |
| SomaBrain | Not available | Port 63996 |
| SomaFractalMemory | Not available | Port 63901 |
| Cognitive Memory | Disabled | Enabled |
| Neuromodulation | Disabled | Enabled |
| Kafka | Optional | Required |
| Sibling Repos | Not needed | Required |

---

## 4. Architecture Views

Per ISO/IEC/IEEE 42010, the following stakeholder concerns are addressed through distinct architectural views.

### 4.1 Logical View

The system follows a three-tier layered architecture:

```
┌─────────────────────────────────────────────────┐
│               Presentation Layer                 │
│  webui/ — Lit 3.x Web Components               │
│  60+ views, 40+ components, 14 stores           │
├─────────────────────────────────────────────────┤
│               Application Layer                  │
│  admin/ — 55 Django apps (domain logic)          │
│  services/ — Service implementations             │
│  (infrastructure concerns)                       │
├─────────────────────────────────────────────────┤
│               Infrastructure Layer               │
│  PostgreSQL, Redis, Kafka, Milvus                │
│  Keycloak, SpiceDB, OPA, Vault                   │
│  SomaBrain, SomaFractalMemory (AAAS only)        │
└─────────────────────────────────────────────────┘
```

**Domain Layer (`admin/`):**

| Domain | Apps | Key Concerns |
|--------|------|-------------|
| Core | `admin/core/` | Chat orchestrator, outbox pattern, models, AgentIQ |
| Auth | `admin/auth/` | Authentication router, OAuth, MFA, PKCE |
| AAAS | `admin/aaas/` | Multi-tenant models, subscription tiers |
| Chat | `admin/chat/` | Chat API endpoints, conversation CRUD |
| Agents | `admin/agents/` | Agent management and configuration |
| Permissions | `admin/permissions/` | RBAC API endpoints |
| Memory | `admin/memory/` | Memory integration hooks |
| Voice | `admin/voice/` | Speech-to-text and text-to-speech |
| Workflows | `admin/workflows/` | Temporal workflow hooks |
| Audit | `admin/audit/` | Audit log endpoints |

**Infrastructure Layer (`services/`):**

| Service | Path | Responsibility |
|---------|------|---------------|
| Gateway | `services/gateway/` | ASGI entrypoint, settings, URL routing, WebSocket consumers |
| Common | `services/common/` | 40+ shared modules: event bus, circuit breaker, rate limiter, policy client, SpiceDB client, health monitor, Redis pool |
| Conversation Worker | `services/conversation_worker/` | Kafka consumer for inbound conversation events |
| Tool Executor | `services/tool_executor/` | Tool execution engine with sandbox management |
| Delegation Gateway | `services/delegation_gateway/` | A2A protocol handling |
| Memory Replicator | `services/memory_replicator/` | Memory synchronization |
| Multimodal | `services/multimodal/` | Multi-modal processing |

### 4.2 Process View

#### 4.2.1 V3 Chat Orchestrator (12-Phase Pipeline)

The V3 chat orchestrator (`admin/core/chat_orchestrator.py`) is the production path for WebSocket and REST chat. It implements a 12-phase pipeline:

| Phase | Description |
|-------|-------------|
| 1 | Input validation and sanitization |
| 2 | Authentication and session resolution |
| 3 | AgentIQ derivation (agent identity, capabilities, constitution) |
| 4 | UnifiedGate authorization check (OPA + SpiceDB) |
| 5 | Context building (conversation history, system prompts) |
| 6 | Tool discovery and registration |
| 7 | Memory recall (SomaBrain in AAAS mode) |
| 8 | Circuit breaker check (SomaBrain + LLM) |
| 9 | LLM invocation (via LiteLLM) |
| 10 | Tool call extraction and execution |
| 11 | Memory storage (SomaBrain + SomaFractalMemory in AAAS mode) |
| 12 | Response delivery and Django signals |

**Tiktoken** is used for accurate token counting (line 52–59). Circuit breakers protect both SomaBrain and LLM calls (line 149–152).

#### 4.2.2 WebSocket Consumer

The WebSocket consumer (`services/gateway/consumers/chat.py`) handles real-time chat:
- URL pattern: `wss://{host}/ws/chat/{agent_id}`
- Authentication: JWT via `Sec-WebSocket-Protocol` subprotocol, query string, Authorization header, or cookie
- Message format: JSON with `type`, `conversation_id`, `content`
- Delegates to V3 orchestrator for message processing

#### 4.2.3 Conversation Worker Pipeline

A separate pipeline exists in `services/conversation_worker/` for Kafka/Temporal event processing:
- Uses `admin/core/application/use_cases/conversation/process_message.py` and `generate_response.py`
- Does **not** call `V3ChatOrchestrator`
- This is identified as architectural debt (see Section 9)

### 4.3 Physical View

#### 4.3.1 Docker Deployment

```
┌──────────────────────────────────────────────────────┐
│                   Docker Host                         │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐       │
│  │ SomaAgent│  │PostgreSQL│  │    Redis      │       │
│  │  :20020  │  │  :20432  │  │    :20379     │       │
│  └──────────┘  └──────────┘  └──────────────┘       │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐       │
│  │Keycloak  │  │  Vault   │  │    Kafka     │       │
│  │  :20880  │  │  :20882  │  │   (optional) │       │
│  └──────────┘  └──────────┘  └──────────────┘       │
│                                                      │
│  AAAS additions:                                     │
│  ┌──────────┐  ┌──────────────────────────────┐      │
│  │SomaBrain│  │  SomaFractalMemory           │      │
│  │  :63996  │  │    :63901                    │      │
│  └──────────┘  └──────────────────────────────┘      │
└──────────────────────────────────────────────────────┘
```

Docker Compose configurations:
- Standalone: `infra/standalone/docker-compose.yml`
- AAAS: `infra/aaas/` (requires sibling repos)
- Root: `docker-compose.yml`

#### 4.3.2 Kubernetes Deployment

Kubernetes manifests are defined in `infra/k8s/` but are incomplete. Manifests need:
- Environment variable injection for dual-mode operation
- OPA/SpiceDB sidecar or service configuration
- Health probe definitions aligned with `services/common/health_monitor.py`

---

## 5. Service Components

### 5.1 Gateway (`services/gateway/`)

| File | Purpose |
|------|---------|
| `main.py` | ASGI entrypoint (`django_asgi`) |
| `settings.py` | Django settings with security hardening |
| `urls.py` | URL routing including WebSocket paths |
| `consumers/chat.py` | WebSocket consumer for real-time chat |

### 5.2 Conversation Worker (`services/conversation_worker/`)

Kafka consumer for inbound conversation events. Uses a separate use-case pipeline rather than the V3 orchestrator.

### 5.3 Tool Executor (`services/tool_executor/`)

Tool execution engine with sandbox management for agent tool invocations.

### 5.4 Delegation Gateway (`services/delegation_gateway/`)

Agent-to-Agent (A2A) protocol handling for task delegation.

### 5.5 Memory Replicator (`services/memory_replicator/`)

Memory synchronization between agent instances and memory backends.

### 5.6 Multimodal Service (`services/multimodal/`)

Multi-modal processing (text, image, audio).

### 5.7 Common Services (`services/common/`) — 40+ Modules

| Module | File | Purpose |
|--------|------|---------|
| Event Bus | `event_bus.py` | Kafka producer/consumer with OpenTelemetry tracing |
| Circuit Breaker | `circuit_breaker.py` | Circuit breaker for external service calls |
| Rate Limiter | `rate_limiter.py` | Redis-based; **fail-closed** on Redis errors (lines 186–196) |
| Policy Client | `policy_client.py` | Real HTTP client for OPA policy evaluation |
| SpiceDB Client | `spicedb_client.py` | Real gRPC client for SpiceDB authorization |
| Health Monitor | `health_monitor.py` | Service health checking |
| Simple Governor | `simple_governor.py` | Load shedding and governance |
| Redis Pool | `redis_pool.py` | Shared Redis connection factory |
| Store Base | `store_base.py` | Base class for all stores |
| Chat Service | `chat_service.py` | Thin wrapper around V3 orchestrator for test compatibility |
| Memory Port | `ports/memory_port.py` | `MemoryPort` protocol (consolidation target) |
| Memory Adapters | `adapters/` | `MemoryServiceProtocol` implementations for SomaFractalMemory HTTP |

---

## 6. Integration Architecture

### 6.1 SomaBrain Integration

Two integration paths exist for the SomaBrain cognitive runtime:

| Path | File | Mode | Mechanism |
|------|------|------|-----------|
| Direct (in-process) | `aaas/brain.py` | AAAS only | `BrainBridge` class; imports `somabrain` Python package |
| HTTP | `admin/core/somabrain_client.py` | Both modes | `SomaBrainClient` class; HTTP REST calls |

**BrainBridge** (`aaas/brain.py`):
- Lines 132–161: `recall()` implemented for both direct and HTTP modes
- Direct mode: imports and calls `somabrain` package in-process
- HTTP mode: falls back to REST API at configured URL
- Port: 63996 (AAAS), or 9696 (direct development)

### 6.2 SomaFractalMemory Integration

SomaFractalMemory is accessed via HTTP adapters:

| File | Protocol | Operations |
|------|----------|-----------|
| `services/common/adapters/` | HTTP REST | `episodic` and `semantic` memory storage/retrieval |
| `services/common/ports/memory_port.py` | Protocol definition | `MemoryPort` interface (not yet adopted by production adapters) |

- Port: 63901 (AAAS), or 10101 (direct development)
- Endpoints: `/api/v1/recall`, `/api/v1/store`

### 6.3 Keycloak Integration

| Aspect | Detail |
|--------|--------|
| Protocol | OIDC |
| Port | 20880 (Standalone) / 63980 (AAAS) |
| Realm | `somaagent` |
| Client | `eye-of-god` (public client) |
| Flows | Password grant, OAuth (Google, GitHub), SAML, LDAP |
| Token TTL | Access: 15 min (httpOnly cookie), Refresh: 7–30 days |

### 6.4 SpiceDB Integration

| Aspect | Detail |
|--------|--------|
| Protocol | gRPC |
| Client | `services/common/spicedb_client.py` — `SpiceDBClient` class |
| Gate | `admin/core/agentiq/unified_gate.py` — real gRPC calls |
| Schema | `schemas/spicedb/schema.zed` |
| Status | `UnifiedGate` uses real SpiceDB; some RBAC API endpoints in `admin/permissions/` still return stub responses |

### 6.5 OPA Integration

| Aspect | Detail |
|--------|--------|
| Protocol | HTTP |
| Client | `services/common/policy_client.py` — `PolicyClient` class |
| Gate | `admin/core/agentiq/unified_gate.py` — real HTTP calls via `PolicyClient` |
| Policies | `policy/` directory (Rego files) |
| Status | Runtime calls are real; policy loading into OPA deployment needs verification |

### 6.6 Integration Dependency Graph

```
                    ┌──────────────┐
                    │  Keycloak    │
                    │  (OIDC)      │
                    └──────┬───────┘
                           │ JWT
┌──────────────┐    ┌──────▼───────┐    ┌──────────────┐
│   OPA        │◄───│  SomaAgent   │───►│   SpiceDB    │
│  (HTTP)      │    │  Gateway     │    │   (gRPC)     │
└──────────────┘    └──────┬───────┘    └──────────────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
       ┌──────▼──┐  ┌──────▼──┐  ┌─────▼───────┐
       │SomaBrain│  │Fractal  │  │  PostgreSQL  │
       │ (AAAS)  │  │ Memory  │  │  Redis       │
       └─────────┘  └─────────┘  └─────────────┘
```

---

## 7. Data Models

### 7.1 Core Models (`admin/core/models/`)

| Model | Purpose |
|-------|---------|
| `Session` | Chat session |
| `SessionEvent` | Session events |
| `Capsule` | Capsule definition |
| `CapsuleInstance` | Running capsule instance |
| `Capability` | Agent capabilities |
| `Constitution` | Agent constitution |
| `Job` | Scheduled jobs |
| `Notification` | User notifications |
| `Prompt` | Prompt templates |
| `FeatureFlag` | Feature flags |
| `UISetting` | UI configuration |
| `AgentSetting` | Agent-specific settings |
| `MemoryReplica` | Memory replica state |
| `Asset` | Asset records |
| `ExecutionRecord` | Execution trace |
| `Provenance` | Data provenance |
| `ModelProfile` | LLM model profile |
| `MultimodalOutcome` | Multimodal processing outcome |
| `DelegationTask` | Delegated task |
| `OutboxMessage` | Transactional outbox |
| `DeadLetterMessage` | Dead letter queue |
| `IdempotencyRecord` | Exactly-once processing |
| `PendingMemory` | Memory synchronization queue |
| `SensorOutbox` | Sensor event outbox |

### 7.2 AAAS Models (`admin/aaas/models/`)

| Model | Purpose |
|-------|---------|
| `Tenant` | Organization with subscription tier |
| `TenantUser` | User-tenant membership with roles |
| `Agent` | AI agent with capsules and feature settings |
| `AgentUser` | User assignment to agents |
| `SubscriptionTier` | Billing subscription tiers |
| `AaasFeature` | Platform feature flags |
| `TierFeature` | Tier-to-feature mapping |
| `FeatureProvider` | Feature provider configuration |
| `UsageRecord` | Usage/billing records |
| `AuditLog` | Audit trail |
| `PlatformConfig` | Platform-wide defaults |
| `AdminProfile` | Admin user profile |
| `TenantSettings` | Per-tenant settings |
| `UserPreferences` | User preferences |
| `UserSession` | Extended user session |
| `ApiKey` | API key storage |

---

## 8. Security Architecture

### 8.1 Authentication

- **Identity Provider:** Keycloak 24 (OIDC)
- **Token Format:** JWT RS256
- **Token Validation:** `admin/common/auth.py` — `decode_token()` function
  - `verify_aud` controlled by `JWT_ISSUER_STRICT` setting (default: `true`) — lines 195–210
- **Session Storage:** Redis-backed, 15-minute TTL, extended on activity
- **Account Lockout:** Redis-based, 5 failed attempts / 15-minute window

### 8.2 Authorization

The `UnifiedGate` (`admin/core/agentiq/unified_gate.py`, lines 130–207) implements a three-layer authorization check:

1. **OPA Policy Evaluation** — Real HTTP calls via `PolicyClient`
2. **SpiceDB Relationship Check** — Real gRPC calls via `SpiceDBClient`
3. **Scope Validation** — Request-level scope verification

The gate is **fail-closed**: any policy engine unavailability denies the request.

### 8.3 Rate Limiting

- **Implementation:** `services/common/rate_limiter.py` — `RedisRateLimiter`
- **Fail Behavior:** **Fail-closed** on Redis errors (lines 186–196): returns `allowed=False`
- **Scope:** Per-user, per-endpoint

### 8.4 Secret Management

- **Vault:** HashiCorp Vault integration for runtime secrets
- **Settings:** `services/gateway/settings.py` line 37 — `SECRET_KEY` uses `secrets.token_urlsafe(50)`, raises `ValueError` in production if default
- **Database:** No SQLite fallback — raises `ValueError` on bad DSN (line 142)

### 8.5 Security Controls Summary

| Control | Implementation | Status |
|---------|---------------|--------|
| Authentication | Keycloak OIDC | Implemented |
| Token Validation | JWT RS256 with audience verification | Implemented |
| Authorization | UnifiedGate (OPA + SpiceDB + Scope) | Implemented (gate); some RBAC API endpoints stubbed |
| Rate Limiting | Redis-based, fail-closed | Implemented |
| Account Lockout | Redis-based, 5 attempts / 15 min | Implemented |
| Secret Management | Vault + secrets.token_urlsafe | Implemented |
| PKCE | OAuth PKCE flow | Implemented |
| TLS | Not enforced at application layer | Gap |
| Audit Logging | Outbox pattern | Partial |

---

## 9. Known Architectural Debt

| ID | Debt Item | Impact | Status |
|----|-----------|--------|--------|
| DEBT-001 | Conversation-worker bypasses V3 orchestrator; uses separate use-case pipeline | Inconsistent chat behavior between WebSocket/REST and Kafka paths | Open |
| DEBT-002 | 9+ memory entry points being consolidated via `MemoryPort` protocol | Fragmented memory access; `MemoryPort` defined but not adopted by production adapters | In Progress |
| DEBT-003 | `permissions/api.py` line 336 returns `allowed:true` unconditionally | Authorization bypass in RBAC API | **P0 — Open** |
| DEBT-004 | Django migrations out of sync for `admin/aaas` and `admin/core` | Schema drift; deployment failures | **P0 — Open** |
| DEBT-005 | WebSocket routing requires `agent_id` but frontend omits it | Chat flow broken | **P0 — Open** |
| DEBT-006 | `pyproject.toml` line 21 references `somabrain` as `../somabrain` path dependency | Non-portable; CI/CD cannot install | **P1 — Open** |
| DEBT-007 | Zero CI/CD pipelines (no `.github/workflows/`) | No automated testing or deployment | **P1 — Open** |
| DEBT-008 | 15 test files / 528+ source files (2.8% coverage) | Insufficient quality assurance | **P1 — Open** |
| DEBT-009 | `brain.py` line 92 falls back to Docker hostname `somastack_aaas:9696` | Hardcoded Docker networking assumption | **P2 — Open** |
| DEBT-010 | `rate_limiter.py` line 67 uses `REDIS_URL` not `SA01_REDIS_URL` | Environment variable inconsistency | **P2 — Open** |
| DEBT-011 | `chat_orchestrator.py` line 750 uses regex-based tool call extraction | Fragile parsing | **P2 — Open** |

---

## Appendix A: Port Namespace Reference

| Service | Standalone (20xxx) | AAAS (63xxx) |
|---------|-------------------|--------------|
| SomaAgent API | 20020 | 63900 |
| PostgreSQL | 20432 | 63932 |
| Redis | 20379 | 63979 |
| Keycloak | 20880 | 63980 |
| Vault | 20882 | — |
| SomaBrain | — | 63996 |
| SomaFractalMemory | — | 63901 |

---

## Appendix B: Environment Variable Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SA01_DEPLOYMENT_MODE` | Yes | `STANDALONE` | Deployment mode: `STANDALONE`, `AAAS`, or `DEV` |
| `SOMA_AAAS_MODE` | Yes | `false` | AAAS feature flag |
| `SA01_DB_DSN` | Yes | — | PostgreSQL connection string |
| `SA01_REDIS_URL` | Yes | — | Redis connection string |
| `POSTGRES_USER` | Yes | `somaagent` | PostgreSQL username |
| `POSTGRES_PASSWORD` | Yes | — | PostgreSQL password |
| `POSTGRES_DB` | Yes | `somaagent` | PostgreSQL database name |
| `KEYCLOAK_URL` | Yes | — | Keycloak base URL |
| `KEYCLOAK_ADMIN` | Yes | `admin` | Keycloak admin username |
| `KEYCLOAK_ADMIN_PASSWORD` | Yes | — | Keycloak admin password |
| `KEYCLOAK_REALM` | Yes | `somaagent` | Keycloak realm name |
| `JWT_ISSUER_STRICT` | No | `true` | Enable strict JWT audience verification |
| `SOMABRAIN_URL` | AAAS | — | SomaBrain service URL |
| `SOMAFRACTALMEMORY_URL` | AAAS | — | SomaFractalMemory service URL |
| `VAULT_DEV_ROOT_TOKEN_ID` | No | — | Vault dev mode root token |
| `SECRET_KEY` | Yes | Generated | Django secret key (auto-generated if not set) |
| `DEBUG` | No | `false` | Django debug mode |

---

End of Document
