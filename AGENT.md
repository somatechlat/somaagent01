# SomaAgent01 - Agent Knowledge Base

## Document Control

| Field | Value |
|-------|-------|
| Document Title | SomaAgent01 Agent Knowledge Base |
| Document Identifier | SOMA-DOC-002 |
| Version | 1.1.0 |
| Date | 2026-06-01 |
| Status | Pre-Production |
| Author | SomaTech Engineering |
| Classification | Internal |

## Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2025-12-30 | SomaTech Engineering | Initial release |
| 1.1.0 | 2026-06-01 | SomaTech Engineering | Updated to reflect actual implementation status; corrected deployment port namespaces; documented known gaps |

---

## 1. Purpose and Scope

### 1.1 Purpose

This document provides canonical context for software engineering agents working on the SomaAgent01 codebase. It serves as the definitive reference for architecture, implementation status, and coding standards.

### 1.2 Scope

This document covers:
- System architecture and technology constraints
- Authentication and authorization mechanisms
- Chat architecture and implementation reality
- Data models and API endpoint inventory
- Testing requirements and infrastructure
- Coding standards (VIBE rules)
- Implementation status (implemented, partial, gap)

This document does not cover:
- Detailed API schemas (see `schemas/`)
- Operational procedures (see `docs/deployment/`)
- Software requirements specifications (see `docs/srs/`)

### 1.3 Intended Audience

- AI software engineering agents
- Human software engineers
- Code reviewers

---

## 2. Normative References

| Document | Identifier | Location |
|----------|------------|----------|
| Project Overview | SOMA-DOC-001 | `README.md` |
| Comprehensive Audit Report | SOMA-AUDIT-001 | `SOMA_AGENT01_COMPREHENSIVE_AUDIT_REPORT.md` |
| VIBE Coding Rules | SOMA-STD-001 | `docs/development/VIBE_CODING_RULES.md` |
| Deployment Modes | SOMA-DEP-001 | `docs/deployment/SOFTWARE_DEPLOYMENT_MODES.md` |

---

## 3. Terms and Definitions

| Term | Definition |
|------|------------|
| AAAS | Agent-As-A-Service |
| BrainBridge | Python class in `aaas/brain.py` providing in-process or HTTP access to SomaBrain |
| MemoryPort | Protocol defined in `services/common/ports/memory_port.py` consolidating memory access |
| V3 Pipeline | 12-phase chat orchestrator defined in `admin/core/chat_orchestrator.py` |
| VIBE | Internal coding standard: Verification, Integration, Build, Enforcement |
| Standalone | Agent-only deployment mode without Brain/Memory |
| JSON Blob Check | Authorization pattern where policy data is read from JSON fields rather than policy engines |

---

## 4. System Architecture

### 4.1 Technology Stack

| Layer | Technology | Constraint |
|-------|------------|------------|
| API Framework | Django 5.1 + Django Ninja 1.3 | FastAPI prohibited |
| ORM | Django ORM | SQLAlchemy prohibited; raw SQL allowed only in helper modules |
| Frontend | Lit 3.x Web Components | React and Alpine.js prohibited |
| Database | PostgreSQL 16 | Port 20432 (standalone) or 63932 (AAAS) |
| Cache | Redis 7 | Port 20379 (standalone) or 63979 (AAAS) |
| Message Broker | Kafka 3.7 (KRaft) | Optional in Standalone mode |
| Vector Database | Milvus 2.3 | Qdrant prohibited |
| Identity | Keycloak 24 | Port 20880 (standalone) or 63980 (AAAS) |
| Authorization | SpiceDB 1.29 | Schema defined; `UnifiedGate` makes real gRPC calls; some RBAC API endpoints remain stubbed |
| Policy Engine | OPA | Policy files exist; `UnifiedGate` and `PolicyClient` make real HTTP calls to OPA |
| Observability | Prometheus + Grafana + OpenTelemetry | Partially wired |

### 4.2 Port Namespaces

**Standalone Namespace (20xxx)**

| Service | Port |
|---------|------|
| SomaAgent API | 20020 |
| PostgreSQL | 20432 |
| Redis | 20379 |
| Keycloak | 20880 |
| Vault | 20882 |

