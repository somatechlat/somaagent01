# SomaAgent01 — Master Task Tracker

**Last Updated:** 2025-12-16  
**SRS Version:** 3.0 (with Multimodal Extension)  
**Status Legend:** `[ ]` Not Started | `[/]` In Progress | `[x]` Completed

---

## 🎯 Current Sprint

### SPRINT-001: Multimodal Capabilities Extension (Planned)
**Target:** Q1 2026  
**Status:** Design Complete, Implementation Pending  
**Feature Flag:** `SA01_ENABLE_multimodal_capabilities=false` (off by default)

---

## 📊 Core System Features (Base SRS Sections 1-15)

### § Gateway Service (Port 8010)
**File:** `services/gateway/main.py` (97 lines)

- [x] FastAPI HTTP gateway with async support
- [x] `/v1/sessions/*` - Session management endpoints
- [x] `/v1/llm/invoke` - LLM invocation (stream/non-stream)
- [x] `/v1/uploads` - File upload processing
- [x] `/v1/admin/*` - Admin endpoints (audit, DLQ, requeue)
- [x] `/v1/health` - Health check endpoints
- [x] AuthMiddleware - Bearer token / API key authentication
- [x] RateLimitMiddleware - Per-tenant rate limiting
- [x] CircuitBreakerMiddleware - Circuit breaker integration
- [x] DegradationMonitor - Degraded mode detection

**Enhancements Needed:**
- [ ] Add multimodal routes (Section 16.9.1)
  - [ ] `GET /v1/multimodal/capabilities`
  - [ ] `POST /v1/multimodal/jobs`
  - [ ] `GET /v1/multimodal/jobs/{id}`
  - [ ] `GET /v1/multimodal/assets/{id}`
  - [ ] `GET /v1/multimodal/provenance/{asset_id}`

---

### § Conversation Worker
**File:** `services/conversation_worker/main.py` (178 lines)

- [x] Kafka consumer for `conversation.inbound` topic
- [x] Clean Architecture Use Cases:
  - [x] ProcessMessageUseCase (453 lines) - Main orchestration
  - [x] GenerateResponseUseCase (285 lines) - LLM response generation
  - [x] StoreMemoryUseCase (203 lines) - Memory operations
  - [x] BuildContextUseCase (114 lines) - Context building
- [x] MessageAnalyzer - Intent/sentiment/tag detection
- [x] PolicyEnforcer - OPA authorization
- [x] ContextBuilder - Context assembly for LLM
- [x] ToolOrchestrator - Tool request delegation

**Enhancements Needed:**
- [ ] Extend ContextBuilder with multimodal awareness (Section 16.2)
- [ ] Support multimodal asset references in context
- [ ] Extract plan from LLM for multimodal requests

---

### § Tool Executor
**File:** `services/tool_executor/main.py` (147 lines)

- [x] Kafka consumer for `tool.requests` topic
- [x] RequestHandler - Policy check, tool dispatch
- [x] ResultPublisher - Result publishing, feedback, memory
- [x] ExecutionEngine - Sandboxed execution
- [x] ToolRegistry - Tool discovery and schema
- [x] Audit logging for tool execution
- [x] Memory capture (policy-gated)

**Enhancements Needed:**
- [ ] Add `multimodal_dispatch()` method (Section 16.9.2)
- [ ] Integrate PolicyGraphRouter for fallbacks
- [ ] Record executions to `multimodal_executions` table
- [ ] Trigger AssetCritic if quality gates enabled

---

### § Upload Processing
**File:** `services/gateway/routers/uploads_full.py`

- [x] File upload with SHA256 hashing
- [x] AttachmentsStore - PostgreSQL-backed storage
- [x] DurablePublisher - Kafka + Outbox pattern
- [x] SessionCache - Redis caching
- [x] Authorization via `authorize_request()`

**Enhancements Needed:**
- [ ] Support multimodal asset uploads (images, videos)
- [ ] Integrate with AssetStore for multimodal assets

---

### § Celery Tasks Architecture
**Files:** `services/common/celery/` (multiple modules)

- [x] SafeTask base class - Metrics and error recording
- [x] core_tasks.py - Infrastructure tasks
- [x] conversation_tasks.py - Conversation domain tasks
  - [x] delegate (3 retries, 60s limit, 60/m rate)
  - [x] build_context (2 retries, 45s limit)
  - [x] store_interaction (2 retries, 45s limit)
  - [x] feedback_loop (2 retries, 45s limit)
- [x] memory_tasks.py - Memory/index domain
  - [x] rebuild_index (1 retry, 90s limit)
  - [x] evaluate_policy (2 retries, 30s limit)
- [x] maintenance_tasks.py - System maintenance
  - [x] publish_metrics (1 retry, 20s limit)
  - [x] cleanup_sessions (1 retry, 120s limit)
  - [x] dead_letter (0 retries, 120/m rate)
- [x] Saga pattern integration

**No enhancements needed for multimodal v1.0**

---

### § SomaBrain Integration
**File:** `python/integrations/soma_client.py` (909 lines)

