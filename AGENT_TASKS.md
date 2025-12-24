# AGENT_TASKS — SomaAgent01 Complete Implementation Tracker

**Document ID:** SA01-AGENT-TASKS-2025-12  
**Version:** 2.0  
**Updated:** 2025-12-24  
**Status:** CANONICAL — Agent Single Source of Truth

> **CRITICAL:** This is the SINGLE task file for tracking ALL implementation.
> Status: `[ ]` Not Started | `[/]` In Progress | `[x]` Complete | `[!]` Blocked

---

## Progress Summary

| Phase | Focus | Status | Tasks |
|-------|-------|--------|-------|
| **0** | SaaS Architecture (Docs) | ✅ Complete | 15/15 |
| **1** | Foundation | ⏳ Ready | 0/28 |
| **2** | Authentication | ⬜ Pending | 0/20 |
| **3** | Platform Admin (Eye of God) | ⬜ Pending | 0/35 |
| **4** | Tenant Admin | ⬜ Pending | 0/28 |
| **5** | Agent UI | ⬜ Pending | 0/35 |
| **6** | SomaBrain Integration | ⬜ Pending | 0/25 |
| **7** | Multimodal & Advanced | ⬜ Pending | 0/40 |

**Total:** ~226 tasks | **Complete:** 15 | **Timeline:** 11-14 weeks

---

## Phase 0: SaaS Architecture Documentation ✅

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

---

## Phase 1: Foundation ✅ COMPLETE

### 1.1 Database Models (Django) ✅ COMPLETE
- [x] SubscriptionTier model (limits, pricing, lago_code)
- [x] Tenant model (org, slug, status, subscription FK)
- [x] TenantUser model (user, tenant, role, status)
- [x] Agent model (tenant FK, config, features, status)
- [x] AgentUser model (agent access, modes allowed)
- [x] AuditLog model (all events)
- [x] SaasFeature, TierFeature, FeatureProvider models
- [x] UsageRecord model
- [x] Initial migration (36KB)

### 1.2 SpiceDB Schema ✅ COMPLETE
- [x] Platform definition (God Mode)
- [x] saas_admin definition with platform->manage_roles
- [x] Tenant definition with role hierarchy
- [x] Agent definition with mode permissions
- [x] Resource permissions (conversation, memory, cognitive, voice, tool)
- [x] SpiceDB client wrapper exists (admin/common/auth.py)
- [x] @require_permission decorator exists

### 1.3 Keycloak Setup ✅ COMPLETE
- [x] Realm config: infrastructure/keycloak/realm-somaagent.json
- [x] 8 platform roles (saas_admin → viewer)
- [x] Google OAuth provider configured
- [x] GitHub OAuth provider configured
- [x] TOTP MFA configuration
- [x] Token lifetimes (15min access, 30min session)
- [x] Custom tenant_id claim mapper

### 1.4 Base Lit Components ✅ COMPLETE
- [x] Design tokens CSS (webui/src/styles/tokens.css - 383 lines)
- [x] saas-* components (sidebar, data-table, stat-card, etc.)
- [x] soma-* components (button, card, input, modal, etc.)
- [x] 22 components total
- [x] 33 views
- [x] 5 stores

### 1.4 Base Lit Components
- [ ] Design tokens CSS (somastack-tokens.css)
- [ ] saas-shell (app container)
- [ ] saas-nav (sidebar navigation)
- [ ] saas-card, saas-table, saas-modal
- [ ] saas-form, saas-input, saas-button
- [ ] saas-toast, saas-badge
- [ ] saas-degraded-banner

---

## Phase 2: Authentication

### 2.1 Login Flow ✅ COMPLETE
- [x] POST /auth/token (password grant + OAuth code)
- [x] POST /auth/refresh (token refresh)
- [x] GET /auth/me (current user info)
- [x] POST /auth/logout (session termination)
- [x] Role-based redirect paths
- [x] Permission mapping from Keycloak roles
- [x] keycloak-service.ts (300 lines) - frontend
- [x] auth-store.ts (270 lines) - Lit Context
- [x] saas-login.ts (33KB) - login view

### 2.2 MFA Setup ⏳ IN PROGRESS
- [ ] POST /auth/mfa/setup - Initialize TOTP
- [ ] POST /auth/mfa/verify - Verify TOTP code
- [ ] saas-mfa-setup.ts view

### 2.3 Password Reset
- [ ] Reset request flow
- [ ] Email integration (via Keycloak)

### 2.4 Invitation Flow
- [ ] POST /saas/users/invite - Send invitation
- [ ] GET /auth/invite/{token} - Accept invitation
- [ ] Onboarding wizard

### 2.5 Session Management ⏳ PARTIAL
- [x] Token refresh (auto-scheduled in frontend)
- [ ] Concurrent session limits
- [ ] Impersonation tokens (SAAS admin only)

---

