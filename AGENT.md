# 🧠 SomaAgent01 - Agent Knowledge Base

> **Purpose**: This file provides comprehensive context for AI agents working on the SomaAgent01 codebase.
> **Last Updated**: 2025-12-30
> **Version**: 1.0.0

---

## 📋 Executive Summary

**SomaAgent01** is an enterprise-grade **Multi-Agent Cognitive Platform** built on **Django 5.0 + Django Ninja**. It's a complete SaaS platform for orchestrating AI agents with:

- Multi-tenant architecture with strict data isolation
- Keycloak-based authentication (OIDC)
- SpiceDB-based fine-grained authorization (Zanzibar-style)
- Real-time chat via WebSocket/SSE
- Integration with SomaBrain (cognitive runtime) and SomaFractalMemory (memory storage)
- Full observability stack (Prometheus, Grafana, Kafka audit logging)
- Open-source-only dependencies across the stack

---

## 🏗️ Architecture Overview

### Technology Stack

| Layer | Technology | Notes |
|-------|------------|-------|
| **API Framework** | Django 5.0 + Django Ninja | 100% Django - NO FastAPI |
| **ORM** | Django ORM | NO SQLAlchemy |
| **Frontend** | Lit 3.x Web Components | NO React (legacy), NO Alpine.js |
| **Database** | PostgreSQL 16 | Port 20432 |
| **Cache** | Redis 7 | Port 20379 |
| **Message Broker** | Kafka 3.7 (KRaft) | Port 20092 |
| **Vector DB** | Milvus 2.3 | Port 20530 (NO Qdrant) |
| **Identity** | Keycloak 24 | Port 20880 |
| **Authorization** | SpiceDB 1.29 | Port 20051 |
| **Policy Engine** | OPA | Port 20181 |
| **Observability** | Prometheus + Grafana | Ports 20090, 20300 |

### Port Namespace

**SomaAgent01 uses port 20xxx** to avoid conflicts:
- PostgreSQL: 20432
- Redis: 20379
- Kafka: 20092
- Milvus: 20530
- SpiceDB: 20051
- OPA: 20181
- Keycloak: 20880
- Prometheus: 20090
- Grafana: 20300
- Django API: 20020
- Frontend: 20080

**Related Services:**
- SomaBrain: Port 30xxx (cognitive runtime)
- SomaFractalMemory: Port 9xxx (memory storage)

### ⚡ The "Perfect Startup" Protocol (Tilt Orchestrated)

**Tilt is the commander.** It enforces a strict, resilient startup sequence to guarantee production parity locally.

1.  **Infrastructure Initialization**: `postgres`, `redis`, `milvus` start first.
    *   *Auto-Provisioning*: `postgres` runs `init_dbs.sql` to create `somabrain`, `somafractalmemory`, `somaagent` DBs automatically.
2.  **Automated Migrations**: `database-migrations` resource runs *before* any app code.
    *   **Database Name Priority**: Services MUST prioritize `SOMA_DB_NAME` environment variable over parsed connection strings. This ensures Tilt can strictly control database targets during migrations (`SOMA_DB_NAME=somafractalmemory` overrides legacy defaults).
    *   **Service Dependency**: `somafractalmemory` and `somabrain` must NOT start until `database-migrations` exits successfully (Exit Code 0).
    *   **Mode Enforcement**: Migrations MUST run with `SA01_DEPLOYMENT_MODE=PROD` to trigger actual schema changes and ensure production-grade resilience.
    *   **Sequence**: SomaFractalMemory (Layer 1) → SomaBrain (Layer 2) → SomaAgent01 (Layer 3).
    *   **Fail-Fast**: Any migration failure halts the entire stack (`set -e`).
3.  **Application Launch**: Apps (`django-api`, `somabrain`, `somafractalmemory`) are blocked until migrations complete.
    *   **Production Runners**: All Python services run via `uvicorn` (ASGI), matching production.

### 🛡️ Resilience & Recovery

**Command**: `make reset-infra`

This is the definitive "Panic Button" for local development. If the stack becomes unstable, orphaned, or corrupted (e.g., "Update error" in Tilt), run this command.

**What it does (via `scripts/reset_infrastructure.sh`):**
1.  **Destruction**: `docker compose down -v` (Wipes all volumes/state).
2.  **Hydration**: Starts `postgres` and **waits** for readiness (no race conditions).
3.  **Migration**: Runs `spicedb migrate head` automatically (prevents "invalid datastore" crashes).
4.  **Launch**: Brings up the full stack.

**Core Infrastructure Rule**:
*   **NO PROFILES**: Core services (`postgres`, `redis`, `kafka`, `milvus`, `spicedb`, `opa`) MUST NOT use `profiles: [...]` in `docker-compose.yml`. They must be visible to Tilt at all times to prevent dependency graph failures.

