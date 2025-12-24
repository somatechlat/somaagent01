# AGENT TASKS — SomaAgent01 WebUI SaaS Implementation

**Document ID:** SA01-AGENT-TASKS-2025-12
**Version:** 1.0
**Created:** 2025-12-24
**Status:** CANONICAL — Agent Single Source of Truth

> **CRITICAL:** This file is used by the AI agent to track implementation progress.
> **DO NOT DELETE OR REPLACE** — Only update status markers.

---

## How to Use This File

- `[ ]` Not started
- `[/]` In progress
- `[x]` Complete
- `[!]` Blocked

---

## Phase 1: Docker Infrastructure (Priority: HIGH)

### 1.1 Docker Deployment
- [x] Main Dockerfile (unified) - 193 lines with build args
- [x] Dockerfile.gateway (Django-only) - 86 lines - FIXED
- [x] Dockerfile.worker (Kafka/Temporal) - 77 lines
- [x] Dockerfile.analyzer (ML) - 114 lines
- [/] Build core profile images - BUILDING (24min+)
- [ ] Verify all services start correctly
- [ ] Document build commands

### 1.2 Docker Compose Profiles
- [ ] `core` - postgres (20432), redis (20379), kafka (20092), gateway (21016)
- [ ] `auth` - postgres, keycloak (20880)
- [ ] `vectors` - etcd, minio (20900), milvus (20530)
- [ ] `security` - spicedb (20051), opa (20181)
- [ ] `observability` - prometheus (20090), grafana (20300)

---

## Phase 2: Integration Testing (Priority: HIGH)

### 2.1 Django Tests
- [x] Run `pytest tests/django/ -v` - 41/47 passing
- [!] Verify SomaBrain connection (port 9696) - BLOCKED: SomaBrain not running
- [ ] All 47 tests passing

### 2.2 End-to-End Tests
- [x] Gateway health check - /api/health endpoint added
- [ ] Chat endpoint test
- [ ] WebSocket connection test

---

## Phase 3: SomaBrain Client Completion (Priority: HIGH)

From CANONICAL_REQUIREMENTS.md Section 14.2:

### 3.1 Standard Mode Endpoints
- [x] `health()` - GET `/health` - ADDED
- [ ] `adaptation_reset()` - POST `/context/adaptation/reset`
- [ ] `act()` - POST `/act` with salience scoring
- [ ] `brain_sleep_mode()` - POST `/api/brain/sleep_mode`
- [ ] `util_sleep()` - POST `/api/util/sleep`
- [ ] `personality_set()` - POST `/personality`
- [ ] `memory_config_get()` - GET `/config/memory`
- [ ] `memory_config_patch()` - PATCH `/config/memory`
- [ ] `cognitive_thread_create()` - POST `/cognitive/thread`
- [ ] `cognitive_thread_next()` - GET `/cognitive/thread/next`
- [ ] `cognitive_thread_reset()` - PUT `/cognitive/thread/reset`

### 3.2 Admin Mode Endpoints (ADMIN ONLY)
- [ ] `list_services()` - GET `/admin/services`
- [ ] `get_service_status()` - GET `/admin/services/{name}`
- [ ] `start_service()` - POST `/admin/services/{name}/start`
- [ ] `stop_service()` - POST `/admin/services/{name}/stop`
- [ ] `restart_service()` - POST `/admin/services/{name}/restart`
- [ ] `sleep_status_all()` - GET `/sleep/status/all`
- [ ] `micro_diag()` - GET `/micro/diag`
- [ ] `get_features()` - GET `/admin/features`
- [ ] `update_features()` - POST `/admin/features`

---

## Phase 4: Eye of God UIX Foundation (Priority: HIGH)

From docs/specs/eye-of-god-uix/tasks.md:

### 4.1 Django Project Setup (Task 1)
- [ ] Django 5.x project at `ui/backend/`
- [ ] Django Ninja API router
- [ ] ASGI with Django Channels
- [ ] PostgreSQL + Redis connections

