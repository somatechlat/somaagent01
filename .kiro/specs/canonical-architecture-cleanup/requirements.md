# Requirements Document

## Introduction

This specification defines the requirements for completing the canonical architecture cleanup and full **Celery-Only Architecture** integration for SomaAgent01. This document merges the existing cleanup requirements with the Celery-Only Architecture & Implementation Guide (v1.0, 2025-11-09).

### Goals

1. Eliminate all violations of the canonical architecture roadmap
2. Remove file-based chat persistence references from 8 files still importing the deleted `persist_chat` module
3. Consolidate Celery tasks into the canonical location with Canvas patterns
4. Configure Celery Beat for periodic task execution (replacing APScheduler)
5. Implement OPA policy integration for task authorization
6. Add Prometheus metrics to all Celery tasks
7. Ensure all code conforms to the single source of truth principle
8. Achieve 100% VIBE Coding Rules compliance

### Current Architecture Status

**Working Correctly (VIBE Compliant ✅):**
- Canonical Celery app at `python/tasks/celery_app.py`
- Gateway integration via `services/gateway/routers/celery_api.py`
- Docker/Helm configurations using correct paths (`python.tasks.celery_app`)
- `services/celery_worker/` directory already deleted
- `python/helpers/persist_chat.py` already deleted
- PostgresSessionStore for session persistence
- AttachmentsStore for file storage (PostgreSQL BYTEA)
- OPA policy client at `services/common/policy_client.py`
- SomaBrain integration via canonical clients

**Violations Remaining (VIBE Non-Compliant ❌):**
- 8 files still import the deleted `persist_chat` module
- `core_tasks.py` not created (missing: build_context, evaluate_policy, store_interaction, feedback_loop, rebuild_index, publish_metrics, cleanup_sessions)
- Beat schedule not configured
- No Canvas patterns (chain/group/chord) for DAG-like flows
- No task_routes for queue routing
- No visibility_timeout configuration
- No OPA integration in Celery tasks
- No Prometheus metrics in Celery tasks (except a2a_chat_task)
- No dedupe pattern in Celery tasks
- UI-Backend endpoint mismatch (settings save broken)
- 5 settings systems instead of 1 canonical cfg

### VIBE Compliance Score

| Area | Current | Target | Gap |
|------|---------|--------|-----|
| Celery App Location | 100% | 100% | ✅ |
| Gateway Integration | 100% | 100% | ✅ |
| Docker/Helm Config | 100% | 100% | ✅ |
| persist_chat Cleanup | 0% | 100% | 8 files |
| core_tasks.py | 0% | 100% | Missing |
| Beat Schedule | 0% | 100% | Missing |
| Canvas Patterns | 0% | 100% | Missing |
| Task Routes | 0% | 100% | Missing |
| OPA in Tasks | 0% | 100% | Missing |
| Prometheus in Tasks | 20% | 100% | Partial |
| Dedupe Pattern | 0% | 100% | Missing |
| Settings Consolidation | 30% | 100% | 5→1 |
| UI-Backend Alignment | 50% | 100% | Endpoints |
| **Overall** | **~45%** | **100%** | **55%** |

## Glossary

- **Canonical**: The ONLY approved implementation — no alternatives permitted
- **VIBE**: Verification, Implementation, Behavior, Execution coding rules
- **PostgresSessionStore**: The repository pattern implementation for session persistence in PostgreSQL
- **persist_chat**: DELETED legacy module that provided file-based chat storage (VIOLATION)
- **save_tmp_chat**: DELETED function from persist_chat module that saved chat to JSON files
- **remove_chat**: DELETED function from persist_chat module that removed chat files
- **get_chat_folder_path**: DELETED function from persist_chat module that returned chat folder path
- **get_chat_msg_files_folder**: DELETED function from persist_chat module that returned message files folder
- **core_tasks**: Consolidated Celery task module to be created at `python/tasks/core_tasks.py`
- **beat_schedule**: Celery Beat configuration for periodic task execution
- **cfg**: Singleton configuration facade at `src/core/config/cfg`
- **SessionEnvelope**: PostgreSQL-backed session metadata container
- **Canvas**: Celery workflow patterns (chain, group, chord) for DAG-like task flows
- **OPA**: Open Policy Agent for authorization decisions
- **dedupe**: Deduplication pattern using Redis SET NX for idempotent task execution
- **visibility_timeout**: Celery broker setting for task redelivery on worker failure

## Requirements

### Requirement 1: persist_chat Import Removal

**User Story:** As a system maintainer, I want all references to the deleted `persist_chat` module removed, so that the codebase compiles without import errors and follows the canonical architecture.

#### Acceptance Criteria

1. WHEN the system imports modules in `python/helpers/task_scheduler.py` THEN the System SHALL NOT reference `persist_chat` or `save_tmp_chat`
2. WHEN the system imports modules in `python/extensions/monologue_start/_60_rename_chat.py` THEN the System SHALL NOT reference `persist_chat`
3. WHEN the system imports modules in `python/extensions/message_loop_end/_90_save_chat.py` THEN the System SHALL NOT reference `persist_chat`
4. WHEN the system imports modules in `python/helpers/mcp_server.py` THEN the System SHALL NOT reference `persist_chat` or `remove_chat`
5. WHEN the system imports modules in `python/helpers/fasta2a_server.py` THEN the System SHALL NOT reference `persist_chat` or `remove_chat`
6. WHEN the system imports modules in `python/tools/scheduler.py` THEN the System SHALL NOT reference `persist_chat` or `remove_chat`
7. WHEN the system imports modules in `python/tools/browser_agent.py` THEN the System SHALL NOT reference `persist_chat` or `get_chat_folder_path`
8. WHEN the system imports modules in `python/extensions/hist_add_tool_result/_90_save_tool_call_file.py` THEN the System SHALL NOT reference `persist_chat` or `get_chat_msg_files_folder`

### Requirement 2: PostgresSessionStore Migration

**User Story:** As a system maintainer, I want session persistence to use PostgresSessionStore exclusively, so that all chat data is stored in PostgreSQL following the canonical architecture.

#### Acceptance Criteria

1. WHEN a chat context is saved THEN the System SHALL use `PostgresSessionStore.append_event()` to persist the session data
2. WHEN a chat context is renamed THEN the System SHALL update the session envelope metadata via `PostgresSessionStore`
3. WHEN a chat is removed THEN the System SHALL use `PostgresSessionStore.delete_session()` to remove the session data
4. WHEN tool call results are saved THEN the System SHALL store them as session events in PostgreSQL
5. WHEN browser screenshots are saved THEN the System SHALL store them via the attachments store or session events

### Requirement 3: Consolidated Celery Tasks (core_tasks.py)

**User Story:** As a system maintainer, I want consolidated Celery tasks in `python/tasks/core_tasks.py`, so that all background tasks are in a single canonical location following the Celery-Only Architecture Guide.

#### Acceptance Criteria

1. WHEN the system requires background task execution THEN the System SHALL import tasks from `python/tasks/` module
2. WHEN `core_tasks.py` is created THEN the System SHALL include `build_context` task for context building operations
3. WHEN `core_tasks.py` is created THEN the System SHALL include `evaluate_policy` task for OPA policy evaluation
4. WHEN `core_tasks.py` is created THEN the System SHALL include `store_interaction` task for interaction storage
5. WHEN `core_tasks.py` is created THEN the System SHALL include `feedback_loop` task for feedback processing
6. WHEN `core_tasks.py` is created THEN the System SHALL include `rebuild_index` task for index rebuilding
7. WHEN `core_tasks.py` is created THEN the System SHALL include `publish_metrics` task for Prometheus metrics publishing
8. WHEN `core_tasks.py` is created THEN the System SHALL include `cleanup_sessions` task for expired session cleanup
9. WHEN tasks are registered THEN the System SHALL use the `@shared_task` decorator with proper configuration (bind=True, max_retries, autoretry_for, retry_backoff, soft_time_limit, time_limit, rate_limit)

### Requirement 4: Celery Beat Schedule Configuration

**User Story:** As a system maintainer, I want Celery Beat schedule configured, so that periodic tasks execute automatically (replacing APScheduler).

#### Acceptance Criteria

1. WHEN the Celery app is configured THEN the System SHALL include a `beat_schedule` configuration in `celery_app.py`
2. WHEN the beat schedule is defined THEN the System SHALL include `publish-metrics-every-minute` task scheduled at 60-second intervals
3. WHEN the beat schedule is defined THEN the System SHALL include `cleanup-expired-sessions-hourly` task scheduled at 3600-second intervals
4. WHEN the beat schedule references tasks THEN the System SHALL use fully qualified task names from `python.tasks.core_tasks`
5. WHEN Celery Beat runs THEN the System SHALL use the DatabaseScheduler for persistence

### Requirement 5: Task Exports and Module Structure

**User Story:** As a system maintainer, I want the `python/tasks/__init__.py` to export all canonical tasks, so that consumers have a single import point.

#### Acceptance Criteria

1. WHEN `python/tasks/__init__.py` is updated THEN the System SHALL export `a2a_chat_task` from `a2a_chat_task.py`
2. WHEN `python/tasks/__init__.py` is updated THEN the System SHALL export all tasks from `core_tasks.py`
3. WHEN the `__all__` list is defined THEN the System SHALL include all exported task names

### Requirement 6: Import Validation

**User Story:** As a developer, I want the codebase to pass all import checks, so that the application starts without module errors.

#### Acceptance Criteria

1. WHEN Python imports are resolved THEN the System SHALL NOT raise `ModuleNotFoundError` for `persist_chat`
2. WHEN Python imports are resolved THEN the System SHALL NOT raise `ImportError` for `save_tmp_chat`, `remove_chat`, `get_chat_folder_path`, or `get_chat_msg_files_folder`
3. WHEN the application starts THEN the System SHALL successfully initialize all modules without import failures
4. WHEN Celery worker starts THEN the System SHALL discover and register all tasks from `python.tasks`

### Requirement 7: Session Persistence Adapter

**User Story:** As a system maintainer, I want a session persistence adapter that bridges AgentContext to PostgresSessionStore, so that existing code can migrate incrementally.

#### Acceptance Criteria

1. WHEN a session adapter is created THEN the System SHALL provide `save_context(context)` method that persists to PostgreSQL
2. WHEN a session adapter is created THEN the System SHALL provide `delete_context(context_id)` method that removes from PostgreSQL
3. WHEN a session adapter is created THEN the System SHALL provide `get_context_folder(context_id)` method that returns a temporary directory path for file operations
4. WHEN the adapter saves a context THEN the System SHALL serialize the context state as a session event

### Requirement 8: Canonical Configuration (cfg Facade) - COMPLETE CONSOLIDATION

**User Story:** As a system maintainer, I want all 5+ configuration systems consolidated into the canonical `cfg` facade, so that there is a single source of truth for runtime configuration.

#### Acceptance Criteria

1. WHEN code requires configuration values THEN the System SHALL import from `src.core.config` and use `cfg.env()`
2. WHEN `services/common/admin_settings.py` accesses configuration THEN the System SHALL delegate to `cfg` instead of `SA01Settings`
3. WHEN `services/common/settings_sa01.py` is used THEN the System SHALL be marked as deprecated with migration path to `cfg`
4. WHEN `services/common/settings_base.py` is used THEN the System SHALL be marked as deprecated with migration path to `cfg`
5. WHEN `services/common/env.py` is used THEN the System SHALL be replaced with `cfg.env()`
6. WHEN `services/common/registry.py` ServiceRegistry is used THEN the System SHALL be replaced with `cfg` ConfigRegistry
7. WHEN `conf/model_profiles.yaml` is loaded THEN the System SHALL migrate to PostgreSQL-backed configuration

#### 5 Settings Systems to Consolidate

| Current System | Location | Action |
|----------------|----------|--------|
| `cfg` | `src/core/config/` | ✅ KEEP - Canonical |
| `SA01Settings` | `services/common/settings_sa01.py` | ❌ DEPRECATE → cfg |
| `BaseServiceSettings` | `services/common/settings_base.py` | ❌ DEPRECATE → cfg |
| `ADMIN_SETTINGS` | `services/common/admin_settings.py` | ❌ REFACTOR → cfg |
| `python/helpers/settings.py` | `python/helpers/settings.py` | ⚠️ SPLIT: UI conversion stays, config access → cfg |
| `env.py` | `services/common/env.py` | ❌ DEPRECATE → cfg.env() |
| `ServiceRegistry` | `services/common/registry.py` | ❌ DEPRECATE → cfg ConfigRegistry |

### Requirement 9: Settings Separation of Concerns

**User Story:** As a system maintainer, I want `python/helpers/settings.py` refactored to separate concerns, so that UI conversion is distinct from settings access.

#### Acceptance Criteria

1. WHEN UI settings are converted for display THEN the System SHALL use conversion functions in `python/helpers/settings.py`
2. WHEN settings values are accessed THEN the System SHALL use `AgentSettingsStore` for agent settings
3. WHEN settings values are accessed THEN the System SHALL use `cfg` for infrastructure configuration
4. WHEN API keys are accessed THEN the System SHALL use `UnifiedSecretManager` via Vault

### Requirement 10: Settings Architecture Documentation

**User Story:** As a developer, I want clear documentation of the canonical settings architecture, so that new code follows the correct patterns.

#### Acceptance Criteria

1. WHEN the roadmap is updated THEN the System SHALL document the three canonical settings systems (cfg, AgentSettingsStore, UiSettingsStore)
2. WHEN the roadmap is updated THEN the System SHALL document the settings precedence order (SA01_* env → Raw env → YAML/JSON → Defaults)
3. WHEN the roadmap is updated THEN the System SHALL list all settings violations and their migration paths

### Requirement 11: Backup Pattern Updates

**User Story:** As a system maintainer, I want file-based backup references updated, so that backups don't reference deleted directories.

#### Acceptance Criteria

1. WHEN `python/helpers/backup.py` is updated THEN the System SHALL NOT reference `tmp/chats/**`
2. WHEN backup patterns are defined THEN the System SHALL reference PostgreSQL-backed session data instead of file paths
3. WHEN prompt templates reference file paths THEN the System SHALL use session event references instead

### Requirement 12: Router Consolidation

**User Story:** As a system maintainer, I want skeleton routers consolidated or removed, so that there is no confusion about canonical implementations.

#### Acceptance Criteria

