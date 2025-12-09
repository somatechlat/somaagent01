# Complete Architecture Analysis Report

**Generated:** December 9, 2025
**VIBE Compliance Status:** ~75% (needs work)

---

## Executive Summary

The SomaAgent01 architecture is **mostly well-designed** but has several areas needing cleanup:

1. ✅ **Conversation Flow** - Clean Architecture with Use Cases
2. ✅ **Session Persistence** - PostgresSessionStore (no file-based)
3. ✅ **Event Bus** - KafkaEventBus with DurablePublisher
4. ⚠️ **Settings** - 58 files still use `os.getenv` instead of `cfg.env()`
5. ⚠️ **File Sizes** - 12 files over 500 lines
6. ✅ **Uploads** - Real AttachmentsStore (PostgreSQL BYTEA)
7. ✅ **Scheduling** - TaskScheduler with PostgresSessionStore
8. ⚠️ **LLM Router** - Needs cleanup (imports from main.py)

---

## 1. CONVERSATION FLOW ✅

**Status:** WELL ARCHITECTED

```
Gateway (FastAPI)
    ↓ POST /v1/chat
KafkaEventBus → conversation.inbound topic
    ↓
ConversationWorker (178 lines - GOOD)
    ↓
ProcessMessageUseCase (Clean Architecture)
    ├── PolicyEnforcer (OPA)
    ├── ContextBuilder (SomaBrain)
    ├── GenerateResponseUseCase (LLM)
    └── PostgresSessionStore
    ↓
KafkaEventBus → conversation.outbound topic
    ↓
Gateway SSE → WebUI
```

**Files:**
- `services/conversation_worker/main.py` (178 lines) ✅
- `src/core/application/use_cases/conversation/process_message.py` ✅
- `src/core/application/use_cases/conversation/generate_response.py` ✅

---

## 2. UPLOADS ✅

**Status:** WELL ARCHITECTED

```
WebUI
    ↓ POST /v1/uploads
uploads_full.py
    ├── authorize_request()
    ├── AttachmentsStore.create() → PostgreSQL BYTEA
    └── DurablePublisher → Kafka
```

**Files:**
- `services/gateway/routers/uploads_full.py` (97 lines) ✅
- `services/common/attachments_store.py` ✅

**Note:** TUS protocol not yet implemented (roadmap item)

---

## 3. TASK SCHEDULING ✅

**Status:** WELL ARCHITECTED

```
TaskScheduler (singleton)
    ├── SchedulerTaskList (repository)
    ├── save_context() → PostgresSessionStore
    └── DeferredTask (async execution)
```

**Files:**
- `python/helpers/task_scheduler.py` (284 lines) ✅
- `python/helpers/scheduler_models.py` (475 lines) ⚠️ Large but acceptable
- `python/helpers/scheduler_repository.py` (154 lines) ✅
- `python/helpers/session_store_adapter.py` (150 lines) ✅

---

## 4. STREAMING / SSE ✅

**Status:** WELL ARCHITECTED

```
Gateway
    ├── /v1/sse/enabled → Check SSE status
    └── SSE Router → Real-time events
        ↓
WebUI (EventSource)
```

**Canonical Event Sequence:**
```
assistant.started → assistant.thinking.started → assistant.delta (repeated)
→ assistant.thinking.final → assistant.final (metadata.done=true)
```

---

## 5. LLM CONNECTION ⚠️

**Status:** NEEDS CLEANUP

```
services/gateway/routers/llm.py
    ↓ imports from main.py (VIOLATION)
    ├── get_llm_credentials_store()
    └── _gateway_slm_client()
```

**Issue:** LLM router imports functions from `main.py` - should use dependency injection.

**Fix Required:**
- Move `get_llm_credentials_store()` to `providers.py`
- Move `_gateway_slm_client()` to `providers.py`
- Update `llm.py` to use `Depends()`

---

## 6. SETTINGS ⚠️

**Status:** NEEDS CONSOLIDATION

### Current Systems (5 → should be 1):

| System | Location | Status |
|--------|----------|--------|
| `cfg` | `src/core/config/` | ✅ CANONICAL |
| `AgentSettingsStore` | `services/common/agent_settings_store.py` | ✅ For agent settings |
| `UiSettingsStore` | `services/common/ui_settings_store.py` | ✅ For UI preferences |
| `os.getenv()` | 58 files | ❌ VIOLATION |
| `src/context_config.py` | Legacy | ❌ VIOLATION |

### Files Using `os.getenv()` (VIOLATIONS):

1. `models.py` - Sets LITELLM_LOG
2. `python/observability/event_publisher.py` - SOMA_BASE_URL
3. `python/helpers/searxng.py` - SEARXNG_URL
4. `python/helpers/dotenv.py` - Multiple env reads
5. `python/helpers/document_query.py` - USER_AGENT
6. `observability/tracing.py` - OTLP_ENDPOINT
7. `src/context_config.py` - Multiple env reads
8. `scripts/*.py` - Various env reads

**Fix Required:**
- Replace all `os.getenv()` with `cfg.env()`
- Delete `src/context_config.py` (migrate to `cfg`)

---

## 7. WEB GUI ✅

**Status:** WELL ARCHITECTED

```
webui/config.js (centralized endpoints)
    ├── API.BASE = "/v1"
    ├── API.SETTINGS = "/settings"
    ├── API.UI_SETTINGS = "/settings/sections"
    └── API.UPLOADS = "/uploads"
```

**Endpoints Alignment:**
| UI Endpoint | Backend Router | Status |
|-------------|----------------|--------|
| `/v1/settings/sections` | `ui_settings.py` | ✅ |
| `/v1/uploads` | `uploads_full.py` | ✅ |
| `/v1/sessions` | `sessions_full.py` | ✅ |
| `/v1/test_connection` | MISSING | ❌ |

