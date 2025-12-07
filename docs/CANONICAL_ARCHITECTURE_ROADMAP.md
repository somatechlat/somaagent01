# SOMAAGENT01 CANONICAL ARCHITECTURE ROADMAP

**Version:** 1.0.0
**Status:** CANONICAL — Single Source of Truth
**Date:** December 1, 2025
**VIBE Compliance:** FULL

---

## 1. SCOPE

This document defines the **ONLY** approved architecture for SomaAgent01.
All code MUST conform to this specification.
Any code that violates this roadmap MUST be removed — no exceptions, no shims, no fallbacks.

---

## 2. PURPOSE

Establish a **centralized, production-grade architecture** that eliminates:

- **5+ duplicate configuration systems** → 1 canonical system
- **2 duplicate Celery applications** → 1 canonical app
- **File-based chat persistence** → VIOLATION, HARD DELETE
- **Multiple settings stores** → 1 canonical store
- **Scattered attachment handling** → 1 canonical store

**GOAL**: Zero duplication, zero file-based storage, zero shims, zero fallbacks.

---

## 3. DEFINITIONS

| Term | Definition |
|------|------------|
| **Canonical** | The ONLY approved implementation — no alternatives |
| **VIOLATION** | Code that contradicts this roadmap — MUST be removed |
| **Single Source of Truth** | One location for each concern — no duplicates |
| **Production-Grade** | Real implementation, no placeholders, no stubs |

---

## 4. DESIGN PATTERNS USED

### 4.1 Pattern Reference Table

| Pattern | Where Applied | Justification |
|---------|---------------|---------------|
| **Singleton** | Configuration (`cfg`), Stores | Single instance, consistent state |
| **Repository** | `PostgresSessionStore`, `AttachmentsStore`, `AgentSettingsStore` | Data access abstraction |
| **Facade** | `src/core/config/cfg` | Simplified interface to complex subsystem |
| **Factory** | `create_celery_app()`, Store constructors | Controlled object creation |
| **Observer** | Kafka event bus, SSE streaming | Decoupled event notification |
| **Strategy** | Secret backends (Vault/env) | Interchangeable algorithms |
| **Dependency Injection** | FastAPI `Depends()` | Testable, decoupled components |
| **Event Sourcing** | `session_events` table | Append-only event log |
| **CQRS** | Read (cache) / Write (PostgreSQL) separation | Optimized read/write paths |
| **Circuit Breaker** | `services/gateway/circuit_breakers.py` | Fault tolerance |
| **Outbox** | `MemoryWriteOutbox` | Reliable event publishing |



---