## Phase 3: Platform Admin (Eye of God) ✅ COMPLETE

### 3.1 Platform Dashboard ✅
- [x] GET /saas/dashboard (dashboard.py - 90 lines)
- [x] DashboardMetrics, TopTenant, RecentEvent schemas
- [x] saas-platform-dashboard.ts view (32KB)

### 3.2 Tenant Management ✅
- [x] GET /saas/tenants
- [x] POST /saas/tenants
- [x] PATCH /saas/tenants/{id}
- [x] DELETE /saas/tenants/{id}
- [x] POST /saas/tenants/{id}/suspend
- [x] POST /saas/tenants/{id}/activate
- [x] tenants.py (165 lines)
- [x] saas-tenants.ts view (16KB)

### 3.3 Role Management ✅
- [x] GET /saas/settings/roles
- [x] PATCH /saas/settings/roles/{id}
- [x] settings.py (186 lines)
- [x] saas-admin-roles-list.ts view

### 3.4 Subscription Tier Builder ✅
- [x] GET /saas/tiers
- [x] POST /saas/tiers
- [x] PATCH /saas/tiers/{id}
- [x] DELETE /saas/tiers/{id}
- [x] tiers.py (173 lines)
- [x] saas-subscriptions.ts view (27KB)

### 3.5 Platform Billing ✅
- [x] GET /saas/billing (BillingMetrics, RevenueByTier)
- [x] GET /saas/billing/invoices
- [x] GET /saas/billing/usage
- [x] GET /saas/billing/usage/{tenant_id}
- [x] billing.py (128 lines)
- [x] saas-billing.ts view (23KB)

### 3.6 Feature Management ✅
- [x] GET /saas/features
- [x] GET /saas/features/{id}
- [x] GET /saas/features/{code}/providers
- [x] POST /saas/features/tiers/{tier_id}/{feature_code}
- [x] features.py (213 lines)

### 3.7 User Management ✅
- [x] GET /saas/admin/users
- [x] POST /saas/admin/users
- [x] GET /saas/admin/users/{id}
- [x] PUT /saas/admin/users/{id}
- [x] DELETE /saas/admin/users/{id}
- [x] users.py (248 lines)
- [x] saas-tenant-users.ts view (19KB)

### 3.8 Agent Management ✅
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

### 3.9 Settings & API Keys ⏳ PARTIAL
- [x] GET /saas/settings/api-keys
- [x] DELETE /saas/settings/api-keys/{id}
- [x] GET /saas/settings/models
- [x] PATCH /saas/settings/models/{id}
- [x] POST /saas/settings/sso
- [x] POST /saas/settings/sso/test
- [ ] POST /saas/settings/api-keys (key generation)

### 3.7 Platform Health
- [ ] Health check endpoints per service
- [ ] saas-health-dashboard view
- [ ] Degradation alerts

---

## Phase 4: Tenant Admin ✅ COMPLETE

### 4.1 Tenant Dashboard ✅
- [x] saas-tenant-dashboard.ts (539 lines)
- [x] Quota stats (Agents, Users, Tokens, Storage)
- [x] Agent list with status indicators
- [x] Quick actions grid
- [x] Sidebar navigation

### 4.2 User Management ✅
- [x] GET /saas/admin/users (with filtering, pagination)
- [x] POST /saas/admin/users (invite)
- [x] PUT /saas/admin/users/{id}
- [x] DELETE /saas/admin/users/{id}
- [x] users.py (248 lines)
- [x] saas-tenant-users.ts view (19KB)

### 4.3 Agent Management ✅
- [x] GET /saas/admin/agents
- [x] POST /saas/admin/agents
- [x] PUT /saas/admin/agents/{id}
- [x] DELETE /saas/admin/agents/{id}
- [x] POST /saas/admin/agents/{id}/start
- [x] POST /saas/admin/agents/{id}/stop
- [x] GET /saas/admin/quota
- [x] tenant_agents.py (356 lines)
- [x] saas-tenant-agents.ts view (20KB)

### 4.4 Tenant Roles ✅
- [x] Roles integrated via users.py
- [x] Role selector in user management

### 4.5 Tenant Settings ✅
- [x] saas-settings.ts view (33KB)

### 4.6 Tenant Billing
- [ ] GET /api/v2/admin/billing
- [ ] POST /api/v2/admin/billing/upgrade
- [ ] saas-tenant-billing view

### 4.7 Audit Log
- [ ] GET /api/v2/admin/audit
- [ ] saas-audit-log view
- [ ] Filters, CSV export

---

## Phase 5: Agent UI 🟢🔵🟣⚪⚫

### 5.1 Agent Configuration (ADM Mode)
- [ ] GET /api/v2/agent/{id}/config
- [ ] PUT /api/v2/agent/{id}/config
- [ ] saas-agent-config view
- [ ] Model configuration tabs
- [ ] Feature flags, MCP servers