---

## 🧭 Software Deployment Modes

**Two software modes are canonical across the three repos:**
- **StandAlone**: each service runs independently with local auth/storage and no required cross-service calls.
- **SomaStackClusterMode**: all three services run as one SaaS; SomaBrain + SomaFractalMemory are inseparable and must run as a paired runtime with shared tenant identity and auth.

**Reference:** `docs/deployment/SOFTWARE_DEPLOYMENT_MODES.md` and `docs/srs/SRS-UNIFIED-SAAS.md`.
**Local baseline:** 15 GB total host memory budget for full-stack local dev (see `docs/deployment/DEPLOYMENT.md`).

---

## 📁 Project Structure

```
somaAgent01/
├── admin/                    # Django apps (THE CORE)
│   ├── api.py               # Master Django Ninja API router
│   ├── auth/                # Authentication (Keycloak integration)
│   │   ├── api.py          # Auth endpoints: /token, /login, /refresh, /logout
│   │   ├── mfa.py          # MFA endpoints
│   │   └── password_reset.py
│   ├── common/              # Shared utilities
│   │   ├── auth.py         # JWT validation, AuthBearer, RoleRequired
│   │   ├── exceptions.py   # Custom exceptions
│   │   └── handlers.py     # Exception handlers
│   ├── core/               # Core models and infrastructure
│   │   └── models.py       # Django ORM models (Session, Capsule, etc.)
│   ├── agents/             # Agent management
│   ├── chat/               # Chat API
│   ├── conversations/      # Conversation management
│   ├── sessions/           # Session management
│   ├── saas/               # Multi-tenant SaaS features
│   ├── memory/             # Memory integration
│   ├── voice/              # Voice (STT/TTS)
│   ├── workflows/          # Temporal workflows
│   └── [40+ more apps]     # See admin/api.py for full list
├── services/                # Service layer
│   ├── gateway/            # Gateway services
│   │   └── auth.py        # JWT + OPA policy integration
│   └── common/             # Shared services
│       ├── audit.py       # Kafka audit publisher
│       ├── rate_limiter.py
│       └── policy_client.py
├── webui/                   # Frontend (Lit 3.x)
│   └── src/
│       ├── views/          # Page components
│       │   ├── saas-login.ts    # Login page (OAuth, SSO, email/password)
│       │   ├── saas-chat.ts     # Chat view (WebSocket, streaming)
│       │   └── saas-mfa-setup.ts
│       ├── services/       # Frontend services
│       │   ├── keycloak-service.ts
│       │   └── websocket-client.ts
│       └── stores/         # State management
│           └── auth-store.ts
├── infra/                   # Infrastructure configs
│   ├── keycloak/           # Keycloak realm config
│   └── docker/             # Docker configs
├── policy/                  # OPA policies (.rego files)
├── schemas/                 # JSON schemas, SpiceDB schema
├── prompts/                 # Agent prompt templates
├── docs/                    # Documentation
│   ├── README.md           # Documentation entry point
│   ├── deployment/         # Deployment guides (infra + software modes)
│   ├── development/        # Contributor rules and standards
│   ├── design/             # Design inventories
│   ├── ui/                 # UI requirements and styling
│   ├── onboarding/         # Agent onboarding
│   ├── governance/         # Steering + violations
│   ├── tasks/              # Unified task trackers
│   ├── legacy/             # Canonical legacy docs
│   ├── srs/                # Software Requirements Specs
│   └── specs/              # Feature specs
├── tests/                   # Test suite
│   ├── unit/               # Unit tests
│   └── integration/        # Integration tests
├── docker-compose.yml       # Full stack deployment
├── manage.py               # Django management
├── pyproject.toml          # Python dependencies
└── docs/development/VIBE_CODING_RULES.md    # CRITICAL: Read this first!
```

---

## 🔐 Authentication Architecture

### Flow Overview

```
User → Login Page → Django API → Keycloak → SpiceDB → Redis → PostgreSQL
```

### Key Components

1. **Keycloak** (Port 20880)
   - OIDC identity provider
   - Realm: `somaagent`
   - Client: `eye-of-god` (public client)
   - Supports: Password grant, OAuth (Google, GitHub), SAML, LDAP

2. **JWT Tokens**
   - Access token: 15 min TTL, httpOnly cookie
   - Refresh token: 7-30 days TTL, httpOnly cookie
   - Claims: `sub`, `email`, `tenant_id`, `realm_access.roles`

3. **SpiceDB** (Port 20051)
   - Zanzibar-style authorization
   - Schema in `schemas/spicedb/`
   - Relationships: user → tenant → agent → conversation

4. **Session Management**
   - Redis-based sessions (key: `session:{user_id}:{session_id}`)
   - 15 min TTL, extended on activity