**AAAS Namespace (63xxx)**

| Service | Port |
|---------|------|
| SomaAgent API | 63900 |
| PostgreSQL | 63932 |
| Redis | 63979 |
| Keycloak | 63980 |
| SomaBrain | 63996 |
| SomaFractalMemory | 63901 |

### 4.3 Deployment Modes

| Mode | Environment Variable | Value | Description |
|------|----------------------|-------|-------------|
| Standalone | `SA01_DEPLOYMENT_MODE` | `STANDALONE` | Agent-only; no Brain or Memory |
| AAAS | `SA01_DEPLOYMENT_MODE` | `AAAS` | Full stack with Brain and Memory |
| Development | `SA01_DEPLOYMENT_MODE` | `DEV` | Development defaults |

**Canonical source**: `config/settings_registry.py` dispatches to `StandaloneSettings` or `AAASSettings` based on `SA01_DEPLOYMENT_MODE`.

---

## 5. Project Structure

```
somaAgent01/
├── admin/                    # 55 Django applications
│   ├── api.py               # Master Django Ninja API router (40+ routers)
│   ├── auth/                # Authentication (Keycloak integration)
│   ├── core/               # Core models, chat orchestrator, outbox pattern
│   ├── aaas/               # Multi-tenant features (Tenant, Subscription, Agent)
│   ├── chat/               # Chat API endpoints
│   ├── agents/             # Agent management
│   ├── memory/             # Memory integration hooks
│   ├── voice/              # Speech-to-text and text-to-speech
│   ├── workflows/          # Temporal workflow hooks
│   └── [45+ additional apps]
├── services/                 # Service layer
│   ├── gateway/             # ASGI entrypoint, Django settings, URL routing
│   ├── common/              # 40+ shared modules
│   │   ├── event_bus.py    # Kafka producer/consumer with OpenTelemetry tracing
│   │   ├── circuit_breaker.py
│   │   ├── rate_limiter.py # Redis-based; FAIL-CLOSED on Redis errors
│   │   ├── policy_client.py # Real HTTP OPA client
│   │   ├── spicedb_client.py # Real gRPC SpiceDB client
│   │   ├── health_monitor.py
│   │   ├── simple_governor.py
│   │   └── ports/memory_port.py # MemoryPort protocol (P3-01)
│   ├── conversation_worker/ # Kafka consumer for chat events
│   ├── tool_executor/       # Tool execution engine
│   ├── delegation_gateway/  # A2A delegation handling
│   ├── memory_replicator/   # Memory synchronization
│   └── multimodal/          # Multi-modal processing
├── webui/                   # Lit 3.x Web Components frontend
│   └── src/
│       ├── views/           # 60+ page views
│       ├── components/      # 40+ reusable components
│       └── stores/          # 14 state stores
├── schemas/                 # JSON schemas and SpiceDB Zed schema
├── policy/                  # OPA Rego policies
├── infra/                   # Docker, Kubernetes, and deployment configs
│   ├── standalone/          # Standalone mode (Agent-only)
│   ├── aaas/                # AAAS mode (requires sibling repositories)
│   └── k8s/                 # Kubernetes manifests
├── tests/                   # Test suite
├── docs/                    # Documentation
├── scripts/                 # Automation scripts
├── config/                  # Centralized settings registry
└── core/                    # Cross-service data models
```

---

## 6. Authentication Architecture

### 6.1 Flow Overview

```
User -> Login Page -> Django API -> Keycloak -> JWT Validation -> PostgreSQL/Redis
```

### 6.2 Components

1. **Keycloak**
   - Port: 20880 (standalone) or 63980 (AAAS)
   - Protocol: OIDC
   - Realm: `somaagent`
   - Client: `eye-of-god` (public client)
   - Supported flows: Password grant, OAuth (Google, GitHub), SAML, LDAP

2. **JWT Tokens**
   - Access token TTL: 15 minutes, httpOnly cookie
   - Refresh token TTL: 7 to 30 days, httpOnly cookie
   - Claims: `sub`, `email`, `tenant_id`, `realm_access.roles`

3. **Session Management**
   - Backend: Redis
   - Key pattern: `session:{user_id}:{session_id}`
   - TTL: 15 minutes, extended on activity

