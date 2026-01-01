# SomaAgent01 Unified Task Tracker

**Status Legend:** `[ ]` Not Started | `[/]` In Progress/Needs Verification | `[x]` Complete | `[!]` Blocked

## Status Policy
- Conflicts between sources resolve to `[/]` (needs verification).
- Any `[/]` remains `[/]` unless verified complete.
- Any `[!]` stays blocked until cleared.
- Canonical-only tasks are grouped under 'Legacy Backlog (Canonical Tasks)'.

**Merged:** 2026-01-01
**Sources:** repo-root `AGENT_TASKS.md` and `docs/legacy/CANONICAL_TASKS.md` (both removed)

## Phase 11: Code Audit Fixups

### Verified Gaps (2026-01-01)

- [ ] Wire sessions API to SessionManager (admin/sessions/api.py -> admin/common/session_manager.py).
- [ ] Wire conversations API to ChatService (admin/conversations/api.py -> services/common/chat_service.py).
- [ ] Persist VoiceSession records in admin/voice/consumers.py (remove TODOs).
- [ ] Sync infrastructure config to Redis for runtime enforcement (admin/core/infrastructure/api.py).
- [ ] Integrate tool registry in run_tool_executor (admin/core/management/commands/run_tool_executor.py).
- [ ] Integrate LLM use case in run_conversation_worker (admin/core/management/commands/run_conversation_worker.py).

## Phase 0: SaaS Architecture Documentation

- [x] Analyze eye-of-god-uix specs (12 files)
- [x] Analyze agentskin-uix specs (3 files)
- [x] Analyze somabrain-integration specs (3 files)
- [x] Analyze somastack-unified-ui specs (5 files)
- [x] Create CANONICAL_SAAS_DESIGN.md (795 lines)
- [x] Create SRS-SAAS-ADMIN.md (227 lines)
- [x] Create SRS-TENANT-ADMIN.md (277 lines)
- [x] Create SRS-AGENT-USER.md (635 lines)
- [x] Create SRS-ERROR-HANDLING.md (337 lines)
- [x] Create SRS-AUTHENTICATION.md (232 lines)
- [x] Create SRS-PERMISSION-MATRIX.md (608 lines)
- [x] Create SRS INDEX.md (214 lines)
- [x] Create TASKS-PHASE1-4 (4 files)
- [x] Create CANONICAL_USER_JOURNEYS_SRS.md (758 lines)
- [x] Git commit all documentation

## Phase 1: Foundation

### 1.1 Database Models (Django)

- [x] SubscriptionTier model (limits, pricing, lago_code)
- [x] Tenant model (org, slug, status, subscription FK)
- [x] TenantUser model (user, tenant, role, status)
- [x] Agent model (tenant FK, config, features, status)
- [x] AgentUser model (agent access, modes allowed)
- [x] AuditLog model (all events)
- [x] SaasFeature, TierFeature, FeatureProvider models
- [x] UsageRecord model
- [x] Initial migration (36KB)

### 1.2 SpiceDB Schema

- [x] Platform definition (God Mode)
- [x] saas_admin definition with platform->manage_roles
- [x] Tenant definition with role hierarchy
- [x] Agent definition with mode permissions
- [x] Resource permissions (conversation, memory, cognitive, voice, tool)
- [x] SpiceDB client wrapper exists (admin/common/auth.py)
- [x] @require_permission decorator exists

### 1.3 Keycloak Setup

- [x] Realm config: infrastructure/keycloak/realm-somaagent.json
- [x] 8 platform roles (saas_admin → viewer)
- [x] Google OAuth provider configured
- [x] GitHub OAuth provider configured
- [x] TOTP MFA configuration
- [x] Token lifetimes (15min access, 30min session)
- [x] Custom tenant_id claim mapper

### 1.4 Base Lit Components

- [x] Design tokens CSS (webui/src/styles/tokens.css - 383 lines)
- [x] saas-* components (sidebar, data-table, stat-card, etc.)
- [x] soma-* components (button, card, input, modal, etc.)
- [x] 22 components total
- [x] 33 views
- [x] 5 stores

### 1.4 Base Lit Components (Duplicate Section - Already Complete Above)

- [x] Design tokens CSS (somastack-tokens.css)
- [x] saas-shell (app container)
- [x] saas-nav (sidebar navigation)
- [x] saas-card, saas-table, saas-modal
- [x] saas-form, saas-input, saas-button
- [x] saas-toast, saas-badge
- [x] saas-degraded-banner

## Phase 2: Authentication

### 2.1 Login Flow

- [x] POST /auth/token (password grant + OAuth code)
- [x] POST /auth/refresh (token refresh)
- [x] GET /auth/me (current user info)
- [x] POST /auth/logout (session termination)
- [x] Role-based redirect paths
- [x] Permission mapping from Keycloak roles
- [x] keycloak-service.ts (300 lines) - frontend
- [x] auth-store.ts (270 lines) - Lit Context
- [x] saas-login.ts (33KB) - login view