### Existing Auth Code

| File | Purpose |
|------|---------|
| `admin/auth/api.py` | Auth router: `/token`, `/login`, `/refresh`, `/logout`, SSO |
| `admin/common/auth.py` | `AuthBearer`, `RoleRequired`, `decode_token()` |
| `services/gateway/auth.py` | JWT + OPA policy integration |
| `webui/src/views/saas-login.ts` | Login page (888 lines, full OAuth/SSO) |
| `webui/src/services/keycloak-service.ts` | Keycloak OIDC client |
| `webui/src/stores/auth-store.ts` | Auth state management |

### User Roles (Priority Order)

1. `saas_admin` → `/platform`
2. `tenant_sysadmin` → `/admin`
3. `tenant_admin` → `/admin`
4. `agent_owner` → `/chat`
5. `developer` → `/chat` (DEV mode)
6. `trainer` → `/chat` (TRN mode)
7. `user` → `/chat`
8. `viewer` → `/chat` (read-only)

---

## 💬 Chat Architecture

### Flow Overview

```
User → Chat UI → WebSocket → Django → SomaBrain → LLM
                                    → SomaFractalMemory
```

### Key Components

1. **WebSocket Protocol**
   - URL: `wss://{host}/ws/chat/{agent_id}`
   - Auth: JWT in cookie
   - Messages: JSON with `type`, `conversation_id`, `content`

2. **SomaBrain** (Port 30101)
   - Cognitive runtime for agents
   - Endpoints: `/api/v1/agents/{id}/sessions`, `/api/v1/agents/{id}/chat`
   - Streaming via SSE

3. **SomaFractalMemory** (Port 9595)
   - Fractal coordinate-based memory
   - Endpoints: `/api/v1/recall`, `/api/v1/store`
   - Memory types: `episodic`, `semantic`

### Existing Chat Code

| File | Purpose |
|------|---------|
| `admin/conversations/api.py` | Conversation CRUD (placeholder) |
| `admin/chat/api/chat.py` | Chat session API |
| `webui/src/views/saas-chat.ts` | Chat view (1063 lines, WebSocket) |
| `webui/src/services/websocket-client.ts` | WebSocket client |

---

## 🗄️ Data Models

### Core Django Models (`admin/core/models.py`)

```python
# Sessions
Session          # Chat session
SessionEvent     # Session events

# Capsules (Agent containers)
Capsule          # Capsule definition
CapsuleInstance  # Running instance

# Infrastructure
Capability       # Agent capabilities
Job              # Scheduled jobs
Notification     # User notifications
Prompt           # Prompt templates
FeatureFlag      # Feature flags
AuditLog         # Audit trail

# Zero Data Loss
OutboxMessage    # Transactional outbox
DeadLetterMessage # DLQ
IdempotencyRecord # Exactly-once
PendingMemory    # Memory sync queue
```

### SaaS Models (`admin/saas/models.py`)

```python
Tenant           # Organization
TenantUser       # User-tenant membership
Subscription     # Billing subscription
AuditLog         # SaaS audit
```

---

## 🔌 API Endpoints

### Master Router (`admin/api.py`)

All endpoints are under `/api/v2/`:

| Prefix | Router | Purpose |
|--------|--------|---------|
| `/auth` | `admin.auth.api` | Authentication |
| `/agents` | `admin.agents.api` | Agent management |
| `/chat` | `admin.chat.api` | Chat sessions |
| `/conversations` | `admin.conversations.api` | Conversations |
| `/sessions` | `admin.sessions.api` | User sessions |
| `/saas` | `admin.saas.api` | SaaS admin |
| `/memory` | `admin.memory.api` | Memory integration |
| `/voice` | `admin.voice.api` | Voice (STT/TTS) |
| `/workflows` | `admin.workflows.api` | Temporal workflows |
| `/audit` | `admin.audit.api` | Audit logs |
| `/permissions` | `admin.permissions.api` | RBAC |
| ... | ... | 40+ more routers |

### Key Auth Endpoints

```
POST /api/v2/auth/token      # Get token (password grant)
POST /api/v2/auth/login      # Email/password login
POST /api/v2/auth/refresh    # Refresh token
POST /api/v2/auth/logout     # Logout
GET  /api/v2/auth/me         # Current user
GET  /api/v2/auth/oauth/{provider}  # OAuth initiation
GET  /api/v2/auth/oauth/callback    # OAuth callback
POST /api/v2/auth/mfa/verify        # MFA verification
```

---

## 🧪 Testing Requirements

### CRITICAL: No Mocks!

Per VIBE Coding Rules and steering files:
- **All tests require real infrastructure**
- No fakeredis, no mocks, no stubs
- Use `docker compose --profile core up -d` for test infra