## 5. CANONICAL ARCHITECTURE DIAGRAM

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION LAYER                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        WEB UI (webui/)                               │   │
│  │  Pattern: MVC (Alpine.js)                                            │   │
│  │  - config.js (SINGLE endpoint definitions)                           │   │
│  │  - api.js (fetchApi with auth headers)                               │   │
│  │  - settings.js, messages.js, stream.js                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API GATEWAY LAYER                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  GATEWAY (FastAPI) — Pattern: Facade + Dependency Injection          │   │
│  │  Location: services/gateway/main.py                                  │   │
│  │  Entry Point: SINGLE — port 8010                                     │   │
│  │                                                                       │   │
│  │  Routers:                                                             │   │
│  │  - /v1/settings/* → ui_settings.py                                  │   │
│  │  - /v1/uploads/* → uploads_full.py                                  │   │
│  │  - /v1/attachments/* → attachments.py                               │   │
│  │  - /v1/session/* → sessions.py                                      │   │
│  │  - /v1/celery/* → celery_api.py                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
┌──────────────────────┐ ┌──────────────────────┐ ┌──────────────────────────┐
│ KAFKA (Observer)     │ │ REDIS (Cache-Aside)  │ │ CELERY (Task Queue)      │
│ - conversation.*     │ │ - Session cache      │ │ Location: python/tasks/  │
│ - tool.*             │ │ - Celery broker      │ │ SINGLE APP (Factory)     │
│ - memory.*           │ │ - Task results       │ │ Queues: default, fast_a2a│
└──────────────────────┘ └──────────────────────┘ └──────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA ACCESS LAYER                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  REPOSITORIES (Pattern: Repository)                                  │   │
│  │  Location: services/common/                                          │   │
│  │                                                                       │   │
│  │  PostgresSessionStore  → session_events, session_envelopes          │   │
│  │  AttachmentsStore      → attachments (BYTEA content)                │   │
│  │  AgentSettingsStore    → agent_settings + Vault                     │   │
│  │  UiSettingsStore       → ui_settings (JSONB)                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PERSISTENCE LAYER                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ POSTGRESQL   │  │ REDIS        │  │ KAFKA        │  │ VAULT        │   │
│  │ - sessions   │  │ - Cache ONLY │  │ - Events     │  │ - Secrets    │   │
│  │ - attachments│  │ - NO secrets │  │ - Pub/Sub    │  │ - API keys   │   │
│  │ - settings   │  │ - NO persist │  │              │  │              │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CONFIGURATION LAYER                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  src/core/config/ — Pattern: Singleton + Facade                      │   │
│  │  Entry Point: cfg (SINGLE — no alternatives)                         │   │
│  │                                                                       │   │
│  │  Precedence: SA01_* env → Raw env → YAML/JSON → Defaults            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```



---

## 6. VIOLATIONS TO REMOVE — HARD DELETE

### 6.1 FILE-BASED STORAGE — CRITICAL VIOLATION

**Rule:** NO file-based persistence. ALL data goes to PostgreSQL.

| File/Directory | Violation Type | Action |
|----------------|----------------|--------|
| `python/helpers/persist_chat.py` | File-based chat storage | **DELETE ENTIRE FILE** |
| `tmp/chats/` | Chat JSON files directory | **DELETE ENTIRE DIRECTORY** |

**Why This Is A Violation:**
- Files are not transactional
- Files don't scale horizontally
- Files can't be queried efficiently
- Files violate single source of truth
- Files are not backed up with PostgreSQL

**Replacement:** `PostgresSessionStore` in `services/common/session_repository.py`

### 6.2 DUPLICATE CELERY APPLICATIONS — CRITICAL VIOLATION

**Rule:** ONE Celery app at `python/tasks/celery_app.py`. No alternatives.

| File/Directory | Violation Type | Action |
|----------------|----------------|--------|
| `services/celery_worker/__init__.py` | Duplicate Celery app factory | **DELETE** |
| `services/celery_worker/tasks.py` | Duplicate task definitions | **DELETE** |
| `services/celery_worker/` | Entire duplicate module | **DELETE ENTIRE DIRECTORY** |

**Why This Is A Violation:**
- Two Celery apps cause task routing confusion
- Maintenance burden doubles
- Testing becomes unreliable
- Violates single source of truth

**Replacement:** Consolidate all tasks into `python/tasks/`

### 6.3 LEGACY CHAT INITIALIZATION — VIOLATION

| File | Function/Code | Action |
|------|---------------|--------|
| `initialize.py` | `initialize_chats()` function | **DELETE FUNCTION** |
| `initialize.py` | `from python.helpers import persist_chat` | **DELETE IMPORT** |
| `agent.py` | All `save_tmp_chat()` calls | **DELETE ALL CALLS** |
| `clean_agent.py` | All `save_tmp_chat()` calls | **DELETE ALL CALLS** |

---

## 7. CANONICAL SINGLE ENTRY POINTS

| Domain | Canonical Location | Pattern | Replaces |
|--------|-------------------|---------|----------|
| **Configuration** | `src/core/config/cfg` | Singleton + Facade | 5 config systems |
| **Settings Storage** | `services/common/agent_settings_store.py` | Repository | File-based settings |
| **Session Storage** | `services/common/session_repository.py` | Repository + Event Sourcing | File-based chat |
| **Attachments** | `services/common/attachments_store.py` | Repository | Local file storage |
| **Celery App** | `python/tasks/celery_app.py` | Factory | `services/celery_worker/` |
| **Secrets** | `services/common/unified_secret_manager.py` | Strategy | Redis secrets, .env |
| **API Gateway** | `services/gateway/main.py` | Facade | N/A |

---

## 8. CANONICAL DATABASE SCHEMA

### 8.1 PostgreSQL Tables (SINGLE SOURCE OF TRUTH)

```sql
-- Session Events (Pattern: Event Sourcing)
CREATE TABLE session_events (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload JSONB NOT NULL
);
CREATE INDEX idx_session_events_session ON session_events(session_id, id);

-- Session Envelopes (Pattern: Aggregate Root)
CREATE TABLE session_envelopes (
    session_id UUID PRIMARY KEY,
    persona_id TEXT,
    tenant TEXT,
    subject TEXT,
    issuer TEXT,
    scope TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    analysis JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Attachments (Pattern: Repository — NO FILE SYSTEM)
CREATE TABLE attachments (
    id UUID PRIMARY KEY,
    tenant TEXT,
    session_id TEXT,
    persona_id TEXT,
    filename TEXT NOT NULL,
    mime TEXT NOT NULL,
    size INTEGER NOT NULL,
    sha256 TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('clean','quarantined')),
    quarantine_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    content BYTEA  -- INLINE STORAGE, NO FILES
);

-- Agent Settings (Pattern: Repository)
CREATE TABLE agent_settings (
    id SERIAL PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    value JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- UI Settings (Pattern: Repository)
CREATE TABLE ui_settings (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL DEFAULT '{}'::jsonb
);
```

### 8.2 Redis Usage (CACHE ONLY — NOT PERSISTENCE)

```
ALLOWED:
- session:{session_id}:meta     → Session metadata cache (TTL: 900s)
- celery                        → Task queue broker
- celery-task-meta-*            → Task results (TTL: 3600s)

FORBIDDEN:
- NO secrets in Redis
- NO persistent data in Redis
- NO file paths in Redis
- NO chat history in Redis
```

### 8.3 Vault Usage (SECRETS ONLY)

```
ALLOWED:
- api_key_{provider}            → LLM API keys
- auth_login                    → UI login
- auth_password                 → UI password
- rfc_password                  → RFC password
- root_password                 → Container root password

FORBIDDEN:
- NO configuration in Vault
- NO non-secret data in Vault
```



---

## 9. CANONICAL CELERY CONFIGURATION

### 9.1 Single Celery App Location

**CANONICAL:** `python/tasks/celery_app.py`
**VIOLATION:** `services/celery_worker/` (DELETE)

### 9.2 Consolidated Tasks

All tasks MUST be in `python/tasks/`:

```
python/tasks/
├── __init__.py              # Exports all tasks
├── celery_app.py            # SINGLE Celery app factory
├── config.py                # Celery/Redis configuration
├── a2a_chat_task.py         # FastA2A communication
├── core_tasks.py            # Consolidated from services/celery_worker/tasks.py
│   ├── build_context()
│   ├── evaluate_policy()
│   ├── store_interaction()
│   ├── feedback_loop()
│   ├── rebuild_index()
│   └── publish_metrics()
├── orchestrator.py          # Task orchestration helpers
└── schedules.py             # Beat schedule definitions (TO CREATE)
```

### 9.3 Task Routing

```python
app.conf.task_routes = {
    "python.tasks.*.delegate*": {"queue": "delegation"},
    "python.tasks.*.browser*": {"queue": "browser"},
    "python.tasks.*.code*": {"queue": "code"},
    "python.tasks.*.heavy*": {"queue": "heavy"},
    "python.tasks.*.a2a*": {"queue": "fast_a2a"},
}
```

### 9.4 Beat Schedule (TO CREATE)

```python
# python/tasks/celery_app.py
app.conf.beat_schedule = {
    "publish-metrics-every-minute": {
        "task": "python.tasks.core_tasks.publish_metrics",
        "schedule": 60.0,
    },
    "cleanup-expired-sessions-hourly": {
        "task": "python.tasks.core_tasks.cleanup_sessions",
        "schedule": 3600.0,
    },
}
```

---

## 10. IMPLEMENTATION PHASES

### Phase 1: HARD DELETE Violations (DESTRUCTIVE)

**Priority:** P0 — IMMEDIATE
**Risk:** HIGH — Breaking changes
**Rollback:** Git revert

| Step | Action | Target |
|------|--------|--------|
| 1.1 | Delete file-based chat | `python/helpers/persist_chat.py` |
| 1.2 | Delete chat directory | `tmp/chats/` |
| 1.3 | Delete duplicate Celery | `services/celery_worker/` (entire directory) |
| 1.4 | Remove persist_chat imports | `agent.py`, `clean_agent.py`, `initialize.py` |
| 1.5 | Remove initialize_chats() | `initialize.py` |

### Phase 2: Celery Consolidation

**Priority:** P0 — IMMEDIATE
**Risk:** MEDIUM — Task routing changes

| Step | Action | Target |
|------|--------|--------|
| 2.1 | Create core_tasks.py | `python/tasks/core_tasks.py` |
| 2.2 | Migrate tasks from deleted module | Copy task logic |
| 2.3 | Add beat_schedule | `python/tasks/celery_app.py` |
| 2.4 | Update gateway imports | `services/gateway/routers/celery_api.py` |

### Phase 3: Configuration Consolidation

**Priority:** P1 — HIGH
**Risk:** LOW — Import changes only

| Step | Action | Target |
|------|--------|--------|
| 3.1 | Ensure all code uses `cfg` | All config imports |
| 3.2 | Refactor admin_settings | Use `cfg` directly |
| 3.3 | Deprecate settings_sa01 | Mark for removal |

### Phase 4: Validation

**Priority:** P1 — HIGH
**Risk:** LOW — Non-destructive

| Step | Action | Verification |
|------|--------|--------------|
| 4.1 | Run all tests | `pytest tests/` |
| 4.2 | Verify UI settings | Manual test |
| 4.3 | Verify chat flow | Manual test |
| 4.4 | Verify attachments | Manual test |
| 4.5 | Verify Celery tasks | Manual test |

---

## 11. FILES TO DELETE (COMPLETE LIST)

```
# FILE-BASED STORAGE VIOLATIONS
python/helpers/persist_chat.py          # DELETE
tmp/chats/                              # DELETE DIRECTORY

# DUPLICATE CELERY VIOLATIONS
services/celery_worker/__init__.py      # DELETE
services/celery_worker/tasks.py         # DELETE
services/celery_worker/__pycache__/     # DELETE
services/celery_worker/                 # DELETE DIRECTORY
```

---

## 12. FILES TO MODIFY (COMPLETE LIST)

```
# REMOVE PERSIST_CHAT IMPORTS AND CALLS
initialize.py                           # Remove initialize_chats(), persist_chat import
agent.py                                # Remove save_tmp_chat() calls
clean_agent.py                          # Remove save_tmp_chat() calls

# UPDATE CELERY IMPORTS
services/gateway/routers/celery_api.py  # Import from python.tasks.celery_app

# CONSOLIDATE CONFIGURATION
services/common/admin_settings.py       # Use cfg directly
```

---

## 13. FILES TO CREATE (COMPLETE LIST)

```
# CONSOLIDATED CELERY TASKS
python/tasks/core_tasks.py              # Tasks from services/celery_worker/tasks.py

# BEAT SCHEDULE (add to existing file)
python/tasks/celery_app.py              # Add beat_schedule configuration
```

---

## 14. SECURITY CONSIDERATIONS

| Concern | Mitigation | Location |
|---------|------------|----------|
| SQL Injection | Parameterized queries (asyncpg) | All `*_store.py` |
| XSS | Content-Type headers | Gateway routers |
| CSRF | Same-origin credentials | `webui/js/api.js` |
| Secret Exposure | Vault storage only | `unified_secret_manager.py` |
| IDOR | authorize_request() | All endpoints |
| Token Handling | httpOnly cookies | `auth.py` |

---

## 15. PERFORMANCE CONSIDERATIONS

| Concern | Mitigation | Location |
|---------|------------|----------|
| N+1 Queries | Connection pooling | asyncpg pools |
| Memory | Streaming responses | SSE, uploads |
| Concurrency | Celery worker pool | Celery config |
| Caching | Redis session cache | `RedisSessionCache` |

---

## 16. VALIDATION CHECKLIST

### Pre-Implementation
- [x] All violations identified
- [x] PostgreSQL schemas verified
- [x] Redis usage verified (cache only)
- [ ] Vault secrets verified

### Post-Implementation
- [x] `python/helpers/persist_chat.py` removed
- [x] `services/celery_worker/` directory removed
- [ ] All persist_chat imports removed (8 files remaining)
- [x] Single Celery app at `python/tasks/`
- [ ] `core_tasks.py` created
- [ ] Beat schedule configured
- [ ] All imports updated
- [ ] All tests pass
- [ ] UI settings flow works
- [ ] Chat flow works (PostgreSQL only)
- [ ] Attachment flow works
- [ ] Celery tasks execute correctly

---

## 17. CURRENT ARCHITECTURE STATUS (December 1, 2025)

### ✅ COMPLETED ITEMS

| Component | Status | Location |
|-----------|--------|----------|
| Canonical Celery App | ✅ DONE | `python/tasks/celery_app.py` |
| Celery Config | ✅ DONE | `python/tasks/config.py` |
| A2A Chat Task | ✅ DONE | `python/tasks/a2a_chat_task.py` |
| Task Orchestrator | ✅ DONE | `python/tasks/orchestrator.py` |
| Gateway Celery Router | ✅ DONE | `services/gateway/routers/celery_api.py` |
| PostgresSessionStore | ✅ DONE | `services/common/session_repository.py` |
| Docker Compose Config | ✅ DONE | Uses `python.tasks.celery_app` |
| Helm Deployment | ✅ DONE | Uses `python.tasks.celery_app` |
| Delete persist_chat.py | ✅ DONE | File removed |
| Delete services/celery_worker/ | ✅ DONE | Directory removed |

### ❌ REMAINING VIOLATIONS

#### persist_chat Import Violations (8 files)

| File | Violation | Required Action |
|------|-----------|-----------------|
| `python/helpers/task_scheduler.py` | `from python.helpers.persist_chat import save_tmp_chat` | Migrate to PostgresSessionStore |
| `python/extensions/monologue_start/_60_rename_chat.py` | `from python.helpers import persist_chat` | Migrate to PostgresSessionStore |
| `python/extensions/message_loop_end/_90_save_chat.py` | `from python.helpers import persist_chat` | Migrate to PostgresSessionStore |
| `python/helpers/mcp_server.py` | `from python.helpers.persist_chat import remove_chat` | Migrate to PostgresSessionStore |
| `python/helpers/fasta2a_server.py` | `from python.helpers.persist_chat import remove_chat` | Migrate to PostgresSessionStore |
| `python/tools/scheduler.py` | `from python.helpers import persist_chat` | Migrate to PostgresSessionStore |
| `python/tools/browser_agent.py` | `from python.helpers import persist_chat` | Migrate to attachments store |
| `python/extensions/hist_add_tool_result/_90_save_tool_call_file.py` | `from python.helpers import persist_chat` | Migrate to session events |

#### Missing Celery Components

| Component | Status | Required Action |
|-----------|--------|-----------------|
| `python/tasks/core_tasks.py` | ❌ MISSING | Create with: build_context, evaluate_policy, store_interaction, feedback_loop, rebuild_index, publish_metrics, cleanup_sessions |
| Beat Schedule | ❌ MISSING | Add to `celery_app.py`: publish-metrics-every-minute, cleanup-expired-sessions-hourly |
| Task Exports | ⚠️ PARTIAL | Update `__init__.py` to export core_tasks |

### 📊 COMPLIANCE SCORE

| Area | Score |
|------|-------|
| Celery App Location | 100% |
| Gateway Integration | 100% |
| Docker/Helm Config | 100% |
| persist_chat Cleanup | 0% (8 files) |
| core_tasks.py | 0% |
| Beat Schedule | 0% |
| Settings Consolidation | 30% (5 systems → 1) |
| **Overall** | **~45%** |

---

## 17.1 SETTINGS SYSTEMS ANALYSIS

### CANONICAL SETTINGS (KEEP)

| System | Location | Purpose | Status |
|--------|----------|---------|--------|
| **cfg** | `src/core/config/` | Centralized config facade | ✅ CANONICAL |
| **AgentSettingsStore** | `services/common/agent_settings_store.py` | PostgreSQL + Vault | ✅ CANONICAL |
| **UiSettingsStore** | `services/common/ui_settings_store.py` | PostgreSQL UI settings | ✅ CANONICAL |

### SETTINGS VIOLATIONS (TO CONSOLIDATE)

| System | Location | Violation | Action |
|--------|----------|-----------|--------|
| `settings_sa01.py` | `services/common/` | Duplicates cfg functionality | Migrate to cfg |
| `settings_base.py` | (removed) | Base class duplicated cfg | ✅ Removed – use cfg |
| `admin_settings.py` | `services/common/` | Wraps SA01Settings | Refactor to use cfg |
| `settings.py` | `python/helpers/` | 1789-line monolith | Split: UI conversion + cfg |

### SETTINGS PRECEDENCE (CANONICAL)

```
SA01_* env → Raw env → YAML/JSON → Defaults
```

### TARGET ARCHITECTURE

```
ALL CODE ──────► src/core/config/cfg (Singleton Facade)
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
   SA01_* env      Raw env        YAML/JSON
        │               │               │
        └───────────────┴───────────────┘
                        │
                        ▼
                   Defaults

Agent Settings ──► AgentSettingsStore (PostgreSQL + Vault)
UI Settings ─────► UiSettingsStore (PostgreSQL)
```

---

## 17.2 UPLOAD, CHAT, STREAMING, SOMABRAIN ANALYSIS

### CANONICAL IMPLEMENTATIONS (WORKING ✅)

| Component | Location | Pattern | Status |
|-----------|----------|---------|--------|
| **Uploads** | `services/gateway/routers/uploads_full.py` | Repository | ✅ CANONICAL |
| **Attachments** | `services/common/attachments_store.py` | PostgreSQL BYTEA | ✅ CANONICAL |
| **Sessions** | `services/gateway/routers/sessions.py` | Repository + SSE | ✅ CANONICAL |
| **Session Store** | `services/common/session_repository.py` | Event Sourcing | ✅ CANONICAL |
| **SomaBrain** | `python/integrations/somabrain_client.py` | HTTP Client | ✅ CANONICAL |
| **Chat** | `services/gateway/routers/chat_full.py` | PostgresSessionStore | ✅ CANONICAL |
| **WebSocket** | `services/gateway/routers/websocket.py` | Streaming | ✅ CANONICAL |
| **SSE** | `services/gateway/routers/sse.py` | Server-Sent Events | ✅ CANONICAL |

### UPLOAD FLOW (CANONICAL)

```
Client ──► /v1/uploads ──► AttachmentsStore.create() ──► PostgreSQL (BYTEA)
```

### CHAT/SESSION FLOW (CANONICAL)

```
Client ──► /v1/session/{id}/events
                │
                ├──► SSE Stream ──► PostgresSessionStore.list_events_after()
                │
                └──► JSON ──► PostgresSessionStore.list_events()
```

### SOMABRAIN INTEGRATION (CANONICAL)

```
Services ──► SomaBrainClient ──► cfg.get_somabrain_url() ──► HTTP to SomaBrain
```

### VIOLATIONS IN UPLOAD/CHAT/STREAMING

| File | Violation | Action |
|------|-----------|--------|
| `python/helpers/backup.py` | References `tmp/chats/**` | Update backup patterns |
| `prompts/agent.system.main.communication_additions.md` | References `tmp/chats/guid/messages/` | Update prompt template |
| `services/gateway/routers/uploads.py` | Skeleton alongside uploads_full.py | Remove or consolidate |
| `services/gateway/routers/chat.py` | Skeleton alongside chat_full.py | Remove or consolidate |
| `services/gateway/routers/memory.py` | Skeleton (ping only) | Implement or remove |

---

## 17.3 WEB UI SETTINGS ARCHITECTURE VIOLATIONS

### CRITICAL: UI-Backend Endpoint Mismatch

| UI Endpoint (webui/config.js) | Backend Endpoint | Status |
|-------------------------------|------------------|--------|
| `POST /v1/settings_save` | **DOES NOT EXIST** | ✅ Removed – use `/v1/settings/sections` |
| `POST /v1/test_connection` | **DOES NOT EXIST** | ❌ VIOLATION |
| `GET /v1/settings/sections` | `GET /v1/settings/sections` | ✅ OK |

### VIBE Rules Violated

- **NO BULLSHIT**: UI calls non-existent endpoints
- **REAL IMPLEMENTATIONS ONLY**: `/v1/test_connection` not implemented
- **CHECK FIRST, CODE SECOND**: UI uses POST, backend expects PUT

### Required Fixes

| File | Current | Required |
|------|---------|----------|
| `webui/config.js` | `SAVE_SETTINGS: "/settings_save"` | `SAVE_SETTINGS` removed; UI uses `/settings/sections` |
| `webui/js/settings.js` | `method: 'POST'` | `method: 'PUT'` |
| `services/gateway/routers/ui_settings.py` | Missing test endpoint | Add `POST /v1/settings/test` |

### Canonical Settings Flow

```
UI (settings.js)
    │
    ├──► GET /v1/settings/sections ──► ui_settings.py ──► AgentSettingsStore ✅
    │
    ├──► PUT /v1/settings/sections ──► ui_settings.py ──► AgentSettingsStore (FIX NEEDED)
    │
    └──► POST /v1/settings/test ──► ui_settings.py ──► LLM Test (TO CREATE)
```

---

## 17.4 MEMORY, SOMABRAIN, CONSTITUTION ANALYSIS

### CANONICAL IMPLEMENTATIONS (VIBE COMPLIANT ✅)

| Component | Location | Status |
|-----------|----------|--------|
| Memory Sync Worker | `services/memory_sync/main.py` | ✅ COMPLIANT |
| SomaClient | `python/integrations/soma_client.py` | ✅ COMPLIANT |
| SomaBrainClient | `python/integrations/somabrain_client.py` | ✅ COMPLIANT |
| Constitution Router | `services/gateway/routers/constitution.py` | ✅ COMPLIANT |
| Memory Mutations | `services/gateway/routers/memory_mutations.py` | ✅ COMPLIANT |
| Messages.js | `webui/js/messages.js` | ✅ COMPLIANT |

### VIOLATIONS FOUND

| File | Violation | VIBE Rule |
|------|-----------|-----------|
| `memory_exports.py` | Uses `Path(job.result_path).read_bytes()` | NO file-based storage |
| `memory_exports.py` | Missing `from pathlib import Path` | REAL IMPLEMENTATIONS ONLY |
| `soma_client.py` | Silent port 9595→9696 rewrite | NO BULLSHIT |

### Memory Sync Flow (CANONICAL)

```
MemorySyncWorker
    │
    ├──► MemoryWriteOutbox.claim_batch() ──► PostgreSQL
    │
    ├──► SomaClient.remember() ──► SomaBrain HTTP
    │
    └──► DurablePublisher.publish() ──► Kafka (memory.wal)
```

### Constitution Flow (CANONICAL)

```
Gateway /constitution/*
    │
    ├──► authorize_request() ──► OPA Policy Check
    │
    └──► SomaBrainClient ──► SomaBrain HTTP
```

---

## 17.5 FILE UPLOAD/DOWNLOAD ARCHITECTURE (TO IMPLEMENT)

### Current State

| Component | Status | Notes |
|-----------|--------|-------|
| `webui/js/uploadsChunked.js` | ✅ EXISTS | Resumable chunked upload client |
| `services/gateway/routers/uploads_full.py` | ⚠️ PARTIAL | Basic upload, no chunking backend |
| `services/common/attachments_store.py` | ✅ EXISTS | PostgreSQL BYTEA storage |
| `services/gateway/routers/av.py` | ❌ SKELETON | Only returns `{"status": "ok"}` |

### Target Architecture (TUS Protocol + ClamAV)

```
Client (uploadsChunked.js)
    │
    ├──► POST /v1/uploads/init ──► Create upload session
    │
    ├──► POST /v1/uploads/{id}/chunk ──► Upload chunk (resumable)
    │         │
    │         └──► SHA-256 incremental hash
    │
    ├──► POST /v1/uploads/{id}/finalize
    │         │
    │         ├──► ClamAV scan (pyclamd)
    │         │         │
    │         │         ├──► Clean ──► AttachmentsStore (PostgreSQL)
    │         │         │
    │         │         └──► Infected ──► Quarantine + reject
    │         │
    │         └──► Link to session_id
    │
    └──► GET /v1/attachments/{id} ──► Stream from PostgreSQL (Range support)
```

### Libraries to Use

| Purpose | Library | Notes |
|---------|---------|-------|
| TUS Protocol | `aiohttp-tus` or custom | Resumable uploads |
| Antivirus | `pyclamd` | ClamAV socket connection |
| Hashing | `hashlib` | SHA-256 streaming |
| Chunked Upload | Existing `uploadsChunked.js` | Frontend already implemented |

### ClamAV Integration

```
Docker Compose:
  clamav:
    image: clamav/clamav:latest
    volumes:
      - clamav-data:/var/lib/clamav
    ports:
      - "3310:3310"  # clamd socket

Python (pyclamd):
  import pyclamd
  cd = pyclamd.ClamdNetworkSocket(host='clamav', port=3310)
  result = cd.scan_stream(file_bytes)
  # result: None (clean) or {'stream': ('FOUND', 'Virus.Name')}
```

---

## 18. DOCUMENT AUTHORITY

```
===============================================================
DOCUMENT STATUS: CANONICAL
AUTHORITY: This document is the SINGLE SOURCE OF TRUTH
VIOLATIONS: Any code not aligned MUST be removed
NO EXCEPTIONS: No shims, no fallbacks, no workarounds
===============================================================
```

**END OF CANONICAL ARCHITECTURE ROADMAP**