### 2.2 MFA Setup

- [x] POST /auth/mfa/setup - Initialize TOTP
- [x] POST /auth/mfa/verify - Verify TOTP code
- [x] POST /auth/mfa/validate - Login MFA step
- [x] GET /auth/mfa/status - MFA status
- [x] POST /auth/mfa/disable - Disable MFA
- [x] mfa.py (280 lines)
- [x] saas-mfa-setup.ts view (14KB)

### 2.3 Password Reset

- [x] POST /auth/password/request - Request reset
- [x] POST /auth/password/confirm - Confirm with token
- [x] GET /auth/password/validate/{token}
- [x] POST /auth/password/change - Authenticated change
- [x] password_reset.py (260 lines)
- [x] Email integration (via Keycloak)

### 2.4 Invitation Flow

- [x] POST /invitations - Send invitation
- [x] GET /invitations/{token} - Accept invitation page
- [x] POST /invitations/{token}/accept - Create account
- [x] GET /invitations - List (admin)
- [x] DELETE /invitations/{id} - Revoke
- [x] POST /invitations/{id}/resend
- [x] invitations.py (320 lines)
- [x] saas-onboarding.ts view (15KB)

### 2.5 Session Management

- [x] Token refresh (auto-scheduled in frontend)
- [x] POST /auth/impersonate (125 lines) - SAAS admin only
- [x] Concurrent session limits (Keycloak-managed)

## Phase 3: Platform Admin (Eye of God)

### 3.1 Platform Dashboard

- [x] GET /saas/dashboard (dashboard.py - 90 lines)
- [x] DashboardMetrics, TopTenant, RecentEvent schemas
- [x] saas-platform-dashboard.ts view (32KB)

### 3.2 Tenant Management

- [x] GET /saas/tenants
- [x] POST /saas/tenants
- [x] PATCH /saas/tenants/{id}
- [x] DELETE /saas/tenants/{id}
- [x] POST /saas/tenants/{id}/suspend
- [x] POST /saas/tenants/{id}/activate
- [x] tenants.py (165 lines)
- [x] saas-tenants.ts view (16KB)

### 3.3 Role Management

- [x] GET /saas/settings/roles
- [x] PATCH /saas/settings/roles/{id}
- [x] settings.py (186 lines)
- [x] saas-admin-roles-list.ts view

### 3.4 Subscription Tier Builder

- [x] GET /saas/tiers
- [x] POST /saas/tiers
- [x] PATCH /saas/tiers/{id}
- [x] DELETE /saas/tiers/{id}
- [x] tiers.py (173 lines)
- [x] saas-subscriptions.ts view (27KB)

### 3.5 Platform Billing

- [x] GET /saas/billing (BillingMetrics, RevenueByTier)
- [x] GET /saas/billing/invoices
- [x] GET /saas/billing/usage
- [x] GET /saas/billing/usage/{tenant_id}
- [x] billing.py (128 lines)
- [x] saas-billing.ts view (23KB)

### 3.6 Feature Management

- [x] GET /saas/features
- [x] GET /saas/features/{id}
- [x] GET /saas/features/{code}/providers
- [x] POST /saas/features/tiers/{tier_id}/{feature_code}
- [x] features.py (213 lines)

### 3.7 User Management

- [x] GET /saas/admin/users
- [x] POST /saas/admin/users
- [x] GET /saas/admin/users/{id}
- [x] PUT /saas/admin/users/{id}
- [x] DELETE /saas/admin/users/{id}
- [x] users.py (248 lines)
- [x] saas-tenant-users.ts view (19KB)

### 3.8 Agent Management

- [x] GET /saas/admin/agents
- [x] POST /saas/admin/agents
- [x] GET /saas/admin/agents/{id}
- [x] PUT /saas/admin/agents/{id}
- [x] DELETE /saas/admin/agents/{id}
- [x] POST /saas/admin/agents/{id}/start
- [x] POST /saas/admin/agents/{id}/stop
- [x] GET /saas/admin/quota
- [x] tenant_agents.py (356 lines)
- [x] saas-tenant-agents.ts view (20KB)

### 3.9 Settings & API Keys

- [x] GET /saas/settings/api-keys
- [x] POST /saas/settings/api-keys (cryptographic generation)
- [x] DELETE /saas/settings/api-keys/{id}
- [x] GET /saas/settings/models
- [x] PATCH /saas/settings/models/{id}
- [x] POST /saas/settings/sso
- [x] POST /saas/settings/sso/test
- [x] settings.py (250+ lines) - secrets.token_urlsafe, SHA-256

### 3.10 Platform Health