4. **SpiceDB and OPA**
   - SpiceDB schema: defined in `schemas/spicedb/schema.zed`
   - OPA policies: defined in `policy/`
   - Runtime behavior: `UnifiedGate` (`admin/core/agentiq/unified_gate.py`) makes real HTTP calls to OPA and real gRPC calls to SpiceDB; it is fail-closed. Some high-level RBAC API endpoints in `admin/permissions/` still return stub responses.

### 6.3 Auth Code Inventory

| File | Purpose |
|------|---------|
| `admin/auth/api.py` | Auth router: `/token`, `/login`, `/refresh`, `/logout`, SSO |
| `admin/common/auth.py` | `AuthBearer`, `RoleRequired`, `decode_token()` |
| `webui/src/views/saas-login.ts` | Login page with OAuth, SSO, email/password |
| `webui/src/services/keycloak-service.ts` | Keycloak OIDC client |
| `webui/src/stores/auth-store.ts` | Auth state management |

### 6.4 Known Auth Issues

| ID | Issue | Location | Severity | Status |
|----|-------|----------|----------|--------|
| AUTH-001 | `ALLOW_INSECURE_AUTH_BYPASS` flag existed historically | `services/gateway/settings.py` | High | **Fixed — removed from code** |
| AUTH-002 | `DEV_MODE = true` hardcoded | `webui/src/main.ts` | High | **Fixed — `DEV_MODE = false`** |
| AUTH-003 | Account lockout not implemented | `admin/auth/api.py` / `admin/common/account_lockout.py` | Medium | **Fixed — implemented via Redis (5 attempts / 15 min)** |
| AUTH-004 | PKCE for OAuth not implemented | `admin/auth/api_oauth.py` / `admin/common/pkce.py` | Medium | **Fixed — PKCE implemented** |

---

## 7. Chat Architecture

### 7.1 Chat Pipeline Reality

The WebSocket and REST chat paths now use the **V3 12-phase orchestrator** as the production pipeline. A second, separate pipeline exists inside the conversation worker for Kafka/Temporal event processing.

**Active pipelines:**

1. **V3 12-phase orchestrator** — `admin/core/chat_orchestrator.py`
   - Used by WebSocket consumer (`services/gateway/consumers/chat.py`)
   - Used by REST chat API (`admin/chat/api/chat.py`)
   - Wrapped by `services/common/chat_service.py` for test compatibility
   - Implements AgentIQ derivation, UnifiedGate checks, context building, tool discovery, circuit breakers, memory storage, and Django signals

2. **Conversation-worker use-case pipeline** — `admin/core/application/use_cases/conversation/process_message.py` + `generate_response.py`
   - Used by `services/conversation_worker/main.py` (AAAS supervisord deployment)
   - Separate context-building and response-generation logic
   - Does not call `V3ChatOrchestrator`

The old fragmented modules under `services/common/chat/` were deleted during the V3 consolidation.

### 7.2 Flow Overview

```
User -> Chat UI -> WebSocket -> ChatConsumer -> V3ChatOrchestrator -> LLM (via LiteLLM)
                                                                   -> SomaBrain (AAAS mode only)
                                                                   -> SomaFractalMemory (AAAS mode only)
```

### 7.3 Components

1. **WebSocket Protocol**
   - URL: `wss://{host}/ws/chat/{agent_id}` (backend requires `agent_id` in path)
   - Authentication: JWT via `Sec-WebSocket-Protocol` subprotocol, query string, Authorization header, or cookie
   - Message format: JSON with `type`, `conversation_id`, `content`

2. **SomaBrain** (AAAS only)
   - Port: 63996
   - Access: `BrainBridge` in `aaas/brain.py` (direct in-process) or `SomaBrainClient` in `admin/core/somabrain_client.py` (HTTP)
   - Modes: Direct (in-process) or HTTP fallback
   - `BrainBridge.recall()` is implemented for both direct and HTTP modes

3. **SomaFractalMemory** (AAAS only)
   - Port: 63901
   - Access: `MemoryServiceProtocol` adapters in `services/common/adapters/`
   - Operations: `episodic` and `semantic` memory storage and retrieval
   - Note: `MemoryPort` protocol in `services/common/ports/memory_port.py` is defined but not adopted by production adapters

