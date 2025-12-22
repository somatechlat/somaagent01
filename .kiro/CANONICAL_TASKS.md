# SomaAgent01 — Canonical Task Tracker

**Document ID:** SA01-TASKS-CANONICAL-2025-12  
**Version:** 4.0  
**Date:** 2025-12-21  
**Status:** CANONICAL — Single Source of Truth

**Status Legend:** `[ ]` Not Started | `[/]` In Progress | `[x]` Completed

---

## Progress Summary

**Total Features Identified:** 250+  
**Completed:** ~90 (36%)  
**In Progress:** ~10 (4%)  
**Planned:** ~150 (60%)

---

## Phase 1: System Hardening & Architecture Fixes

### 1.1 Refactoring & Cleanup

- [ ] Move `degradation_monitor.py` to `services/common/`
- [ ] Integrate `DegradationMonitor` into `ConversationWorker`
- [ ] Remove `persist_chat` imports globally
- [ ] Consolidate all config usage to `src.core.config.cfg`

### 1.2 Security Implementation

- [ ] Add `slowapi` to implementation dependencies
- [ ] Implement Redis-backed rate limits on Upload endpoints
- [ ] Implement `OPAPolicyAdapter` and enforce checks in `ToolExecutor`
- [ ] Enforce ClamAV scanning on all file uploads (Quarantine flow)
- [ ] Finalize TUS Protocol (HEAD, DELETE, Expiry Cleaning)

---

## Phase 2: SomaBrain Integration

### 2.1 Core Cognitive Endpoints (HIGH Priority)

#### Task 2.1.1: Implement adaptation_reset() Method
**File**: `somaAgent01/python/integrations/soma_client.py`
- [ ] Add method to reset adaptation engine via `/context/adaptation/reset`
- [ ] Support `tenant_id`, `base_lr`, `reset_history` parameters
- [ ] Integration test against live SomaBrain

#### Task 2.1.2: Implement act() Method
**File**: `somaAgent01/python/integrations/soma_client.py`
- [ ] Add method for action execution via `/act`
- [ ] Support `task_key`, `context`, `max_steps`, `tenant_id` parameters
- [ ] Integration test against live SomaBrain

#### Task 2.1.3: Add reset_adaptation() to somabrain_integration.py
**File**: `somaAgent01/python/somaagent/somabrain_integration.py`
- [ ] Add high-level wrapper for adaptation reset
- [ ] Clear `agent.data["adaptation_state"]` on success
- [ ] Integration test passes

#### Task 2.1.4: Add execute_action() to somabrain_integration.py
**File**: `somaAgent01/python/somaagent/somabrain_integration.py`
- [ ] Add high-level wrapper for action execution
- [ ] Return action results with salience scores
- [ ] Integration test passes

### 2.2 Sleep Management (MEDIUM Priority)

#### Task 2.2.1: Implement util_sleep() Method
- [ ] Add method for `/api/util/sleep` endpoint
- [ ] Support `target_state`, `ttl_seconds`, `async_mode`, `trace_id`

#### Task 2.2.2: Implement brain_sleep_mode() Method
- [ ] Add method for `/api/brain/sleep_mode` endpoint
- [ ] Support all target states (active|light|deep|freeze)

#### Task 2.2.3: Implement sleep_status_all() Method (ADMIN MODE)
- [ ] Add method for `/sleep/status/all` endpoint
- [ ] Requires admin authentication

#### Task 2.2.4: Add transition_sleep_state() to somabrain_integration.py
- [ ] Add high-level wrapper for sleep state transitions
- [ ] Update `agent.data["sleep_state"]`

#### Task 2.2.5: Update cognitive.py Sleep Logic
- [ ] Use `brain_sleep_mode()` instead of `sleep_cycle()`
- [ ] Add state-based sleep management

### 2.3 Admin & Service Management (ADMIN MODE ONLY)

#### Task 2.3.1: Implement Admin Service Methods
- [ ] `list_services()` - GET `/admin/services`
- [ ] `get_service_status(name)` - GET `/admin/services/{name}`
- [ ] `start_service(name)` - POST `/admin/services/{name}/start`
- [ ] `stop_service(name)` - POST `/admin/services/{name}/stop`
- [ ] `restart_service(name)` - POST `/admin/services/{name}/restart`

#### Task 2.3.2: Implement Personality Management
- [ ] `set_personality(state)` - POST `/personality`

#### Task 2.3.3: Implement Memory Configuration Methods
- [ ] `get_memory_config()` - GET `/config/memory`
- [ ] `patch_memory_config(config)` - PATCH `/config/memory`

### 2.4 Cognitive Thread Management