### Test Infrastructure

```bash
# Start test infrastructure
docker compose --profile core up -d

# Run tests
pytest

# Run specific test
pytest tests/test_auth.py -v
```

### Property-Based Testing

Use **Hypothesis** for property tests:
- Minimum 100 iterations per property
- Tag format: `Feature: {name}, Property {N}: {description}`

---

## 🚨 VIBE Coding Rules (CRITICAL)

### The 7 Rules

1. **NO BULLSHIT** - No mocks, no placeholders, no TODOs
2. **CHECK FIRST, CODE SECOND** - Review architecture before coding
3. **NO UNNECESSARY FILES** - Modify existing files when possible
4. **REAL IMPLEMENTATIONS ONLY** - Production-grade code always
5. **DOCUMENTATION = TRUTH** - Verify from official docs
6. **COMPLETE CONTEXT REQUIRED** - Understand full flow first
7. **REAL DATA, REAL SERVERS** - Use actual services

### Django Purity (STRICT)

- **ONLY** Django ORM (NO SQLAlchemy)
- **ONLY** Django Migrations (NO Alembic)
- **ONLY** Django Ninja (NO FastAPI)
- **ONLY** Lit 3.x (NO React, NO Alpine.js)
- **ONLY** Milvus (NO Qdrant)

### Forbidden Patterns

❌ Mocks, stubs, placeholders
❌ Hardcoded values in production code
❌ TODO, FIXME, "implement later"
❌ Inventing APIs or syntax
❌ Guessing behavior
❌ Creating unnecessary files

---

## 📊 Current Implementation Status

### ✅ Implemented (Existing)

| Component | File | Status |
|-----------|------|--------|
| Auth Router | `admin/auth/api.py` | Full (login, OAuth, SSO, MFA) |
| JWT Validation | `admin/common/auth.py` | Full |
| Login Page | `webui/src/views/saas-login.ts` | Full (888 lines) |
| Chat View | `webui/src/views/saas-chat.ts` | Full (1063 lines) |
| Keycloak Service | `webui/src/services/keycloak-service.ts` | Full |
| Auth Store | `webui/src/stores/auth-store.ts` | Full |
| Core Models | `admin/core/models.py` | Full |
| Rate Limiter | `services/common/rate_limiter.py` | Full |
| Audit Publisher | `services/common/audit.py` | Full |

### ⚠️ Placeholder/Incomplete

| Component | File | Status |
|-----------|------|--------|
| Sessions API | `admin/sessions/api.py` | Placeholder (returns static data) |
| Conversations API | `admin/conversations/api.py` | Placeholder (returns static data) |
| SessionManager | N/A | Missing (no Redis session storage) |
| SpiceDB Client | N/A | Missing (no fine-grained permissions) |
| ChatService | N/A | Missing (no SomaBrain integration) |
| WebSocket Consumer | N/A | Missing (no Django Channels) |

### 🔴 Gaps to Implement

1. **SessionManager** - Redis session storage with TTL
2. **Account Lockout** - Track failed attempts, lock after 5 failures
3. **PKCE for OAuth** - Secure OAuth code exchange
4. **SpiceDB Integration** - Fine-grained permission checks
5. **ChatService** - Real SomaBrain/SomaFractalMemory integration
6. **WebSocket Consumer** - Django Channels for streaming
7. **Audit Logging** - Structured events to Kafka

---

## 🔗 Related Services

### SomaBrain (Port 30xxx)

Cognitive runtime for AI agents:
- API: `http://localhost:30101`
- Endpoints: `/api/v1/agents/{id}/sessions`, `/api/v1/agents/{id}/chat`
- Streaming: SSE

### SomaFractalMemory (Port 9xxx)

Fractal coordinate-based memory:
- API: `http://localhost:9595`
- Endpoints: `/api/v1/recall`, `/api/v1/store`
- Backends: PostgreSQL, Redis, Milvus

---

## 🚀 Quick Start

### Development Setup

```bash
# 1. Clone and setup
cd somaAgent01
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Start infrastructure
docker compose --profile core --profile auth --profile security up -d

# 3. Run migrations
python manage.py migrate

# 4. Start Django
python manage.py runserver 0.0.0.0:8020

# 5. Start frontend (separate terminal)
cd webui
bun install
bun run dev
```

### Environment Variables

```bash
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=somastack2024
POSTGRES_DB=somaagent

# Redis
REDIS_PASSWORD=somastack2024

# Keycloak
KEYCLOAK_URL=http://localhost:20880
KEYCLOAK_REALM=somaagent
KEYCLOAK_CLIENT_ID=eye-of-god

# SpiceDB
SPICEDB_TOKEN=somaagent-spicedb-token

# External Services
SOMABRAIN_URL=http://localhost:30101
SOMAFRACTALMEMORY_URL=http://localhost:9595
```