### 7.4 Chat Code Inventory

| File | Purpose |
|------|---------|
| `admin/chat/api/chat.py` | Chat and Conversation CRUD; delegates create/send to V3 orchestrator |
| `admin/core/chat_orchestrator.py` | V3 12-phase pipeline (production path) |
| `services/common/chat_service.py` | Thin test-compatibility wrapper around V3 orchestrator |
| `services/gateway/consumers/chat.py` | WebSocket consumer; delegates to V3 orchestrator |
| `admin/core/application/use_cases/conversation/process_message.py` | Conversation-worker pipeline (separate from V3) |
| `webui/src/views/saas-chat.ts` | Chat view (WebSocket) |
| `webui/src/services/websocket-client.ts` | WebSocket client |

---

## 8. Data Models

### 8.1 Core Models (`admin/core/models/`)

```python
Session              # Chat session
SessionEvent         # Session events
Capsule              # Capsule definition
CapsuleInstance      # Running instance
Capability           # Agent capabilities
Constitution         # Agent constitution
Job                  # Scheduled jobs
Notification         # User notifications
Prompt               # Prompt templates
FeatureFlag          # Feature flags
UISetting            # UI configuration
AgentSetting         # Agent-specific settings
MemoryReplica        # Memory replica state
Asset                # Asset records
ExecutionRecord      # Execution trace
Provenance           # Data provenance
ModelProfile         # LLM model profile
MultimodalOutcome    # Multimodal processing outcome
DelegationTask       # Delegated task
OutboxMessage        # Transactional outbox
DeadLetterMessage    # Dead letter queue
IdempotencyRecord    # Exactly-once processing
PendingMemory        # Memory synchronization queue
SensorOutbox         # Sensor event outbox
```

### 8.2 AAAS Models (`admin/aaas/models/`)

```python
Tenant               # Organization with subscription tier
TenantUser           # User-tenant membership with roles
Agent                # AI agent with capsules and feature settings
AgentUser            # User assignment to agents
SubscriptionTier     # Billing subscription tiers
AaasFeature          # Platform feature flags
TierFeature          # Tier-to-feature mapping
FeatureProvider      # Feature provider config
UsageRecord          # Usage/billing records
AuditLog             # Audit trail (moved from admin.core)
PlatformConfig       # Platform-wide defaults (renamed from GlobalDefault)
AdminProfile         # Admin user profile
TenantSettings       # Per-tenant settings
UserPreferences      # User preferences
UserSession          # Extended user session
ApiKey               # API key storage
```

---

## 9. API Endpoints

### 9.1 Master Router (`admin/api.py`)

All endpoints are mounted under `/api/v2/`:

| Prefix | Router | Purpose |
|--------|--------|---------|
| `/auth` | `admin.auth.api` | Authentication |
| `/agents` | `admin.agents.api` | Agent management |
| `/chat` | `admin.chat.api` | Chat sessions |
| `/conversations` | `admin.conversations.api` | Conversations |
| `/sessions` | `admin.sessions.api` | User sessions |
| `/aaas` | `admin.aaas.api` | AAAS administration |
| `/memory` | `admin.memory.api` | Memory integration |
| `/voice` | `admin.voice.api` | Voice services |
| `/workflows` | `admin.workflows.api` | Temporal workflows |
| `/audit` | `admin.audit.api` | Audit logs |
| `/permissions` | `admin.permissions.api` | Role-based access control |
| ... | ... | 40+ additional routers |

### 9.2 Key Auth Endpoints

```
POST /api/v2/auth/token              # Password grant token exchange
POST /api/v2/auth/login              # Email and password login
POST /api/v2/auth/refresh            # Token refresh
POST /api/v2/auth/logout             # Logout and token revocation
GET  /api/v2/auth/me                 # Current user information
GET  /api/v2/auth/oauth/{provider}   # OAuth initiation
GET  /api/v2/auth/oauth/callback     # OAuth callback
POST /api/v2/auth/mfa/verify         # Multi-factor authentication verification
```

---

## 10. Testing

### 10.1 Policy