#### Task 2.4.1: Implement Cognitive Thread Methods
- [ ] `create_thread(tenant_id, options)` - POST `/cognitive/thread`
- [ ] `get_next_option(tenant_id)` - GET `/cognitive/thread/next`
- [ ] `reset_thread(tenant_id)` - PUT `/cognitive/thread/reset`

### 2.5 Diagnostics & Feature Flags (ADMIN MODE ONLY)

#### Task 2.5.1: Implement Diagnostic Methods
- [ ] `micro_diag()` - GET `/micro/diag`
- [ ] `get_features()` - GET `/admin/features`
- [ ] `update_features(overrides)` - POST `/admin/features`

### 2.6 Integration Tests

#### Task 2.6.1: Create Integration Test Suite
**File**: `somaAgent01/tests/test_somabrain_integration.py`
- [ ] `test_adaptation_reset` - Verify reset clears state
- [ ] `test_act_execution` - Verify action execution with salience
- [ ] `test_sleep_state_transitions` - Verify all state transitions
- [ ] `test_admin_services` - Verify service management (ADMIN mode)
- [ ] `test_personality_management` - Verify personality state
- [ ] `test_memory_config` - Verify configuration management
- [ ] `test_cognitive_threads` - Verify thread lifecycle
- [ ] `test_diagnostics` - Verify diagnostic retrieval (ADMIN mode)

---

## Phase 3: WebUI Testing & Stability

### 3.1 End-to-End Testing (Playwright)

- [ ] `test_navigation.py`: Sidebar, Responsive Breakpoints
- [ ] `test_chat.py`: Send/Receive, Streaming, Stop Generation
- [ ] `test_settings.py`: Persistence, API Key toggles
- [ ] `test_uploads.py`: TUS simulation, Drag & Drop
- [ ] `test_sessions.py`: Create, Rename, Delete flows
- [ ] `test_a11y.py`: Axe-core scans on critical pages

---

## Phase 4: Capsule Marketplace

### 4.1 Marketplace Backend

- [ ] `GET /v1/capsules/registry` (List Public)
- [ ] `POST /v1/capsules/install/{id}`

### 4.2 Marketplace Frontend

- [ ] Build `features/capsules/store.js`
- [ ] Create Registry Grid Layout & Card Components
- [ ] Implement Install/Update flows with progress indication

---

## Phase 5: Memory & Intelligence

### 5.1 Memory Dashboard

- [ ] Wire `memory.store.js` to real `GET /v1/memory` endpoints
- [ ] Render Force-Directed Graph of memory nodes
- [ ] Subscribe to `memory.created` events for live updates

---

## Phase 6: Multimodal Capabilities Extension

**Feature Flag:** `SA01_ENABLE_multimodal_capabilities` (default: false)

### 6.1 Foundation & Data Model (Phase 1)

#### 6.1.1 Data Model & Schema
- [x] Create `multimodal_assets` table
- [x] Create `multimodal_capabilities` registry table
- [x] Create `multimodal_job_plans` table
- [x] Create `multimodal_executions` table
- [x] Create `asset_provenance` table
- [x] Migration scripts with rollback support

#### 6.1.2 Capability Registry
- [x] Implement `CapabilityRegistry` service
- [x] `find_candidates(modality, constraints)` method
- [x] `register(tool_id, provider, modalities, ...)` method
- [x] Register existing providers (OpenAI, Stability, Mermaid, PlantUML, Playwright)
- [x] Health/availability tracking per capability
- [ ] Periodic health checks (cron 60s)
- [ ] Circuit breaker integration

#### 6.1.3 Policy Graph Router
- [x] Implement `PolicyGraphRouter` service
- [x] Define deterministic provider ordering per modality
- [x] `route()` method with OPA integration
- [x] Budget/quota enforcement per modality
- [ ] Circuit breaker integration for multimodal providers

### 6.2 Asset Pipeline & Provenance (Phase 2)

#### 6.2.1 Asset Storage & Management
- [x] Create `AssetStore` service
- [x] PostgreSQL bytea storage (v1)
- [x] SHA256 checksum deduplication
- [ ] S3 integration
- [ ] Asset lifecycle management

#### 6.2.2 Provenance System
- [x] Create `ProvenanceRecorder` service
- [x] Redaction: prompts, params, PII
- [x] Quality gate tracking
- [ ] Provenance querying API
- [ ] Audit trail integration

### 6.3 Task Planning & Compilation (Phase 3)

#### 6.3.1 Task DSL & Plan Schema
- [x] Define JSON schema for Task DSL v1.0
- [x] Implement JobPlanner service
- [x] Implement ExecutionTracker service