### 5.2 Chat Interface (STD Mode)
- [ ] GET /api/v2/chat/conversations
- [ ] POST /api/v2/chat/conversations
- [ ] POST /api/v2/chat/messages
- [ ] WebSocket streaming
- [ ] saas-chat-view layout
- [ ] saas-conversation-list sidebar
- [ ] saas-chat-panel messages
- [ ] saas-chat-input with attachments

### 5.3 Memory Browser
- [ ] GET /api/v2/memory
- [ ] POST /api/v2/memory/search
- [ ] DELETE /api/v2/memory/{id}
- [ ] saas-memory-view layout
- [ ] Virtual scrolling
- [ ] Memory graph visualization

### 5.4 Developer Mode (DEV)
- [ ] saas-debug-console
- [ ] saas-api-logs
- [ ] saas-mcp-inspector
- [ ] saas-tool-playground
- [ ] saas-ws-monitor

### 5.5 Trainer Mode (TRN)
- [ ] GET /api/v2/cognitive/neuromodulators
- [ ] PUT /api/v2/cognitive/neuromodulators
- [ ] POST /api/v2/cognitive/sleep-cycle
- [ ] saas-cognitive-panel
- [ ] Neuromodulator sliders
- [ ] Sleep cycle controls

### 5.6 Voice Integration
- [ ] Voice store (state machine)
- [ ] Local voice (Whisper/Kokoro)
- [ ] AgentVoiceBox WebSocket
- [ ] saas-voice-button
- [ ] saas-voice-overlay

### 5.7 Degraded Mode (DGR)
- [ ] DegradationMonitor integration
- [ ] Degradation banner
- [ ] Session-only memory fallback
- [ ] LLM fallback chain

---

## Phase 6: SomaBrain Integration

### 6.1 Core Endpoints
- [ ] adaptation_reset() - POST /context/adaptation/reset
- [ ] act() - POST /act with salience
- [ ] brain_sleep_mode() - POST /api/brain/sleep_mode
- [ ] util_sleep() - POST /api/util/sleep

### 6.2 Memory Endpoints
- [ ] personality_set() - POST /personality
- [ ] memory_config_get() - GET /config/memory
- [ ] memory_config_patch() - PATCH /config/memory

### 6.3 Cognitive Thread
- [ ] cognitive_thread_create()
- [ ] cognitive_thread_next()
- [ ] cognitive_thread_reset()

### 6.4 Admin Endpoints (ADMIN mode only)
- [ ] list_services()
- [ ] get_service_status()
- [ ] start/stop/restart_service()
- [ ] sleep_status_all()
- [ ] micro_diag()
- [ ] get_features() / update_features()

### 6.5 Integration Tests
- [ ] test_adaptation_reset
- [ ] test_act_execution
- [ ] test_sleep_transitions
- [ ] test_admin_services

---

## Phase 7: Multimodal & Advanced Features

### 7.1 Capability Registry
- [ ] CapabilityRegistry service
- [ ] register(), find_candidates()
- [ ] Health tracking, circuit breakers

### 7.2 Asset Pipeline
- [ ] AssetStore service
- [ ] SHA256 deduplication
- [ ] S3 integration
- [ ] ProvenanceRecorder

### 7.3 Multimodal Execution
- [ ] OpenAI DALL-E adapter
- [ ] Mermaid diagram adapter
- [ ] Playwright screenshot adapter
- [ ] DAG execution engine

### 7.4 Quality Gating
- [ ] AssetCritic service
- [ ] LLM quality evaluation
- [ ] Bounded retry logic

### 7.5 Temporal Workflows
- [ ] Conversation workflow
- [ ] Tool execution workflow
- [ ] A2A workflow
- [ ] Maintenance workflows

### 7.6 Observability
- [ ] Prometheus metrics on all services
- [ ] OpenTelemetry spans
- [ ] Grafana dashboards

---

## Document References

| Document | Lines | Purpose |
|----------|-------|---------|
| CANONICAL_SAAS_DESIGN.md | 795 | Master design |
| CANONICAL_USER_JOURNEYS_SRS.md | 758 | User journeys |
| CANONICAL_REQUIREMENTS.md | 433 | All requirements |
| CANONICAL_TASKS.md | 505 | Legacy task list |
| SRS-PERMISSION-MATRIX.md | 608 | Permission architecture |
| docs/srs/* | 7 files | Role-specific SRS |
| docs/tasks/* | 4 files | Phase task details |

---

## Quick Start: Phase 1

```bash
cd /Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgent01

# 1. Database models
# Edit: admin/core/models/

# 2. SpiceDB schema
# Edit: schemas/spicedb/schema.zed

# 3. Keycloak
# Edit: infrastructure/keycloak/

# 4. Lit components
# Edit: webui/src/components/
```

---

**Last Updated:** 2025-12-24
**Maintained By:** Gemini Agent