- [x] SomaClient singleton HTTP client
- [x] Circuit breaker (threshold=3, cooldown=15s)
- [x] Retry logic (max_retries=2, base=150ms)
- [x] API endpoints:
  - [x] `/remember` - Store memory
  - [x] `/recall` - Recall memories
  - [x] `/neuromodulators` - Get/update neuromod state
  - [x] `/context/adaptation/state` - Get adaptation weights
  - [x] `/sleep/run` - Trigger sleep cycle
  - [x] `/persona/{pid}` - Persona management
  - [x] `/context/feedback` - Submit feedback

**Enhancements Needed:**
- [ ] Store multimodal execution outcomes (Section 16.6)
- [ ] Query outcomes for Portfolio Ranking (Section 16.5)
- [ ] Extend feedback schema for tool/model/quality metrics

---

### § Cognitive Processing
**File:** `agent.py` (400 lines)

- [x] FSM orchestration
- [x] Neuromodulation application
  - [x] exploration_factor (dopamine-based)
  - [x] creativity_boost
  - [x] patience_factor (serotonin-based)
  - [x] empathy_boost
  - [x] focus_factor (noradrenaline-based)
  - [x] alertness_boost
- [x] Natural neuromodulator decay
- [x] Sleep cycle triggering (cognitive_load > 0.8)

**No enhancements needed for multimodal v1.0**

---

### § Degraded Mode Architecture
**File:** `services/common/degradation_monitor.py`

- [x] DegradationMonitor service
- [x] Core components monitoring:
  - [x] somabrain
  - [x] database
  - [x] kafka
  - [x] redis
  - [x] gateway
  - [x] auth_service
  - [x] tool_executor
- [x] Degradation thresholds (response_time, error_rate, circuit_failure_rate)
- [x] Degradation levels (NONE, MINOR, MODERATE, SEVERE, CRITICAL)
- [x] Circuit breaker integration

**Enhancements Needed:**
- [ ] Implement real health checks (Section 13.2)
  - [ ] Real DB connectivity test
  - [ ] Real Kafka broker connectivity
  - [ ] Real Redis PING command
- [ ] Add multimodal provider health checks

---

### § A2A (Agent-to-Agent) Architecture

- [x] FastA2A server (DynamicA2AProxy ASGI)
- [x] a2a_chat tool (client)
- [x] Skills advertised: code_execution, file_management, web_browsing
- [x] Token-authenticated endpoints
- [x] Temporary context per conversation

**Documentation Gap:**
- [ ] Document A2A protocol fully (Section 13.1)

---

### § Data Storage Architecture

#### PostgreSQL Tables (Existing)
- [x] session_envelopes - Session metadata
- [x] session_events - Event timeline
- [x] dlq_messages - Dead letter queue
- [x] attachments - File storage
- [x] audit_events - Audit log
- [x] outbox - Transactional outbox
- [x] memory_write_outbox - Memory retry queue

#### PostgreSQL Tables (Multimodal Extension - NEW)
- [ ] multimodal_assets - Asset storage (images/videos/diagrams)
- [ ] multimodal_capabilities - Tool/model registry
- [ ] multimodal_job_plans - Task DSL storage
- [ ] multimodal_executions - Execution history
- [ ] asset_provenance - Audit trail for assets

#### Redis Usage
- [x] `session:{id}` - Session cache
- [x] `policy:requeue:{id}` - Blocked events (3600s TTL)
- [x] `dedupe:{key}` - Idempotency (3600s TTL)
- [x] `rate_limit:{tenant}` - Rate limiting

#### Kafka Topics
- [x] conversation.inbound - User messages (Gateway → Worker)
- [x] conversation.outbound - Responses (Worker → Gateway SSE)
- [x] tool.requests - Tool execution (Worker → ToolExecutor)
- [x] tool.results - Tool results (ToolExecutor → Worker)
- [x] audit.events - Audit trail (All → AuditWorker)
- [x] dlq.events - Failed tasks (SafeTask → Admin)
- [x] memory.wal - Memory WAL (All → MemorySync)
- [x] task.feedback.dlq - Failed feedback (Tasks → Admin)

---

### § Security Architecture

- [x] Authentication:
  - [x] External: Bearer Token / API Key (`services/gateway/auth.py`)
  - [x] Internal: X-Internal-Token (service-to-service)
  - [x] OPA policy evaluation (`services/common/policy_client.py`)
- [x] Authorization actions:
  - [x] conversation.send (ConversationPolicyEnforcer)
  - [x] tool.execute (ToolExecutor)
  - [x] memory.write (ResultPublisher)
  - [x] delegate.task (Celery delegate)
  - [x] admin.* (Gateway admin routes)
- [x] Secrets management:
  - [x] API Keys (Redis encrypted via `SA01_CRYPTO_FERNET_KEY`)
  - [x] Provider Credentials (Web UI Settings)
  - [x] Internal Tokens (Environment `SA01_AUTH_INTERNAL_TOKEN`)
- [x] Security hardening:
  - [x] TLS 1.3 only, HSTS, OCSP stapling
  - [x] mTLS for service-to-service
  - [x] JWS request signing
  - [x] Circuit breakers and exponential backoff
  - [x] Key hygiene (rotation, revocation)