#### 6.3.2 Intent & Plan Extraction
- [ ] Extend `ContextBuilder` with multimodal awareness
- [ ] Create multimodal prompt templates
- [ ] Implement LLM-based plan generator
- [ ] Plan validation and error handling

### 6.4 Execution Engine (Phase 4)

#### 6.4.1 Multimodal Provider Adapters
- [x] Create base provider interface
- [x] OpenAI DALL-E adapter
- [x] Mermaid diagram adapter
- [x] Playwright screenshot adapter
- [ ] Stability AI adapter
- [ ] PlantUML diagram adapter

#### 6.4.2 Execution Orchestration
- [x] Create `MultimodalExecutor` service
- [x] DAG execution with dependencies
- [ ] Integrate workflow dispatch via Temporal

### 6.5 Quality Gating (Phase 5)

- [ ] Implement `AssetCritic` service
- [ ] Define rubrics per asset type
- [ ] LLM-based quality evaluation
- [ ] Bounded retry logic (MAX_REWORK_ATTEMPTS=2)
- [ ] Track quality metrics and rework rates

### 6.6 Learning & Ranking (Phase 6)

- [ ] Extend SomaBrain schema for tool/model outcomes
- [ ] Record execution outcomes to SomaBrain
- [ ] Implement `PortfolioRanker` service
- [ ] Shadow mode implementation
- [ ] Active mode (opt-in via feature flag)

### 6.7 SRS Document Generation (Phase 7)

- [ ] Create `SRSComposer` service
- [ ] Support versioning and change tracking
- [ ] Generate markdown with embedded assets
- [ ] (Optional) PDF export with Pandoc
- [ ] Create asset bundles (ZIP with manifest)

### 6.8 API & UI Integration (Phase 8)

#### 6.8.1 Gateway API Extensions
- [ ] `GET /v1/multimodal/capabilities`
- [ ] `POST /v1/multimodal/jobs`
- [ ] `GET /v1/multimodal/jobs/{id}`
- [ ] `GET /v1/multimodal/assets/{id}`
- [ ] `GET /v1/multimodal/provenance/{asset_id}`

#### 6.8.2 UI/UX Integration
- [ ] Extend provider cards with modality tags
- [ ] Support per-request modality overrides
- [ ] Display asset previews in conversation
- [ ] Show provenance and quality feedback

### 6.9 Security & Governance (Phase 9)

- [ ] Create `policy/multimodal.rego`
- [ ] Add data classification constraints
- [ ] Provider allowlists by modality
- [ ] Cost/quota policies per modality
- [ ] (Optional) Asset encryption at rest
- [ ] Access control checks on asset retrieval

### 6.10 Observability & Metrics (Phase 10)

- [ ] Add Prometheus metrics for multimodal operations
- [ ] Add OpenTelemetry spans for multimodal jobs
- [ ] Monitor asset storage usage

### 6.11 Testing & Verification (Phase 11)

#### Unit Tests
- [ ] test_capability_registry.py
- [ ] test_policy_graph_router.py
- [ ] test_asset_store.py
- [ ] test_asset_critic.py
- [ ] test_portfolio_ranker.py
- [ ] test_plan_compiler.py

#### Integration Tests
- [ ] test_multimodal_providers.py
- [ ] test_multimodal_job.py
- [ ] test_soma_outcomes.py

#### E2E Golden Tests
- [ ] test_srs_generation.py
- [ ] test_provider_failures.py
- [ ] test_quality_gates.py

#### Chaos & Resilience Tests
- [ ] test_circuit_breaker.py
- [ ] test_resume.py

### 6.12 Documentation & Deployment (Phase 12)

- [x] Update SRS.md with multimodal architecture
- [x] Create MULTIMODAL_DESIGN.md
- [ ] Document capability registry format
- [ ] Document plan DSL schema
- [ ] Add runbook for operations
- [ ] Define environment variables
- [ ] Create deployment manifests
- [ ] Add feature flags for phased rollout

---

## Phase 7: Temporal Migration

- [ ] Add Temporal services to compose/helm (HA-ready layout)
- [ ] Port conversation/tool/A2A/maintenance flows to Temporal workflows
- [ ] Expose gateway Temporal workflow start/describe/terminate endpoints
- [ ] Update degradation monitor and health checks to include Temporal
- [ ] Remove legacy task codepaths/tests; add Temporal workflow tests

---

## Phase 8: Observability (Prometheus-Only)

- [ ] Expose `/metrics` on all services and Temporal workers
- [ ] Add Temporal/Kafka/Postgres exporters; define scrape jobs
- [ ] Add service-level histograms/counters for latency, errors, queue lag
- [ ] Wire OpenTelemetry propagation; optional OTLP export guarded by env flag
- [ ] Provide Prometheus alert rules for gateway errors, Kafka lag, Temporal failures