### 4.2 SpiceDB Integration (Task 2)
- [ ] SpiceDB container in docker-compose
- [ ] Permission schema (schema.zed)
- [ ] SpiceDB gRPC client
- [ ] `@require_permission` decorator
- [ ] Permission caching (Redis, TTL 60s)

### 4.3 Lit Project Setup (Task 3)
- [ ] Lit 3.x project with Vite
- [ ] TypeScript strict mode
- [ ] @vaadin/router for SPA
- [ ] @lit/context for state

### 4.4 Base UI Components (Task 4)
- [ ] `eog-button`, `eog-input`, `eog-select`
- [ ] `eog-toggle`, `eog-slider`, `eog-spinner`
- [ ] `eog-modal`, `eog-toast`

### 4.5 Auth Store & Service (Task 5)
- [ ] AuthStore with Lit signals
- [ ] JWT token management
- [ ] Session restoration

### 4.6 WebSocket Client (Task 6)
- [ ] Connection with token auth
- [ ] Reconnection with exponential backoff
- [ ] Heartbeat (20s interval)

### 4.7 API Client (Task 7)
- [ ] Base ApiClient class
- [ ] Retry logic (3 attempts)
- [ ] Token injection

### 4.8 App Shell (Task 8)
- [ ] `eog-app` root component
- [ ] `eog-header`, `eog-sidebar`, `eog-main`
- [ ] Route configuration

---

## Phase 5: Core Features (Priority: HIGH)

### 5.1 Mode Store & Selector (Task 9)
- [ ] ModeStore with available modes
- [ ] Permission check on mode change
- [ ] `eog-mode-selector` component
- [ ] DEGRADED mode transition

### 5.2 Theme Store & AgentSkin (Task 10)
- [ ] ThemeStore with theme list
- [ ] Theme validation (26 variables)
- [ ] Contrast ratio validation (WCAG AA)
- [ ] Live preview mode

### 5.3 Settings Views (Task 11)
- [ ] `eog-settings-view` with tabs
- [ ] Agent, External, Connectivity, System tabs
- [ ] Settings persistence

### 5.4 Chat View (Task 13-14)
- [ ] `eog-chat-view` layout
- [ ] `eog-conversation-list` sidebar
- [ ] `eog-chat-panel`, `eog-message`, `eog-chat-input`
- [ ] Streaming response display
- [ ] Kafka message publishing

### 5.5 Themes View (Task 15)
- [ ] `eog-themes-view` gallery
- [ ] Theme upload, download/install
- [ ] Rate limiting (10 uploads/hour)

### 5.6 Django Models (Task 16)
- [ ] Tenant, User, Settings, Theme, FeatureFlag, AuditLog models
- [ ] Migrations

---

## Phase 6: SaaS Admin Backend (Priority: HIGH)

From docs/specs/eye-of-god-uix/SAAS_ADMIN_SRS.md:

### 6.1 Tenant Management APIs
- [ ] `GET /api/v2/saas/tenants` - List tenants
- [ ] `POST /api/v2/saas/tenants` - Create tenant
- [ ] `GET /api/v2/saas/tenants/{id}` - Get tenant
- [ ] `PUT /api/v2/saas/tenants/{id}` - Update tenant
- [ ] `DELETE /api/v2/saas/tenants/{id}` - Delete tenant
- [ ] `POST /api/v2/saas/tenants/{id}/suspend` - Suspend
- [ ] `POST /api/v2/saas/tenants/{id}/activate` - Activate

### 6.2 Subscription APIs
- [ ] `GET /api/v2/saas/subscriptions` - List tiers
- [ ] `POST /api/v2/saas/subscriptions` - Create tier
- [ ] `PUT /api/v2/saas/tenants/{id}/subscription` - Assign tier