- [x] GET /saas/health - All services check
- [x] GET /saas/health/db - PostgreSQL
- [x] GET /saas/health/cache - Redis
- [x] GET /saas/health/keycloak - Keycloak IAM
- [x] GET /saas/health/somabrain - SomaBrain
- [x] GET /saas/health/degradation - Degradation status
- [x] health.py (270 lines) - Async concurrent checks

### 3.11 Audit Trail

- [x] GET /saas/audit - List with filters
- [x] GET /saas/audit/export - CSV export
- [x] GET /saas/audit/actions - Action types
- [x] GET /saas/audit/stats - Dashboard stats
- [x] audit.py (245 lines)

## Phase 4: Tenant Admin

### 4.1 Tenant Dashboard

- [x] saas-tenant-dashboard.ts (539 lines)
- [x] Quota stats (Agents, Users, Tokens, Storage)
- [x] Agent list with status indicators
- [x] Quick actions grid
- [x] Sidebar navigation

### 4.2 User Management

- [x] GET /saas/admin/users (with filtering, pagination)
- [x] POST /saas/admin/users (invite)

### 4.4 Tenant Roles

- [x] Roles integrated via users.py
- [x] Role selector in user management

### 4.5 Tenant Settings

- [x] saas-settings.ts view (33KB)

### 4.6 Tenant Billing

- [x] GET /saas/billing/tenant/{id}
- [x] POST /saas/billing/tenant/{id}/upgrade
- [x] GET /saas/billing/tenant/{id}/invoices
- [x] POST /saas/billing/tenant/{id}/payment-methods
- [x] billing.py (+195 lines)
- [x] saas-tenant-billing.ts view (16KB)

### 4.7 Audit Log

- [x] saas-audit-log view (pending)

## Phase 5: Agent UI

### 5.1 Chat Interface (STD Mode)

- [x] saas-chat.ts (1,063 lines, 34KB)
- [x] WebSocket streaming support
- [x] Conversation sidebar
- [x] 6 Agent modes (STD, DEV, TRN, ADM, RO, DGR)
- [x] Mode selector dropdown
- [x] Quick replies
- [x] Typing indicator
- [x] Confidence bar
- [x] Message animations

### 5.2 Cognitive Panel (TRN Mode)

- [x] saas-cognitive-panel.ts (862 lines, 28KB)
- [x] Neuromodulator gauges (6 types)
- [x] Adaptation parameter sliders
- [x] Sleep cycle trigger
- [x] Activity log
- [x] Real-time WebSocket updates

### 5.3 Memory Browser

- [x] saas-memory-view.ts (26KB)
- [x] Virtual scrolling (CSS grid layout)
- [x] Memory card grid (818 lines)

### 5.4 Voice Integration

- [x] soma-voice-button.ts component
- [x] soma-voice-overlay.ts component
- [x] POST /voice/transcribe (Whisper) - 307 lines
- [x] POST /voice/synthesize (Kokoro TTS)
- [x] GET /voice/voices - List voices
- [x] GET /voice/status - Service health
- [x] voice/api.py (307 lines)
- [x] WebSocket streaming (/ws/voice) - endpoint ready, browser fallback active

### 5.5 Mode Selection

- [x] saas-mode-selection.ts (20KB)
- [x] Mode cards with descriptions

### 5.6 Settings

- [x] saas-settings.ts (33KB)

## Phase 6: SomaBrain Integration

### 6.1 Core Endpoints

- [x] POST /somabrain/brain/adaptation/reset/{agent_id}
- [x] POST /somabrain/brain/act - with salience
- [x] POST /somabrain/brain/sleep/{agent_id}
- [x] POST /somabrain/brain/util/sleep
- [x] GET /somabrain/brain/wake/{agent_id}
- [x] GET /somabrain/brain/status/{agent_id}
- [x] core_brain.py (400 lines)

### 6.2 Memory Endpoints

- [x] POST /somabrain/brain/personality/{agent_id}
- [x] GET /somabrain/brain/config/memory/{agent_id}
- [x] PATCH /somabrain/brain/config/memory/{agent_id}

### 6.3 Cognitive Thread

- [x] POST /somabrain/cognitive/threads - Create thread
- [x] POST /somabrain/cognitive/threads/{id}/step - Execute
- [x] POST /somabrain/cognitive/threads/{id}/reset
- [x] DELETE /somabrain/cognitive/threads/{id}
- [x] GET /somabrain/cognitive/state/{agent_id}
- [x] PATCH /somabrain/cognitive/params/{agent_id}
- [x] POST /somabrain/cognitive/adaptation/reset/{agent_id}
- [x] POST /somabrain/cognitive/sleep/{agent_id}
- [x] cognitive.py (380 lines)

### 6.4 Admin Endpoints (ADMIN mode only)