Per VIBE standard SOMA-STD-001:
- All tests require real infrastructure where possible
- No fakeredis; minimal mocks (note: some existing test files violate this)
- Tests skip gracefully when infrastructure is unavailable

### 10.2 Execution

```bash
# Start standalone stack for testing
cd infra/standalone && docker compose up -d

# Run full test suite
DJANGO_SETTINGS_MODULE=services.gateway.settings pytest tests/ -v

# Run unit tests only (no external dependencies)
pytest tests/unit/ -v
```

### 10.3 Test Markers

| Marker | Meaning |
|--------|---------|
| `aaas` | Requires full AAAS stack |
| `standalone` | Standalone mode tests |
| `slow` | Long-running tests |
| `infra` | Requires infrastructure |
| `live` | Live integration tests |

---

## 11. VIBE Coding Rules

### 11.1 The Seven Rules

1. No mocks, no placeholders, no TODOs (note: codebase contains ~173 TODO/FIXME/XXX/HACK/NotImplementedError occurrences as of 2026-06-12)
2. Check architecture before coding
3. Modify existing files when possible
4. Production-grade code only
5. Documentation must match reality (note: docs have severe drift)
6. Understand full flow before implementing
7. Use actual services and data

### 11.2 Django Purity (Strict)

- ONLY Django ORM (NO SQLAlchemy)
- ONLY Django Migrations (NO Alembic)
- ONLY Django Ninja (NO FastAPI)
- ONLY Lit 3.x (NO React, NO Alpine.js)
- ONLY Milvus (NO Qdrant)

### 11.3 Forbidden Patterns

- Mocks, stubs, placeholders
- Hardcoded values in production code
- TODO, FIXME, "implement later"
- Inventing APIs or syntax
- Guessing behavior
- Creating unnecessary files

---

## 12. Implementation Status

### 12.1 Implemented and Working

| Component | File | Status |
|-----------|------|--------|
| Auth Router | `admin/auth/api.py` | Full implementation |
| JWT Validation | `admin/common/auth.py` | Full implementation |
| Login Page | `webui/src/views/saas-login.ts` | Full implementation (888 lines) |
| Chat View | `webui/src/views/saas-chat.ts` | Full implementation (1063 lines) |
| Keycloak Service | `webui/src/services/keycloak-service.ts` | Full implementation |
| Core Models | `admin/core/models.py` | Full implementation |
| Rate Limiter | `services/common/rate_limiter.py` | Full; FAIL-CLOSED on Redis error |
| Circuit Breaker | `services/common/circuit_breaker.py` | Full implementation |
| Health Monitor | `services/common/health_monitor.py` | Full implementation |
| Event Bus | `services/common/event_bus.py` | Full implementation |
| Settings Registry | `config/settings_registry.py` | Full implementation |

### 12.2 Partially Implemented

| Component | File | Status |
|-----------|------|--------|
| Chat Orchestrator | `admin/core/chat_orchestrator.py` | V3 pipeline is the production path for WebSocket/REST; conversation worker still uses separate use-case pipeline |
| BrainBridge | `aaas/brain.py` | Direct and HTTP modes implemented; `recall()` implemented for both modes |
| SpiceDB Client | `services/common/spicedb_client.py` | Real gRPC client; some high-level RBAC API endpoints still return stubs |
| Policy Client | `services/common/policy_client.py` | Real HTTP OPA client; `UnifiedGate` uses it |
| Audit Publisher | `admin/core/models.py` OutboxMessage | Outbox exists; not wired to all endpoints |
| WebSocket Consumer | `services/gateway/consumers/chat.py` | Wired to V3 orchestrator; chat is blocked by frontend WebSocket URL mismatch and missing agent selector |
| MemoryPort Adapters | `services/common/ports/memory_port.py` | Protocol defined; production adapters implement `MemoryServiceProtocol` instead |

### 12.3 Gaps