### 6.3 Tier Builder APIs
- [ ] `GET /api/v2/saas/tiers` - List tiers
- [ ] `POST /api/v2/saas/tiers` - Create tier
- [ ] `GET /api/v2/saas/tiers/{id}` - Get tier with features
- [ ] `PUT /api/v2/saas/tiers/{id}` - Update tier
- [ ] `DELETE /api/v2/saas/tiers/{id}` - Delete tier
- [ ] `GET /api/v2/saas/features/catalog` - List features
- [ ] `GET /api/v2/saas/features/{feature}/schema` - Get schema

### 6.4 Usage & Billing APIs
- [ ] `GET /api/v2/saas/usage` - Platform usage
- [ ] `GET /api/v2/saas/tenants/{id}/usage` - Tenant usage
- [ ] `GET /api/v2/saas/billing` - Billing summary

### 6.5 Database Schema
- [ ] `subscription_tiers` table
- [ ] `tenants` table
- [ ] `tenant_users` table
- [ ] `agents` table
- [ ] `agent_users` table
- [ ] `usage_records` table
- [ ] `saas_features` table
- [ ] `saas_tier_features` table
- [ ] `saas_feature_providers` table

---

## Phase 7: SaaS Admin Frontend (Priority: MEDIUM)

### 7.1 SAAS Dashboard
- [ ] `eog-platform-dashboard` - Platform overview
- [ ] Revenue/billing summary
- [ ] System health metrics

### 7.2 Tenant Views
- [ ] `eog-tenant-list` - Tenant grid
- [ ] `eog-tenant-form` - Create/edit modal
- [ ] Suspend/Activate flows

### 7.3 Subscription Views
- [ ] `eog-subscription-manager` - Tier config
- [ ] `eog-tier-builder` - Drag-drop composer
- [ ] Feature settings modals (full-screen)

### 7.4 User Management
- [ ] `eog-user-table` - User list
- [ ] `eog-role-selector` - Role dropdown
- [ ] Invite/remove flows

### 7.5 Agent Management
- [ ] `eog-agent-grid` - Agent cards
- [ ] `eog-agent-form` - Create/configure
- [ ] Quota enforcement

---

## Phase 8: Voice Integration (Priority: MEDIUM)

### 8.1 Voice Store (Task 17)
- [ ] VoiceStore with provider state
- [ ] Voice state machine

### 8.2 Local Voice Service (Task 18)
- [ ] Microphone capture
- [ ] VAD (WebRTC)
- [ ] Whisper STT, Kokoro TTS

### 8.3 AgentVoiceBox Integration (Task 19)
- [ ] WebSocket connection
- [ ] Speech-on-speech
- [ ] Turn detection

### 8.4 Voice UI (Tasks 21-22)
- [ ] `eog-voice-button`
- [ ] `eog-voice-overlay` with visualizer

---

## Phase 9: Advanced Features (Priority: MEDIUM)

### 9.1 Memory View (Task 23)
- [ ] `eog-memory-view` layout
- [ ] Virtual scrolling (10K+ items)
- [ ] Memory CRUD

### 9.2 Cognitive Panel (Task 24)
- [ ] Neuromodulator gauges
- [ ] Adaptation panel
- [ ] Sleep controls

### 9.3 Admin Dashboard (Task 25)
- [ ] User management
- [ ] Tenant management
- [ ] System health

### 9.4 Audit Log (Task 26)
- [ ] Virtual scrolling table
- [ ] Date/action/user filters
- [ ] CSV export

### 9.5 Tool Catalog (Task 27)
- [ ] Tool grid
- [ ] Permission by mode
- [ ] Real-time output

### 9.6 Scheduler (Task 28)
- [ ] Task list
- [ ] Cron expression builder
- [ ] Execution history

---

## Phase 10: Optimization (Priority: LOW)

### 10.1 Service Worker (Task 29)
- [ ] Asset caching
- [ ] Offline fallback

### 10.2 Code Splitting (Task 30)
- [ ] Manual chunks in Vite
- [ ] Initial bundle < 100KB

### 10.3 Virtual Scrolling (Task 31)
- [ ] `eog-virtual-list` component