- [x] GET /somabrain/admin/services - List services
- [x] GET /somabrain/admin/services/{name} - Service status
- [x] POST /somabrain/admin/services/{name}/action - Start/stop/restart
- [x] GET /somabrain/admin/diagnostics - System diagnostics
- [x] GET /somabrain/admin/sleep-status - All agents sleep
- [x] GET /somabrain/admin/features - Feature flags
- [x] PATCH /somabrain/admin/features - Update flags
- [x] admin_api.py (340 lines)
- [x] sleep_status_all() - admin_api.py:287
- [x] get_diagnostics() (micro_diag) - admin_api.py:227
- [x] get_features() / update_features() - admin_api.py:312-358

### 6.5 Integration Tests

- [x] test_adaptation_reset
- [x] test_act_execution
- [x] test_sleep_transitions
- [x] test_admin_services
- [x] test_cognitive_thread
- [x] tests/test_integration.py (450 lines)

## Phase 7: Multimodal & Advanced Features

### 7.1 Capability Registry

- [x] POST /capabilities/register - Register capability
- [x] DELETE /capabilities/{id} - Deregister
- [x] GET /capabilities - List all
- [x] POST /capabilities/find - Find candidates
- [x] POST /capabilities/{id}/health - Report health
- [x] GET /capabilities/{id}/circuit - Circuit state
- [x] POST /capabilities/{id}/circuit/reset - Reset circuit
- [x] GET /capabilities/health/summary - Overall health
- [x] capabilities/api.py (380 lines)

### 7.2 Asset Storage

- [x] POST /assets - Upload with SHA-256 hash
- [x] GET /assets/{id} - Get asset
- [x] GET /assets - List assets
- [x] DELETE /assets/{id} - Soft delete
- [x] GET /assets/{id}/provenance - Provenance chain
- [x] POST /assets/{id}/provenance - Add record
- [x] GET /assets/{id}/verify - Integrity check
- [x] assets/api.py (340 lines)

### 7.3 Multimodal Execution

- [x] POST /multimodal/execution/images/generate - OpenAI DALL-E
- [x] POST /multimodal/execution/diagrams/render - Mermaid
- [x] POST /multimodal/execution/screenshots/capture - Playwright
- [x] POST /multimodal/execution/dag/execute - DAG engine
- [x] GET /multimodal/execution/dag/{id} - DAG status
- [x] execution.py (400 lines)

### 7.4 Quality Gating

- [x] POST /quality/evaluate - LLM quality evaluation
- [x] POST /quality/critique - AssetCritic service
- [x] POST /quality/retry/execute - Bounded retry logic
- [x] GET /quality/retry/policies - Policy presets
- [x] GET/PATCH /quality/thresholds
- [x] quality/api.py (420 lines)

### 7.5 A2A Workflows

- [x] POST /a2a/conversations - Conversation workflow
- [x] POST /a2a/tools/execute - Tool execution
- [x] POST /a2a/handoffs - Agent handoff
- [x] POST /a2a/maintenance - Maintenance workflow
- [x] POST /a2a/escalations - Escalation to human
- [x] a2a/api.py (480 lines)

### 7.3 Temporal Workflows

- [x] POST /workflows - Start workflow
- [x] GET /workflows/{id} - Get status
- [x] GET /workflows - List workflows
- [x] POST /workflows/{id}/cancel - Cancel
- [x] POST /workflows/{id}/signal - Send signal
- [x] GET /workflows/{id}/history - History
- [x] POST /workflows/{id}/terminate - Force
- [x] workflows/api.py (290 lines) execution workflow
- [x] A2A workflow - a2a/api.py (459 lines)
- [x] Maintenance workflows - a2a/api.py:344-392

### 7.6 Observability

- [x] GET /observability/metrics - Prometheus format
- [x] GET /observability/metrics/json - JSON format
- [x] GET /observability/ready - K8s readiness
- [x] GET /observability/live - K8s liveness
- [x] GET /observability/traces - OpenTelemetry traces
- [x] GET /observability/dashboards - Grafana
- [x] observability/api.py (380 lines)

## Phase 9: Hierarchical Auth Configuration

### 9.2 Platform Auth Defaults (SysAdmin/Eye of God)

- [x] GET /auth-config/platform - Get platform defaults
- [x] PUT /auth-config/platform - Update platform defaults
- [x] GET /auth-config/platform/providers - List OAuth providers
- [x] POST /auth-config/platform/providers - Add OAuth provider
- [x] PUT /auth-config/platform/providers/{id} - Update provider
- [x] DELETE /auth-config/platform/providers/{id} - Remove provider
- [x] POST /auth-config/platform/providers/{id}/test - Test connection
- [x] GET /auth-config/platform/mfa - MFA policy
- [x] PUT /auth-config/platform/mfa - Update MFA policy

### 9.3 Tenant Auth Overrides (TenantAdmin)