---

## 📚 Key Documentation

| Document | Path | Purpose |
|----------|------|---------|
| VIBE Rules | `docs/development/VIBE_CODING_RULES.md` | **READ FIRST** |
| README | `docs/README.md` | Project overview |
| Deployment | `docs/deployment/DEPLOYMENT.md` | Deployment guide |
| Software Modes | `docs/deployment/SOFTWARE_DEPLOYMENT_MODES.md` | StandAlone vs SomaStackClusterMode |
| Contributing | `docs/development/CONTRIBUTING.md` | Contribution guide |
| Inventory | `docs/design/INVENTORY.md` | Component inventory |
| Agent Tasks | `docs/tasks/AGENT_TASKS.md` | Current tasks |

### Specs (`.kiro/specs/`)

| Spec | Status | Purpose |
|------|--------|---------|
| `login-to-chat-journey/` | In Progress | Login → Chat user journey |

---

## 🎯 For AI Agents

### Before You Code

1. **Read `docs/development/VIBE_CODING_RULES.md`** - Non-negotiable
2. **Check existing code** - Don't reinvent
3. **Understand the flow** - Data flow, dependencies
4. **Use real infrastructure** - No mocks

### Key Files to Read

```
admin/api.py                    # Master API router
admin/auth/api.py               # Auth implementation
admin/common/auth.py            # JWT utilities
admin/core/models.py            # Django models
services/gateway/auth.py        # Gateway auth
webui/src/views/saas-login.ts   # Login page
webui/src/views/saas-chat.ts    # Chat view
docker-compose.yml              # Infrastructure
```

### Common Tasks

| Task | Key Files |
|------|-----------|
| Add API endpoint | `admin/{app}/api.py` |
| Add Django model | `admin/{app}/models.py` |
| Add frontend view | `webui/src/views/{name}.ts` |
| Add service | `services/common/{name}.py` |
| Add test | `tests/unit/{area}/test_{name}.py` |

---

**End of Agent Knowledge Base**


---

## 🔧 Detailed Component Reference

### Authentication Components

#### Backend: `admin/auth/api.py`

```python
# Key endpoints implemented:
POST /auth/token          # Password grant token exchange
POST /auth/login          # Email/password login
POST /auth/refresh        # Token refresh
POST /auth/logout         # Logout + token revocation
GET  /auth/me             # Current user info
GET  /auth/oauth/{provider}  # OAuth initiation
GET  /auth/oauth/callback    # OAuth callback
POST /auth/mfa/verify        # MFA verification
POST /auth/impersonate       # Admin impersonation
POST /auth/sso/test          # SSO connection test
POST /auth/sso/configure     # SSO configuration
POST /auth/register          # User registration

# Key schemas:
TokenRequest, TokenResponse, RefreshRequest, UserResponse
LoginRequest, RegisterRequest, ImpersonationRequest
SSOConfigRequest, SSOTestRequest
```

#### Backend: `admin/common/auth.py`

```python
# Key classes:
KeycloakConfig      # Keycloak configuration from env
TokenPayload        # Decoded JWT payload model
JWKSCache           # JWKS public key cache

# Security classes for Django Ninja:
AuthBearer          # Basic JWT authentication
RoleRequired        # JWT + role check
TenantRequired      # JWT + tenant extraction

# Key functions:
get_keycloak_config()  # Get cached Keycloak config
decode_token(token)    # Decode and validate JWT
get_current_user(request)  # Get user from request
require_roles(*roles)  # Decorator for role check
```

#### Frontend: `webui/src/views/saas-login.ts`

```typescript
// Features implemented:
- Email/password login form
- OAuth buttons (Google, GitHub)
- Enterprise SSO modal (OIDC, SAML, LDAP, AD, Okta, Azure, Ping, OneLogin)
- Password visibility toggle
- Remember me checkbox
- Forgot password link
- Form validation
- Loading states
- Error handling

// Key methods:
handleLogin()           # Email/password submission
handleOAuth(provider)   # OAuth initiation
handleSSOSubmit()       # Enterprise SSO
validateEmail(email)    # Email validation
```

#### Frontend: `webui/src/services/keycloak-service.ts`

```typescript
// Features:
- Keycloak OIDC integration
- Token management
- Token refresh
- Logout
- User info retrieval

// Key methods:
init()                  # Initialize Keycloak
login()                 # Redirect to Keycloak login
logout()                # Logout and clear tokens
getToken()              # Get current access token
refreshToken()          # Refresh access token
getUserInfo()           # Get user profile
```

### Chat Components

#### Frontend: `webui/src/views/saas-chat.ts`