**Enhancements Needed:**
- [ ] OPA policies for multimodal (Section 16.10.1)
  - [ ] `policy/multimodal.rego` - Provider allowlists, budget constraints
- [ ] Asset encryption at rest (optional, Section 16.10.2)
- [ ] Provenance redaction (Section 16.10.3)

---

### § Observability Architecture

#### Prometheus Metrics (Existing)
- [x] `somabrain_http_requests_total` (Counter)
- [x] `somabrain_request_seconds` (Histogram)
- [x] `conversation_worker_messages_total` (Counter)
- [x] `conversation_worker_processing_seconds` (Histogram)
- [x] `sa01_core_tasks_total` (Counter)
- [x] `sa01_core_task_latency_seconds` (Histogram)
- [x] `gateway_sse_connections` (Gauge)
- [x] `fsm_transition_total` (Counter)

#### Prometheus Metrics (Multimodal Extension - NEW)
- [ ] `multimodal_capability_selection_total` (Counter)
- [ ] `multimodal_execution_latency_seconds` (Histogram)
- [ ] `multimodal_execution_cost_estimate_cents` (Histogram)
- [ ] `multimodal_fallback_total` (Counter)
- [ ] `multimodal_quality_score` (Histogram)
- [ ] `multimodal_rework_attempts_total` (Counter)
- [ ] `portfolio_ranker_shadow_divergence_total` (Counter)
- [ ] `capability_health_status` (Gauge)

#### OpenTelemetry Tracing
- [x] Trace propagation (`opentelemetry.propagate.inject`)
- [x] Span creation (`tracer.start_as_current_span`)
- [ ] Multimodal job tracing (Section 16.11.2)

**Enhancements Needed:**
- [ ] Add circuit breaker state transition metrics (Section 13.2)

---

### § Capsule Domain Integration (SomaAgentHub)

**Current Status:** Partially Implemented

- [/] CapsuleDefinition data model alignment
  - [ ] Extend manifest `policy` block with 25+ fields
  - [ ] Persist as canonical CapsuleDefinition in Postgres
- [ ] CapsuleInstance runtime activation records
  - [ ] Create table for capsule instance tracking
  - [ ] Include in audit and task tagging
- [/] Service & data flow integration
  - [ ] Task Capsule Repo as source of truth
  - [ ] Orchestrator `/capsules` serving normalized data
  - [ ] Manifest storage (raw YAML + normalized spec)
- [ ] API contracts convergence
  - [ ] `POST /capsules` (CapsuleSpec)
  - [ ] `POST /v1/capsules` (manifest upload)
  - [ ] `POST /workflows/{id}/run` with capsule reference
  - [ ] `POST /v1/capsule/results`
- [ ] Enforcement & policy hooks
  - [ ] Egress/domain allow/deny at gateway/tool executor
  - [ ] `max_wall_clock_seconds`, `max_concurrent_nodes` enforcement
  - [ ] `rl_export_allowed` / `rl_excluded_fields` enforcement
  - [ ] Classification/retention purge jobs
  - [ ] Audit with capsule_definition_id/version
- [ ] Capsule Creator (Admin UI & Pipeline)
  - [ ] UI workflow for capsule creation
  - [ ] Settings schema builder
  - [ ] Policy presets (Prod/Training/Test/Dev)
  - [ ] Validation step
  - [ ] Signing integration (cosign/sigstore)
  - [ ] Export (`.tgz` + `.sig`)
  - [ ] `POST /v1/capsules/build` endpoint
  - [ ] `POST /v1/capsules/sign` endpoint
  - [ ] `POST /v1/capsules/publish` endpoint
  - [ ] `GET /v1/capsules/drafts` endpoint
- [ ] Marketplace & Versioned Capsule Model
  - [ ] `Capsule` + `CapsuleVersion` tables
  - [ ] Marketplace Manager module
  - [ ] `MarketplaceClient` in agent
  - [ ] `CapsuleInstaller` module
  - [ ] Local registry tracking
  - [ ] GUI: Marketplace tab, Installed tab
  - [ ] Entitlement checks
  - [ ] Telemetry to Hub

**Priority:** MEDIUM (foundational for capsule ecosystem)

---

### § Settings Persistence Requirements

#### REQ-PERSIST-001: Feature Flags Database Persistence
**Priority:** HIGH  
**Status:** NOT IMPLEMENTED

- [ ] Create `feature_flags` table (tenant_id, key, enabled, profile_override)
- [ ] Implement `FeatureFlagsStore` service
  - [ ] `get_flags(tenant)` method
  - [ ] `set_flag(tenant, key, enabled)` method
  - [ ] `get_profile(tenant)` method
- [ ] UI integration in `ui_settings`
  - [ ] Feature Flags section with 14 toggles
  - [ ] Profile selector (minimal/standard/enhanced/max)
- [ ] Agent reload trigger on flag change (<5s)
- [ ] Multi-tenant support

**Current:** 14 feature flags read-only from environment variables