1. WHEN `services/gateway/routers/uploads.py` exists alongside `uploads_full.py` THEN the System SHALL consolidate into a single canonical router
2. WHEN `services/gateway/routers/chat.py` exists alongside `chat_full.py` THEN the System SHALL consolidate into a single canonical router
3. WHEN `services/gateway/routers/memory.py` contains only skeleton code THEN the System SHALL implement full functionality or remove the router

### Requirement 13: Web UI Settings Endpoint Alignment

**User Story:** As a system maintainer, I want the Web UI settings endpoints aligned with the backend, so that settings can be saved correctly.

#### Acceptance Criteria

1. WHEN `webui/config.js` defines `SAVE_SETTINGS` THEN the System SHALL use `/settings/sections` instead of `/settings_save`
2. WHEN `webui/js/settings.js` saves settings THEN the System SHALL use HTTP PUT method instead of POST
3. WHEN the UI calls save settings THEN the System SHALL successfully persist to PostgreSQL via AgentSettingsStore
4. WHEN the UI fetches settings THEN the System SHALL receive valid sections from `/v1/settings/sections`

### Requirement 14: Test Connection Endpoint

**User Story:** As a system maintainer, I want a test connection endpoint implemented, so that users can verify LLM API credentials.

#### Acceptance Criteria

1. WHEN `webui/config.js` defines `TEST_CONNECTION` THEN the System SHALL have a corresponding backend endpoint
2. WHEN the test connection endpoint is called THEN the System SHALL validate the provided API key against the LLM provider
3. WHEN the test succeeds THEN the System SHALL return `{"success": true}`
4. WHEN the test fails THEN the System SHALL return `{"success": false, "error": "<reason>"}`

### Requirement 15: Memory Exports PostgreSQL Migration

**User Story:** As a system maintainer, I want memory exports to use PostgreSQL storage instead of file paths, so that the architecture follows the canonical pattern.

#### Acceptance Criteria

1. WHEN export job results are stored THEN the System SHALL use PostgreSQL BYTEA or JSONB instead of file paths
2. WHEN export job results are downloaded THEN the System SHALL retrieve from PostgreSQL instead of filesystem
3. WHEN `services/gateway/routers/memory_exports.py` is updated THEN the System SHALL NOT use `Path` for file operations
4. WHEN the export job store is updated THEN the System SHALL store result data inline instead of `result_path`

### Requirement 16: SomaClient Logging Enhancement

**User Story:** As a system maintainer, I want SomaClient to log warnings for legacy port detection instead of silently rewriting, so that configuration issues are visible.

#### Acceptance Criteria

1. WHEN SomaClient detects legacy port 9595 THEN the System SHALL log a WARNING with the original and rewritten URL
2. WHEN SomaClient rewrites a port THEN the System SHALL include the rewrite in metrics/telemetry
3. WHEN SOMA_BASE_URL is not set THEN the System SHALL raise a clear error instead of using a default

### Requirement 17: TUS Protocol File Upload

**User Story:** As a system maintainer, I want a state-of-the-art file upload/download system with resumable uploads, streaming, and antivirus scanning, so that file handling is robust and secure.

#### Acceptance Criteria

1. WHEN a file upload is initiated THEN the System SHALL use the TUS protocol (tus.io) for resumable uploads
2. WHEN a file upload is interrupted THEN the System SHALL allow resumption from the last successful chunk
3. WHEN a file is uploaded THEN the System SHALL compute SHA-256 hash for integrity verification
4. WHEN a file is uploaded THEN the System SHALL scan it using ClamAV via clamd socket connection
5. WHEN a file fails antivirus scan THEN the System SHALL quarantine the file and return status "quarantined"
6. WHEN a file passes antivirus scan THEN the System SHALL store it in PostgreSQL with status "clean"
7. WHEN a file is downloaded THEN the System SHALL support HTTP Range requests for partial downloads
8. WHEN a file is downloaded THEN the System SHALL stream content directly from PostgreSQL BYTEA

### Requirement 18: Attachment-Session Linking

**User Story:** As a system maintainer, I want file attachments linked to chat messages, so that files are associated with their conversation context.

#### Acceptance Criteria

1. WHEN a file is uploaded with a session_id THEN the System SHALL create an attachment record linked to that session
2. WHEN a message references an attachment THEN the System SHALL store the attachment_id in the message event
3. WHEN a session is deleted THEN the System SHALL cascade delete associated attachments
4. WHEN attachments are listed THEN the System SHALL filter by session_id and return metadata

### Requirement 19: Battle-Tested Library Usage

**User Story:** As a system maintainer, I want the upload system to use existing battle-tested libraries, so that we don't reinvent the wheel.

#### Acceptance Criteria

1. WHEN implementing TUS protocol THEN the System SHALL use `tusd` or `aiohttp-tus` library
2. WHEN implementing antivirus scanning THEN the System SHALL use `pyclamd` library for ClamAV integration
3. WHEN implementing file hashing THEN the System SHALL use `hashlib` with streaming for large files
4. WHEN implementing chunked uploads THEN the System SHALL use existing `webui/js/uploadsChunked.js` as foundation

### Requirement 20: Celery Canvas Patterns

**User Story:** As a system maintainer, I want Celery Canvas patterns (chain/group/chord) implemented for DAG-like task flows, so that complex workflows are deterministic and observable.

#### Acceptance Criteria

1. WHEN sequential tasks are required THEN the System SHALL use `chain()` pattern for ordered execution
2. WHEN parallel tasks are required THEN the System SHALL use `group()` pattern for fan-out execution
3. WHEN aggregation after parallel tasks is required THEN the System SHALL use `chord()` pattern for fan-in
4. WHEN bulk operations are required THEN the System SHALL use `group()` with `apply_async()`
5. WHEN Canvas workflows are created THEN the System SHALL validate all inputs/outputs via schemas

### Requirement 21: Celery Task Queue Routing

**User Story:** As a system maintainer, I want Celery task routing configured, so that tasks are distributed to appropriate queues based on their type.

#### Acceptance Criteria

1. WHEN `celery_app.py` is configured THEN the System SHALL define `task_routes` for queue routing
2. WHEN delegation tasks are submitted THEN the System SHALL route to `delegation` queue
3. WHEN browser tasks are submitted THEN the System SHALL route to `browser` queue
4. WHEN code execution tasks are submitted THEN the System SHALL route to `code` queue
5. WHEN heavy computation tasks are submitted THEN the System SHALL route to `heavy` queue
6. WHEN A2A tasks are submitted THEN the System SHALL route to `fast_a2a` queue

### Requirement 22: Celery Reliability Configuration

**User Story:** As a system maintainer, I want Celery reliability settings configured, so that tasks are resilient to failures and worker crashes.

#### Acceptance Criteria

1. WHEN `celery_app.py` is configured THEN the System SHALL set `task_acks_late=True` for late acknowledgment
2. WHEN `celery_app.py` is configured THEN the System SHALL set `task_reject_on_worker_lost=True` for redelivery
3. WHEN `celery_app.py` is configured THEN the System SHALL set `visibility_timeout` to at least 7200 seconds
4. WHEN `celery_app.py` is configured THEN the System SHALL set `result_expires` to 86400 seconds
5. WHEN tasks are defined THEN the System SHALL use `autoretry_for` with `retry_backoff=True` and `retry_jitter=True`

### Requirement 23: OPA Policy Integration in Tasks

**User Story:** As a system maintainer, I want OPA policy checks integrated into Celery tasks, so that task execution is authorized before processing.

#### Acceptance Criteria

1. WHEN a delegation task is executed THEN the System SHALL call `allow_delegate(tenant_id, subagent_url)` before processing
2. WHEN OPA denies a task THEN the System SHALL raise `PermissionError` and increment failure metrics
3. WHEN OPA allows a task THEN the System SHALL proceed with task execution
4. WHEN OPA is unavailable THEN the System SHALL fail-closed (deny by default)

### Requirement 24: Prometheus Metrics in Celery Tasks

**User Story:** As a system maintainer, I want Prometheus metrics in all Celery tasks, so that task execution is observable.

#### Acceptance Criteria

1. WHEN a task starts THEN the System SHALL increment `celery_tasks_total` counter with task label
2. WHEN a task succeeds THEN the System SHALL increment `celery_tasks_success` counter
3. WHEN a task fails THEN the System SHALL increment `celery_tasks_failed` counter
4. WHEN a task executes THEN the System SHALL record duration in `celery_task_duration_seconds` histogram
5. WHEN metrics are exposed THEN the System SHALL serve `/metrics` endpoint on workers

### Requirement 25: Task Deduplication Pattern

**User Story:** As a system maintainer, I want task deduplication implemented, so that duplicate task submissions are idempotent.

#### Acceptance Criteria

1. WHEN a task is submitted THEN the System SHALL generate or accept a `request_id` for deduplication
2. WHEN a task starts THEN the System SHALL check Redis with `SET NX` for the dedupe key
3. WHEN a duplicate task is detected THEN the System SHALL return `{"status": "duplicate", "request_id": "..."}` without re-executing
4. WHEN the dedupe key is set THEN the System SHALL use a TTL of 3600 seconds

### Requirement 26: Celery Worker Metrics Server

**User Story:** As a system maintainer, I want Celery workers to expose Prometheus metrics, so that SRE can monitor worker health.

#### Acceptance Criteria

1. WHEN a Celery worker starts THEN the System SHALL start a metrics HTTP server on `METRICS_PORT` (default 8001)
2. WHEN metrics are scraped THEN the System SHALL expose task counters, histograms, and health status
3. WHEN Flower is deployed THEN the System SHALL connect to the Redis broker for queue inspection

### Requirement 27: Data Contract Compliance

**User Story:** As a system maintainer, I want all A2A communication to follow defined data contracts, so that inter-service communication is reliable.

#### Acceptance Criteria

1. WHEN an A2A request is sent THEN the System SHALL include `message`, `metadata` (tenant, request_id), `data`, and `subagent_url`
2. WHEN an A2A response is received THEN the System SHALL parse `status` (ok|error), `data`, and `errors` fields
3. WHEN SomaBrain is called THEN the System SHALL use `/recall`, `/remember`, `/context/feedback` endpoints via the adapter

---

## Tool Repository & Autodiscovery Analysis

### Vision: Dynamic Permission-Controlled Tool Ecosystem

The target architecture enables:
1. **Permission-based tool access** via OPA/policy infrastructure
2. **Default tool catalog** managed centrally for SomaAgent01 on first start
3. **Agent can dynamically discover and add tools** based on LLM decisions
4. **Tools are restricted by permissions** the agent has been granted

### Complete Tool Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AGENT TOOL DECISION FLOW                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. SYSTEM PROMPT GENERATION                                                 │
│     ├── agent.system.tools.md ──► {{tools}} placeholder                     │
│     ├── agent.system.tools.py ──► CallSubordinate.get_variables()           │
│     │         │                                                              │
│     │         └──► Collects all agent.system.tool.*.md files                │
│     │                   │                                                    │
│     │                   └──► Returns {"tools": joined_tool_prompts}         │
│     │                                                                        │
│     └── MCP Tools ──► MCPConfig.get_tools_prompt()                          │
│                                                                              │
│  2. LLM DECISION                                                             │
│     ├── LLM receives system prompt with available tools                     │
│     └── LLM outputs JSON: {"tool_name": "...", "tool_args": {...}}          │
│                                                                              │
│  3. TOOL RESOLUTION (agent.py::process_tools)                               │
│     ├── extract_tools.json_parse_dirty(msg) ──► Parse tool request          │
│     ├── Try MCP first: MCPConfig.get_tool(agent, tool_name)                 │
│     └── Fallback: agent.get_tool(name, method, args, ...)                   │
│                   │                                                          │
│                   ├──► agents/{profile}/tools/{name}.py (profile-specific)  │
│                   └──► python/tools/{name}.py (default)                     │
│                                                                              │
│  4. PERMISSION CHECK (ConversationPolicyEnforcer)                           │
│     └── check_tool_request_policy(tenant, persona_id, tool_name, tool_args) │
│               │                                                              │
│               └──► OPA: PolicyRequest(action="tool.request", resource=tool) │
│                         │                                                    │
│                         └──► policy/tool_policy.rego ──► allow/deny         │
│                                                                              │
│  5. TOOL EXECUTION                                                           │
│     ├── tool.before_execution(**tool_args)                                  │
│     ├── call_extensions("tool_execute_before", ...)                         │
│     ├── response = tool.execute(**tool_args)                                │
│     ├── call_extensions("tool_execute_after", ...)                          │
│     ├── tool.after_execution(response)                                      │
│     └── _track_tool_execution_for_learning(tool_name, args, response)       │
│                                                                              │
│  6. TOOL EXECUTOR SERVICE (for heavy/sandboxed tools)                       │
│     ├── Kafka: tool.requests topic                                          │
│     ├── ToolExecutor.tool_registry.get(tool_name)                           │
│     ├── ExecutionEngine.execute(tool, args)                                 │
│     └── Kafka: tool.results topic                                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Current Tool Architecture Status

The SomaAgent01 tool system has **THREE DISTINCT TOOL SUBSYSTEMS** that need analysis:

#### 1. Agent Tools (`python/tools/`) — Agent-Side Tool Execution

**Location:** `python/tools/`
**Base Class:** `python/helpers/tool.py::Tool`
**Discovery:** Dynamic file-based loading via `extract_tools.load_classes_from_file()`

**Available Tools (23 files):**
| Tool File | Status | Description |
|-----------|--------|-------------|
| `a2a_chat.py` | ✅ Active | FastA2A agent communication |
| `behaviour_adjustment.py` | ✅ Active | Agent behavior modification |
| `browser_agent.py` | ⚠️ persist_chat import | Browser automation |
| `call_subordinate.py` | ✅ Active | Subordinate agent delegation |
| `catalog.py` | ✅ Active | Tool catalog singleton |
| `code_execution_tool.py` | ✅ Active | Code execution |
| `document_query.py` | ✅ Active | Document querying |
| `input.py` | ✅ Active | User input handling |
| `memory_delete.py` | ✅ Active | Memory deletion |
| `memory_forget.py` | ✅ Active | Memory forgetting |
| `memory_load.py` | ✅ Active | Memory loading |
| `memory_save.py` | ✅ Active | Memory saving |
| `models.py` | ✅ Active | Tool data models |
| `notify_user.py` | ✅ Active | User notifications |
| `response.py` | ✅ Active | Response handling |
| `scheduler.py` | ⚠️ persist_chat import | Task scheduling |
| `search_engine.py` | ✅ Active | Search functionality |
| `unknown.py` | ✅ Active | Unknown tool fallback |
| `vision_load.py` | ✅ Active | Vision/image loading |
| `browser_do._py` | ❌ Disabled | Browser actions (disabled) |
| `browser_open._py` | ❌ Disabled | Browser open (disabled) |
| `browser._py` | ❌ Disabled | Browser base (disabled) |
| `knowledge_tool._py` | ❌ Disabled | Knowledge tool (disabled) |