```typescript
// Features implemented:
- Agent selection dropdown
- Conversation list sidebar
- Message input with Enter/Shift+Enter
- Message history display
- Streaming response rendering
- WebSocket connection management
- Reconnection with backoff
- Mode switching (STD, DEV, TRN, RO)
- Typing indicators
- Error handling

// Key methods:
initializeChat(agentId)     # Initialize chat session
sendMessage(content)        # Send user message
handleStreamToken(delta)    # Handle streaming response
reconnectWebSocket()        # Reconnect with backoff
switchAgent(agentId)        # Switch to different agent
```

### Session Components

#### Backend: `admin/sessions/api.py` (PLACEHOLDER)

```python
# Current status: Returns static/placeholder data
# Needs implementation:
- Real Redis session storage
- Session CRUD operations
- Session statistics
- Security actions (terminate, force logout)

# Endpoints defined but not implemented:
GET  /sessions/current       # Get current session
POST /sessions/current/refresh  # Refresh session
POST /sessions/current/logout   # Logout
GET  /sessions/users/{user_id}  # List user sessions
DELETE /sessions/users/{user_id}  # Force logout user
GET  /sessions                # List all sessions (admin)
DELETE /sessions/{session_id}  # Terminate session
GET  /sessions/stats          # Session statistics
POST /sessions/security/terminate-all  # Emergency logout
```

### Conversation Components

#### Backend: `admin/conversations/api.py` (PLACEHOLDER)

```python
# Current status: Returns static/placeholder data
# Needs implementation:
- Real PostgreSQL storage
- SomaBrain integration
- Message streaming

# Endpoints defined but not implemented:
GET  /conversations           # List conversations
POST /conversations           # Start conversation
GET  /conversations/{id}      # Get conversation
PATCH /conversations/{id}     # Update conversation
DELETE /conversations/{id}    # Delete conversation
GET  /conversations/{id}/messages  # List messages
POST /conversations/{id}/messages  # Send message
POST /conversations/{id}/chat      # Chat with agent
GET  /conversations/{id}/stream    # Stream info
POST /conversations/{id}/end       # End conversation
POST /conversations/{id}/archive   # Archive conversation
GET  /conversations/{id}/stats     # Conversation stats
POST /conversations/{id}/export    # Export conversation
POST /conversations/search         # Search conversations
```

---

## 🔄 Integration Points

### LLM Provider Integration (LiteLLM)

Chat streaming uses LiteLLM-backed providers configured via Django ORM (`admin.llm.models.LLMModelConfig`)
and runtime settings (`admin/core/helpers/settings_defaults.py`).

The chat flow selects:

- `chat_model_provider`
- `chat_model_name`
- `chat_model_api_base` (optional)

All LLM calls are made directly via LiteLLM (no SomaBrain chat endpoint).

### SomaFractalMemory Integration

```python
# Base URL: http://localhost:9595 (or SOMA_MEMORY_URL / SOMA_FRACTAL_MEMORY_URL env)
# Auth: Bearer SOMA_MEMORY_API_TOKEN (or SOMA_API_TOKEN), X-Soma-Tenant header

# Memory Recall (Search)
POST /memories/search
Body: {
    "query": "string",
    "top_k": 5,
    "filters": { "agent_id": "uuid", "user_id": "uuid" }
}

# Memory Store
POST /memories
Body: {
    "coord": "comma-separated vector",
    "payload": {
        "content": "string",
        "agent_id": "uuid",
        "user_id": "uuid",
        "conversation_id": "uuid",
        "timestamp": "iso8601"
    },
    "memory_type": "episodic"
}
```

### SpiceDB Integration

```python
# Base URL: localhost:20051 (gRPC)
# Token: SPICEDB_TOKEN env var

# Check Permission
CheckPermission(
    resource=ObjectReference(object_type="agent", object_id="uuid"),
    permission="activate_std",
    subject=SubjectReference(object=ObjectReference(object_type="user", object_id="uuid"))
)

# Lookup Resources
LookupResources(
    resource_object_type="agent",
    permission="view",
    subject=SubjectReference(object=ObjectReference(object_type="user", object_id="uuid"))
)

# Schema (schemas/spicedb/):
definition user {}
definition tenant { relation sysadmin, admin, developer, trainer, member, viewer: user }
definition agent { relation tenant: tenant, owner, admin, developer, trainer, user, viewer: user }
definition conversation { relation agent: agent, owner: user }
```

### Kafka Integration

```python
# Broker: localhost:20092 (or KAFKA_BROKERS env)

# Audit Topics:
audit.auth      # Login, logout, session events
audit.chat      # Conversation, message events
audit.security  # Permission denied, lockout events

# Event Schema:
{
    "event_type": "auth.login",
    "timestamp": "iso8601",
    "user_id": "uuid",
    "tenant_id": "uuid",
    "ip_address": "string",
    "user_agent": "string",
    "metadata": {...}
}
```