---

## Phase 9: Transactional Integrity & Explainability

- [ ] Add compensations for every workflow activity
- [ ] Implement deterministic IDs/idempotency keys + outbox/tombstones
- [ ] Add "describe run/failure" endpoint
- [ ] Add reconciliation workflow to detect/auto-heal orphaned compensations
- [ ] Add Prom metrics: compensations_total, rollback_latency_seconds

---

## Phase 10: Messaging/Storage/Replication/Backups

- [ ] Enforce Kafka idempotent producers with deterministic keys
- [ ] Uploads/assets: metadata-first writes, checksum dedupe, compensating delete
- [ ] Postgres HA + PITR-ready configs
- [ ] Redis clustering for prod
- [ ] Structured audit on all state changes

---

## Phase 11: AgentSkin UIX

### 11.1 Theme Gallery & Discovery
- [ ] Grid gallery with preview images, search, filters
- [ ] One-Click Switching without page reload
- [ ] Drag/Drop Install with validation
- [ ] Live Preview with split-screen

### 11.2 Backend
- [ ] FastAPI router `/v1/skins` with list/get/upload/delete
- [ ] PostgreSQL `agent_skins` table
- [ ] JSON schema validation on upload

### 11.3 Security
- [ ] Admin-Only Uploads via OPA (ADMIN mode only)
- [ ] XSS Hardening
- [ ] Tenant Isolation

---

## Phase 12: Settings Persistence

### 12.1 Feature Flags Database Persistence
- [ ] Create `feature_flags` table
- [ ] Implement `FeatureFlagsStore` service
- [ ] UI integration in `ui_settings`
- [ ] Agent reload trigger on flag change

### 12.2 AgentConfig UI Exposure
- [ ] Add `agent_config` section to `ui_settings`
- [ ] Implement `load_agent_config(tenant)` loader
- [ ] Validation for knowledge subdirectory existence

---

## Completed Work

### Recent Completions (2025-12-16)
- [x] Secret Manager VIBE fix - Replaced silent defaults with fail-fast errors
- [x] Secret Manager comprehensive unit tests
- [x] SRS Multimodal Extension Design (Section 16 added to SRS.md v3.0)
- [x] MULTIMODAL_DESIGN.md - Detailed architectural design
- [x] Implementation Plan - 12-phase rollout strategy
- [x] Master Task Tracker created

### Core System Features (Completed)
- [x] FastAPI HTTP gateway with async support
- [x] Session management endpoints
- [x] LLM invocation (stream/non-stream)
- [x] File upload processing
- [x] Admin endpoints (audit, DLQ, requeue)
- [x] Health check endpoints
- [x] AuthMiddleware, RateLimitMiddleware, CircuitBreakerMiddleware
- [x] DegradationMonitor
- [x] Kafka consumer for conversation.inbound
- [x] Clean Architecture Use Cases
- [x] MessageAnalyzer, PolicyEnforcer, ContextBuilder, ToolOrchestrator
- [x] SomaClient singleton HTTP client
- [x] Circuit breaker and retry logic
- [x] Core SomaBrain API endpoints
- [x] FSM orchestration
- [x] Neuromodulation application
- [x] Temporal Workflows (Conversation, ToolExecutor, A2A)

---

## Backlog (Priority Ordered)

### High Priority
1. Feature Flags Database Persistence (REQ-PERSIST-001)
2. SomaBrain Integration Phase 1 (Core Cognitive Endpoints)
3. Real Health Checks for DegradationMonitor
4. Multimodal Extension Phase 1 (Foundation & Data Model)

### Medium Priority
1. AgentConfig UI Exposure (REQ-PERSIST-002)
2. Capsule Domain Integration completion
3. Multimodal Extension Phase 2-4 (Asset Pipeline, Execution)
4. SomaBrain Sleep Management

### Low Priority
1. A2A Protocol full documentation
2. Circuit Breaker Metrics
3. Memory namespace clarity documentation
4. SomaBrain Diagnostics & Feature Flags

---

## Next Steps (Immediate Actions)

1. **SomaBrain Integration** - Implement missing endpoints (adaptation_reset, act)
2. **Database Migrations** - Create multimodal tables
3. **Capability Registry** - Implement tool/model discovery service
4. **Policy Graph Router** - Implement deterministic provider selection
5. **Provider Adapters** - Complete DALL-E, Mermaid, Playwright
6. **Temporal Migration** - Port workflows to Temporal
7. **Observability** - Expose `/metrics` on all services

---

**Last Updated:** 2025-12-21  
**Maintained By:** Development Team