| ID | Gap | Priority | Status |
|----|-----|----------|--------|
| GAP-001 | Account lockout -- track failed attempts, lock after 5 failures | Medium | **Fixed** |
| GAP-002 | PKCE for OAuth -- secure code exchange | Medium | **Fixed** |
| GAP-003 | Real SpiceDB integration -- full API endpoint wiring with gRPC calls | High | Partial — `UnifiedGate` uses real SpiceDB; RBAC endpoints still stubbed |
| GAP-004 | Real OPA integration -- actual policy engine calls | High | **Fixed in `UnifiedGate`/`PolicyClient`** |
| GAP-005 | Audit logging -- wire outbox publisher to all endpoints | Medium | Open |
| GAP-006 | Chat system degradation -- wire HealthMonitor and SimpleGovernor into chat | Medium | **Fixed in V3 orchestrator** |
| GAP-007 | Redis connection pooling -- shared factory | Low | Open |
| GAP-008 | V3 Chat Orchestrator -- make it the production path | High | **Fixed for WebSocket/REST** |
| GAP-009 | Chat UI WebSocket contract -- frontend omits `agent_id` | High | Open |
| GAP-010 | Chat UI agent selector -- no selector when user has multiple agents | High | Open |
| GAP-011 | SomaBrain URL resolution -- default URL is empty/wrong | High | Open |

---

## 13. Related Services

### 13.1 SomaBrain

- Port: 63996 (AAAS) or 9696 (direct)
- API: `http://localhost:63996` or `http://localhost:9696`
- Endpoints: `/api/v1/agents/{id}/sessions`, `/api/v1/agents/{id}/chat`
- Streaming: Server-Sent Events
- Note: `somabrain` Python package is referenced as a path dependency (`../somabrain`) in `pyproject.toml`. This repository does not contain SomaBrain source code.

### 13.2 SomaFractalMemory

- Port: 63901 (AAAS) or 10101 (direct)
- API: `http://localhost:63901` or `http://localhost:10101`
- Endpoints: `/api/v1/recall`, `/api/v1/store`
- Memory types: `episodic`, `semantic`
- Note: This repository does not contain SomaFractalMemory source code.

---

## 14. Quick Start

### 14.1 Standalone Development Setup

```bash
cd somaAgent01
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cd infra/standalone
cp .env.example .env
# Edit .env: set POSTGRES_PASSWORD, KEYCLOAK_ADMIN_PASSWORD, VAULT_DEV_ROOT_TOKEN_ID
docker compose up -d

# Run migrations
docker compose exec somaagent_standalone python manage.py migrate

# Access points:
# API: http://localhost:20020
# Keycloak: http://localhost:20880
```

### 14.2 Required Environment Variables

```bash
# Database
POSTGRES_USER=somaagent
POSTGRES_PASSWORD=<required>
POSTGRES_DB=somaagent
SA01_DB_DSN=postgresql://somaagent:<password>@somaagent_postgres:5432/somaagent

# Redis
SA01_REDIS_URL=redis://somaagent_redis:6379/0

# Keycloak
KEYCLOAK_URL=http://somaagent_keycloak:8080
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=<required>
KEYCLOAK_REALM=somaagent

# Deployment Mode
SA01_DEPLOYMENT_MODE=STANDALONE
SOMA_AAAS_MODE=false
```

### 14.3 Canonical Patterns

| Pattern | Canonical File | Rule |
|---------|----------------|------|
| Configuration | `config.settings_registry.SettingsRegistry` | Single source of truth for environment variables |
| Redis Pool | `services.common.redis_pool.get_async_redis_pool()` | Never call `redis.from_url()` directly |
| Store Base | `services.common.store_base.BaseStore` | All new stores inherit from this |
| Rate Limiting | `services.common.rate_limiter.RedisRateLimiter` | Only rate limiter to use |
| Auth | `admin.common.auth.AuthBearer` | Only auth dependency for Ninja APIs |

---

## 15. Notes for Future Agents

1. Always check existing code first. Many features are claimed in documentation but not implemented.
2. Use the correct port namespace: somaAgent01 = 20xxx (standalone) or 63xxx (AAAS).
3. Do not use mocks in tests. Use real Docker infrastructure when available.
4. Use Django Ninja only. No FastAPI, no SQLAlchemy.
5. Use Lit 3.x only. No React, no Alpine.js.
6. Read the audit report (`SOMA_AGENT01_COMPREHENSIVE_AUDIT_REPORT.md`) for true system health assessment.
7. Documentation drifts from reality. SRS documents describe intent, not implementation. Trust the code.

---

End of Document