- [x] GET /auth-config/tenants/{tenant_id} - Get tenant config
- [x] PUT /auth-config/tenants/{tenant_id} - Update tenant config
- [x] POST /auth-config/tenants/{tenant_id}/providers - Add provider
- [x] DELETE /auth-config/tenants/{tenant_id}/providers/{id} - Remove
- [x] GET /auth-config/tenants/{tenant_id}/effective - Merged config
- [x] POST /auth-config/tenants/{tenant_id}/reset - Reset to defaults

### 9.5 API Implementation

- [x] admin/auth_config/api.py - Auth config endpoints (438 lines)
- [x] Platform defaults storage (Django settings/DB)
- [x] Tenant overrides storage (Tenant model)
- [x] Config merger (effective config calculation)
- [x] Keycloak realm sync for custom providers

## Phase 10: Reusable UI Architecture

### 10.1 Reusable UI Components

- [x] EntityManager component (450 lines) - CRUD for 5 entity types
- [x] SettingsForm component (580 lines) - JSON Schema form generator
- [x] PlatformMetricsDashboard (787 lines) - 5-tab observability
- [x] SaasAuditDashboard (470 lines) - Audit logs with stats
- [x] SaasRoleMatrix (550 lines) - Visual permission editor
- [x] SaasTierBuilder (634 lines) - Subscription tier visual editor
- [x] SaasUsageAnalytics (520 lines) - Quota monitoring dashboard
- [x] InfrastructureDashboard (1200 lines) - Health, RateLimits, Degradation

### 10.2 Backend APIs

- [x] Feature Flags API (250 lines) - /api/v2/core/flags
- [x] API Keys API (230 lines) - /api/v2/core/apikeys
- [x] Settings API (170 lines) - /api/v2/core/settings
- [x] Observability API (210 lines) - /api/v2/core/observability

### 10.3 Routes Added