---

## 📋 Implementation Checklist

### Phase 1: Authentication Hardening

- [ ] **SessionManager** (`services/common/session_manager.py`)
  - [ ] `create_session()` - Redis storage with TTL
  - [ ] `get_session()` - Session retrieval
  - [ ] `update_activity()` - TTL extension
  - [ ] `delete_session()` - Session deletion
  - [ ] `delete_user_sessions()` - Force logout

- [ ] **Account Lockout** (modify `admin/auth/api.py`)
  - [ ] Track failed attempts in Redis (`login_attempts:{email}`)
  - [ ] Lock after 5 failures (`lockout:{email}`)
  - [ ] Return 403 with `retry_after`

- [ ] **PKCE for OAuth** (modify `admin/auth/api.py`)
  - [ ] Generate `code_verifier` (43-128 chars)
  - [ ] Compute `code_challenge` (SHA256)
  - [ ] Store in Redis (`oauth_state:{state}`)
  - [ ] Validate on callback

### Phase 2: Authorization

- [ ] **SpiceDB Client** (`services/common/spicedb_client.py`)
  - [ ] `check_permission()` - Single permission check
  - [ ] `get_permissions()` - All permissions for user
  - [ ] `lookup_resources()` - Resources user can access

- [ ] **Permission Integration**
  - [ ] Query permissions on login
  - [ ] Cache in session
  - [ ] Filter agent list by permissions

### Phase 3: Chat Integration

- [ ] **ChatService** (`services/common/chat_service.py`)
  - [ ] `create_conversation()` - PostgreSQL insert
  - [ ] `initialize_agent_session()` - SomaBrain call
  - [ ] `recall_memories()` - SomaFractalMemory call
  - [ ] `send_message()` - Stream from SomaBrain
  - [ ] `store_memory()` - Async memory storage
  - [ ] `generate_title()` - Utility model call

- [ ] **WebSocket Consumer** (`services/gateway/consumers/chat.py`)
  - [ ] Connection authentication
  - [ ] Message handling
  - [ ] Streaming response
  - [ ] Heartbeat (ping/pong)
  - [ ] Reconnection handling

### Phase 4: Audit & Observability

- [ ] **Audit Logging** (enhance `services/common/audit.py`)
  - [ ] Login events (success/failure)
  - [ ] Logout events
  - [ ] Session events
  - [ ] Permission denied events
  - [ ] Chat session events

### Phase 5: Frontend Enhancements

- [ ] **Token Refresh Deduplication** (`webui/src/stores/auth-store.ts`)
  - [ ] Promise-based lock
  - [ ] Single refresh request

- [ ] **Role-Based Redirect** (`webui/src/stores/auth-store.ts`)
  - [ ] `getDefaultRoute(roles)` function
  - [ ] Return URL validation (same-origin)

- [ ] **Email Validation** (`webui/src/views/saas-login.ts`)
  - [ ] RFC 5322 compliant validation
  - [ ] Inline error display

---

## 🧪 Property Tests to Implement

| # | Property | Validates |
|---|----------|-----------|
| 1 | Email Validation (RFC 5322) | Req 1.2, 2.1 |
| 2 | JWT Decode/Encode Round-Trip | Req 2.3 |
| 3 | Account Lockout After N Failures | Req 2.5 |
| 4 | PKCE Code Generation | Req 3.1 |
| 5 | OAuth State Validation | Req 3.2 |
| 6 | Session Round-Trip | Req 5.1 |
| 7 | Permission Resolution Consistency | Req 5.2 |
| 8 | Role-Based Redirect Routing | Req 6.1 |
| 9 | Return URL Same-Origin Validation | Req 6.2 |
| 10 | Token Refresh Deduplication | Req 10.5 |
| 11 | Audit Event Structure | Req 12.1 |

---

## 🔍 Debugging Tips

### Check Keycloak

```bash
# Health check
curl http://localhost:20880/health/ready

# Get realm config
curl http://localhost:20880/realms/somaagent/.well-known/openid-configuration
```

### Check SpiceDB

```bash
# Health check (gRPC)
grpcurl -plaintext localhost:20051 grpc.health.v1.Health/Check

# Check schema
zed schema read --endpoint=localhost:20051 --token=somaagent-spicedb-token
```

### Check Redis

```bash
# Connect
redis-cli -p 20379 -a somastack2024

# Check sessions
KEYS session:*

# Check lockouts
KEYS lockout:*
```

### Check Kafka

```bash
# List topics
docker exec somaagent-kafka kafka-topics.sh --list --bootstrap-server localhost:9092

# Consume audit events
docker exec somaagent-kafka kafka-console-consumer.sh --topic audit.auth --from-beginning --bootstrap-server localhost:9092
```