#### REQ-PERSIST-002: AgentConfig UI Exposure
**Priority:** MEDIUM  
**Status:** NOT IMPLEMENTED

- [ ] Add `agent_config` section to `ui_settings`
  - [ ] profile (select)
  - [ ] knowledge_subdirs (json array)
  - [ ] memory_subdir (text)
  - [ ] code_exec_ssh_enabled (toggle)
  - [ ] code_exec_ssh_addr (text)
  - [ ] code_exec_ssh_port (number)
  - [ ] code_exec_ssh_user (text)
- [ ] Implement `load_agent_config(tenant)` loader
- [ ] Validation for knowledge subdirectory existence
- [ ] Backward compatibility with existing agents

**Current:** 5 AgentConfig settings code-level only (not persisted)

---

## 🎨 Multimodal Capabilities Extension (Section 16)

**SRS Reference:** SRS‑MMX‑2025‑12‑16 v1.0  
**Feature Flag:** `SA01_ENABLE_multimodal_capabilities` (default: false)  
**Status:** PLANNED — Design complete, implementation pending  
**Rollout:** v1.0-alpha (Dev) → v1.1-beta (Pilot) → v1.2-rc (Staging) → v2.0-prod (GA)

---

### Phase 1: Foundation & Data Model (A + E)

#### 1.1 Data Model & Schema
- [x] Create `multimodal_assets` table
  - [x] Schema: id, tenant_id, asset_type, format, storage_path, content (bytea), checksum, metadata
  - [x] Indexes: tenant_id, asset_type, checksum uniqueness
- [x] Create `multimodal_capabilities` registry table
  - [x] Schema: tool_id, provider, modalities[], input_schema, output_schema, constraints, cost_tier, health_status
  - [x] Unique constraint: (tool_id, provider)
- [x] Create `multimodal_job_plans` table
  - [x] Schema: id, tenant_id, session_id, plan_json, status, timestamps
- [x] Create `multimodal_executions` table
  - [x] Schema: plan_id, step_index, tool_id, provider, status, asset_id, latency_ms, cost_estimate, quality_score
  - [x] Indexes: plan_id, tenant_id + status + created_at
- [x] Create `asset_provenance` table
  - [x] Schema: asset_id (PK FK), request_id, execution_id, prompt_summary, generation_params, user_id
- [x] Migration scripts with rollback support
  - [x] File: `infra/postgres/init/017_multimodal_schema.sql`

#### 1.2 Capability Registry (E)
- [x] Implement `CapabilityRegistry` service
  - [x] File: `services/common/capability_registry.py`
  - [x] `find_candidates(modality, constraints)` method
  - [x] `register(tool_id, provider, modalities, ...)` method
  - [x] Constraint matching logic in `find_candidates()`
  - [x] Unit tests: `tests/unit/test_capability_registry.py` (21 tests)
- [x] Register existing providers with modality support (via seed data)
  - [x] OpenAI: image (DALL-E 3)
  - [x] Stability: image (Stable Diffusion)
  - [x] Mermaid: diagram (local rendering)
  - [x] PlantUML: diagram (local rendering)
  - [x] Playwright: screenshot
- [x] Health/availability tracking per capability
  - [x] `update_health()` method
  - [x] `reset_failure_count()` method
  - [ ] Periodic health checks (cron 60s) — Phase 3
  - [ ] Circuit breaker integration — Phase 3

#### 1.3 Policy Graph Router (A)
- [x] Implement `PolicyGraphRouter` service
  - [x] File: `services/common/policy_graph_router.py`
  - [x] Define fallback ladders per modality:
    - [x] `image_diagram`: mermaid → plantuml → dalle3
    - [x] `image_photo`: dalle3 → stability
    - [x] `screenshot`: playwright
    - [x] `video_short`: (prepared for future)
  - [x] `route()` method with OPA integration
  - [x] `_check_policy()` for capability authorization
  - [x] `_check_budget()` for cost tier filtering
  - [x] Unit tests: `tests/unit/test_policy_graph_router.py` (29 tests)
- [x] Integrated with existing OPA policy enforcement via PolicyClient
- [x] Budget/quota enforcement per modality
- [ ] Circuit breaker integration for multimodal providers — Phase 3


---

### Phase 2: Asset Pipeline & Provenance

#### 2.1 Asset Storage & Management
- [x] Create `AssetStore` service
  - [x] File: `services/common/asset_store.py`
  - [x] PostgreSQL bytea storage (v1)
  - [x] SHA256 checksum deduplication
  - [x] `create()` method with auto-dedup
  - [x] `get()`, `get_by_checksum()`, `list()`, `delete()` methods
  - [x] MIME type detection
  - [x] Unit tests: `tests/unit/test_asset_store.py` (19 tests)
- [x] Asset versioning logic (checksum-based dedup)
- [ ] S3 integration — Phase 4
- [ ] Asset lifecycle management — Phase 5

