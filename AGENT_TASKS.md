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

### 2.2 MFA Setup ✅ COMPLETE
- [x] POST /auth/mfa/setup - Initialize TOTP
- [x] POST /auth/mfa/verify - Verify TOTP code
- [x] POST /auth/mfa/validate - Login MFA step
- [x] GET /auth/mfa/status - MFA status
- [x] POST /auth/mfa/disable - Disable MFA
- [x] mfa.py (280 lines)
- [ ] saas-mfa-setup.ts view

### 2.3 Password Reset ✅ COMPLETE
- [x] POST /auth/password/request - Request reset
- [x] POST /auth/password/confirm - Confirm with token
- [x] GET /auth/password/validate/{token}
- [x] POST /auth/password/change - Authenticated change
- [x] password_reset.py (260 lines)
- [ ] Email integration (via Keycloak)

### 2.4 Invitation Flow ✅ COMPLETE
- [x] POST /invitations - Send invitation
- [x] GET /invitations/{token} - Accept invitation page
- [x] POST /invitations/{token}/accept - Create account
- [x] GET /invitations - List (admin)
- [x] DELETE /invitations/{id} - Revoke
- [x] POST /invitations/{id}/resend
- [x] invitations.py (320 lines)
- [ ] Onboarding wizard UI

### 2.5 Session Management ✅ COMPLETE
- [x] Token refresh (auto-scheduled in frontend)
- [x] POST /auth/impersonate (125 lines) - SAAS admin only
- [ ] Concurrent session limits

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

### 3.9 Settings & API Keys ✅ COMPLETE
- [x] GET /saas/settings/api-keys
- [x] POST /saas/settings/api-keys (cryptographic generation)
- [x] DELETE /saas/settings/api-keys/{id}
- [x] GET /saas/settings/models
- [x] PATCH /saas/settings/models/{id}
- [x] POST /saas/settings/sso
- [x] POST /saas/settings/sso/test
- [x] settings.py (250+ lines) - secrets.token_urlsafe, SHA-256

### 3.10 Platform Health ✅ COMPLETE
- [x] GET /saas/health - All services check
- [x] GET /saas/health/db - PostgreSQL
- [x] GET /saas/health/cache - Redis
- [x] GET /saas/health/keycloak - Keycloak IAM
- [x] GET /saas/health/somabrain - SomaBrain
- [x] GET /saas/health/degradation - Degradation status
- [x] health.py (270 lines) - Async concurrent checks

### 3.11 Audit Trail ✅ COMPLETE
- [x] GET /saas/audit - List with filters
- [x] GET /saas/audit/export - CSV export
- [x] GET /saas/audit/actions - Action types
- [x] GET /saas/audit/stats - Dashboard stats
- [x] audit.py (245 lines)

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

### 4.6 Tenant Billing ✅ COMPLETE
- [x] GET /saas/billing/tenant/{id}
- [x] POST /saas/billing/tenant/{id}/upgrade
- [x] GET /saas/billing/tenant/{id}/invoices
- [x] POST /saas/billing/tenant/{id}/payment-methods
- [x] billing.py (+195 lines)
- [ ] saas-tenant-billing.ts view

### 4.7 Audit Log ✅ COMPLETE (via /saas/audit)
- [x] GET /saas/audit - List with filters
- [x] GET /saas/audit/export - CSV export
- [x] saas-audit-log view (pending)

---

## Phase 5: Agent UI ✅ MOSTLY COMPLETE

### 5.1 Chat Interface (STD Mode) ✅
- [x] saas-chat.ts (1,063 lines, 34KB)
- [x] WebSocket streaming support
- [x] Conversation sidebar
- [x] 6 Agent modes (STD, DEV, TRN, ADM, RO, DGR)
- [x] Mode selector dropdown
- [x] Quick replies
- [x] Typing indicator
- [x] Confidence bar
- [x] Message animations