**Discovery Flow:**
```
agent.py::get_tool_class()
    │
    ├──► Try: agents/{profile}/tools/{name}.py (profile-specific)
    │
    └──► Fallback: python/tools/{name}.py (default)
            │
            └──► extract_tools.load_classes_from_file()
                    │
                    └──► importlib.util.spec_from_file_location()
```

#### 2. Tool Executor Tools (`services/tool_executor/tools.py`) — Service-Side Execution

**Location:** `services/tool_executor/tools.py`
**Base Class:** `services/tool_executor/tools.py::BaseTool`
**Registry:** `services/tool_executor/tool_registry.py::ToolRegistry`
**Discovery:** Static `AVAILABLE_TOOLS` dictionary

**Available Tools (7 tools):**
| Tool | Status | Description |
|------|--------|-------------|
| `echo` | ✅ Active | Echo text back |
| `timestamp` | ✅ Active | Current timestamp |
| `code_execute` | ✅ Active | Python code execution |
| `file_read` | ✅ Active | File reading (sandboxed) |
| `http_fetch` | ✅ Active | HTTP fetching |
| `canvas_append` | ✅ Active | Canvas content appending |
| `document_ingest` | ✅ Active | Document ingestion (PDF, images, text) |

**Discovery Flow:**
```
ToolExecutor.start()
    │
    └──► tool_registry.load_all_tools()
            │
            └──► for name, tool in AVAILABLE_TOOLS.items():
                    │
                    └──► self.register(tool)
```

#### 3. Tool Catalog (`services/common/tool_catalog.py`) — PostgreSQL-Backed Catalog

**Location:** `services/common/tool_catalog.py`
**Storage:** PostgreSQL `tool_catalog` table
**Purpose:** Runtime enable/disable of tools per tenant

**Schema:**
```sql
CREATE TABLE tool_catalog (
    name TEXT PRIMARY KEY,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    description TEXT,
    params JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE tenant_tool_flags (
    tenant_id TEXT NOT NULL,
    tool_name TEXT NOT NULL REFERENCES tool_catalog(name),
    enabled BOOLEAN NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (tenant_id, tool_name)
);
```

**API Endpoints:**
- `GET /v1/tool-catalog` — List all tools
- `PUT /v1/tool-catalog/{name}` — Update tool settings

### VIBE Compliance Analysis

| Aspect | Status | Issue |
|--------|--------|-------|
| **Single Source of Truth** | ❌ VIOLATION | 3 separate tool systems |
| **No File Storage** | ⚠️ PARTIAL | Agent tools use file-based discovery |
| **Real Implementations** | ✅ COMPLIANT | All tools have real implementations |
| **No Placeholders** | ✅ COMPLIANT | No stub tools |
| **persist_chat Imports** | ❌ VIOLATION | 2 tools import deleted module |

### Violations Found

| File | Violation | Impact |
|------|-----------|--------|
| `python/tools/browser_agent.py` | `from python.helpers import persist_chat` | Import error |
| `python/tools/scheduler.py` | `from python.helpers import persist_chat` | Import error |

### Recommendations

1. **Consolidate Tool Systems**: Consider unifying the 3 tool subsystems into a single canonical registry
2. **Fix persist_chat Imports**: Remove imports from `browser_agent.py` and `scheduler.py`
3. **Add JSON Schema Registry**: Implement `tool_registry.json` as specified in SRS.md
4. **Enable Disabled Tools**: Review `._py` files and either enable or remove them

---

### Requirement 28: Tool Repository Consolidation

**User Story:** As a system maintainer, I want a unified tool repository with consistent discovery, so that tool management is centralized and VIBE compliant.

#### Acceptance Criteria

1. WHEN tools are discovered THEN the System SHALL use a single canonical registry pattern
2. WHEN `python/tools/browser_agent.py` is loaded THEN the System SHALL NOT import `persist_chat`
3. WHEN `python/tools/scheduler.py` is loaded THEN the System SHALL NOT import `persist_chat`
4. WHEN tools are registered THEN the System SHALL store metadata in PostgreSQL `tool_catalog` table
5. WHEN tools are enabled/disabled THEN the System SHALL use `ToolCatalogStore` for persistence
6. WHEN disabled tools exist (._py files) THEN the System SHALL either enable or remove them

### Requirement 29: Tool Executor Service Integration

**User Story:** As a system maintainer, I want the tool executor service to integrate with the canonical tool catalog, so that tool availability is consistent across the system.

#### Acceptance Criteria

1. WHEN `ToolRegistry.load_all_tools()` is called THEN the System SHALL check `ToolCatalogStore.is_enabled()` for each tool
2. WHEN a tool is disabled in the catalog THEN the System SHALL NOT register it in the executor
3. WHEN a tool execution is requested THEN the System SHALL verify the tool is enabled before execution
4. WHEN tool schemas are generated THEN the System SHALL use `input_schema()` from each tool

### Requirement 30: Tool Discovery Documentation

**User Story:** As a developer, I want clear documentation of the tool discovery process, so that new tools can be added correctly.

#### Acceptance Criteria

1. WHEN the roadmap is updated THEN the System SHALL document the three tool subsystems
2. WHEN the roadmap is updated THEN the System SHALL document the tool discovery flow
3. WHEN the roadmap is updated THEN the System SHALL document how to add new tools
4. WHEN the roadmap is updated THEN the System SHALL document the tool catalog schema

### Requirement 31: Default Tool Catalog Initialization

**User Story:** As a system maintainer, I want a default tool catalog seeded on first SomaAgent01 startup, so that agents have a baseline set of tools available.

#### Acceptance Criteria

1. WHEN SomaAgent01 starts for the first time THEN the System SHALL seed the `tool_catalog` table with default tools
2. WHEN default tools are seeded THEN the System SHALL include: echo, timestamp, code_execute, file_read, http_fetch, canvas_append, document_ingest
3. WHEN default tools are seeded THEN the System SHALL include: memory_load, memory_save, memory_delete, memory_forget
4. WHEN default tools are seeded THEN the System SHALL include: search_engine, document_query, response, notify_user
5. WHEN a tool is seeded THEN the System SHALL store its JSON schema in the `params` column

### Requirement 32: Dynamic Tool Discovery by Agent

**User Story:** As an agent, I want to dynamically discover and add tools based on LLM decisions, so that I can expand my capabilities within permission boundaries.

#### Acceptance Criteria

1. WHEN an agent requests a new tool THEN the System SHALL check if the tool exists in the catalog
2. WHEN a tool exists but is disabled THEN the System SHALL check OPA policy for `tool.enable` permission
3. WHEN OPA allows tool enablement THEN the System SHALL enable the tool for that tenant/persona
4. WHEN an agent discovers an MCP tool THEN the System SHALL register it in the catalog with `source=mcp`
5. WHEN a tool is dynamically added THEN the System SHALL log the addition with tenant, persona, and timestamp

### Requirement 33: OPA Tool Permission Policy

**User Story:** As a security administrator, I want OPA policies to control tool access, so that agents can only use tools they have permission for.

#### Acceptance Criteria

1. WHEN `policy/tool_policy.rego` is updated THEN the System SHALL define rules for `tool.request` action
2. WHEN a tool request is evaluated THEN the System SHALL check tenant-level tool permissions
3. WHEN a tool request is evaluated THEN the System SHALL check persona-level tool restrictions
4. WHEN a tool is in the deny list THEN the System SHALL return `allow=false` with reason
5. WHEN OPA is unavailable THEN the System SHALL fail-closed (deny all tool requests)

### Requirement 34: Tool Prompt Generation from Catalog

**User Story:** As a system maintainer, I want tool prompts generated from the catalog, so that the LLM only sees tools the agent has permission to use.

#### Acceptance Criteria

1. WHEN `get_tools_prompt(agent)` is called THEN the System SHALL filter tools by agent permissions
2. WHEN tools are filtered THEN the System SHALL check `ToolCatalogStore.is_enabled(tool_name)` for each tool
3. WHEN tools are filtered THEN the System SHALL check OPA policy for `tool.view` permission
4. WHEN a tool prompt file exists (`agent.system.tool.{name}.md`) THEN the System SHALL include it in the prompt
5. WHEN a tool has no prompt file THEN the System SHALL generate a prompt from its JSON schema

### Requirement 35: Tool Execution Tracking for Learning

**User Story:** As a system maintainer, I want tool executions tracked in SomaBrain, so that the agent can learn from tool usage patterns.

#### Acceptance Criteria

1. WHEN a tool is executed THEN the System SHALL call `_track_tool_execution_for_learning(tool_name, args, response)`
2. WHEN tracking tool execution THEN the System SHALL send to SomaBrain `/context/feedback` endpoint
3. WHEN tracking tool execution THEN the System SHALL include success/failure status
4. WHEN tracking tool execution THEN the System SHALL include execution duration
5. WHEN SomaBrain is unavailable THEN the System SHALL queue the tracking event for later delivery

### Requirement 36: Tenant-Specific Tool Flags

**User Story:** As a multi-tenant administrator, I want per-tenant tool enablement, so that different tenants can have different tool capabilities.

#### Acceptance Criteria

1. WHEN a tool is enabled/disabled for a tenant THEN the System SHALL store in `tenant_tool_flags` table
2. WHEN checking tool availability THEN the System SHALL check tenant-specific flags first
3. WHEN tenant flag is not set THEN the System SHALL fall back to global `tool_catalog.enabled`
4. WHEN a tenant is created THEN the System SHALL inherit default tool flags from global catalog
5. WHEN listing tools for a tenant THEN the System SHALL merge global and tenant-specific flags

### Requirement 37: Tool Schema Validation

**User Story:** As a system maintainer, I want tool arguments validated against JSON schemas, so that invalid tool calls are rejected before execution.

#### Acceptance Criteria

1. WHEN a tool is called THEN the System SHALL validate `tool_args` against the tool's `input_schema()`
2. WHEN validation fails THEN the System SHALL return a clear error message to the agent
3. WHEN validation fails THEN the System SHALL NOT execute the tool
4. WHEN a tool has no schema THEN the System SHALL allow any arguments (backward compatibility)
5. WHEN schema validation is performed THEN the System SHALL use `jsonschema` library



---

## Additional Requirements from Merged Architecture Analysis

### Requirement 38: File-Based Backup Pattern Removal

**User Story:** As a system maintainer, I want file-based backup patterns removed, so that backups reference PostgreSQL-backed data instead of filesystem paths.

#### Acceptance Criteria

1. WHEN `python/helpers/backup.py` defines patterns THEN the System SHALL NOT reference `tmp/settings.json`
2. WHEN `python/helpers/backup.py` defines patterns THEN the System SHALL NOT reference `tmp/chats/**`
3. WHEN `python/helpers/backup.py` defines patterns THEN the System SHALL NOT reference `tmp/scheduler/**`
4. WHEN `python/helpers/backup.py` defines patterns THEN the System SHALL NOT reference `tmp/uploads/**`
5. WHEN backup is created THEN the System SHALL export from PostgreSQL tables instead of filesystem

### Requirement 39: File-Based Logging Migration

**User Story:** As a system maintainer, I want file-based logging migrated to structured logging, so that logs are centralized and queryable.

#### Acceptance Criteria

1. WHEN `python/helpers/print_style.py` logs output THEN the System SHALL NOT write to `logs/*.html`
2. WHEN logging is performed THEN the System SHALL use structured JSON logging to stdout
3. WHEN logs are collected THEN the System SHALL be compatible with Kafka/ELK ingestion
4. WHEN debug logs are needed THEN the System SHALL use the existing telemetry infrastructure

### Requirement 40: Speech Endpoint Implementation or Removal

**User Story:** As a system maintainer, I want speech endpoints to have real implementations or be removed, so that there are no fake/placeholder endpoints.

#### Acceptance Criteria