### 10.4 Performance Testing (Task 32)
- [ ] k6 load tests
- [ ] 10K concurrent WebSocket

### 10.5 Accessibility (Task 33)
- [ ] axe-core tests
- [ ] WCAG AA compliance

### 10.6 Security (Task 34)
- [ ] OWASP ZAP scan
- [ ] XSS prevention

---

## Phase 11: Zero Data Loss Architecture (Priority: CRITICAL) ✅

### 11.1 Transactional Outbox Pattern
- [x] `OutboxMessage` Django model
- [x] `DeadLetterMessage` Django model
- [x] `IdempotencyRecord` Django model
- [x] `PendingMemory` Django model (degradation queue)

### 11.2 Django Management Commands
- [x] `publish_outbox` - Kafka outbox publisher
- [x] `sync_memories` - SomaBrain degradation recovery

### 11.3 Django Signals
- [x] `memory_created` signal
- [x] `conversation_message` signal
- [x] `tool_executed` signal
- [x] `OutboxEntryManager` for transactional outbox

### 11.4 Documentation
- [x] `docs/ZERO_DATA_LOSS_ARCHITECTURE.md` - SRS specification
- [x] `docs/ZERO_DATA_LOSS_IMPLEMENTATION.md` - Status document

### 11.5 Integration (Pending)
- [ ] Wire conversation_worker to use outbox
- [ ] Wire tool_executor to use outbox
- [ ] Configure Kafka exactly-once in docker-compose

### 11.6 Monitoring (Pending)
- [ ] Prometheus metrics for outbox depth
- [ ] DLQ depth alerting
- [ ] Sync lag monitoring

---

## Phase 12: Refactoring & Documentation ✅

### 12.1 Legacy Code Removal
- [x] HARD DELETE `services/ui/` directory
- [x] HARD DELETE `services/ui_proxy/` directory
- [x] Remove legacy FAISS code from `admin/core/helpers/memory.py`
- [x] Remove legacy app reference from `services/gateway/main.py`

### 12.2 Documentation
- [x] `docs/USER_JOURNEYS.md` - 15 user journey flows
- [x] `docs/GAP_ANALYSIS.md` - Current status vs requirements

### 12.3 Bug Fixes
- [x] Add `health()` method to `SomaBrainClient`
- [x] Add `/api/health` endpoint to gateway
- [x] Fix circular import in `admin/llm`
- [x] Add `@pytest.mark.django_db` to ORM tests

---

## Phase 13: LLM Degradation & Resilience ✅

### 13.1 LLM Degradation Service
- [x] `LLMDegradationService` with automatic failover
- [x] Provider health tracking (HEALTHY/DEGRADED/UNAVAILABLE)
- [x] Fallback chains by use case (chat, coding, fast, embedding)
- [x] Circuit breaker integration

### 13.2 Centralized Notification Service
- [x] `DegradationNotificationService` (Django + Kafka)
- [x] Kafka topic: `degradation.events`
- [x] Suppression window to prevent alert storms
- [x] Webhook callback support

### 13.3 Integration
- [x] LLM health check in DegradationMonitor
- [x] LLM added to service dependencies
- [x] `_check_llm_health()` method
- [x] Circuit breaker for LLM providers

### 13.4 Documentation
- [x] `docs/RESILIENCE_ARCHITECTURE.md` - Complete architecture

---

## References

- **Eye of God UIX**: `docs/specs/eye-of-god-uix/`
- **CANONICAL_REQUIREMENTS.md**: 100+ requirements
- **CANONICAL_TASKS.md**: 250+ features
- **VIBE_CODING_RULES.md**: Coding standards
- **ZERO_DATA_LOSS_ARCHITECTURE.md**: ZDL SRS specification
- **RESILIENCE_ARCHITECTURE.md**: Degradation & resilience architecture

---

**Total Tasks:** ~190
**Completed Today:** 35+ tasks (Phase 11, 12, 13)
**Estimated Duration:** 10+ weeks

---

**Last Updated:** 2025-12-24