#### 2.2 Provenance System
- [x] Create `ProvenanceRecorder` service
  - [x] File: `services/common/provenance_recorder.py`
  - [x] `record()` method with redaction policy
  - [x] Redaction: prompts, params, PII (SSN, email, API keys, credit cards)
  - [x] Quality gate tracking
  - [x] OpenTelemetry trace correlation
  - [x] Unit tests: `tests/unit/test_provenance_recorder.py` (20 tests)
- [ ] Provenance querying API — Phase 5
- [ ] Audit trail integration — Phase 5

---

### Phase 3: Task Planning & Compilation (D)

#### 3.1 Task DSL & Plan Schema
- [x] Define JSON schema for Task DSL v1.0
  - [x] File: `schemas/task_dsl_v1.json`
  - [x] Fields: version, metadata, tasks[], budget, policy_overrides
  - [x] Task fields: task_id, step_type, modality, depends_on, params, constraints, quality_gate
- [x] Implement JobPlanner service (plan validation + compilation)
  - [x] File: `services/common/job_planner.py`
  - [x] Validate: no circular dependencies, all references exist, valid step types
  - [x] Topological ordering (Kahn's algorithm)
  - [x] Step types: generate_image, generate_diagram, capture_screenshot, generate_video, compose_document, transform_asset
  - [x] Unit tests: `tests/unit/test_job_planner.py` (24 tests)
- [x] Implement ExecutionTracker service
  - [x] File: `services/common/execution_tracker.py`
  - [x] Track execution state, metrics, quality scores
  - [x] Unit tests: `tests/unit/test_execution_tracker.py` (11 tests)

#### 3.2 Intent & Plan Extraction
- [ ] Extend `ContextBuilder` with multimodal awareness
  - [ ] File: `services/conversation_worker/context_builder.py`
  - [ ] Detect multimodal intent keywords (diagram, screenshot, image, video)
- [ ] Create multimodal prompt templates
  - [ ] File: `prompts/multimodal_plan_extraction.txt`
  - [ ] Prompt LLM to generate Task DSL JSON
- [ ] Implement LLM-based plan generator
  - [ ] Use existing LLM invoke with multimodal prompt
  - [ ] Parse JSON response into Task DSL
- [ ] Plan validation and error handling
- [ ] Support user constraints (budgets, timeboxes, policy overrides)

---

### Phase 4: Execution Engine

#### 4.1 Multimodal Provider Adapters
- [x] Create base provider interface
  - [x] File: `services/multimodal/base_provider.py`
  - [x] `MultimodalProvider` abstract base class
  - [x] `GenerationRequest`, `GenerationResult` dataclasses
  - [x] Exception hierarchy (ProviderError, RateLimitError, etc.)
- [x] Implement provider adapters:
  - [x] OpenAI DALL-E adapter
    - [x] File: `services/multimodal/dalle_provider.py`
    - [x] Size/quality/style options, cost estimation
  - [x] Mermaid diagram adapter
    - [x] File: `services/multimodal/mermaid_provider.py`
    - [x] Local CLI execution, SVG/PNG output
  - [x] Playwright screenshot adapter
    - [x] File: `services/multimodal/playwright_provider.py`
    - [x] Viewport config, full-page capture
  - [ ] Stability AI adapter — Future
  - [ ] PlantUML diagram adapter — Future
- [x] Unit tests: `tests/unit/test_multimodal_providers.py` (30 tests)

#### 4.2 Execution Orchestration
- [x] Create `MultimodalExecutor` service
  - [x] File: `services/tool_executor/multimodal_executor.py`
  - [x] DAG execution with dependencies
  - [x] Concurrency controls (await steps)
  - [x] Resource limits (handled by providers)
  - [x] Integration with `AssetStore` and `ExecutionTracker`
  - [x] Error handling & retries
- [ ] Integrate with existing Celery task system - Future
- [x] Unit tests: `tests/unit/test_multimodal_executor.py` (5 tests)
- [ ] Support partial progress and resumption (Implemented basic logic)

---

### Phase 5: Quality Gating (C - Producer + Critic)

#### 5.1 Quality Evaluation System
- [ ] Implement `AssetCritic` service
  - [ ] File: `services/common/asset_critic.py`
  - [ ] `evaluate(asset, rubric, context)` method
  - [ ] Vision model integration (GPT-4V primary, Claude fallback, heuristics fallback)
  - [ ] `_evaluate_image()` method
  - [ ] `_evaluate_diagram()` method (heuristics: resolution, element count)
- [ ] Define rubrics per asset type
  - [ ] Schema: criteria[], min_overall_score
  - [ ] Criteria: clarity, relevance, aesthetic (with weights and thresholds)
- [ ] LLM-based quality evaluation
  - [ ] Prompt template: evaluate image for clarity/relevance/aesthetic
  - [ ] Parse JSON response: passes, score, feedback
- [ ] User-defined acceptance criteria support

#### 5.2 Rework & Fallback Integration
- [ ] Integrate Critic with PolicyGraphRouter fallbacks
- [ ] Bounded retry logic (MAX_REWORK_ATTEMPTS=2)
- [ ] Re-prompt loop with feedback
  - [ ] Append feedback to original prompt
  - [ ] Regenerate asset
- [ ] Track quality metrics and rework rates
  - [ ] Prometheus metric: `multimodal_rework_attempts_total`
- [ ] Feed outcomes to SomaBrain for learning

---

### Phase 6: Learning & Ranking (B - Portfolio Selector)

#### 6.1 SomaBrain Integration for Tool Selection
- [ ] Extend SomaBrain schema for tool/model outcomes
  - [ ] Fields: task_type, modality, tool_id, model, provider, success, latency_ms, cost_estimate, quality_score
  - [ ] Universe: "multimodal_outcomes"
- [ ] Record execution outcomes to SomaBrain
  - [ ] Call `soma.context_feedback()` after each execution
- [ ] Create decision record schema
  - [ ] Fields: chosen_capability, fallback_ladder, rationale

#### 6.2 Ranking System (Shadow Mode First)
- [ ] Implement `PortfolioRanker` service
  - [ ] File: `services/common/portfolio_ranker.py`
  - [ ] `rank(candidates, task_type, modality, tenant_id)` method
  - [ ] Query SomaBrain for outcomes: `soma.recall(query="task_type:X modality:Y", universe="multimodal_outcomes")`
  - [ ] Compute metrics: success_rate, avg_latency, avg_quality, avg_cost
  - [ ] Weighted scoring: 0.4·success + 0.2·(1-norm_latency) + 0.3·quality + 0.1·(1-norm_cost)
- [ ] Shadow mode implementation
  - [ ] Ranking computed but not used
  - [ ] Log divergence: actual vs shadow choice
  - [ ] Prometheus metric: `portfolio_ranker_shadow_divergence_total`
- [ ] Active mode (opt-in via feature flag)
  - [ ] Ranking used as tie-breaker within A's allowed set
  - [ ] Safety: B never overrides A's hard constraints (OPA, budget, health)
- [ ] Exploration policy (optional, off by default)
  - [ ] Probability ε=0.05 to select random capability
  - [ ] Configurable per tenant: `exploration_rate`

---

### Phase 7: SRS Document Generation

#### 7.1 SRS Composer
- [ ] Create `SRSComposer` service
  - [ ] File: `services/common/srs_composer.py`
  - [ ] `compose(title, sections, asset_ids, metadata)` method
  - [ ] Fetch assets from AssetStore
  - [ ] Build ISO 29148 markdown structure
  - [ ] Embed assets (base64 inline for images, links for large assets)
  - [ ] Generate traceability matrices
- [ ] Support versioning and change tracking
  - [ ] Document version in metadata
  - [ ] Diff support for revisions

#### 7.2 Output Formats
- [ ] Generate markdown with embedded assets
- [ ] (Optional) PDF export with rendering toolchain
  - [ ] Pandoc integration
  - [ ] LaTeX template for professional output
- [ ] Create asset bundles (ZIP with manifest)
  - [ ] `manifest.json`: lists all assets with checksums
- [ ] Provenance summary document
  - [ ] JSON format: assets[], tools_used[], execution_times[]

---

### Phase 8: API & UI Integration

#### 8.1 Gateway API Extensions
- [ ] Add multimodal routes to Gateway
  - [ ] File: `services/gateway/main.py`
  - [ ] `GET /v1/multimodal/capabilities` - List tools/models by modality
  - [ ] `POST /v1/multimodal/jobs` - Submit job plan
  - [ ] `GET /v1/multimodal/jobs/{id}` - Job status
  - [ ] `GET /v1/multimodal/assets/{id}` - Download asset (proper Content-Type)
  - [ ] `GET /v1/multimodal/provenance/{asset_id}` - Audit trail
- [ ] Extend `/v1/llm/invoke` for multimodal requests
  - [ ] Accept `multimodal: true` flag
  - [ ] Route to plan extraction flow

#### 8.2 UI/UX Integration
- [ ] Extend provider cards with modality tags
  - [ ] File: `services/gateway/routers/ui_settings.py`
  - [ ] Add `modalities` field: ["text", "image", "video"]
  - [ ] Add `recommended_for` hints: ["diagrams", "photorealistic images"]
  - [ ] Add `multimodal_models` object: {image: [...], vision: [...]}
- [ ] Support per-request modality overrides
  - [ ] UI dropdown: "Use this provider for images"
- [ ] Display asset previews in conversation
  - [ ] Inline thumbnails
  - [ ] Click to expand full-size
- [ ] Show provenance and quality feedback
  - [ ] Link to `/v1/multimodal/provenance/{asset_id}`
  - [ ] Display quality score, generation time, cost

---

### Phase 9: Security & Governance

#### 9.1 OPA Policy Extensions
- [ ] Create `policy/multimodal.rego`
  - [ ] `allow_multimodal` - Tenant plan check (enterprise/pro)
  - [ ] `allow_provider` - Provider allowlists by modality
  - [ ] `within_budget` - Cost tier and budget remaining checks
- [ ] Add data classification constraints
  - [ ] Restrict high-risk tools for sensitive tenants
- [ ] Provider allowlists by modality
  - [ ] image: openai, stability
  - [ ] video: runway, pika (enterprise-only)
- [ ] Cost/quota policies per modality
  - [ ] Max cost per request
  - [ ] Monthly budget caps
- [ ] Per-tenant multimodal permissions

#### 9.2 Asset Security
- [ ] (Optional) Asset encryption at rest
  - [ ] Envelope encryption: AES-256-GCM(content, DEK)
  - [ ] KMS integration for DEK encryption
  - [ ] Store encrypted_dek in asset metadata
  - [ ] Policy-gated: enabled for data_classification="sensitive"
- [ ] Access control checks on asset retrieval
  - [ ] Tenant ownership validation
  - [ ] OPA policy: `asset.read` action
- [ ] Asset retention policies
  - [ ] S3 lifecycle policies (archive after 90 days, delete after 365 days)
  - [ ] Configurable per tenant
- [ ] Secure deletion
  - [ ] Overwrite before delete (optional, configurable)
- [ ] Audit all asset operations
  - [ ] Log to `audit_events` table

---

### Phase 10: Observability & Metrics

#### 10.1 Metrics & Instrumentation
- [ ] Add Prometheus metrics:
  - [ ] `multimodal_capability_selection_total` (Counter: modality, tool_id, provider, decision_source)
  - [ ] `multimodal_execution_latency_seconds` (Histogram: modality, tool_id, provider, status)
  - [ ] `multimodal_execution_cost_estimate_cents` (Histogram: modality, tool_id, provider)
  - [ ] `multimodal_fallback_total` (Counter: modality, tool_id, fallback_reason)
  - [ ] `multimodal_quality_score` (Histogram: modality, tool_id)
  - [ ] `multimodal_rework_attempts_total` (Counter: modality, reason)
  - [ ] `portfolio_ranker_shadow_divergence_total` (Counter: modality, task_type)
  - [ ] `capability_health_status` (Gauge: tool_id, provider)
- [ ] Monitor asset storage usage
  - [ ] S3 bucket size metrics
  - [ ] PostgreSQL bytea column size (if fallback used)

#### 10.2 Distributed Tracing
- [ ] Add OpenTelemetry spans:
  - [ ] Root span: `multimodal_job`
  - [ ] Child spans: `plan_extraction`, `plan_compilation`, `step_NN_*`
  - [ ] Nested spans: `capability_discovery`, `policy_routing`, `portfolio_ranking`, `execution_attempt_N`, `quality_evaluation`
- [ ] Propagate trace context across services
  - [ ] Gateway → Worker → ToolExecutor → External Providers
- [ ] Link traces to provenance records
  - [ ] Store trace_id in asset_provenance table

---

### Phase 11: Testing & Verification

#### 11.1 Unit Tests
All tests in `tests/unit/multimodal/`

- [ ] test_capability_registry.py
  - [ ] Test `find_candidates()` with various modalities
  - [ ] Test constraint matching logic
  - [ ] Test registration and updates
- [ ] test_policy_graph_router.py
  - [ ] Test fallback ladder construction
  - [ ] Test OPA integration (mocked)
  - [ ] Test budget filtering
  - [ ] Test user override logic
- [ ] test_asset_store.py
  - [ ] Test create/get with PostgreSQL
  - [ ] Test S3 integration (mocked)
  - [ ] Test SHA256 deduplication
  - [ ] Test provenance recording
- [ ] test_asset_critic.py
  - [ ] Test image evaluation (mocked vision model)
  - [ ] Test diagram heuristics
  - [ ] Test pass/fail scoring
- [ ] test_portfolio_ranker.py
  - [ ] Test SomaBrain outcomes querying
  - [ ] Test scoring algorithm
  - [ ] Test shadow vs active mode behavior
- [ ] test_plan_compiler.py
  - [ ] Test JSON → DAG compilation
  - [ ] Test validation (circular deps, missing refs)
  - [ ] Test topological ordering

#### 11.2 Integration Tests
All tests in `tests/integration/multimodal/`

- [ ] test_multimodal_providers.py
  - [ ] Test OpenAI DALL-E integration (requires API key)
  - [ ] Test Stability AI integration (requires API key)
  - [ ] Test Mermaid local rendering
  - [ ] Test PlantUML local rendering
  - [ ] Test Playwright screenshot
- [ ] test_multimodal_job.py
  - [ ] Test end-to-end job execution
  - [ ] Submit plan: "Generate SRS with 2 diagrams and 1 screenshot"
  - [ ] Verify assets created in DB/S3
  - [ ] Verify SRS markdown generated
  - [ ] Check provenance records
- [ ] test_soma_outcomes.py
  - [ ] Execute multimodal task
  - [ ] Verify outcome recorded to SomaBrain
  - [ ] Query outcomes for ranking
  - [ ] Test shadow ranker behavior

#### 11.3 E2E Golden Tests
All tests in `tests/e2e/multimodal/`

- [ ] test_srs_generation.py
  - [ ] `test_full_srs_with_multimodal`
    - [ ] User: "Create ISO SRS for feature X with architecture diagrams and UI screenshots"
    - [ ] Verify: plan extracted, tasks executed, assets generated, SRS assembled
    - [ ] Check: markdown output, asset bundle, provenance summary
- [ ] test_fallback_scenarios.py
  - [ ] `test_dalle_failure_fallback`
    - [ ] Mock DALL-E 503 error
    - [ ] Verify: fallback to Stability AI, success
    - [ ] Check: `multimodal_fallback_total` metric incremented
- [ ] test_quality_gates.py
  - [ ] `test_diagram_quality_rework`
    - [ ] Generate diagram with quality gate enabled
    - [ ] Mock Critic: first attempt score < threshold
    - [ ] Verify: re-generation, second attempt passes
    - [ ] Check: `multimodal_rework_attempts_total` = 1

#### 11.4 Chaos & Resilience Tests
All tests in `tests/chaos/multimodal/`

- [ ] test_circuit_breaker.py
  - [ ] Simulate repeated provider failures (5 failures in 10s)
  - [ ] Verify: circuit opens
  - [ ] Check: future requests skip primary, use fallback
  - [ ] Test: circuit recovery after cooldown (60s)
- [ ] test_resume.py
  - [ ] Start 5-step job
  - [ ] Kill process after step 3
  - [ ] Resume job
  - [ ] Verify: steps 1-3 not re-executed, execution resumes at step 4

---

### Phase 12: Documentation & Deployment

#### 12.1 Documentation
- [x] Update SRS.md with multimodal architecture (Section 16)
- [x] Create MULTIMODAL_DESIGN.md (detailed design)
- [ ] Document capability registry format
  - [ ] File: `docs/multimodal/CAPABILITY_REGISTRY.md`
- [ ] Document plan DSL schema
  - [ ] File: `docs/multimodal/TASK_DSL.md`
- [ ] Add runbook for operations
  - [ ] File: `docs/multimodal/OPERATIONS_RUNBOOK.md`
  - [ ] Include: troubleshooting, monitoring, cost optimization

#### 12.2 Configuration & Deployment
- [ ] Define environment variables
  - [ ] `SA01_ENABLE_multimodal_capabilities` (default: false)
  - [ ] `SA01_MULTIMODAL_S3_BUCKET`
  - [ ] `SA01_MULTIMODAL_MAX_ASSET_SIZE_MB` (default: 50)
  - [ ] `SA01_MULTIMODAL_QUALITY_GATES_ENABLED` (default: false)
  - [ ] `SA01_PORTFOLIO_RANKER_MODE` (shadow/active, default: shadow)
- [ ] Create deployment manifests
  - [ ] Docker: update `Dockerfile` with multimodal deps (mmdc, plantuml)
  - [ ] Kubernetes: update `infra/k8s/` manifests
- [ ] Add feature flags for phased rollout
  - [ ] Per-tenant multimodal enablement
  - [ ] Per-tenant quality gates toggle
  - [ ] Per-tenant portfolio ranker mode
- [ ] Configure provider credentials management
  - [ ] Store in existing SecretManager
  - [ ] UI for API key input (DALL-E, Stability, Runway, Pika)
- [ ] Set up monitoring dashboards
  - [ ] Grafana: multimodal metrics panel
  - [ ] Alerts: high fallback rates, quality gate failures, budget overruns

---

## ✅ Completed Work

### Recent Completions (2025-12-16)
- [x] Secret Manager VIBE fix - Replaced silent fallbacks with fail-fast errors
- [x] Secret Manager comprehensive unit tests
- [x] SRS Multimodal Extension Design (Section 16 added to SRS.md v3.0)
- [x] MULTIMODAL_DESIGN.md - Detailed architectural design
- [x] Implementation Plan - 12-phase rollout strategy
- [x] Master Task Tracker created (this file)

---

## 📋 Backlog (Priority Ordered)

### High Priority
1. Feature Flags Database Persistence (REQ-PERSIST-001)
2. Multimodal Extension Phase 1 (Foundation & Data Model)
3. Real Health Checks for DegradationMonitor

### Medium Priority
1. AgentConfig UI Exposure (REQ-PERSIST-002)
2. Capsule Domain Integration completion
3. Multimodal Extension Phase 2-4 (Asset Pipeline, Execution)

### Low Priority
1. A2A Protocol full documentation
2. Circuit Breaker Metrics
3. Memory namespace clarity documentation

---

## 🚀 Next Steps (Immediate Actions)

1. **Review & Approve** Multimodal Extension design docs
2. **Database Migrations** - Create 5 new multimodal tables
3. **Capability Registry** - Implement tool/model discovery service
4. **Policy Graph Router** - Implement deterministic fallback ladders
5. **Provider Adapters** - Start with DALL-E, Mermaid, Playwright

---

## 📊 Progress Summary

**Total Features Identified:** 250+  
**Completed:** ~90 (36%)  
**In Progress:** ~10 (4%)  
**Planned:** ~150 (60%)

**Current Sprint:** Multimodal Capabilities Extension (12 phases, 100+ tasks)  
**Target Completion:** Q1 2026 (phased rollout)

---

**End of Master Task Tracker**  
**Last Updated:** 2025-12-16 17:26 EST  
**Maintained By:** Development Team + AI Assistant