1. WHEN `/v1/speech/transcribe` is called THEN the System SHALL use Whisper for real transcription OR return 501 Not Implemented
2. WHEN `/v1/speech/tts/kokoro` is called THEN the System SHALL generate real audio OR return 501 Not Implemented
3. WHEN `/v1/speech/realtime/session` is called THEN the System SHALL create a real WebSocket session OR return 501 Not Implemented
4. WHEN audio_support feature is disabled THEN the System SHALL return 503 Service Unavailable for all speech endpoints
5. IF speech endpoints are removed THEN the System SHALL update webui/components/chat/speech/* to handle unavailability

### Requirement 41: Skeleton Router Removal

**User Story:** As a system maintainer, I want skeleton routers removed, so that there is no confusion about canonical implementations.

#### Acceptance Criteria

1. WHEN `services/gateway/routers/uploads.py` exists alongside `uploads_full.py` THEN the System SHALL delete `uploads.py`
2. WHEN `services/gateway/routers/chat.py` exists alongside `chat_full.py` THEN the System SHALL delete `chat.py`
3. WHEN `services/gateway/routers/memory.py` contains only skeleton code THEN the System SHALL delete `memory.py`
4. WHEN routers are deleted THEN the System SHALL update `services/gateway/routers/__init__.py` imports

### Requirement 42: Disabled Tool File Cleanup

**User Story:** As a system maintainer, I want disabled tool files (._py) removed, so that the codebase is clean and unambiguous.

#### Acceptance Criteria

1. WHEN `python/tools/browser_do._py` exists THEN the System SHALL delete the file
2. WHEN `python/tools/browser_open._py` exists THEN the System SHALL delete the file
3. WHEN `python/tools/browser._py` exists THEN the System SHALL delete the file
4. WHEN `python/tools/knowledge_tool._py` exists THEN the System SHALL delete the file
5. WHEN disabled tools are deleted THEN the System SHALL verify no imports reference them

### Requirement 43: Degradation Mode Documentation

**User Story:** As a developer, I want degradation mode behavior documented, so that the system's offline capabilities are understood.

#### Acceptance Criteria

1. WHEN the roadmap is updated THEN the System SHALL document SomaBrain health states (up, degraded, down)
2. WHEN the roadmap is updated THEN the System SHALL document circuit breaker configuration
3. WHEN the roadmap is updated THEN the System SHALL document UI indicators for offline mode
4. WHEN the roadmap is updated THEN the System SHALL document graceful shutdown procedure

### Requirement 44: LLM Provider Configuration Consolidation

**User Story:** As a system maintainer, I want LLM provider configuration consolidated, so that all 4 model configurations use the canonical settings architecture.

#### Acceptance Criteria

1. WHEN Chat Model is configured THEN the System SHALL store settings in `AgentSettingsStore` (provider, name, api_base, ctx_length, vision, rate limits, kwargs)
2. WHEN Utility Model is configured THEN the System SHALL store settings in `AgentSettingsStore` (provider, name, api_base, ctx_length, rate limits, kwargs)
3. WHEN Embedding Model is configured THEN the System SHALL store settings in `AgentSettingsStore` (provider, name, api_base, rate limits, kwargs)
4. WHEN Browser Model is configured THEN the System SHALL store settings in `AgentSettingsStore` (provider, name, api_base, vision, rate limits, kwargs, http_headers)
5. WHEN API keys are retrieved THEN the System SHALL use `UnifiedSecretManager` via Vault (api_key_{provider})
6. WHEN provider routing is performed THEN the System SHALL use LiteLLM's `{provider}/{model}` format
7. WHEN `initialize.py` creates ModelConfig THEN the System SHALL read from `get_settings()` which uses AgentSettingsStore

### Requirement 45: Streaming Architecture Documentation

**User Story:** As a developer, I want streaming architecture documented, so that SSE, WebSocket, and Kafka patterns are understood.

#### Acceptance Criteria

1. WHEN the roadmap is updated THEN the System SHALL document SSE endpoint patterns
2. WHEN the roadmap is updated THEN the System SHALL document WebSocket endpoint patterns
3. WHEN the roadmap is updated THEN the System SHALL document Kafka topic naming conventions
4. WHEN the roadmap is updated THEN the System SHALL document streaming feature flags

### Requirement 46: Degradation Mode VIBE Compliance

**User Story:** As a system maintainer, I want degradation mode to be VIBE compliant and production-grade, so that the system handles failures gracefully without violations.

#### Acceptance Criteria

1. WHEN `src/core/config/loader.py` handles configuration THEN the System SHALL NOT use legacy fallbacks (VIBE: NO FALLBACKS)
2. WHEN `src/core/clients/somabrain.py` circuit breaker is configured THEN the System SHALL use `cfg.env()` for thresholds and cooldown
3. WHEN exceptions are handled THEN the System SHALL use specific exception types, not generic `except Exception:`
4. WHEN comments reference fake patterns THEN the System SHALL remove misleading comments about "fake fallback responses"
5. WHEN circuit breaker state changes THEN the System SHALL emit Prometheus metrics (state gauge, failures counter, state changes counter)

### Requirement 47: Enhanced Circuit Breaker

**User Story:** As a system maintainer, I want an enhanced circuit breaker with half-open state and metrics, so that SomaBrain failures are handled with production-grade resilience.

#### Acceptance Criteria

1. WHEN circuit breaker is implemented THEN the System SHALL support three states: closed, open, half-open
2. WHEN circuit breaker opens THEN the System SHALL transition to half-open after cooldown period
3. WHEN in half-open state THEN the System SHALL allow limited requests to test recovery
4. WHEN circuit breaker configuration is needed THEN the System SHALL use `SA01_SOMA_CB_THRESHOLD`, `SA01_SOMA_CB_COOLDOWN_SEC`, `SA01_SOMA_CB_HALF_OPEN_CALLS`
5. WHEN circuit breaker state changes THEN the System SHALL log structured events with context

### Requirement 48: Cascading Failure Prevention

**User Story:** As a system maintainer, I want cascading failure prevention, so that one service failure does not bring down the entire system.

#### Acceptance Criteria

1. WHEN a service fails THEN the System SHALL evaluate dependent services for degradation
2. WHEN `DegradationManager` is implemented THEN the System SHALL maintain service dependency graph
3. WHEN PostgreSQL fails THEN the System SHALL degrade conversation_worker, tool_executor, gateway, memory_sync
4. WHEN SomaBrain fails THEN the System SHALL degrade conversation_worker and memory_sync
5. WHEN Kafka fails THEN the System SHALL degrade conversation_worker and tool_executor

### Requirement 49: Enhanced Health Checks

**User Story:** As a system maintainer, I want enhanced health checks with latency monitoring and parallel execution, so that system health is accurately assessed.

#### Acceptance Criteria

1. WHEN health checks are performed THEN the System SHALL execute PostgreSQL, Redis, Kafka, SomaBrain checks in parallel
2. WHEN PostgreSQL latency exceeds 1000ms THEN the System SHALL mark service as degraded
3. WHEN circuit breaker is open THEN the System SHALL mark SomaBrain as failed without additional requests
4. WHEN circuit breaker is half-open THEN the System SHALL mark SomaBrain as degraded
5. WHEN health check endpoint is called THEN the System SHALL return detailed service states and error messages

---

## Complete Violations Summary

### Total Violations: 22

| Priority | Count | Description |
|----------|-------|-------------|
| P0 - Critical | 8 | persist_chat imports (system breaking) |
| P1 - High | 7 | Architecture violations (file-based, fake implementations) |
| P2 - Medium | 7 | Cleanup (skeleton routers, disabled tools) |

### VIBE Compliance Score

| Metric | Current | Target |
|--------|---------|--------|
| persist_chat Cleanup | 0% | 100% |
| Settings Consolidation | 30% | 100% |
| File-Based Removal | 40% | 100% |
| Speech Implementation | 0% | 100% |
| Skeleton Removal | 0% | 100% |
| Tool Cleanup | 0% | 100% |
| **Overall** | **~45%** | **100%** |

---

## Context Builder Requirements (ADOPTED - Production Ready)

### Requirement 50: Context Builder Preload Integration

**User Story:** As a system maintainer, I want the Context Builder integrated into preload.py, so that the system has warm-up and reduced cold start latency.

#### Acceptance Criteria

1. WHEN `preload.py` executes THEN the System SHALL import and instantiate `ContextBuilder`
2. WHEN preload runs THEN the System SHALL warm up the context builder with a test query
3. WHEN preload fails for context builder THEN the System SHALL log the error and continue
4. WHEN `SOMA_MAX_TOKENS` env var is set THEN the System SHALL use it for configuration
5. WHEN `SOMA_RECALL_TOPK` env var is set THEN the System SHALL use it for retrieval top_k

### Requirement 51: Presidio PII Redaction

**User Story:** As a system maintainer, I want PII redaction using Presidio, so that sensitive data is protected.

#### Acceptance Criteria

1. WHEN `PresidioRedactor` is created THEN the System SHALL instantiate Presidio engines
2. WHEN text is redacted THEN the System SHALL analyze for PII entities
3. WHEN PII is detected THEN the System SHALL anonymize using Presidio operators
4. WHEN redaction is performed THEN the System SHALL cache results per document
5. WHEN `presidio-analyzer` is required THEN the System SHALL list it in requirements.txt

---

## Message & Conversation Improvements (ADOPTED from SomaAgent01 Analysis)

### Requirement 52: Unified Conversation Class

**User Story:** As a system maintainer, I want a central Conversation class with turn tracking and auto-retry, so that conversation state is managed consistently.

#### Acceptance Criteria

1. WHEN a conversation is created THEN the System SHALL instantiate `Conversation` with session_id, tenant_id
2. WHEN a turn is added THEN the System SHALL track turn history with timestamps
3. WHEN token usage is recorded THEN the System SHALL track input/output tokens per turn
4. WHEN an LLM call fails THEN the System SHALL retry with exponential backoff (max 3)
5. WHEN conversation state changes THEN the System SHALL emit `conversation_turns_total` metric

### Requirement 53: Structured Tool Result Handling

**User Story:** As a system maintainer, I want tool results automatically merged into context, so that tool execution is seamless.

#### Acceptance Criteria

1. WHEN `run_tool()` is called THEN the System SHALL return structured `ToolResult`
2. WHEN a tool succeeds THEN the System SHALL merge result into conversation context
3. WHEN a tool fails THEN the System SHALL format error as system message
4. WHEN tool execution completes THEN the System SHALL record `tool_latency_seconds`
5. WHEN tool results are merged THEN the System SHALL validate against output schema

### Requirement 54: Pydantic Message Validation

**User Story:** As a system maintainer, I want messages validated with Pydantic, so that schema compliance is enforced.

#### Acceptance Criteria

1. WHEN a message is received THEN the System SHALL validate against `MessageSchema`
2. WHEN validation fails THEN the System SHALL return 422 with validation errors
3. WHEN message content exceeds limits THEN the System SHALL reject with `content_too_large`
4. WHEN message role is invalid THEN the System SHALL reject with `invalid_role`
5. WHEN message is validated THEN the System SHALL normalize encoding

### Requirement 55: Multi-Tenant Context Persistence

**User Story:** As a system maintainer, I want context persistence with Redis and tenant isolation, so that state survives restarts.

#### Acceptance Criteria

1. WHEN context is stored THEN the System SHALL use Redis with tenant-prefixed keys
2. WHEN context is retrieved THEN the System SHALL verify tenant ownership
3. WHEN context expires THEN the System SHALL use configurable TTL (default 24h)
4. WHEN Redis is unavailable THEN the System SHALL fall back to PostgreSQL
5. WHEN context is deleted THEN the System SHALL cascade delete session events

### Requirement 56: Conversation Observability

**User Story:** As a system maintainer, I want Prometheus metrics for conversation handling, so that message flow is observable.

#### Acceptance Criteria

1. WHEN a turn completes THEN the System SHALL increment `conversation_turns_total`
2. WHEN a message is processed THEN the System SHALL record `message_processing_seconds`
3. WHEN tool execution occurs THEN the System SHALL record `tool_latency_seconds`
4. WHEN streaming completes THEN the System SHALL record `streaming_duration_seconds`
5. WHEN errors occur THEN the System SHALL increment `conversation_errors_total`

### Requirement 57: Automatic Turn Tracking

**User Story:** As a system maintainer, I want automatic turn tracking with retry logic, so that conversation flow is deterministic.

#### Acceptance Criteria

1. WHEN a user message is received THEN the System SHALL create turn with auto-increment turn_id
2. WHEN an assistant response is generated THEN the System SHALL associate with current turn
3. WHEN a tool is called mid-turn THEN the System SHALL stitch result into turn
4. WHEN a turn fails THEN the System SHALL retry with same turn_id (idempotent)
5. WHEN turn history is retrieved THEN the System SHALL return chronological order

### Requirement 58: Context Window Management

**User Story:** As a system maintainer, I want automatic context window management, so that conversations don't exceed model limits.

#### Acceptance Criteria

1. WHEN context exceeds model limit THEN the System SHALL summarize older turns
2. WHEN summarization occurs THEN the System SHALL preserve recent N turns intact
3. WHEN context is trimmed THEN the System SHALL emit `context_trimmed` event
4. WHEN important messages are marked THEN the System SHALL preserve during trimming
5. WHEN budget is calculated THEN the System SHALL reserve tokens for system prompt

### Requirement 59: Conversation State Machine

**User Story:** As a system maintainer, I want a conversation state machine, so that lifecycle is well-defined.

#### Acceptance Criteria

1. WHEN conversation starts THEN the System SHALL transition to `active` state
2. WHEN waiting for input THEN the System SHALL transition to `waiting` state
3. WHEN processing response THEN the System SHALL transition to `processing` state
4. WHEN error occurs THEN the System SHALL transition to `error` state with reason
5. WHEN conversation ends THEN the System SHALL transition to `completed` state

---

## Dynamic Tool Registry (ADOPTED - Improves existing tool architecture)

### Requirement 60: Enhanced Tool Registry

**User Story:** As a system maintainer, I want a dynamic Tool Registry with hooks, so that tools are managed uniformly.

#### Acceptance Criteria

1. WHEN a tool is registered THEN the System SHALL store in `ToolRegistry` with schema
2. WHEN `get_tool(name)` is called THEN the System SHALL return executor or raise error
3. WHEN tool executes THEN the System SHALL call before/execute/after hooks
4. WHEN tools are listed THEN the System SHALL return all with schemas
5. WHEN tool is disabled THEN the System SHALL remove and emit `tool_disabled` event

---

## Requirements Summary (FINAL - REVISED)

**Total Requirements: 60**

| Category | Requirements | Count |
|----------|--------------|-------|
| persist_chat Cleanup | 1-2 | 2 |
| Celery Architecture | 3-6, 20-27 | 12 |
| Settings Consolidation | 8-10 | 3 |
| UI-Backend Alignment | 13-14 | 2 |
| File Upload | 17-19 | 3 |
| Tool Architecture | 28-37, 60 | 11 |
| Merged Architecture | 38-45 | 8 |
| Degradation Mode | 46-49 | 4 |
| Context Builder | 50-51 | 2 |
| Message & Conversation | 52-59 | 8 |
| Other | 7, 11-12, 15-16 | 5 |

### What Was ADOPTED from SomaAgent01:

| Feature | Why Adopted | Benefit |
|---------|-------------|---------|
| Unified Conversation Class | Better state management | Consistency, reliability |
| Structured Tool Results | Cleaner integration | Less manual code |
| Pydantic Validation | Schema enforcement | Fewer runtime errors |
| Redis Context Persistence | Survives restarts | Production-grade |
| Turn Tracking | Deterministic flow | Easier debugging |
| Context Window Management | Prevents overflow | Model compatibility |
| State Machine | Clear lifecycle | Observability |
| Enhanced Tool Registry | Uniform execution | Extensibility |

### What Was SKIPPED (Not needed for SomaAgent01):

| Feature | Why Skipped | Reason |
|---------|-------------|--------|
| RL Policy Network | Overkill | We use rule-based selection |
| Q-Network | Overkill | No RL training needed |
| State Encoder | Already have | ContextBuilder does this |
| Replay Buffer | Not needed | No RL training |
| World Model | Already have | SomaBrain integration |
| RL Trainer Service | Not needed | No ML training loop |

### VIBE Compliance Score (Final)

| Metric | Current | Target |
|--------|---------|--------|
| persist_chat Cleanup | 0% | 100% |
| Settings Consolidation | 30% | 100% |
| Context Builder | 85% | 100% |
| Degradation Mode | 75% | 100% |
| Tool Architecture | 60% | 100% |
| Message/Conversation | 20% | 100% |
| **Overall** | **~45%** | **100%** |

## New Requirements – Constitution-Centric Prompting (Added Dec 2, 2025)

### Requirement 67: Constitution-Sourced Base System Prompt
- Base system prompt SHALL be fetched from the signed Constitution artifact (via SomaBrain/constitution service), verified (signature/hash), cached only in memory, and included in every turn. No filesystem or baked-in defaults. Fail-closed (503) if verification or fetch fails. Emit `constitution_version` in metadata/feedback.

### Requirement 68: Persona Overlay Bound to Constitution
- Persona prompt fragments SHALL layer on top of the Constitution without overriding its rules. Persona data is per-tenant/agent, versioned, OPA-checked on updates, and tagged in feedback (`persona_version`). Tool preferences in persona MUST respect Constitution allow/deny + OPA.

### Requirement 69: Live In-Memory Prompt Composition
- Prompt composition SHALL be live per request: Constitution base + persona + planner priors + health/safety banners. Providers use short TTL memory caches; cache invalidated on Constitution/persona reload. No disk writes.

### Requirement 70: Planner Priors from SomaBrain
- For each turn, the system SHALL call SomaBrain `plan_suggest` with tenant/persona/session/intent/tags to fetch priors on successful tasks/tools. Priors are injected into the system prompt; on miss/failure, proceed without priors and record `planner_priors_miss` metric.

### Requirement 71: Constitution-Tied Tool Exposure
- Tools shown to the LLM SHALL be filtered by Constitution allow/deny plus OPA. Denied tools SHALL never appear in prompts even if enabled elsewhere. Tool prompts carry `constitution_version` and tenant/persona scope.

1. WHEN health checks are performed THEN the System SHALL execute PostgreSQL, Redis, Kafka, SomaBrain checks in parallel
2. WHEN PostgreSQL latency exceeds 1000ms THEN the System SHALL mark service as degraded
3. WHEN circuit breaker is open THEN the System SHALL mark SomaBrain as failed without additional requests
4. WHEN circuit breaker is half-open THEN the System SHALL mark SomaBrain as degraded
5. WHEN health check endpoint is called THEN the System SHALL return detailed service states and error messages

---

## Context Builder Requirements

### Requirement 50: Context Builder Preload Integration

**User Story:** As a system maintainer, I want the Context Builder integrated into preload.py, so that the system has warm-up and reduced cold start latency.

#### Acceptance Criteria

1. WHEN `preload.py` executes THEN the System SHALL import and instantiate `ContextBuilder`
2. WHEN preload runs THEN the System SHALL warm up the context builder with a test query
3. WHEN preload fails for context builder THEN the System SHALL log the error and continue with other preloads
4. WHEN `SOMA_MAX_TOKENS` env var is set THEN the System SHALL use it for context builder configuration
5. WHEN `SOMA_RECALL_TOPK` env var is set THEN the System SHALL use it for retrieval top_k configuration

### Requirement 51: Presidio PII Redaction Implementation

**User Story:** As a system maintainer, I want PII redaction implemented using Presidio, so that sensitive data is protected in context snippets.

#### Acceptance Criteria

1. WHEN `PresidioRedactor` is created THEN the System SHALL instantiate `AnalyzerEngine` and `AnonymizerEngine`
2. WHEN text is redacted THEN the System SHALL analyze for PII entities (email, phone, SSN, credit card)
3. WHEN PII is detected THEN the System SHALL anonymize using Presidio's default operators
4. WHEN redaction is performed THEN the System SHALL cache analyzer results per document to reduce latency
5. WHEN `presidio-analyzer` is required THEN the System SHALL list it in `requirements.txt` with pinned version

### Requirement 52: Optimal Token Budgeting

**User Story:** As a system maintainer, I want optimal token budgeting using knapsack algorithm, so that high-value snippets are not dropped unnecessarily.

#### Acceptance Criteria

1. WHEN `USE_OPTIMAL_BUDGET` env flag is set to true THEN the System SHALL use knapsack-style budgeting
2. WHEN optimal budgeting is used THEN the System SHALL maximize total score within token budget
3. WHEN greedy budgeting is used (default) THEN the System SHALL take snippets in score order until budget exhausted
4. WHEN budgeting algorithm is selected THEN the System SHALL log which algorithm is being used
5. WHEN optimal budgeting exceeds time limit THEN the System SHALL fall back to greedy algorithm

### Requirement 53: Context Builder Feedback Enhancement

**User Story:** As a system maintainer, I want enhanced feedback payloads, so that SomaBrain learning has complete context.

#### Acceptance Criteria

1. WHEN feedback is sent THEN the System SHALL include `doc_id`, `success`, `score`, `timestamp`, `tenant`
2. WHEN feedback is sent THEN the System SHALL include execution duration
3. WHEN SomaBrain is unavailable THEN the System SHALL queue feedback for later delivery
4. WHEN feedback queue exceeds 1000 items THEN the System SHALL drop oldest items and log warning
5. WHEN feedback is successfully delivered THEN the System SHALL clear from queue

### Requirement 54: Context Builder Error Handling

**User Story:** As a system maintainer, I want robust error handling in the context builder, so that failures are graceful and observable.

#### Acceptance Criteria

1. WHEN SomaBrain retrieval fails THEN the System SHALL retry up to 3 times with exponential backoff
2. WHEN all retries fail THEN the System SHALL mark SomaBrain as degraded and continue with empty snippets
3. WHEN timeout occurs THEN the System SHALL use `asyncio.wait_for(..., timeout=5)` for external calls
4. WHEN error occurs THEN the System SHALL emit `context_builder_errors_total` Prometheus counter
5. WHEN degraded mode is entered THEN the System SHALL reduce top_k from 8 to 3

### Requirement 55: Context Builder Testing

**User Story:** As a developer, I want comprehensive tests for the context builder, so that correctness is verified.

#### Acceptance Criteria

1. WHEN property tests are run THEN the System SHALL verify token budget never exceeds max_prompt_tokens
2. WHEN property tests are run THEN the System SHALL verify redacted text contains no PII patterns
3. WHEN property tests are run THEN the System SHALL verify snippet ordering is deterministic
4. WHEN integration tests are run THEN the System SHALL test against real SomaBrain instance
5. WHEN E2E tests are run THEN the System SHALL verify full pipeline with Presidio redaction

---

## Requirements Summary

**Total Requirements: 55**

| Category | Requirements | Count |
|----------|--------------|-------|
| persist_chat Cleanup | 1-2 | 2 |
| Celery Architecture | 3-6, 20-27 | 12 |
| Settings Consolidation | 8-10 | 3 |
| UI-Backend Alignment | 13-14 | 2 |
| File Upload | 17-19 | 3 |
| Tool Architecture | 28-37 | 10 |
| Merged Architecture | 38-45 | 8 |
| Degradation Mode | 46-49 | 4 |
| Context Builder | 50-55 | 6 |
| Other | 7, 11-12, 15-16 | 5 |

### VIBE Compliance Score (Updated)

| Metric | Current | Target |
|--------|---------|--------|
| persist_chat Cleanup | 0% | 100% |
| Settings Consolidation | 30% | 100% |
| File-Based Removal | 40% | 100% |
| Context Builder | 85% | 100% |
| Degradation Mode | 75% | 100% |
| Tool Architecture | 60% | 100% |
| **Overall** | **~50%** | **100%** |


---

## Message & Conversation Architecture Requirements

### Analysis: SomaAgent01 vs SomaAgent01 Comparison

Based on the comprehensive comparison, SomaAgent01 needs significant improvements in message handling, conversation management, and streaming architecture to match SomaAgent01's production-grade patterns.

| Aspect | SomaAgent01 | SomaAgent01 Current | Gap |
|--------|------------|---------------------|-----|
| Conversation abstraction | Central `Conversation` class | Manual state dicts | ❌ CRITICAL |
| Tool result handling | Structured, auto-merged | Manual insertion | ❌ HIGH |
| Streaming API | Hooks, pause/resume | Raw generator | ❌ HIGH |
| Message validation | Pydantic models | Minimal validation | ❌ HIGH |
| Context persistence | Redis/in-memory | Temp in-process | ❌ CRITICAL |
| Observability | Prometheus metrics | Ad-hoc logs | ⚠️ MEDIUM |
| Security/Policy | OPA middleware | No policy layer | ❌ CRITICAL |

### Requirement 56: Unified Conversation Class

**User Story:** As a system maintainer, I want a central Conversation class with built-in turn history, token usage tracking, and automatic retry, so that conversation state is managed consistently.

#### Acceptance Criteria

1. WHEN a conversation is created THEN the System SHALL instantiate a `Conversation` class with session_id, tenant_id, and persona_id
2. WHEN a turn is added THEN the System SHALL automatically track turn history with timestamps
3. WHEN token usage is recorded THEN the System SHALL track input_tokens, output_tokens, and total_tokens per turn
4. WHEN an LLM call fails THEN the System SHALL automatically retry with exponential backoff (max 3 retries)
5. WHEN conversation state changes THEN the System SHALL emit `conversation_turns_total` Prometheus metric

### Requirement 57: Structured Tool Result Handling

**User Story:** As a system maintainer, I want tool results automatically merged into conversation context, so that tool execution is seamless and consistent.

#### Acceptance Criteria

1. WHEN `run_tool()` is called THEN the System SHALL return a structured `ToolResult` with status, data, and error fields
2. WHEN a tool succeeds THEN the System SHALL automatically merge the result into the conversation context
3. WHEN a tool fails THEN the System SHALL format the error and add it to the conversation as a system message
4. WHEN tool execution completes THEN the System SHALL record `tool_latency_seconds` Prometheus histogram
5. WHEN tool results are merged THEN the System SHALL validate against the tool's output schema

### Requirement 58: Enhanced Streaming API

**User Story:** As a system maintainer, I want a streaming API with tool callbacks, pause/resume, and error handling, so that real-time responses are robust and controllable.

#### Acceptance Criteria

1. WHEN streaming tokens THEN the System SHALL support `tool_callback` hooks for mid-stream tool execution
2. WHEN streaming is paused THEN the System SHALL buffer tokens and resume from the last position
3. WHEN a streaming error occurs THEN the System SHALL emit a structured error event and attempt recovery
4. WHEN streaming completes THEN the System SHALL emit a `stream_complete` event with token counts
5. WHEN streaming is cancelled THEN the System SHALL clean up resources and emit `stream_cancelled` event

### Requirement 59: Pydantic Message Validation

**User Story:** As a system maintainer, I want all messages validated with Pydantic models, so that schema compliance is enforced at runtime.

#### Acceptance Criteria

1. WHEN a message is received THEN the System SHALL validate against `MessageSchema` Pydantic model
2. WHEN validation fails THEN the System SHALL return a 422 error with detailed validation errors
3. WHEN message content exceeds size limits THEN the System SHALL reject with `content_too_large` error
4. WHEN message role is invalid THEN the System SHALL reject with `invalid_role` error
5. WHEN message is validated THEN the System SHALL normalize content-type and encoding

### Requirement 60: Multi-Tenant Context Persistence

**User Story:** As a system maintainer, I want context persistence with Redis and per-tenant isolation, so that conversation state survives restarts and tenants are isolated.

#### Acceptance Criteria

1. WHEN context is stored THEN the System SHALL use Redis with tenant-prefixed keys
2. WHEN context is retrieved THEN the System SHALL verify tenant ownership before returning
3. WHEN context expires THEN the System SHALL use configurable TTL (default 24 hours)
4. WHEN Redis is unavailable THEN the System SHALL fall back to PostgreSQL-backed storage
5. WHEN context is deleted THEN the System SHALL cascade delete all related session events

### Requirement 61: Conversation Observability

**User Story:** As a system maintainer, I want comprehensive Prometheus metrics for conversation handling, so that message flow is fully observable.

#### Acceptance Criteria

1. WHEN a conversation turn completes THEN the System SHALL increment `conversation_turns_total` counter
2. WHEN a message is processed THEN the System SHALL record `message_processing_seconds` histogram
3. WHEN tool execution occurs THEN the System SHALL record `tool_latency_seconds` histogram
4. WHEN streaming completes THEN the System SHALL record `streaming_duration_seconds` histogram
5. WHEN errors occur THEN the System SHALL increment `conversation_errors_total` counter with error_type label

### Requirement 62: OPA Message Policy Middleware

**User Story:** As a system maintainer, I want OPA middleware for message policy enforcement, so that rate limits, size limits, and role-based access are enforced.

#### Acceptance Criteria

1. WHEN a message is received THEN the System SHALL evaluate OPA policy for `message.send` action
2. WHEN message size exceeds policy limit THEN the System SHALL reject with `policy_violation` error
3. WHEN rate limit is exceeded THEN the System SHALL return 429 with `Retry-After` header
4. WHEN role-based access is denied THEN the System SHALL return 403 with policy reason
5. WHEN OPA is unavailable THEN the System SHALL fail-closed (deny all messages)

### Requirement 63: Automatic Turn Tracking

**User Story:** As a system maintainer, I want automatic turn tracking with retry logic and tool-result stitching, so that conversation flow is deterministic.

#### Acceptance Criteria

1. WHEN a user message is received THEN the System SHALL create a new turn with auto-incrementing turn_id
2. WHEN an assistant response is generated THEN the System SHALL associate it with the current turn
3. WHEN a tool is called mid-turn THEN the System SHALL stitch the tool result into the turn
4. WHEN a turn fails THEN the System SHALL retry with the same turn_id (idempotent)
5. WHEN turn history is retrieved THEN the System SHALL return turns in chronological order

### Requirement 64: Context Window Management

**User Story:** As a system maintainer, I want automatic context window management, so that conversations don't exceed model limits.

#### Acceptance Criteria

1. WHEN context exceeds model limit THEN the System SHALL automatically summarize older turns
2. WHEN summarization occurs THEN the System SHALL preserve the most recent N turns intact
3. WHEN context is trimmed THEN the System SHALL emit `context_trimmed` event with before/after token counts
4. WHEN important messages are marked THEN the System SHALL preserve them during trimming
5. WHEN context budget is calculated THEN the System SHALL reserve tokens for system prompt and tool results

### Requirement 65: Message Content Normalization

**User Story:** As a system maintainer, I want message content normalized for encoding and content-type, so that all messages are consistently formatted.

#### Acceptance Criteria

1. WHEN message content is received THEN the System SHALL normalize to UTF-8 encoding
2. WHEN content contains HTML THEN the System SHALL sanitize to prevent XSS
3. WHEN content contains markdown THEN the System SHALL preserve formatting
4. WHEN content contains code blocks THEN the System SHALL detect and tag language
5. WHEN content is empty or whitespace-only THEN the System SHALL reject with `empty_content` error

### Requirement 66: Conversation State Machine

**User Story:** As a system maintainer, I want a conversation state machine, so that conversation lifecycle is well-defined and observable.

#### Acceptance Criteria

1. WHEN a conversation starts THEN the System SHALL transition to `active` state
2. WHEN waiting for user input THEN the System SHALL transition to `waiting` state
3. WHEN processing a response THEN the System SHALL transition to `processing` state
4. WHEN an error occurs THEN the System SHALL transition to `error` state with reason
5. WHEN conversation ends THEN the System SHALL transition to `completed` state and persist final state

---

## Requirements Summary (Updated)

**Total Requirements: 66**

| Category | Requirements | Count |
|----------|--------------|-------|
| persist_chat Cleanup | 1-2 | 2 |
| Celery Architecture | 3-6, 20-27 | 12 |
| Settings Consolidation | 8-10 | 3 |
| UI-Backend Alignment | 13-14 | 2 |
| File Upload | 17-19 | 3 |
| Tool Architecture | 28-37 | 10 |
| Merged Architecture | 38-45 | 8 |
| Degradation Mode | 46-49 | 4 |
| Context Builder | 50-55 | 6 |
| Message & Conversation | 56-66 | 11 |
| Other | 7, 11-12, 15-16 | 5 |

### VIBE Compliance Score (Final)

| Metric | Current | Target |
|--------|---------|--------|
| persist_chat Cleanup | 0% | 100% |
| Settings Consolidation | 30% | 100% |
| File-Based Removal | 40% | 100% |
| Context Builder | 85% | 100% |
| Degradation Mode | 75% | 100% |
| Tool Architecture | 60% | 100% |
| Message/Conversation | 20% | 100% |
| **Overall** | **~45%** | **100%** |


---

## SomaAgent01 Advanced Features Integration

### Analysis: SomaAgent01 RL/ML Features for SomaAgent01

Based on the SomaAgent01 feature blueprint, SomaAgent01 needs advanced reinforcement learning and tool orchestration capabilities to achieve full SomaAgent01 parity.

| Feature | SomaAgent01 | SomaAgent01 Current | Gap |
|---------|------------|---------------------|-----|
| Tool Registry | Dynamic `ToolRegistry` with hooks | Static policy_client | ❌ CRITICAL |
| State Encoder | Sentence transformer embeddings | None | ❌ CRITICAL |
| Policy Network | MLP with softmax | None | ❌ HIGH |
| Q-Network | Dueling architecture | None | ❌ HIGH |
| World Model | Somabrain kernel integration | Manual calls | ⚠️ MEDIUM |
| Replay Buffer | Persistent with transitions | Outbox only | ❌ HIGH |
| Reward Model | Success + latency + safety | Basic telemetry | ❌ HIGH |
| RL Trainer | Background training service | None | ❌ CRITICAL |

### Requirement 67: Dynamic Tool Registry

**User Story:** As a system maintainer, I want a dynamic Tool Registry with hook methods, so that tools can be registered, discovered, and executed uniformly.

#### Acceptance Criteria

1. WHEN a tool is registered THEN the System SHALL store it in `ToolRegistry` with name, schema, and executor
2. WHEN `get_tool(name)` is called THEN the System SHALL return the tool executor or raise `ToolNotFoundError`
3. WHEN a tool is executed THEN the System SHALL call `before_execution()`, `execute()`, and `after_execution()` hooks
4. WHEN tools are listed THEN the System SHALL return all registered tools with their schemas
5. WHEN a tool is disabled THEN the System SHALL remove it from the registry and emit `tool_disabled` event

### Requirement 68: State Encoder Module

**User Story:** As a system maintainer, I want a State Encoder that converts conversation context to embeddings, so that the RL system can process state representations.

#### Acceptance Criteria

1. WHEN `StateEncoder.encode()` is called THEN the System SHALL use sentence-transformers to generate embeddings
2. WHEN encoding user text THEN the System SHALL combine with memory snapshot (top 5 values)
3. WHEN encoding is performed THEN the System SHALL truncate to max 128 tokens
4. WHEN the encoder is initialized THEN the System SHALL load `all-MiniLM-L6-v2` model by default
5. WHEN encoding fails THEN the System SHALL return a zero vector and log warning

### Requirement 69: Policy Network

**User Story:** As a system maintainer, I want a Policy Network that selects actions based on state, so that tool selection is learned from experience.

#### Acceptance Criteria

1. WHEN `PolicyNet.forward()` is called THEN the System SHALL return action probabilities via softmax
2. WHEN the network is initialized THEN the System SHALL create MLP with configurable hidden size (default 128)
3. WHEN action is sampled THEN the System SHALL use the probability distribution for exploration
4. WHEN policy is updated THEN the System SHALL use policy gradient with advantage
5. WHEN policy loss is computed THEN the System SHALL emit `policy_loss` Prometheus metric

### Requirement 70: Q-Network (Value Function)

**User Story:** As a system maintainer, I want a Dueling Q-Network for value estimation, so that action values can be learned for better decision making.

#### Acceptance Criteria

1. WHEN `DuelingQNet.forward()` is called THEN the System SHALL return Q-values using V(s) + A(s,a) - mean(A)
2. WHEN the network is initialized THEN the System SHALL create feature, value, and advantage heads
3. WHEN Q-values are computed THEN the System SHALL use the dueling architecture for stability
4. WHEN Q-loss is computed THEN the System SHALL use MSE between predicted and target Q-values
5. WHEN Q-loss is computed THEN the System SHALL emit `q_loss` Prometheus metric

### Requirement 71: World Model Wrapper

**User Story:** As a system maintainer, I want a World Model that predicts next states using Somabrain kernels, so that the agent can plan ahead.

#### Acceptance Criteria

1. WHEN `WorldModel.predict_next()` is called THEN the System SHALL use Somabrain `graph_heat` kernel
2. WHEN prediction is refined THEN the System SHALL apply `lanczos_chebyshev` approximation
3. WHEN Somabrain is unavailable THEN the System SHALL return the input state unchanged
4. WHEN prediction is performed THEN the System SHALL record `world_model_latency_seconds` histogram
5. WHEN prediction fails THEN the System SHALL log error and return fallback state

### Requirement 72: Replay Buffer

**User Story:** As a system maintainer, I want a Replay Buffer that stores transitions, so that the RL trainer can sample experience for learning.

#### Acceptance Criteria

1. WHEN a transition is pushed THEN the System SHALL store `(state, action, reward, next_state, done)`
2. WHEN buffer exceeds capacity THEN the System SHALL remove oldest transitions (FIFO)
3. WHEN `sample(batch_size)` is called THEN the System SHALL return random batch of transitions
4. WHEN buffer is persisted THEN the System SHALL write to JSON file every 1000 transitions
5. WHEN buffer is loaded THEN the System SHALL restore from JSON file on startup

### Requirement 73: Reward Model

**User Story:** As a system maintainer, I want a Reward Model that combines success, latency, and safety, so that the agent optimizes for multiple objectives.

#### Acceptance Criteria

1. WHEN `compute_reward()` is called THEN the System SHALL return `base + latency_penalty + safety_bonus`
2. WHEN action succeeds THEN the System SHALL use base reward of +1.0
3. WHEN action fails THEN the System SHALL use base reward of -1.0
4. WHEN latency is high THEN the System SHALL apply penalty of `-0.001 * latency_ms`
5. WHEN safety score is provided THEN the System SHALL apply bonus of `+0.5 * safety_score`

### Requirement 74: RL Trainer Service

**User Story:** As a system maintainer, I want an RL Trainer service that runs in the background, so that the policy and Q-network are continuously improved.

#### Acceptance Criteria

1. WHEN trainer starts THEN the System SHALL load policy, Q-network, and replay buffer
2. WHEN training step runs THEN the System SHALL sample batch of 64 transitions
3. WHEN Q-target is computed THEN the System SHALL use `reward + gamma * max(Q_next) * (1 - done)`
4. WHEN policy is updated THEN the System SHALL use advantage-weighted policy gradient
5. WHEN training completes THEN the System SHALL emit `avg_reward` Prometheus gauge

### Requirement 75: RL Feature Flag

**User Story:** As a system maintainer, I want an RL feature flag, so that RL can be enabled/disabled without code changes.

#### Acceptance Criteria

1. WHEN `RL_ENABLED=true` THEN the System SHALL use PolicyNet for tool selection
2. WHEN `RL_ENABLED=false` THEN the System SHALL use rule-based tool selection
3. WHEN RL is enabled THEN the System SHALL start the RL trainer service
4. WHEN RL is disabled THEN the System SHALL stop the RL trainer service
5. WHEN feature flag changes THEN the System SHALL log the transition and emit event

### Requirement 76: RL Safety Constraints

**User Story:** As a system maintainer, I want RL safety constraints via OPA, so that unsafe actions are blocked regardless of policy output.

#### Acceptance Criteria

1. WHEN action is selected THEN the System SHALL evaluate OPA policy for `rl.action` permission
2. WHEN safety_score < 0.7 THEN the System SHALL reject the action and select next-best
3. WHEN OPA denies action THEN the System SHALL log reason and increment `rl_blocked_actions_total`
4. WHEN all actions are blocked THEN the System SHALL fall back to safe default action
5. WHEN safety violation occurs THEN the System SHALL apply negative reward of -2.0

### Requirement 77: RL Observability

**User Story:** As a system maintainer, I want comprehensive RL observability, so that training progress and agent behavior are fully monitored.

#### Acceptance Criteria

1. WHEN policy loss is computed THEN the System SHALL emit `rl_policy_loss` Prometheus gauge
2. WHEN Q-loss is computed THEN the System SHALL emit `rl_q_loss` Prometheus gauge
3. WHEN reward is computed THEN the System SHALL emit `rl_avg_reward` Prometheus gauge
4. WHEN action is selected THEN the System SHALL emit `rl_action_selected` counter with action label
5. WHEN training epoch completes THEN the System SHALL emit `rl_training_epochs_total` counter

### Requirement 78: Tool Prompt Templates

**User Story:** As a system maintainer, I want tool prompt templates aligned with SomaAgent01 format, so that LLM tool requests are consistent.

#### Acceptance Criteria

1. WHEN tool prompts are generated THEN the System SHALL use `agent.system.tool.{name}.md` format
2. WHEN tool schema is defined THEN the System SHALL include JSON schema in prompt
3. WHEN tool is called THEN the System SHALL parse JSON response matching schema
4. WHEN tool response is invalid THEN the System SHALL retry with clarification prompt
5. WHEN tool prompts are updated THEN the System SHALL reload without restart

---

## Requirements Summary (Final)

**Total Requirements: 78**

| Category | Requirements | Count |
|----------|--------------|-------|
| persist_chat Cleanup | 1-2 | 2 |
| Celery Architecture | 3-6, 20-27 | 12 |
| Settings Consolidation | 8-10 | 3 |
| UI-Backend Alignment | 13-14 | 2 |
| File Upload | 17-19 | 3 |
| Tool Architecture | 28-37 | 10 |
| Merged Architecture | 38-45 | 8 |
| Degradation Mode | 46-49 | 4 |
| Context Builder | 50-55 | 6 |
| Message & Conversation | 56-66 | 11 |
| SomaAgent01 RL/ML | 67-78 | 12 |
| Other | 7, 11-12, 15-16 | 5 |

### VIBE Compliance Score (Final)

| Metric | Current | Target |
|--------|---------|--------|
| persist_chat Cleanup | 0% | 100% |
| Settings Consolidation | 30% | 100% |
| File-Based Removal | 40% | 100% |
| Context Builder | 85% | 100% |
| Degradation Mode | 75% | 100% |
| Tool Architecture | 60% | 100% |
| Message/Conversation | 20% | 100% |
| RL/ML Features | 0% | 100% |
| **Overall** | **~40%** | **100%** |

### Implementation Roadmap Summary

| Milestone | Description | Effort |
|-----------|-------------|--------|
| M0 | Repo hygiene, persist_chat cleanup | 1 day |
| M1 | Tool Registry integration | 2 days |
| M2 | State Encoder & Policy | 2 days |
| M3 | Q-Network & Reward | 2 days |
| M4 | Replay Buffer | 1 day |
| M5 | World Model Wrapper | 3 days |
| M6 | RL Trainer Service | 3 days |
| M7 | Observability | 1 day |
| M8 | Testing & Safety | 2 days |
| M9 | Canary rollout | 2 days |
| **Total** | | **~19 days** |


---

## Agent Self-Tool-Management (CRITICAL - Agent Autonomy)

### Requirement 61: Agent Tool Removal

**User Story:** As a user, I want to tell the agent to remove a tool from its available tools, so that I can customize the agent's capabilities.

#### Acceptance Criteria

1. WHEN user says "remove tool X" THEN the Agent SHALL check OPA policy for `tool.disable` permission
2. WHEN OPA allows THEN the Agent SHALL call `ToolRegistry.disable(tool_name)`
3. WHEN tool is disabled THEN the System SHALL remove it from agent's tool prompt
4. WHEN tool is disabled THEN the System SHALL emit `tool_disabled` event with agent_id and tool_name
5. WHEN OPA denies THEN the Agent SHALL respond "I don't have permission to disable that tool"

### Requirement 62: Agent Tool Creation

**User Story:** As a user, I want the agent to create new tools by writing code, so that the agent can extend its own capabilities.

#### Acceptance Criteria

1. WHEN user requests a new tool THEN the Agent SHALL check OPA policy for `tool.create` permission
2. WHEN OPA allows THEN the Agent SHALL generate tool code following `python/tools/` template
3. WHEN tool code is generated THEN the Agent SHALL write to `python/tools/{tool_name}.py`
4. WHEN tool file is created THEN the Agent SHALL create matching prompt `prompts/agent.system.tool.{tool_name}.md`
5. WHEN tool is created THEN the Agent SHALL register with `ToolRegistry.register()`

### Requirement 63: Tool Auto-Discovery

**User Story:** As a system maintainer, I want tools auto-discovered from the filesystem, so that new tools are available without restart.

#### Acceptance Criteria

1. WHEN `ToolRegistry.scan()` is called THEN the System SHALL scan `python/tools/*.py` for Tool classes
2. WHEN a new tool file is detected THEN the System SHALL dynamically import and register
3. WHEN a tool file is removed THEN the System SHALL unregister the tool
4. WHEN auto-discovery runs THEN the System SHALL validate tool schema before registration
5. WHEN auto-discovery completes THEN the System SHALL emit `tools_discovered` event with count

### Requirement 64: Agent Tool Replacement

**User Story:** As a user, I want to tell the agent to replace one tool with another, so that I can swap implementations.

#### Acceptance Criteria

1. WHEN user says "replace tool X with Y" THEN the Agent SHALL check OPA for both `tool.disable` and `tool.create`
2. WHEN OPA allows THEN the Agent SHALL disable old tool and create new tool
3. WHEN replacement is atomic THEN the System SHALL ensure no gap in functionality
4. WHEN replacement fails THEN the System SHALL rollback and keep original tool
5. WHEN replacement succeeds THEN the Agent SHALL confirm "I've replaced X with Y"

### Requirement 65: Tool Permission Boundaries

**User Story:** As a security administrator, I want OPA policies to control which tools agents can create/modify, so that dangerous tools are prevented.

#### Acceptance Criteria

1. WHEN agent attempts `tool.create` THEN OPA SHALL check against allowed tool categories
2. WHEN agent attempts to create tool with `code_execution` THEN OPA SHALL require elevated permission
3. WHEN agent attempts to create tool with `network_access` THEN OPA SHALL require elevated permission
4. WHEN agent attempts to create tool with `file_system` THEN OPA SHALL require elevated permission
5. WHEN tool creation is denied THEN the System SHALL log security event with reason

### Requirement 66: Tool Code Validation

**User Story:** As a system maintainer, I want agent-generated tool code validated before execution, so that malicious code is prevented.

#### Acceptance Criteria

1. WHEN agent generates tool code THEN the System SHALL run static analysis (AST check)
2. WHEN code contains `eval()`, `exec()`, or `__import__` THEN the System SHALL reject
3. WHEN code contains network calls THEN the System SHALL verify against allowed domains
4. WHEN code passes validation THEN the System SHALL sandbox-test before registration
5. WHEN validation fails THEN the System SHALL return specific error to agent

### Requirement 67: Tool Prompt Auto-Generation

**User Story:** As a system maintainer, I want tool prompts auto-generated from schemas, so that new tools are immediately usable.

#### Acceptance Criteria

1. WHEN a tool is registered without prompt file THEN the System SHALL generate from `input_schema()`
2. WHEN prompt is generated THEN the System SHALL include tool name, description, parameters
3. WHEN prompt is generated THEN the System SHALL follow `agent.system.tool.*.md` format
4. WHEN tool schema changes THEN the System SHALL regenerate prompt
5. WHEN prompt generation fails THEN the System SHALL use minimal fallback prompt

### Requirement 68: Agent Tool Listing

**User Story:** As a user, I want to ask the agent what tools it has available, so that I know its capabilities.

#### Acceptance Criteria

1. WHEN user asks "what tools do you have" THEN the Agent SHALL list all enabled tools
2. WHEN listing tools THEN the Agent SHALL include name, description, and status
3. WHEN listing tools THEN the Agent SHALL indicate which are built-in vs agent-created
4. WHEN listing tools THEN the Agent SHALL show permission level required
5. WHEN no tools are available THEN the Agent SHALL explain why

---

## Requirements Summary (FINAL)

**Total Requirements: 68**

| Category | Requirements | Count |
|----------|--------------|-------|
| persist_chat Cleanup | 1-2 | 2 |
| Celery Architecture | 3-6, 20-27 | 12 |
| Settings Consolidation | 8-10 | 3 |
| UI-Backend Alignment | 13-14 | 2 |
| File Upload | 17-19 | 3 |
| Tool Architecture | 28-37 | 10 |
| Merged Architecture | 38-45 | 8 |
| Degradation Mode | 46-49 | 4 |
| Context Builder | 50-51 | 2 |
| Message & Conversation | 52-59 | 8 |
| Enhanced Tool Registry | 60 | 1 |
| **Agent Self-Tool-Management** | **61-68** | **8** |
| Other | 7, 11-12, 15-16 | 5 |

### Agent Tool Autonomy Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    AGENT TOOL SELF-MANAGEMENT                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  USER: "Remove search_engine tool"                              │
│     │                                                            │
│     ▼                                                            │
│  AGENT: Check OPA policy (tool.disable)                         │
│     │                                                            │
│     ├── DENIED → "I don't have permission"                      │
│     │                                                            │
│     └── ALLOWED → ToolRegistry.disable("search_engine")         │
│                   │                                              │
│                   └── Tool removed, prompt updated               │
│                                                                  │
│  USER: "Create a DuckDuckGo search tool"                        │
│     │                                                            │
│     ▼                                                            │
│  AGENT: Check OPA policy (tool.create + network_access)         │
│     │                                                            │
│     ├── DENIED → "I need elevated permission for network tools" │
│     │                                                            │
│     └── ALLOWED → Generate code → Validate → Write file         │
│                   │                                              │
│                   └── ToolRegistry.register() → Auto-discovered │
│                                                                  │
│  USER: "What tools do you have?"                                │
│     │                                                            │
│     ▼                                                            │
│  AGENT: List all enabled tools with descriptions                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### VIBE Compliance Score (Final)

| Metric | Current | Target |
|--------|---------|--------|
| persist_chat Cleanup | 0% | 100% |
| Settings Consolidation | 30% | 100% |
| Context Builder | 85% | 100% |
| Degradation Mode | 75% | 100% |
| Tool Architecture | 60% | 100% |
| Message/Conversation | 20% | 100% |
| Agent Tool Autonomy | 0% | 100% |
| **Overall** | **~40%** | **100%** |


---

## Centralized Architecture Infrastructure (MANDATORY)

### All Features MUST Use This Infrastructure:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SOMAAGENT01 CENTRALIZED ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   Gateway   │    │ Conversation│    │    Tool     │    │   Memory    │  │
│  │   Service   │───▶│   Worker    │───▶│  Executor   │───▶│    Sync     │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│         │                  │                  │                  │          │
│         ▼                  ▼                  ▼                  ▼          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         KAFKA EVENT BUS                              │   │
│  │  Topics: conversation.*, tool.*, memory.*, agent.*, audit.*         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│         │                  │                  │                  │          │
│         ▼                  ▼                  ▼                  ▼          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │ PostgreSQL  │    │    Redis    │    │     OPA     │    │  SomaBrain  │  │
│  │  Sessions   │    │    Cache    │    │   Policy    │    │   Memory    │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│         │                  │                  │                  │          │
│         └──────────────────┴──────────────────┴──────────────────┘          │
│                                    │                                         │
│                                    ▼                                         │
│                         ┌─────────────────────┐                             │
│                         │    Prometheus +     │                             │
│                         │    Observability    │                             │
│                         └─────────────────────┘                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Requirement 69: Centralized Event Bus for Tool Operations

**User Story:** As a system maintainer, I want all tool operations to go through Kafka, so that tool events are auditable and observable.

#### Acceptance Criteria

1. WHEN a tool is created THEN the System SHALL publish to `agent.tool.created` Kafka topic
2. WHEN a tool is disabled THEN the System SHALL publish to `agent.tool.disabled` Kafka topic
3. WHEN a tool is executed THEN the System SHALL publish to `tool.execution.started` and `tool.execution.completed`
4. WHEN tool events are published THEN the System SHALL include tenant_id, agent_id, tool_name, timestamp
5. WHEN Kafka is unavailable THEN the System SHALL queue events in PostgreSQL outbox

### Requirement 70: PostgreSQL Tool Registry Store

**User Story:** As a system maintainer, I want tool registry persisted in PostgreSQL, so that tool state survives restarts.

#### Acceptance Criteria

1. WHEN a tool is registered THEN the System SHALL store in `tool_catalog` table
2. WHEN a tool is agent-created THEN the System SHALL store code in `agent_tools` table with agent_id
3. WHEN tool state changes THEN the System SHALL update `tool_catalog.enabled` and `updated_at`
4. WHEN tool is queried THEN the System SHALL check `tenant_tool_flags` for tenant-specific overrides
5. WHEN PostgreSQL schema is missing THEN the System SHALL auto-migrate on startup

### Requirement 71: Redis Tool Cache

**User Story:** As a system maintainer, I want tool metadata cached in Redis, so that tool lookups are fast.

#### Acceptance Criteria

1. WHEN a tool is registered THEN the System SHALL cache schema in Redis with TTL 3600s
2. WHEN `get_tool()` is called THEN the System SHALL check Redis before PostgreSQL
3. WHEN tool is modified THEN the System SHALL invalidate Redis cache
4. WHEN Redis is unavailable THEN the System SHALL fall back to PostgreSQL
5. WHEN cache is populated THEN the System SHALL use tenant-prefixed keys

### Requirement 72: OPA Tool Policy Enforcement

**User Story:** As a system maintainer, I want all tool operations authorized via OPA, so that security is centralized.

#### Acceptance Criteria

1. WHEN agent attempts `tool.create` THEN the System SHALL call OPA with `{action: "tool.create", agent_id, tool_category}`
2. WHEN agent attempts `tool.disable` THEN the System SHALL call OPA with `{action: "tool.disable", agent_id, tool_name}`
3. WHEN agent attempts `tool.execute` THEN the System SHALL call OPA with `{action: "tool.execute", agent_id, tool_name, args}`
4. WHEN OPA denies THEN the System SHALL log to `audit.policy.denied` Kafka topic
5. WHEN OPA is unavailable THEN the System SHALL fail-closed (deny all)

### Requirement 73: SomaBrain Tool Learning

**User Story:** As a system maintainer, I want tool usage tracked in SomaBrain, so that the agent learns from tool effectiveness.

#### Acceptance Criteria

1. WHEN a tool execution completes THEN the System SHALL send feedback to SomaBrain `/context/feedback`
2. WHEN feedback is sent THEN the System SHALL include tool_name, success, latency, user_satisfaction
3. WHEN agent creates a tool THEN the System SHALL store tool description in SomaBrain for recall
4. WHEN agent selects tools THEN the System SHALL query SomaBrain for tool effectiveness history
5. WHEN SomaBrain is unavailable THEN the System SHALL queue feedback for later delivery

### Requirement 74: Prometheus Tool Metrics

**User Story:** As a system maintainer, I want comprehensive tool metrics, so that tool usage is fully observable.

#### Acceptance Criteria

1. WHEN a tool is created THEN the System SHALL increment `agent_tools_created_total{agent_id, tool_name}`
2. WHEN a tool is disabled THEN the System SHALL increment `agent_tools_disabled_total{agent_id, tool_name}`
3. WHEN a tool is executed THEN the System SHALL record `tool_execution_duration_seconds{tool_name}`
4. WHEN a tool fails THEN the System SHALL increment `tool_execution_errors_total{tool_name, error_type}`
5. WHEN tool policy is denied THEN the System SHALL increment `tool_policy_denied_total{agent_id, action}`

### Requirement 75: Conversation Service Integration

**User Story:** As a system maintainer, I want conversation worker to use centralized tool registry, so that tool access is consistent.

#### Acceptance Criteria

1. WHEN conversation worker starts THEN the System SHALL load tools from `ToolCatalogStore`
2. WHEN agent requests tool THEN the System SHALL check `ToolRegistry.get_tool()` with OPA validation
3. WHEN tool execution is needed THEN the System SHALL route to `ToolExecutor` service via Kafka
4. WHEN tool result returns THEN the System SHALL merge into conversation via `Conversation` class
5. WHEN tool is unavailable THEN the System SHALL return structured error to agent

### Requirement 76: Agent Tool Sandbox

**User Story:** As a system maintainer, I want agent-created tools sandboxed, so that malicious code cannot harm the system.

#### Acceptance Criteria

1. WHEN agent-created tool executes THEN the System SHALL run in isolated Docker container
2. WHEN sandbox executes THEN the System SHALL limit CPU (1 core), memory (512MB), time (30s)
3. WHEN sandbox has network access THEN the System SHALL use allowlist of domains
4. WHEN sandbox writes files THEN the System SHALL use ephemeral volume, deleted after execution
5. WHEN sandbox violates limits THEN the System SHALL kill process and return timeout error

### Requirement 77: Audit Trail for Tool Operations

**User Story:** As a security administrator, I want complete audit trail for tool operations, so that all changes are traceable.

#### Acceptance Criteria

1. WHEN a tool is created THEN the System SHALL log to `audit.tool.created` with full code hash
2. WHEN a tool is disabled THEN the System SHALL log to `audit.tool.disabled` with reason
3. WHEN a tool is executed THEN the System SHALL log to `audit.tool.executed` with args (sanitized)
4. WHEN audit events are stored THEN the System SHALL use PostgreSQL `audit_log` table
5. WHEN audit is queried THEN the System SHALL support filtering by agent_id, tool_name, date range

---

## Infrastructure Module Requirements (CREATE IF MISSING)

### Requirement 78: ToolCatalogStore Module

**User Story:** As a system maintainer, I want a canonical ToolCatalogStore module, so that tool persistence is centralized.

#### Acceptance Criteria

1. IF `services/common/tool_catalog.py` does not exist THEN the System SHALL create it
2. WHEN ToolCatalogStore is created THEN the System SHALL implement `register()`, `disable()`, `get()`, `list()`
3. WHEN ToolCatalogStore is created THEN the System SHALL use PostgreSQL for persistence
4. WHEN ToolCatalogStore is created THEN the System SHALL use Redis for caching
5. WHEN ToolCatalogStore is created THEN the System SHALL emit Kafka events for all mutations

### Requirement 79: AgentToolGenerator Module

**User Story:** As a system maintainer, I want a canonical AgentToolGenerator module, so that agent tool creation is standardized.

#### Acceptance Criteria

1. IF `services/common/agent_tool_generator.py` does not exist THEN the System SHALL create it
2. WHEN AgentToolGenerator is created THEN the System SHALL implement `generate_code()`, `validate_code()`, `write_tool()`
3. WHEN AgentToolGenerator is created THEN the System SHALL use AST for code validation
4. WHEN AgentToolGenerator is created THEN the System SHALL generate matching prompt file
5. WHEN AgentToolGenerator is created THEN the System SHALL integrate with ToolCatalogStore

### Requirement 80: ToolSandboxManager Module

**User Story:** As a system maintainer, I want a canonical ToolSandboxManager module, so that agent tools are safely executed.

#### Acceptance Criteria

1. IF `services/tool_executor/sandbox_manager.py` does not exist THEN the System SHALL create it
2. WHEN ToolSandboxManager is created THEN the System SHALL implement `create_sandbox()`, `execute()`, `cleanup()`
3. WHEN ToolSandboxManager is created THEN the System SHALL use Docker for isolation
4. WHEN ToolSandboxManager is created THEN the System SHALL enforce resource limits
5. WHEN ToolSandboxManager is created THEN the System SHALL integrate with OPA for network allowlist

### Requirement 81: ConversationManager Module

**User Story:** As a system maintainer, I want a canonical ConversationManager module, so that conversation state is centralized.

#### Acceptance Criteria

1. IF `services/conversation_worker/conversation_manager.py` does not exist THEN the System SHALL create it
2. WHEN ConversationManager is created THEN the System SHALL implement `Conversation` class with turn tracking
3. WHEN ConversationManager is created THEN the System SHALL use PostgreSQL for persistence
4. WHEN ConversationManager is created THEN the System SHALL use Redis for active session cache
5. WHEN ConversationManager is created THEN the System SHALL integrate with ContextBuilder

---

## FINAL Requirements Summary

**Total Requirements: 81**

| Category | Requirements | Count |
|----------|--------------|-------|
| persist_chat Cleanup | 1-2 | 2 |
| Celery Architecture | 3-6, 20-27 | 12 |
| Settings Consolidation | 8-10 | 3 |
| UI-Backend Alignment | 13-14 | 2 |
| File Upload | 17-19 | 3 |
| Tool Architecture | 28-37 | 10 |
| Merged Architecture | 38-45 | 8 |
| Degradation Mode | 46-49 | 4 |
| Context Builder | 50-51 | 2 |
| Message & Conversation | 52-59 | 8 |
| Enhanced Tool Registry | 60 | 1 |
| Agent Self-Tool-Management | 61-68 | 8 |
| **Centralized Infrastructure** | **69-77** | **9** |
| **Module Creation** | **78-81** | **4** |
| Other | 7, 11-12, 15-16 | 5 |

### Infrastructure Checklist

| Module | Location | Status |
|--------|----------|--------|
| ToolCatalogStore | `services/common/tool_catalog.py` | ✅ EXISTS |
| AgentToolGenerator | `services/common/agent_tool_generator.py` | ❌ CREATE |
| ToolSandboxManager | `services/tool_executor/sandbox_manager.py` | ⚠️ VERIFY |
| ConversationManager | `services/conversation_worker/conversation_manager.py` | ❌ CREATE |
| PolicyClient | `services/common/policy_client.py` | ✅ EXISTS |
| KafkaEventBus | `services/common/event_bus.py` | ✅ EXISTS |
| PostgresSessionStore | `services/common/session_repository.py` | ✅ EXISTS |
| RedisSessionCache | `services/common/session_repository.py` | ✅ EXISTS |
| ContextBuilder | `python/somaagent/context_builder.py` | ✅ EXISTS |
| SomaBrainClient | `python/integrations/somabrain_client.py` | ✅ EXISTS |


---

## Prompt Repository Migration (FILE → PostgreSQL)

### Current State Analysis

The current system loads prompts from **FILES**:
```python
# agent.py - CURRENT (FILE-BASED - VIOLATION)
def parse_prompt(self, _prompt_file: str, **kwargs):
    dirs = [files.get_abs_path("prompts")]
    prompt = files.parse_file(_prompt_file, _directories=dirs, **kwargs)
    return prompt
```

This violates VIBE rules:
- ❌ File-based storage
- ❌ No versioning
- ❌ No tenant isolation
- ❌ No audit trail
- ❌ Requires restart for changes

### Requirement 69: PostgreSQL Prompt Repository

**User Story:** As a system maintainer, I want prompts stored in PostgreSQL, so that they are versioned, tenant-isolated, and changeable without restart.

#### Acceptance Criteria

1. WHEN a prompt is stored THEN the System SHALL use `prompt_repository` PostgreSQL table
2. WHEN a prompt is retrieved THEN the System SHALL use `PromptRepository.get(name, tenant_id)`
3. WHEN a prompt is updated THEN the System SHALL create new version, not overwrite
4. WHEN prompt history is needed THEN the System SHALL return all versions with timestamps
5. WHEN prompts are migrated THEN the System SHALL import all `prompts/*.md` files to PostgreSQL

### Requirement 70: Prompt Repository Schema

**User Story:** As a system maintainer, I want a proper schema for prompts, so that they are structured and queryable.

#### Acceptance Criteria

1. WHEN `prompt_repository` table is created THEN the System SHALL include: id, name, content, tenant_id, version, created_at, created_by
2. WHEN prompt is tenant-specific THEN the System SHALL store with tenant_id
3. WHEN prompt is global THEN the System SHALL store with tenant_id = NULL
4. WHEN prompt is retrieved THEN the System SHALL check tenant-specific first, then global fallback
5. WHEN prompt schema is defined THEN the System SHALL include JSONB metadata field

### Requirement 71: Prompt Repository API

**User Story:** As a system maintainer, I want a PromptRepository class, so that prompts are accessed uniformly.

#### Acceptance Criteria

1. WHEN `PromptRepository.get(name)` is called THEN the System SHALL return latest version
2. WHEN `PromptRepository.get(name, version=N)` is called THEN the System SHALL return specific version
3. WHEN `PromptRepository.set(name, content)` is called THEN the System SHALL create new version
4. WHEN `PromptRepository.list()` is called THEN the System SHALL return all prompt names
5. WHEN `PromptRepository.history(name)` is called THEN the System SHALL return all versions

### Requirement 72: Agent Prompt Loading Migration

**User Story:** As a system maintainer, I want agent.py to load prompts from PostgreSQL, so that file-based loading is eliminated.

#### Acceptance Criteria

1. WHEN `agent.parse_prompt()` is called THEN the System SHALL use `PromptRepository.get()`
2. WHEN `agent.read_prompt()` is called THEN the System SHALL use `PromptRepository.get()`
3. WHEN prompt is not in PostgreSQL THEN the System SHALL NOT fall back to files (fail explicitly)
4. WHEN prompt is loaded THEN the System SHALL cache in Redis for performance
5. WHEN prompt cache expires THEN the System SHALL reload from PostgreSQL

### Requirement 73: Tool Prompt Repository Integration

**User Story:** As a system maintainer, I want tool prompts stored in PostgreSQL, so that agent-created tools have persistent prompts.

#### Acceptance Criteria

1. WHEN agent creates a tool THEN the System SHALL store prompt in `prompt_repository` with name `agent.system.tool.{tool_name}.md`
2. WHEN tool prompt is generated THEN the System SHALL use `PromptRepository.set()`
3. WHEN tool is disabled THEN the System SHALL mark prompt as inactive (not delete)
4. WHEN tool prompt is updated THEN the System SHALL create new version
5. WHEN tool prompts are listed THEN the System SHALL filter by `agent.system.tool.*` pattern

### Requirement 74: Prompt Template Variables

**User Story:** As a system maintainer, I want prompt templates to support variables, so that dynamic content is injected.

#### Acceptance Criteria

1. WHEN prompt contains `{{variable}}` THEN the System SHALL replace with provided value
2. WHEN prompt contains `{{tools}}` THEN the System SHALL inject enabled tool list
3. WHEN prompt contains `{{memories}}` THEN the System SHALL inject relevant memories
4. WHEN prompt contains `{{datetime}}` THEN the System SHALL inject current datetime
5. WHEN variable is missing THEN the System SHALL raise `PromptVariableError`

### Requirement 75: Prompt Migration Script

**User Story:** As a system maintainer, I want a migration script, so that existing file prompts are imported to PostgreSQL.

#### Acceptance Criteria

1. WHEN migration runs THEN the System SHALL scan `prompts/*.md` files
2. WHEN file is found THEN the System SHALL insert into `prompt_repository` with version=1
3. WHEN migration completes THEN the System SHALL log count of migrated prompts
4. WHEN migration is re-run THEN the System SHALL skip existing prompts (idempotent)
5. WHEN migration fails THEN the System SHALL rollback and report errors

---

## Centralized Architecture Requirements

### Requirement 76: Single Source of Truth for All Configuration

**User Story:** As a system maintainer, I want ALL configuration in PostgreSQL, so that there is a single source of truth.

#### Acceptance Criteria

1. WHEN prompts are needed THEN the System SHALL use `PromptRepository` (PostgreSQL)
2. WHEN tools are needed THEN the System SHALL use `ToolCatalogStore` (PostgreSQL)
3. WHEN settings are needed THEN the System SHALL use `AgentSettingsStore` (PostgreSQL)
4. WHEN secrets are needed THEN the System SHALL use `UnifiedSecretManager` (Vault)
5. WHEN ANY file-based config is detected THEN the System SHALL log deprecation warning

### Requirement 77: No File-Based Storage Rule

**User Story:** As a system maintainer, I want NO file-based storage for runtime data, so that the system is stateless and scalable.

#### Acceptance Criteria

1. WHEN prompts are stored THEN the System SHALL NOT use filesystem
2. WHEN tools are stored THEN the System SHALL NOT use filesystem
3. WHEN sessions are stored THEN the System SHALL NOT use filesystem
4. WHEN attachments are stored THEN the System SHALL NOT use filesystem
5. WHEN ANY file write is attempted for runtime data THEN the System SHALL raise `FileStorageViolationError`

---

## Requirements Summary (FINAL)

**Total Requirements: 77**

| Category | Requirements | Count |
|----------|--------------|-------|
| persist_chat Cleanup | 1-2 | 2 |
| Celery Architecture | 3-6, 20-27 | 12 |
| Settings Consolidation | 8-10 | 3 |
| UI-Backend Alignment | 13-14 | 2 |
| File Upload | 17-19 | 3 |
| Tool Architecture | 28-37 | 10 |
| Merged Architecture | 38-45 | 8 |
| Degradation Mode | 46-49 | 4 |
| Context Builder | 50-51 | 2 |
| Message & Conversation | 52-59 | 8 |
| Enhanced Tool Registry | 60 | 1 |
| Agent Self-Tool-Management | 61-68 | 8 |
| **Prompt Repository (NEW)** | **69-75** | **7** |
| **Centralized Architecture** | **76-77** | **2** |
| Other | 7, 11-12, 15-16 | 5 |

### Centralized Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                 SOMAAGENT01 CENTRALIZED ARCHITECTURE            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Agent     │  │   Gateway   │  │   Worker    │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                      │
│         └────────────────┼────────────────┘                      │
│                          │                                       │
│                          ▼                                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    CANONICAL STORES                        │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │                                                            │  │
│  │  ┌─────────────────┐  ┌─────────────────┐                 │  │
│  │  │ PromptRepository│  │ ToolCatalogStore│                 │  │
│  │  │   (PostgreSQL)  │  │   (PostgreSQL)  │                 │  │
│  │  └─────────────────┘  └─────────────────┘                 │  │
│  │                                                            │  │
│  │  ┌─────────────────┐  ┌─────────────────┐                 │  │
│  │  │AgentSettingsStore│ │PostgresSessionStore│              │  │
│  │  │   (PostgreSQL)  │  │   (PostgreSQL)  │                 │  │
│  │  └─────────────────┘  └─────────────────┘                 │  │
│  │                                                            │  │
│  │  ┌─────────────────┐  ┌─────────────────┐                 │  │
│  │  │UnifiedSecretMgr │  │  RedisCache     │                 │  │
│  │  │    (Vault)      │  │   (Redis)       │                 │  │
│  │  └─────────────────┘  └─────────────────┘                 │  │
│  │                                                            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ❌ NO FILE STORAGE FOR:                                        │
│     - Prompts (use PromptRepository)                            │
│     - Tools (use ToolCatalogStore)                              │
│     - Sessions (use PostgresSessionStore)                       │
│     - Settings (use AgentSettingsStore)                         │
│     - Secrets (use UnifiedSecretManager)                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Additional Requirements – Dynamic Task Registry & SomaBrain Feedback (NEW)

- **Registry Creation:** The system SHALL create a Postgres-backed `task_registry` with fields `{name, module_path, callable, queue, limits, schema, enabled, tenant_scope, artifact_hash, created_by, created_at}` and Redis cache for fast lookup.
- **Dynamic Load/Reload:** Celery workers SHALL load tasks from the registry at start and on a reload signal (Redis pub/sub or Celery control), registering tasks via `app.register_task()`; tasks outside the registry SHALL NOT be accepted.
- **Policy Enforcement:** All registry operations and executions SHALL be gated by OPA actions `task.view`, `task.execute`, `task.enable`; denials SHALL fail closed and be audited.
- **Schema & Safety:** Each task SHALL include JSON Schema for args, per-task rate limits, and Redis SETNX dedupe; artifact hashes SHALL be verified before load; only signed artifacts from a trusted plugins path/object store SHALL be allowed.
- **Feedback to SomaBrain:** After each task execution, the system SHALL send a standardized `task_feedback` payload `{task_name, session_id, persona_id, success, latency_ms, error_type, score, tags}` to SomaBrain; if SomaBrain is DOWN, feedback SHALL be queued (outbox/DLQ) for retry.
- **Planning Priors:** When planning tasks, the system SHALL fetch prior task patterns/memories from SomaBrain and expose them to the planner/LLM; task memories SHALL be tagged by tenant/persona/task for recall.
- **Observability:** Dynamic tasks SHALL emit Prometheus metrics (counters/histograms with tenant/persona labels) and appear in Flower; audit events SHALL be published for register/execute/deny paths.

## Additional Requirements – SomaBrain-First Context & Auto-Summary (NEW)

- **Recall First:** ContextBuilder SHALL attempt SomaBrain recall on every build; on DEGRADE use reduced k; on DOWN skip recall and queue retry.
- **Auto Summary:** The system SHALL summarize long histories and retrieved snippets into concise “session summaries,” store them in SomaBrain with tags `{tenant, persona, session, task}`, and reuse them to reduce token load.
- **Tagging:** All stored events/summaries SHALL include SomaBrain coordinates and tags (tenant, persona, task/tool) in session events for later deep-link recall.
- **Planning Priors:** Before generating plans/tool choices, the system SHALL fetch prior task/tool patterns from SomaBrain and inject them into planner prompts.
- **Feedback Standardization:** Tool executions SHALL send `tool_feedback` (same fields as task_feedback) to SomaBrain; failures SHALL enqueue for retry.
- **Policy Enrichment:** Policy inputs SHALL include SomaBrain risk/sensitivity signals when available; policy decisions SHALL fail closed on errors.