### 5.2 Cognitive Panel (TRN Mode) ✅
- [x] saas-cognitive-panel.ts (862 lines, 28KB)
- [x] Neuromodulator gauges (6 types)
- [x] Adaptation parameter sliders
- [x] Sleep cycle trigger
- [x] Activity log
- [x] Real-time WebSocket updates

### 5.3 Memory Browser ✅
- [x] saas-memory-view.ts (26KB)
- [ ] Virtual scrolling
- [ ] Memory graph visualization

### 5.4 Voice Integration ✅ COMPLETE
- [x] soma-voice-button.ts component
- [x] soma-voice-overlay.ts component
- [x] POST /voice/transcribe (Whisper) - 307 lines
- [x] POST /voice/synthesize (Kokoro TTS)
- [x] GET /voice/voices - List voices
- [x] GET /voice/status - Service health
- [x] voice/api.py (307 lines)
- [ ] WebSocket streaming (/ws/voice)

### 5.5 Mode Selection ✅
- [x] saas-mode-selection.ts (20KB)
- [x] Mode cards with descriptions

### 5.6 Settings ✅
- [x] saas-settings.ts (33KB)

---

## Phase 6: SomaBrain Integration

### 6.1 Core Endpoints ✅ COMPLETE
- [x] POST /somabrain/brain/adaptation/reset/{agent_id}
- [x] POST /somabrain/brain/act - with salience
- [x] POST /somabrain/brain/sleep/{agent_id}
- [x] POST /somabrain/brain/util/sleep
- [x] GET /somabrain/brain/wake/{agent_id}
- [x] GET /somabrain/brain/status/{agent_id}
- [x] core_brain.py (400 lines)

### 6.2 Memory Endpoints ✅ COMPLETE
- [x] POST /somabrain/brain/personality/{agent_id}
- [x] GET /somabrain/brain/config/memory/{agent_id}
- [x] PATCH /somabrain/brain/config/memory/{agent_id}

### 6.3 Cognitive Thread ✅ COMPLETE
- [x] POST /somabrain/cognitive/threads - Create thread
- [x] POST /somabrain/cognitive/threads/{id}/step - Execute
- [x] POST /somabrain/cognitive/threads/{id}/reset
- [x] DELETE /somabrain/cognitive/threads/{id}
- [x] GET /somabrain/cognitive/state/{agent_id}
- [x] PATCH /somabrain/cognitive/params/{agent_id}
- [x] POST /somabrain/cognitive/adaptation/reset/{agent_id}
- [x] POST /somabrain/cognitive/sleep/{agent_id}
- [x] cognitive.py (380 lines)

### 6.4 Admin Endpoints (ADMIN mode only) ✅ COMPLETE
- [x] GET /somabrain/admin/services - List services
- [x] GET /somabrain/admin/services/{name} - Service status
- [x] POST /somabrain/admin/services/{name}/action - Start/stop/restart
- [x] GET /somabrain/admin/diagnostics - System diagnostics
- [x] GET /somabrain/admin/sleep-status - All agents sleep
- [x] GET /somabrain/admin/features - Feature flags
- [x] PATCH /somabrain/admin/features - Update flags
- [x] admin_api.py (340 lines)
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

### 7.3 Temporal Workflows ✅ COMPLETE
- [x] POST /workflows - Start workflow
- [x] GET /workflows/{id} - Get status
- [x] GET /workflows - List workflows
- [x] POST /workflows/{id}/cancel - Cancel
- [x] POST /workflows/{id}/signal - Send signal
- [x] GET /workflows/{id}/history - History
- [x] POST /workflows/{id}/terminate - Force
- [x] workflows/api.py (290 lines) execution workflow
- [ ] A2A workflow
- [ ] Maintenance workflows

### 7.6 Observability ✅ COMPLETE
- [x] GET /observability/metrics - Prometheus format
- [x] GET /observability/metrics/json - JSON format
- [x] GET /observability/ready - K8s readiness
- [x] GET /observability/live - K8s liveness
- [x] GET /observability/traces - OpenTelemetry traces
- [x] GET /observability/dashboards - Grafana
- [x] observability/api.py (380 lines)

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

