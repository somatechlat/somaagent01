# SaaS Admin Journey — Master Implementation Tasks

**Document:** SAAS-ADMIN-JOURNEY-TASKS.md  
**Version:** 1.0.0  
**Date:** 2026-01-05  
**Target:** SaaS Admin "Day 0" Platform Setup Journey  

---

## Quick Stats

| Metric | Value |
|--------|-------|
| Total Tasks | 150+ |
| Phases | 3 |
| Effort Estimate | 6-8 weeks |
| P0 (Critical) | 85 tasks |
| P1 (Important) | 40 tasks |

---

## Journey Flow Summary

```
Login → Platform Dashboard → Health Check → Tier Setup → Model Catalog → Rate Limits → Create First Tenant
```

---

## Development Guidelines (MANDATORY)

### Style Guides — MUST USE

| File | Purpose |
|------|---------|
| [tokens.css](file:///Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgent01/webui/src/styles/tokens.css) | CSS design tokens |
| [UI_STYLE_GUIDE_EXTENSION.md](file:///Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgent01/docs/ui/UI_STYLE_GUIDE_EXTENSION.md) | Component patterns |
| [SRS-UI-ARCHITECTURE-PATTERNS.md](file:///Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgent01/docs/srs/SRS-UI-ARCHITECTURE-PATTERNS.md) | 5 reusable patterns |

### Token Usage

```css
/* ✅ DO THIS */
background: var(--saas-bg-card);
color: var(--saas-text-primary);

/* ❌ NOT THIS */
background: #ffffff;
color: #1a1a1a;
```

---

## PHASE 1: Foundation (Week 1-2)

### 1.1 Django Models

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| Create `Tenant` model | P0 | 2h | ❌ |
| Create `User` model extension | P0 | 2h | ❌ |
| Create `Agent` model | P0 | 3h | ❌ |
| Create `Subscription` model | P0 | 2h | ❌ |
| Create `SubscriptionTier` model | P0 | 1h | ❌ |
| Create `AuditLog` model | P0 | 2h | ❌ |
| Initial migration `0001_initial.py` | P0 | 1h | ❌ |
| Add indexes `0002_add_indexes.py` | P0 | 1h | ❌ |
| Add constraints `0003_add_constraints.py` | P0 | 1h | ❌ |

### 1.2 SpiceDB Authorization

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| Define platform schema | P0 | 1h | ❌ |
| Define tenant schema | P0 | 2h | ❌ |
| Define agent schema | P0 | 2h | ❌ |
| Create SpiceDB client wrapper | P0 | 2h | ❌ |
| Create permission middleware | P0 | 3h | ❌ |
| Create permission decorators | P0 | 2h | ⚠️ Partial |
| Test permission checks | P0 | 3h | ❌ |

### 1.3 Keycloak Configuration

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| Create `somaagent` realm | P0 | 1h | ❌ |
| Configure Google OAuth | P0 | 1h | ❌ |
| Configure GitHub OAuth | P0 | 1h | ❌ |
| Enable MFA (TOTP) | P0 | 1h | ❌ |
| Configure token lifetimes | P0 | 30m | ❌ |
| Create client for Django | P0 | 1h | ❌ |

### 1.4 Base Lit Components

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| `saas-shell` (app shell) | P0 | 4h | ❌ |
| `saas-nav` (navigation) | P0 | 3h | ❌ |
| `saas-card` (stat card) | P0 | 2h | ❌ |
| `saas-table` (data table) | P0 | 4h | ❌ |
| `saas-modal` (dialog) | P0 | 3h | ❌ |
| `saas-form` (form wrapper) | P0 | 3h | ❌ |
| `saas-input` (form input) | P0 | 2h | ❌ |
| `saas-button` (buttons) | P0 | 1h | ❌ |
| `saas-toast` (notifications) | P0 | 2h | ❌ |
| `saas-badge` (status badges) | P0 | 1h | ❌ |
| Design tokens CSS file | P0 | 2h | ❌ |

### 1.5 API Foundation

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| Create API app | P0 | 1h | ❌ |
| Configure routers | P0 | 1h | ❌ |
| Create auth middleware | P0 | 3h | ❌ |
| Create error handlers | P0 | 2h | ❌ |
| Create base schemas | P0 | 2h | ❌ |
| Setup OpenAPI docs | P0 | 1h | ❌ |

### 1.6 Mandatory Configuration Wizard (Day 0 Step 2)

> **CRITICAL:** Admin cannot access dashboard until this is confirmed.

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| Create `ConfigService` (read/write env/secrets) | P0 | 4h | ❌ |
| `GET /api/v2/setup/config` (masked values) | P0 | 2h | ❌ |
| `POST /api/v2/setup/config` (update & restart) | P0 | 4h | ❌ |
| `saas-setup-wizard.ts` (The "God Screen") | P0 | 6h | ❌ |
| Config Middleware (Block `/platform` if unconfigured) | P0 | 2h | ❌ |
| Validate connection to all 12 services | P0 | 4h | ❌ |

---

## PHASE 2: Authentication (Week 2-3)

### 2.1 Login Flow

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| `/auth/login` endpoint | P0 | 3h | ❌ |
| `/auth/logout` endpoint | P0 | 2h | ❌ |
| `/auth/refresh` endpoint | P0 | 2h | ❌ |
| `/auth/me` endpoint | P0 | 1h | ❌ |
| Google OAuth redirect | P0 | 2h | ❌ |
| Google OAuth callback | P0 | 3h | ❌ |
| GitHub OAuth redirect | P0 | 2h | ❌ |
| GitHub OAuth callback | P0 | 3h | ❌ |

### 2.2 Login UI

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| Create `saas-login.ts` component | P0 | 4h | ❌ |
| Implement form validation | P0 | 2h | ❌ |
| Add OAuth buttons | P0 | 2h | ❌ |
| Handle error states | P0 | 2h | ❌ |
| Add loading states | P0 | 1h | ❌ |
| Implement remember me | P1 | 1h | ❌ |

### 2.3 MFA

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| MFA setup endpoint | P0 | 3h | ❌ |
| MFA verify endpoint | P0 | 2h | ❌ |
| `saas-mfa-setup.ts` component | P0 | 4h | ❌ |
| `saas-mfa-verify.ts` component | P0 | 3h | ❌ |
| Generate backup codes | P0 | 2h | ❌ |
| Store backup codes (encrypted) | P0 | 2h | ❌ |

### 2.4 Session Management

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| Create session store (Redis) | P0 | 2h | ❌ |
| Token refresh middleware | P0 | 3h | ❌ |
| Session invalidation | P0 | 2h | ❌ |
| Active sessions list | P1 | 3h | ❌ |
| Force logout other sessions | P1 | 2h | ❌ |

### 2.5 Password Reset

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| Forgot password endpoint | P0 | 2h | ❌ |
| Reset password endpoint | P0 | 2h | ❌ |
| Email template | P0 | 1h | ❌ |
| `saas-forgot-password.ts` | P0 | 2h | ❌ |
| `saas-reset-password.ts` | P0 | 2h | ❌ |

### 2.6 Invitation Flow

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| Invitation endpoint | P0 | 3h | ❌ |
| Accept invitation endpoint | P0 | 3h | ❌ |
| Invitation email template | P0 | 1h | ❌ |
| `saas-accept-invite.ts` | P0 | 3h | ❌ |
| Handle expired invitations | P0 | 1h | ❌ |

---

## PHASE 3: Admin Interfaces (Week 3-5)

### 3.1 Platform Admin API

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| `GET /saas/stats` | P0 | 2h | ❌ |
| `GET /saas/tenants` | P0 | 2h | ❌ |
| `POST /saas/tenants` | P0 | 4h | ❌ |
| `GET /saas/tenants/{id}` | P0 | 1h | ❌ |
| `PUT /saas/tenants/{id}` | P0 | 2h | ❌ |
| `DELETE /saas/tenants/{id}` | P0 | 3h | ❌ |
| `POST /saas/tenants/{id}/suspend` | P0 | 2h | ❌ |
| `POST /saas/tenants/{id}/impersonate` | P0 | 3h | ❌ |
| `GET/PUT /saas/subscriptions` | P0 | 3h | ❌ |
| `GET /saas/billing/revenue` | P1 | 3h | ❌ |
| `GET /saas/health` | P0 | 2h | ❌ |

### 3.2 Platform Admin UI

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| `saas-platform-dashboard.ts` | P0 | 6h | ❌ |
| `saas-tenant-list.ts` | P0 | 4h | ❌ |
| `saas-tenant-create.ts` | P0 | 3h | ❌ |
| `saas-tenant-detail.ts` | P0 | 4h | ❌ |
| `saas-subscription-tiers.ts` | P0 | 4h | ❌ |
| `saas-platform-health.ts` | P0 | 4h | ❌ |
| `saas-revenue-dashboard.ts` | P1 | 5h | ❌ |

### 3.3 Tenant Admin API

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| `GET /admin/stats` | P0 | 2h | ❌ |
| `GET /admin/users` | P0 | 2h | ❌ |
| `POST /admin/users/invite` | P0 | 4h | ❌ |
| `GET/PUT/DELETE /admin/users/{id}` | P0 | 3h | ❌ |
| `POST /admin/users/{id}/resend` | P0 | 1h | ❌ |
| `GET /admin/agents` | P0 | 2h | ❌ |
| `POST /admin/agents` | P0 | 5h | ❌ |
| `GET/PUT /admin/agents/{id}` | P0 | 3h | ❌ |
| `DELETE /admin/agents/{id}` | P0 | 3h | ❌ |
| `POST /admin/agents/{id}/start` | P0 | 2h | ❌ |
| `POST /admin/agents/{id}/stop` | P0 | 2h | ❌ |
| `GET/POST/DELETE /admin/agents/{id}/users` | P0 | 3h | ❌ |
| `GET/PUT /admin/settings` | P0 | 2h | ❌ |
| `GET /admin/audit` | P0 | 3h | ❌ |
| `GET /admin/usage` | P1 | 3h | ❌ |
| `GET /admin/billing` | P1 | 2h | ❌ |
| `POST /admin/billing/upgrade` | P1 | 4h | ❌ |

### 3.4 Tenant Admin UI

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| `saas-tenant-dashboard.ts` | P0 | 5h | ❌ |
| `saas-users.ts` | P0 | 4h | ❌ |
| `saas-user-invite.ts` | P0 | 3h | ❌ |
| `saas-user-detail.ts` | P0 | 3h | ❌ |
| `saas-agents.ts` | P0 | 5h | ❌ |
| `saas-agent-create.ts` | P0 | 4h | ❌ |
| `saas-agent-config.ts` | P0 | 6h | ❌ |
| `saas-agent-users.ts` | P0 | 3h | ❌ |
| `saas-tenant-settings.ts` | P0 | 5h | ❌ |
| `saas-tenant-audit.ts` | P0 | 4h | ❌ |
| `saas-usage.ts` | P1 | 4h | ❌ |
| `saas-tenant-billing.ts` | P1 | 5h | ❌ |

### 3.5 Supporting Services

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| QuotaService implementation | P0 | 4h | ❌ |
| Quota → user invite integration | P0 | 1h | ❌ |
| Quota → agent create integration | P0 | 1h | ❌ |
| Quota warning UI component | P0 | 3h | ❌ |
| AuditService implementation | P0 | 4h | ❌ |
| Audit Kafka producer | P0 | 2h | ❌ |

### 3.6 Lago Billing Integration

| Task | Priority | Effort | Status |
|------|----------|--------|--------|
| Lago API client | P0 | 4h | ❌ |
| Create customer on tenant create | P0 | 2h | ❌ |
| Subscribe to plan | P0 | 3h | ❌ |
| Usage metering | P0 | 4h | ❌ |
| Webhook receiver | P0 | 4h | ❌ |
| Invoice display | P1 | 3h | ❌ |
| Payment method update | P1 | 4h | ❌ |

---

## CRITICAL GAPS (From Expert Analysis)

These are the high-priority gaps identified in the expert analysis:

| Gap | Fix | Priority | Effort |
|-----|-----|----------|--------|
| Sessions API placeholder | Implement Redis session storage | P0 | 1 day |
| Conversations API placeholder | Implement PostgreSQL + SomaBrain | P0 | 1 day |
| No WebSocket consumer | Add Django Channels consumer | P0 | 1 day |
| No unified execution | Create `SomaOrchestrator` | P0 | 1 day |
| Wire orchestrator | Connect to all entry points | P0 | 1 day |

**Total Gap Remediation:** 5 developer days

---

## Implementation Order (Recommended)

### Sprint 1 (Week 1-2): Foundation
1. Django Models + Migrations
2. SpiceDB Schema + Client
3. Keycloak Realm Setup
4. Base Lit Components

### Sprint 2 (Week 2-3): Auth
1. Login Flow (Backend + Frontend)
2. Session Management (Redis)
3. MFA Implementation
4. OAuth Providers

### Sprint 3 (Week 3-4): Platform Admin
1. Platform Dashboard (`/platform`)
2. Tenant CRUD
3. Health Monitoring
4. Subscription Tiers

### Sprint 4 (Week 4-5): Tenant Admin
1. Tenant Dashboard (`/admin`)
2. User Management
3. Agent Management
4. Quota Enforcement

### Sprint 5 (Week 5-6): Gap Remediation
1. Sessions API
2. Conversations API
3. WebSocket Consumer
4. SomaOrchestrator

---

## Files to Create

| Path | Purpose |
|------|---------|
| `core/models.py` | Tenant, User, Agent, Subscription models |
| `spicedb/schema.zed` | Authorization schema |
| `keycloak/realm.json` | Keycloak realm export |
| `api/routers/auth.py` | Auth endpoints |
| `api/routers/saas.py` | Platform admin endpoints |
| `api/routers/admin.py` | Tenant admin endpoints |
| `services/quota.py` | Quota enforcement |
| `services/audit.py` | Audit logging |
| `middleware/auth.py` | Token refresh middleware |
| `webui/src/views/saas-login.ts` | Login component |
| `webui/src/views/saas-platform-dashboard.ts` | Platform dashboard |
| `webui/src/views/saas-tenant-list.ts` | Tenant management |
| `webui/src/components/saas-shell.ts` | App shell |

---

**Status Legend:**
- ❌ Not Started
- ⚠️ Partial / In Progress
- ✅ Complete

**Ready to start implementation.**