---

## 📝 Notes for Future Agents

1. **Always check existing code first** - Many features are already implemented
2. **Use the port namespace** - somaAgent01 = 20xxx, somabrain = 30xxx, somafractalmemory = 9xxx
3. **No mocks in tests** - Use real Docker infrastructure
4. **Django Ninja only** - No FastAPI, no SQLAlchemy
5. **Lit 3.x only** - No React, no Alpine.js
6. **Read docs/development/VIBE_CODING_RULES.md** - It's not optional

---

**End of Agent Knowledge Base (Extended)**

---

## 🛡️ VIBE Architectural Audit (2025-01-02)

### 🧠 The "Cognitive Operating System"
The 2025-01-02 audit reveals that SomaAgent01 has evolved beyond a standard chatbot into a **Self-Governing Cognitive Operating System**.

#### 1. The Pre-Flight Cortex (SimpleGovernor)
- **Status**: ✅ Implemented & Wired
- **Location**: `services/common/simple_governor.py` (279 lines, production-grade)
- **Function**: Transforms stochastic LLM calls into deterministic, budgeted transactions.
- **Mechanism**:
  - **Fixed Lane Allocation**: Binary ratios (Normal vs Degraded) with field-tested percentages.
  - **No AIQ Scoring**: Removed over-engineering from deprecated AgentIQ.
  - **Rescue Path**: Automatically degrades to safe-mode if context quality drops below thresholds (Critical Health).

#### 2. The Autonomic Nervous System (DegradationMonitor)
- **Status**: ✅ Implemented
- **Function**: "Proprioception" for the agent.
- **Mechanism**:
  - Monitors `SomaBrain`, `Redis`, `PostgreSQL`, `Kafka` in real-time.
  - Triggers **Degradation Levels** (Minor -> Critical).
  - Wired into `ContextBuilder` to dynamically shrink context windows when `SomaBrain` (Long-Term Memory) is unreachable.

### 🚀 "Next Level" Recommendations

#### 1. **Complete the "Real Auth" Loop (VIBE Rule 47)**
- **Current Gap**: The UI works for humans (Login Page), but Automation (QA Bots) lacks a "Real Auth" mechanism.
- **Solution**: Implement the `tests/e2e/helpers/auth.py` helper to perform a programmatic OIDC login against Keycloak (Port 49010) to obtain a verified JWT for Playwright.
- **Impact**: Enables 100% End-to-End verification of the *secured* chat flow.

#### 2. **Activate "Self-Healing" Protocols**
- **Current State**: DegradationMonitor *observes* but only *adapts* context.
- **Next Level**: Connect Governor decisions to Infrastructure scaling.
  - If `AIQ_Predicted` < 40 for 5 minutes → Trigger `Scale Up` via Temporal Workflow.
  - If `SomaBrain` latency > 2s → Circuit Break to `LocalMemory` (Redis-only).

#### 3. **Unify the Chat Stream**
- **Current State**: `ChatConsumer` streams tokens.
- **Next Level**: Enforce **Structured Thinking** in the stream.
  - Stream `<think>` blocks to the UI for "Agent Thought Bubble" visualization.
  - Stream `GovernorDecision` metadata (Latency, AIQ) to the UI "Debug Panel" (for Developers).

---

**End of Agent Knowledge Base (Extended - Audit 2025-01-02)**

---

---

## 🧠 Critical Architecture: Cognitive vs. Persistence Layers

**Definition of Roles** (Strict adherence required):

### 1. SomaBrain = The Cognitive Engine
*   **Role**: Active Thinking, Reasoning, Contextualization.
*   **Responsibility**:
    - Manages the *state* of the conversation from a cognitive perspective.
    - Decides *what* to say based on memory and context.
    - Owners of **Active Memory**.
*   **Data Flow**:
    - **Read**: `ChatService.recall_memories()` pulls context from here (via SomaFractalMemory).
    - **Write**: `ChatService.store_memory()` pushes new experiences here (via SomaFractalMemory).

### 2. PostgreSQL = The Persistence Layer
*   **Role**: Passive Storage, Verification, Failsafe.
*   **Responsibility**:
    - Manages the *record* of the conversation.
    - Ensures zero data loss (ACID compliance).
    - Owners of **The Transcript**.
*   **Data Flow**:
    - **Write**: `ChatService` writes every user/assistant message to `MessageModel` *immediately* (synchronously).
    - **Read**: `ChatService.generate_title()` reads from here for non-cognitive utility tasks.

**Why this separation?**
If SomaBrain (Cognition) crashes or hallucinates, PostgreSQL (The Persistence Layer) retains the hard truth.
**NEVER** use Postgres for cognitive context retrieval (RAG). **ALWAYS** use SomaBrain/FractalMemory.