---

## 8. SESSION PERSISTENCE ✅

**Status:** WELL ARCHITECTED

```
session_store_adapter.py (bridge)
    ├── save_context() → PostgresSessionStore.append_event()
    ├── delete_context() → PostgresSessionStore.delete_session()
    ├── record_tool_result() → PostgresSessionStore.append_event()
    └── save_screenshot_attachment() → AttachmentsStore.insert()
```

**No file-based persistence** - All uses PostgreSQL.

---

## 9. EVENT BUS ✅

**Status:** WELL ARCHITECTED

```
KafkaEventBus (services/common/event_bus.py)
    ├── publish() → Kafka topic
    ├── consume() → Kafka consumer
    └── DurablePublisher (with outbox fallback)
```

**Topics:**
- `conversation.inbound` - Incoming messages
- `conversation.outbound` - Responses
- `tool.requests` - Tool execution requests
- `tool.results` - Tool execution results
- `audit.events` - Audit trail

---

## 10. CELERY TASKS ✅

**Status:** WELL ARCHITECTED

```
python/tasks/celery_app.py
    ├── beat_schedule (publish_metrics, cleanup_sessions)
    ├── task_routes (delegation, fast_a2a, heavy, default)
    └── visibility_timeout = 7200

python/tasks/core_tasks.py (215 lines)
    ├── delegate
    ├── build_context
    ├── store_interaction
    ├── feedback_loop
    ├── rebuild_index
    ├── evaluate_policy
    ├── publish_metrics
    └── cleanup_sessions
```

---

## VIOLATIONS SUMMARY

### Critical (Must Fix):

| Issue | Files | Fix |
|-------|-------|-----|
| `os.getenv()` usage | 58 files | Replace with `cfg.env()` |
| `src/context_config.py` | 1 file | Delete, migrate to `cfg` |
| LLM router imports | 1 file | Use dependency injection |
| Missing test_connection | 1 endpoint | Implement |

### Medium (Should Fix):

| Issue | Files | Fix |
|-------|-------|-----|
| Files > 500 lines | 12 files | Decompose |
| Duplicate metrics | 2 files | Consolidate |

### Low (Nice to Have):

| Issue | Files | Fix |
|-------|-------|-----|
| TUS protocol | uploads | Implement resumable uploads |
| ClamAV scanning | uploads | Add antivirus |

---

## RECOMMENDED TASK ORDER

1. **Phase 1: Config Consolidation** (HIGH PRIORITY)
   - Replace 58 `os.getenv()` calls with `cfg.env()`
   - Delete `src/context_config.py`
   - Update `python/helpers/dotenv.py`

2. **Phase 2: LLM Router Fix** (HIGH PRIORITY)
   - Move functions to `providers.py`
   - Update `llm.py` to use `Depends()`

3. **Phase 3: Missing Endpoints** (MEDIUM PRIORITY)
   - Implement `/v1/test_connection`

4. **Phase 4: File Decomposition** (MEDIUM PRIORITY)
   - `models.py` (1245 lines)
   - `soma_client.py` (908 lines)
   - `backup.py` (920 lines)

5. **Phase 5: Advanced Features** (LOW PRIORITY)
   - TUS protocol for uploads
   - ClamAV integration
   - Enhanced circuit breaker

---

## ARCHITECTURE DIAGRAM

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              WEB UI (Alpine.js)                              │
│  webui/config.js → Centralized API endpoints                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GATEWAY (FastAPI - 97 lines)                         │
│  services/gateway/main.py                                                    │
│  ├── /v1/uploads → uploads_full.py → AttachmentsStore (PostgreSQL)          │
│  ├── /v1/settings → ui_settings.py → AgentSettingsStore (PostgreSQL+Vault)  │
│  ├── /v1/sessions → sessions_full.py → PostgresSessionStore                 │
│  ├── /v1/llm → llm.py → SLM Client (LiteLLM)                               │
│  └── /v1/chat → chat_full.py → KafkaEventBus                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
┌──────────────────────┐  ┌──────────────────┐  ┌──────────────────────┐
│   KAFKA EVENT BUS    │  │     REDIS        │  │     POSTGRESQL       │
│  conversation.*      │  │  Session Cache   │  │  Sessions, Settings  │
│  tool.*              │  │  Rate Limits     │  │  Attachments, Audit  │
│  audit.*             │  │  Dedupe Keys     │  │  Tool Catalog        │
└──────────────────────┘  └──────────────────┘  └──────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CONVERSATION WORKER (178 lines)                           │
│  services/conversation_worker/main.py                                        │
│  └── ProcessMessageUseCase (Clean Architecture)                             │
│      ├── PolicyEnforcer → OPA                                               │
│      ├── ContextBuilder → SomaBrain                                         │
│      ├── GenerateResponseUseCase → LLM                                      │
│      └── PostgresSessionStore                                               │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL SERVICES                                    │
│  ├── SomaBrain (localhost:9696) - Memory, Neuromodulation, Adaptation       │
│  ├── OPA (localhost:8181) - Policy Enforcement                              │
│  ├── Vault - Secret Management                                              │
│  └── LLM Providers (OpenAI, Anthropic, etc.) via LiteLLM                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## CONCLUSION

The architecture is **fundamentally sound** with Clean Architecture patterns, proper separation of concerns, and real implementations. The main issues are:

1. **58 files using `os.getenv()`** - Easy to fix, just replace with `cfg.env()`
2. **12 large files** - Need decomposition but not blocking
3. **Missing test_connection endpoint** - Quick implementation needed

**Estimated effort to reach 100% VIBE compliance:** 2-3 days of focused work.