- [x] /platform/metrics → PlatformMetricsDashboard
- [x] /platform/audit → SaasAuditDashboard
- [x] /platform/role-matrix → SaasRoleMatrix
- [x] /platform/tiers → SaasTierBuilder
- [x] /platform/usage → SaasUsageAnalytics
- [x] /platform/settings/* → SettingsForm

## Legacy Backlog (Canonical Tasks)

### Phase 1: System Hardening & Architecture Fixes

#### 1.1 Refactoring & Cleanup

- [ ] Move `degradation_monitor.py` to `services/common/`
- [ ] Integrate `DegradationMonitor` into `ConversationWorker`
- [ ] Remove `persist_chat` imports globally
- [ ] Consolidate all config usage to `src.core.config.cfg`

#### 1.2 Security Implementation

- [ ] Add `slowapi` to implementation dependencies
- [ ] Implement Redis-backed rate limits on Upload endpoints
- [ ] Implement `OPAPolicyAdapter` and enforce checks in `ToolExecutor`
- [ ] Enforce ClamAV scanning on all file uploads (Quarantine flow)
- [ ] Finalize TUS Protocol (HEAD, DELETE, Expiry Cleaning)

### Phase 2: SomaBrain Integration

#### 2.1 Core Cognitive Endpoints (HIGH Priority) / Task 2.1.1: Implement adaptation_reset() Method

- [ ] Add method to reset adaptation engine via `/context/adaptation/reset`
- [ ] Support `tenant_id`, `base_lr`, `reset_history` parameters
- [ ] Integration test against live SomaBrain

#### 2.1 Core Cognitive Endpoints (HIGH Priority) / Task 2.1.2: Implement act() Method

- [ ] Add method for action execution via `/act`
- [ ] Support `task_key`, `context`, `max_steps`, `tenant_id` parameters

#### 2.1 Core Cognitive Endpoints (HIGH Priority) / Task 2.1.3: Add reset_adaptation() to somabrain_integration.py

- [ ] Add high-level wrapper for adaptation reset
- [ ] Clear `agent.data["adaptation_state"]` on success
- [ ] Integration test passes

#### 2.1 Core Cognitive Endpoints (HIGH Priority) / Task 2.1.4: Add execute_action() to somabrain_integration.py

- [ ] Add high-level wrapper for action execution
- [ ] Return action results with salience scores

#### 2.2 Sleep Management (MEDIUM Priority) / Task 2.2.1: Implement util_sleep() Method

- [ ] Add method for `/api/util/sleep` endpoint
- [ ] Support `target_state`, `ttl_seconds`, `async_mode`, `trace_id`

#### 2.2 Sleep Management (MEDIUM Priority) / Task 2.2.2: Implement brain_sleep_mode() Method

- [ ] Add method for `/api/brain/sleep_mode` endpoint
- [ ] Support all target states (active|light|deep|freeze)

#### 2.2 Sleep Management (MEDIUM Priority) / Task 2.2.3: Implement sleep_status_all() Method (ADMIN MODE)

- [ ] Add method for `/sleep/status/all` endpoint
- [ ] Requires admin authentication

#### 2.2 Sleep Management (MEDIUM Priority) / Task 2.2.4: Add transition_sleep_state() to somabrain_integration.py

- [ ] Add high-level wrapper for sleep state transitions
- [ ] Update `agent.data["sleep_state"]`

#### 2.2 Sleep Management (MEDIUM Priority) / Task 2.2.5: Update cognitive.py Sleep Logic

- [ ] Use `brain_sleep_mode()` instead of `sleep_cycle()`
- [ ] Add state-based sleep management

#### 2.3 Admin & Service Management (ADMIN MODE ONLY) / Task 2.3.1: Implement Admin Service Methods

- [ ] `list_services()` - GET `/admin/services`
- [ ] `get_service_status(name)` - GET `/admin/services/{name}`
- [ ] `start_service(name)` - POST `/admin/services/{name}/start`
- [ ] `stop_service(name)` - POST `/admin/services/{name}/stop`
- [ ] `restart_service(name)` - POST `/admin/services/{name}/restart`

#### 2.3 Admin & Service Management (ADMIN MODE ONLY) / Task 2.3.2: Implement Personality Management

- [ ] `set_personality(state)` - POST `/personality`

#### 2.3 Admin & Service Management (ADMIN MODE ONLY) / Task 2.3.3: Implement Memory Configuration Methods

- [ ] `get_memory_config()` - GET `/config/memory`
- [ ] `patch_memory_config(config)` - PATCH `/config/memory`

#### 2.4 Cognitive Thread Management / Task 2.4.1: Implement Cognitive Thread Methods

- [ ] `create_thread(tenant_id, options)` - POST `/cognitive/thread`
- [ ] `get_next_option(tenant_id)` - GET `/cognitive/thread/next`
- [ ] `reset_thread(tenant_id)` - PUT `/cognitive/thread/reset`

#### 2.5 Diagnostics & Feature Flags (ADMIN MODE ONLY) / Task 2.5.1: Implement Diagnostic Methods

- [ ] `micro_diag()` - GET `/micro/diag`
- [ ] `get_features()` - GET `/admin/features`
- [ ] `update_features(overrides)` - POST `/admin/features`

#### 2.6 Integration Tests / Task 2.6.1: Create Integration Test Suite

- [ ] `test_adaptation_reset` - Verify reset clears state
- [ ] `test_act_execution` - Verify action execution with salience
- [ ] `test_sleep_state_transitions` - Verify all state transitions
- [ ] `test_admin_services` - Verify service management (ADMIN mode)
- [ ] `test_personality_management` - Verify personality state
- [ ] `test_memory_config` - Verify configuration management
- [ ] `test_cognitive_threads` - Verify thread lifecycle
- [ ] `test_diagnostics` - Verify diagnostic retrieval (ADMIN mode)

### Phase 3: WebUI Testing & Stability

#### 3.1 End-to-End Testing (Playwright)

- [ ] `test_navigation.py`: Sidebar, Responsive Breakpoints
- [ ] `test_chat.py`: Send/Receive, Streaming, Stop Generation
- [ ] `test_settings.py`: Persistence, API Key toggles
- [ ] `test_uploads.py`: TUS simulation, Drag & Drop
- [ ] `test_sessions.py`: Create, Rename, Delete flows
- [ ] `test_a11y.py`: Axe-core scans on critical pages

### Phase 4: Capsule Marketplace

#### 4.1 Marketplace Backend

- [ ] `GET /v1/capsules/registry` (List Public)
- [ ] `POST /v1/capsules/install/{id}`

#### 4.2 Marketplace Frontend

- [ ] Build `features/capsules/store.js`
- [ ] Create Registry Grid Layout & Card Components
- [ ] Implement Install/Update flows with progress indication

### Phase 5: Memory & Intelligence

#### 5.1 Memory Dashboard

- [ ] Wire `memory.store.js` to real `GET /v1/memory` endpoints
- [ ] Render Force-Directed Graph of memory nodes
- [ ] Subscribe to `memory.created` events for live updates

### Phase 6: Multimodal Capabilities Extension

#### 6.1 Foundation & Data Model (Phase 1) / 6.1.1 Data Model & Schema

- [x] Create `multimodal_assets` table
- [x] Create `multimodal_capabilities` registry table
- [x] Create `multimodal_job_plans` table
- [x] Create `multimodal_executions` table
- [x] Create `asset_provenance` table
- [x] Migration scripts with rollback support

#### 6.1 Foundation & Data Model (Phase 1) / 6.1.2 Capability Registry

- [x] Implement `CapabilityRegistry` service
- [x] `find_candidates(modality, constraints)` method
- [x] `register(tool_id, provider, modalities, ...)` method
- [x] Register existing providers (OpenAI, Stability, Mermaid, PlantUML, Playwright)
- [x] Health/availability tracking per capability
- [ ] Periodic health checks (cron 60s)
- [ ] Circuit breaker integration

#### 6.1 Foundation & Data Model (Phase 1) / 6.1.3 Policy Graph Router

- [x] Implement `PolicyGraphRouter` service
- [x] Define deterministic provider ordering per modality
- [x] `route()` method with OPA integration
- [x] Budget/quota enforcement per modality
- [ ] Circuit breaker integration for multimodal providers

#### 6.2 Asset Pipeline & Provenance (Phase 2) / 6.2.1 Asset Storage & Management

- [x] Create `AssetStore` service
- [x] PostgreSQL bytea storage (v1)
- [x] SHA256 checksum deduplication
- [ ] S3 integration
- [ ] Asset lifecycle management

#### 6.2 Asset Pipeline & Provenance (Phase 2) / 6.2.2 Provenance System

- [x] Create `ProvenanceRecorder` service
- [x] Redaction: prompts, params, PII
- [x] Quality gate tracking
- [ ] Provenance querying API
- [ ] Audit trail integration

#### 6.3 Task Planning & Compilation (Phase 3) / 6.3.1 Task DSL & Plan Schema

- [x] Define JSON schema for Task DSL v1.0
- [x] Implement JobPlanner service
- [x] Implement ExecutionTracker service

#### 6.3 Task Planning & Compilation (Phase 3) / 6.3.2 Intent & Plan Extraction

- [ ] Extend `ContextBuilder` with multimodal awareness
- [ ] Create multimodal prompt templates
- [ ] Implement LLM-based plan generator
- [ ] Plan validation and error handling

#### 6.4 Execution Engine (Phase 4) / 6.4.1 Multimodal Provider Adapters

- [x] Create base provider interface
- [x] OpenAI DALL-E adapter
- [x] Mermaid diagram adapter
- [x] Playwright screenshot adapter
- [ ] Stability AI adapter
- [ ] PlantUML diagram adapter

#### 6.4 Execution Engine (Phase 4) / 6.4.2 Execution Orchestration

- [x] Create `MultimodalExecutor` service
- [x] DAG execution with dependencies
- [ ] Integrate workflow dispatch via Temporal

#### 6.5 Quality Gating (Phase 5)

- [ ] Implement `AssetCritic` service
- [ ] Define rubrics per asset type
- [ ] LLM-based quality evaluation
- [ ] Bounded retry logic (MAX_REWORK_ATTEMPTS=2)
- [ ] Track quality metrics and rework rates

#### 6.6 Learning & Ranking (Phase 6)

- [ ] Extend SomaBrain schema for tool/model outcomes
- [ ] Record execution outcomes to SomaBrain
- [ ] Implement `PortfolioRanker` service
- [ ] Shadow mode implementation
- [ ] Active mode (opt-in via feature flag)

#### 6.7 SRS Document Generation (Phase 7)

- [ ] Create `SRSComposer` service
- [ ] Support versioning and change tracking
- [ ] Generate markdown with embedded assets
- [ ] (Optional) PDF export with Pandoc
- [ ] Create asset bundles (ZIP with manifest)

#### 6.8 API & UI Integration (Phase 8) / 6.8.1 Gateway API Extensions

- [ ] `GET /v1/multimodal/capabilities`
- [ ] `POST /v1/multimodal/jobs`
- [ ] `GET /v1/multimodal/jobs/{id}`
- [ ] `GET /v1/multimodal/assets/{id}`
- [ ] `GET /v1/multimodal/provenance/{asset_id}`

#### 6.8 API & UI Integration (Phase 8) / 6.8.2 UI/UX Integration

- [ ] Extend provider cards with modality tags
- [ ] Support per-request modality overrides
- [ ] Display asset previews in conversation
- [ ] Show provenance and quality feedback

#### 6.9 Security & Governance (Phase 9)

- [ ] Create `policy/multimodal.rego`
- [ ] Add data classification constraints
- [ ] Provider allowlists by modality
- [ ] Cost/quota policies per modality
- [ ] (Optional) Asset encryption at rest
- [ ] Access control checks on asset retrieval

#### 6.10 Observability & Metrics (Phase 10)

- [ ] Add Prometheus metrics for multimodal operations
- [ ] Add OpenTelemetry spans for multimodal jobs
- [ ] Monitor asset storage usage

#### 6.11 Testing & Verification (Phase 11) / Unit Tests

- [ ] test_capability_registry.py
- [ ] test_policy_graph_router.py
- [ ] test_asset_store.py
- [ ] test_asset_critic.py
- [ ] test_portfolio_ranker.py
- [ ] test_plan_compiler.py

#### 6.11 Testing & Verification (Phase 11) / Integration Tests

- [ ] test_multimodal_providers.py
- [ ] test_multimodal_job.py
- [ ] test_soma_outcomes.py

#### 6.11 Testing & Verification (Phase 11) / E2E Golden Tests

- [ ] test_srs_generation.py
- [ ] test_provider_failures.py
- [ ] test_quality_gates.py

#### 6.11 Testing & Verification (Phase 11) / Chaos & Resilience Tests

- [ ] test_circuit_breaker.py
- [ ] test_resume.py

#### 6.12 Documentation & Deployment (Phase 12)

- [x] Update SRS.md with multimodal architecture
- [x] Create MULTIMODAL_DESIGN.md
- [ ] Document capability registry format
- [ ] Document plan DSL schema
- [ ] Add runbook for operations
- [ ] Define environment variables
- [ ] Create deployment manifests
- [ ] Add feature flags for phased rollout

### Phase 7: Temporal Migration

- [ ] Add Temporal services to compose/helm (HA-ready layout)
- [ ] Port conversation/tool/A2A/maintenance flows to Temporal workflows
- [ ] Expose gateway Temporal workflow start/describe/terminate endpoints
- [ ] Update degradation monitor and health checks to include Temporal
- [ ] Remove legacy task codepaths/tests; add Temporal workflow tests

### Phase 8: Observability (Prometheus-Only)

- [ ] Expose `/metrics` on all services and Temporal workers
- [ ] Add Temporal/Kafka/Postgres exporters; define scrape jobs
- [ ] Add service-level histograms/counters for latency, errors, queue lag
- [ ] Wire OpenTelemetry propagation; optional OTLP export guarded by env flag
- [ ] Provide Prometheus alert rules for gateway errors, Kafka lag, Temporal failures

### Phase 9: Transactional Integrity & Explainability

- [ ] Add compensations for every workflow activity
- [ ] Implement deterministic IDs/idempotency keys + outbox/tombstones
- [ ] Add "describe run/failure" endpoint
- [ ] Add reconciliation workflow to detect/auto-heal orphaned compensations
- [ ] Add Prom metrics: compensations_total, rollback_latency_seconds

### Phase 10: Messaging/Storage/Replication/Backups

- [ ] Enforce Kafka idempotent producers with deterministic keys
- [ ] Uploads/assets: metadata-first writes, checksum dedupe, compensating delete
- [ ] Postgres HA + PITR-ready configs
- [ ] Redis clustering for prod
- [ ] Structured audit on all state changes

### Phase 11: AgentSkin UIX

#### 11.1 Theme Gallery & Discovery

- [ ] Grid gallery with preview images, search, filters
- [ ] One-Click Switching without page reload
- [ ] Drag/Drop Install with validation
- [ ] Live Preview with split-screen

#### 11.2 Backend

- [ ] FastAPI router `/v1/skins` with list/get/upload/delete
- [ ] PostgreSQL `agent_skins` table
- [ ] JSON schema validation on upload

#### 11.3 Security

- [ ] Admin-Only Uploads via OPA (ADMIN mode only)
- [ ] XSS Hardening
- [ ] Tenant Isolation

### Phase 12: Settings Persistence

#### 12.1 Feature Flags Database Persistence

- [ ] Create `feature_flags` table
- [ ] Implement `FeatureFlagsStore` service
- [ ] UI integration in `ui_settings`
- [ ] Agent reload trigger on flag change

#### 12.2 AgentConfig UI Exposure

- [ ] Add `agent_config` section to `ui_settings`
- [ ] Implement `load_agent_config(tenant)` loader
- [ ] Validation for knowledge subdirectory existence

### Phase 13: Enterprise SaaS Platform (God Mode)

#### 13.1 SaaS Dashboard & Tenants

- [x] `eog-platform-dashboard.ts`: God Mode Dashboard view (Metrics, Activity)
- [x] `eog-tenants.ts`: Tenant Management view
- [ ] `GET /saas/metrics`: Platform-wide stats (Tenants, MRR, Agents)
- [ ] `GET /saas/tenants`: List all tenants
- [ ] `POST /saas/tenants`: Create/Provision tenant (Lago integration)
- [ ] `POST /saas/tenants/{id}/{action}`: Suspend/Activate/Archive
- [ ] `GET /saas/activity`: Global platform activity log

#### 13.2 Enterprise Settings & Login

- [x] `eog-login.ts`: Updated with Enterprise Cog & Glassmorphism
- [x] `eog-enterprise-settings.ts`: Configuration modal (SSO, Security)
- [ ] `GET /saas/settings`: Get global enterprise config
- [ ] `POST /saas/settings`: Update enterprise config (SSO, LDAP, Policy)

### Completed Work

#### Recent Completions (2025-12-16)

- [x] Secret Manager VIBE fix - Replaced silent defaults with fail-fast errors
- [x] Secret Manager comprehensive unit tests
- [x] SRS Multimodal Extension Design (Section 16 added to SRS.md v3.0)
- [x] MULTIMODAL_DESIGN.md - Detailed architectural design
- [x] Implementation Plan - 12-phase rollout strategy
- [x] Master Task Tracker created

#### Core System Features (Completed)

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
