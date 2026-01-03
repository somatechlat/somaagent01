# SRS: SAAS Initialization — Complete Seed Data & View Registry

**Document ID:** SA01-SRS-SEED-DATA-2025-12
**Purpose:** Define ALL default data loaded when SAAS is created, complete permission matrix, and all UI views
**Status:** CANONICAL REFERENCE

---

## 1. Complete Permission Matrix

### 1.1 All Granular Permissions (45+)

| Resource | Permission | Description | Scope |
|----------|------------|-------------|-------|
| **PLATFORM** | `platform:manage` | Full platform management | Platform |
| | `platform:read_metrics` | View platform metrics | Platform |
| | `platform:manage_billing` | Manage billing settings | Platform |
| | `platform:manage_features` | Enable/disable features | Platform |
| | `platform:impersonate` | Impersonate tenant admins | Platform |
| **TENANT** | `tenant:create` | Create new tenants | Platform |
| | `tenant:read` | View tenant details | Platform/Tenant |
| | `tenant:update` | Update tenant settings | Tenant |
| | `tenant:delete` | Delete tenants | Platform |
| | `tenant:suspend` | Suspend/activate tenants | Platform |
| | `tenant:manage_subscription` | Change subscription tier | Platform |
| | `tenant:view_billing` | View billing information | Tenant |
| | `tenant:manage_users` | Manage tenant users | Tenant |
| **USER** | `user:create` | Create users | Tenant |
| | `user:read` | View user details | Tenant |
| | `user:update` | Update user profiles | Tenant/Self |
| | `user:delete` | Delete users | Tenant |
| | `user:assign_roles` | Assign roles to users | Tenant |
| | `user:revoke_roles` | Revoke roles from users | Tenant |
| | `user:reset_password` | Reset user passwords | Tenant |
| | `user:manage_mfa` | Enable/disable MFA | Tenant |
| | `user:view_activity` | View user activity logs | Tenant |
| **AGENT** | `agent:create` | Create agents | Tenant |
| | `agent:read` | View agent details | Agent |
| | `agent:update` | Update agent config | Agent |
| | `agent:delete` | Delete agents | Tenant |
| | `agent:start` | Start agents | Agent |
| | `agent:stop` | Stop agents | Agent |
| | `agent:configure_personality` | Edit personality | Agent |
| | `agent:configure_tools` | Manage agent tools | Agent |
| | `agent:view_logs` | View agent logs | Agent |
| | `agent:export` | Export agent data | Agent |
| **CONVERSATION** | `conversation:create` | Start conversations | Agent |
| | `conversation:read` | View conversations | Agent |
| | `conversation:update` | Edit conversations | Agent |
| | `conversation:delete` | Delete conversations | Agent |
| | `conversation:send_message` | Send messages | Agent |
| | `conversation:view_history` | View full history | Agent |
| | `conversation:export` | Export conversations | Agent |
| | `conversation:search` | Search conversations | Agent |
| **MEMORY** | `memory:read` | View memories | Agent |
| | `memory:create` | Create memories | Agent |
| | `memory:update` | Update memories | Agent |
| | `memory:delete` | Delete memories | Agent |
| | `memory:search` | Search memories | Agent |
| | `memory:export` | Export memories | Agent |
| | `memory:configure_retention` | Memory retention settings | Tenant |
| **TOOL** | `tool:read` | View available tools | Agent |
| | `tool:execute` | Execute tools | Agent |
| | `tool:create` | Create custom tools | Tenant |
| | `tool:update` | Update tool config | Tenant |
| | `tool:delete` | Delete tools | Tenant |
| | `tool:approve` | Approve tool executions | Tenant |
| **FILE** | `file:upload` | Upload files | Agent |
| | `file:read` | View/download files | Agent |
| | `file:delete` | Delete files | Agent |
| | `file:share` | Share files | Agent |
| **APIKEY** | `apikey:create` | Create API keys | Tenant |
| | `apikey:read` | View API keys | Tenant |
| | `apikey:revoke` | Revoke API keys | Tenant |
| | `apikey:rotate` | Rotate API keys | Tenant |
| **INTEGRATION** | `integration:create` | Create integrations | Tenant |
| | `integration:read` | View integrations | Tenant |
| | `integration:update` | Update integrations | Tenant |
| | `integration:delete` | Delete integrations | Tenant |
| | `integration:sync` | Trigger syncs | Tenant |
| **AUDIT** | `audit:read` | View audit logs | Tenant |
| | `audit:export` | Export audit logs | Tenant |
| | `audit:configure_retention` | Audit retention | Tenant |
| **BACKUP** | `backup:create` | Create backups | Tenant |
| | `backup:read` | View backups | Tenant |
| | `backup:restore` | Restore backups | Tenant |
| | `backup:delete` | Delete backups | Tenant |
| | `backup:configure_schedule` | Configure schedules | Tenant |
| **BILLING** | `billing:view_invoices` | View invoices | Tenant |
| | `billing:view_usage` | View usage | Tenant |
| | `billing:manage_payment` | Manage payment methods | Tenant |
| | `billing:view_subscription` | View subscription | Tenant |
| | `billing:change_plan` | Change plans | Tenant |
| **VOICE** | `voice_persona:create` | Create voice personas | Agent |
| | `voice_persona:read` | View voice personas | Agent |
| | `voice_persona:update` | Update voice personas | Agent |
| | `voice_persona:delete` | Delete voice personas | Agent |
| | `voice_persona:set_default` | Set default persona | Agent |
| | `voice_session:create` | Start voice sessions | Agent |
| | `voice_session:read` | View voice sessions | Agent |
| | `voice_session:terminate` | Terminate sessions | Agent |
| | `voice_model:read` | View voice models | Platform |
| | `voice_model:create` | Create voice models | Platform |
| | `voice_model:update` | Update voice models | Platform |
| | `voice_model:delete` | Delete voice models | Platform |
| **INFRASTRUCTURE** | `infra:view` | View infrastructure status | Platform |
| | `infra:configure` | Configure services | Platform |
| | `infra:ratelimit` | Manage rate limits | Platform |

**Total: 78 Granular Permissions**

---

## 2. Predefined Roles (Seed Data)

### 2.1 Role Definitions

| Role ID | Name | Scope | Permissions |
|---------|------|-------|-------------|
| `saas_super_admin` | SAAS Super Administrator | Platform | `*` (All) |
| `tenant_admin` | Tenant Administrator | Tenant | `tenant:read`, `tenant:update`, `user:*`, `agent:*`, `conversation:*`, `memory:*`, `tool:*`, `file:*`, `apikey:*`, `integration:*`, `audit:read`, `backup:read`, `billing:view_*` |
| `tenant_manager` | Tenant Manager | Tenant | `tenant:read`, `user:create`, `user:read`, `user:update`, `agent:*`, `conversation:read`, `memory:read`, `tool:read`, `file:*` |
| `agent_owner` | Agent Owner | Agent | `agent:read`, `agent:update`, `agent:start`, `agent:stop`, `agent:configure_*`, `agent:view_logs`, `agent:export`, `conversation:*`, `memory:*`, `tool:read`, `tool:execute`, `file:upload`, `file:read` |
| `agent_operator` | Agent Operator | Agent | `agent:read`, `agent:start`, `agent:stop`, `agent:view_logs`, `conversation:*`, `memory:read`, `memory:search`, `tool:read`, `tool:execute`, `file:upload`, `file:read` |
| `user` | Standard User | Tenant | `agent:read`, `conversation:create`, `conversation:read`, `conversation:send_message`, `conversation:view_history`, `memory:read`, `file:upload`, `file:read` |
| `viewer` | Viewer | Tenant | `agent:read`, `conversation:read`, `memory:read`, `file:read` |
| `billing_admin` | Billing Administrator | Tenant | `billing:*`, `tenant:read` |
| `security_auditor` | Security Auditor | Tenant | `audit:read`, `audit:export`, `user:read`, `user:view_activity`, `apikey:read`, `backup:read` |
| `infra_admin` | Infrastructure Administrator | Platform | `infra:*`, `platform:read_metrics` |

---

## 3. Default Subscription Tiers (Seed Data)

### 3.1 Tier Definitions

| Tier | Slug | Price | Lago Code | Active | Public |
|------|------|-------|-----------|--------|--------|
| Free | `free` | $0/mo | `soma_free` | ✅ | ✅ |
| Starter | `starter` | $29/mo | `soma_starter` | ✅ | ✅ |
| Team | `team` | $99/mo | `soma_team` | ✅ | ✅ |
| Enterprise | `enterprise` | Custom | `soma_enterprise` | ✅ | ❌ |

### 3.2 Tier Quotas

| Quota | Free | Starter | Team | Enterprise |
|-------|------|---------|------|------------|
| `max_agents` | 1 | 5 | 25 | 999999 |
| `max_users_per_agent` | 3 | 10 | 50 | 999999 |
| `max_monthly_voice_minutes` | 0 | 60 | 500 | 5000 |
| `max_monthly_api_calls` | 100 | 10000 | 100000 | 999999 |
| `max_storage_gb` | 0.5 | 5 | 50 | 500 |

---

## 4. Default Features (Seed Data)

### 4.1 Feature Catalog

| Code | Name | Category | Billable | Default |
|------|------|----------|----------|---------|
| `memory` | Memory Integration | MEMORY | Yes | Enabled |
| `voice` | Voice Integration | VOICE | Yes | Disabled |
| `mcp` | MCP Servers | MCP | No | Enabled |
| `browser_agent` | Browser Automation | BROWSER | No | Disabled |
| `code_execution` | Code Execution | CODE_EXEC | No | Disabled |
| `vision` | Vision/Image Processing | VISION | No | Disabled |
| `delegation` | Agent Delegation | DELEGATION | No | Disabled |
| `file_upload` | File Upload | TOOLS | No | Enabled |
| `export` | Data Export | TOOLS | No | Disabled |

### 4.2 Tier Feature Matrix (Seed Data)

| Feature | Free | Starter | Team | Enterprise |
|---------|------|---------|------|------------|
| `memory` | ❌ | ✅ | ✅ | ✅ |
| `voice` | ❌ | ❌ | ✅ | ✅ |
| `mcp` | ❌ | ✅ | ✅ | ✅ |
| `browser_agent` | ❌ | ❌ | ✅ | ✅ |
| `code_execution` | ❌ | ❌ | ✅ | ✅ |
| `vision` | ❌ | ✅ | ✅ | ✅ |
| `delegation` | ❌ | ❌ | ❌ | ✅ |
| `file_upload` | ✅ | ✅ | ✅ | ✅ |
| `export` | ❌ | ✅ | ✅ | ✅ |

---

## 5. Default Rate Limits (Seed Data)

### 5.1 Global Rate Limits

| Key | Limit | Window | Policy | Description |
|-----|-------|--------|--------|-------------|
| `api_calls` | 1000 | 1 hour | HARD | API requests per hour |
| `llm_tokens` | 100000 | 24 hours | SOFT | LLM tokens per day |
| `voice_minutes` | 60 | 24 hours | SOFT | Voice minutes per day |
| `file_uploads` | 50 | 1 hour | HARD | File uploads per hour |
| `memory_queries` | 500 | 1 hour | SOFT | Memory searches per hour |
| `websocket_connections` | 100 | - | HARD | Concurrent WebSocket connections |

### 5.2 Per-Tier Rate Limits

| Key | Free | Starter | Team | Enterprise |
|-----|------|---------|------|------------|
| `api_calls` | 100 | 1000 | 10000 | 999999 |
| `llm_tokens` | 10000 | 100000 | 1000000 | 999999 |
| `voice_minutes` | 0 | 60 | 500 | 5000 |

---

## 6. Complete View Registry (All UI Screens)

### 6.1 Platform Admin Views

| Route | Component | Purpose | Implemented |
|-------|-----------|---------|-------------|
| `/platform` | `platform-dashboard.ts` | Platform overview | ✅ |
| `/platform/tenants` | `tenant-list.ts` | Tenant management | ✅ |
| `/platform/tenants/:id` | `tenant-detail.ts` | Tenant detail | ✅ |
| `/platform/tenants/create` | `tenant-create.ts` | Create tenant | ⚠️ |
| `/platform/subscriptions` | `subscription-tiers.ts` | Tier management | ✅ |
| `/platform/subscriptions/:id` | `tier-detail.ts` | Tier detail/edit | ⚠️ |
| `/platform/permissions` | `saas-permissions.ts` | Permission browser | ⚠️ |
| `/platform/roles` | `saas-admin-roles-list.ts` | Role management | ✅ |
| `/platform/roles/create` | `role-builder.ts` | Custom role builder | ❌ |
| `/platform/billing` | `platform-billing.ts` | Global billing | ⚠️ |
| `/platform/audit` | `platform-audit.ts` | Global audit log | ⚠️ |
| `/platform/features` | `feature-catalog.ts` | Feature management | ❌ |
| `/platform/infrastructure` | `infrastructure-dashboard.ts` | Service health | ❌ |
| `/platform/infrastructure/redis` | `redis-admin.ts` | Redis config | ❌ |
| `/platform/infrastructure/redis/ratelimits` | `ratelimit-editor.ts` | Rate limit config | ❌ |
| `/platform/infrastructure/temporal` | `temporal-admin.ts` | Workflow admin | ❌ |
| `/platform/infrastructure/qdrant` | `qdrant-admin.ts` | Vector DB admin | ❌ |
| `/platform/infrastructure/auth` | `keycloak-admin.ts` | Auth admin | ❌ |
| `/platform/infrastructure/billing` | `lago-admin.ts` | Billing admin | ❌ |
| `/platform/infrastructure/somabrain` | `somabrain-admin.ts` | Memory admin | ❌ |
| `/platform/infrastructure/voice` | `voice-admin.ts` | Voice admin | ❌ |
| `/platform/infrastructure/mcp` | `mcp-registry.ts` | MCP server registry | ❌ |
| `/platform/infrastructure/storage` | `storage-admin.ts` | S3 admin | ❌ |
| `/platform/infrastructure/email` | `email-admin.ts` | SMTP admin | ❌ |

### 6.2 Tenant Admin Views

| Route | Component | Purpose | Implemented |
|-------|-----------|---------|-------------|
| `/admin` | `tenant-dashboard.ts` | Tenant overview | ✅ |
| `/admin/users` | `user-list.ts` | User management | ✅ |
| `/admin/users/:id` | `user-detail.ts` | User detail | ⚠️ |
| `/admin/agents` | `agent-list.ts` | Agent management | ✅ |
| `/admin/agents/:id` | `agent-detail.ts` | Agent detail | ⚠️ |
| `/admin/agents/create` | `agent-create.ts` | Create agent | ⚠️ |
| `/admin/billing` | `tenant-billing.ts` | Tenant billing | ⚠️ |
| `/admin/audit` | `tenant-audit.ts` | Tenant audit log | ⚠️ |
| `/admin/settings` | `tenant-settings.ts` | Tenant settings | ⚠️ |
| `/admin/settings/api-keys` | `api-keys.ts` | API key management | ⚠️ |
| `/admin/settings/integrations` | `integrations.ts` | Integration config | ❌ |
| `/admin/settings/roles` | `tenant-roles.ts` | Tenant role config | ❌ |

### 6.3 Agent User Views

| Route | Component | Purpose | Implemented |
|-------|-----------|---------|-------------|
| `/chat` | `chat-view.ts` | Chat interface | ✅ |
| `/chat/:conversationId` | `chat-view.ts` | Specific conversation | ✅ |
| `/memory` | `memory-browser.ts` | Memory browser | ✅ |
| `/memory/:id` | `memory-detail.ts` | Memory detail | ⚠️ |
| `/settings` | `agent-settings.ts` | Agent settings | ✅ |
| `/settings/voice` | `voice-settings.ts` | Voice config | ⚠️ |
| `/settings/memory` | `memory-settings.ts` | Memory config | ⚠️ |
| `/settings/tools` | `tool-settings.ts` | Tool config | ⚠️ |
| `/profile` | `user-profile.ts` | User profile | ⚠️ |

### 6.4 Developer Mode Views

| Route | Component | Purpose | Implemented |
|-------|-----------|---------|-------------|
| `/dev/console` | `debug-console.ts` | Debug console | ⚠️ |
| `/dev/mcp` | `mcp-inspector.ts` | MCP inspector | ⚠️ |
| `/dev/logs` | `log-viewer.ts` | Log viewer | ❌ |

### 6.5 Trainer Mode Views

| Route | Component | Purpose | Implemented |
|-------|-----------|---------|-------------|
| `/trn/cognitive` | `cognitive-panel.ts` | Neuromodulators | ⚠️ |
| `/trn/memory` | `memory-trainer.ts` | Memory training | ❌ |

### 6.6 Authentication Views

| Route | Component | Purpose | Implemented |
|-------|-----------|---------|-------------|
| `/login` | `login-page.ts` | Login | ✅ |
| `/logout` | `logout-page.ts` | Logout | ✅ |
| `/register` | `register-page.ts` | Registration | ⚠️ |
| `/forgot-password` | `forgot-password.ts` | Password reset | ⚠️ |

---

## 7. Summary Statistics

| Category | Total | Implemented | Partial | Missing |
|----------|-------|-------------|---------|---------|
| Granular Permissions | 78 | N/A | N/A | N/A |
| Predefined Roles | 10 | N/A | N/A | N/A |
| Subscription Tiers | 4 | N/A | N/A | N/A |
| Features | 9 | N/A | N/A | N/A |
| Rate Limits | 6 | N/A | N/A | N/A |
| UI Views (Total) | 48 | 12 | 18 | 18 |
| - Platform Admin | 24 | 5 | 4 | 15 |
| - Tenant Admin | 12 | 3 | 7 | 2 |
| - Agent User | 9 | 3 | 5 | 1 |
| - Developer Mode | 3 | 0 | 2 | 1 |

---

## 8. Django Fixture Data (Seed Commands)

```bash
# Load all seed data
python manage.py loaddata fixtures/permissions.json
python manage.py loaddata fixtures/roles.json
python manage.py loaddata fixtures/tiers.json
python manage.py loaddata fixtures/features.json
python manage.py loaddata fixtures/tier_features.json
python manage.py loaddata fixtures/rate_limits.json

# Or single command
python manage.py seed_saas_data
```

---

## 9. Migration Priority (Implementation Order)

### Phase 1: Core (Required)
1. ✅ Permissions (already in code)
2. ✅ Roles (already in code)
3. ⚠️ Tiers (needs ORM migration)
4. ⚠️ Features (needs ORM migration)
5. ⚠️ Rate Limits (needs new model)

### Phase 2: Platform Admin Views (High Priority)
1. ❌ Infrastructure Dashboard
2. ❌ Rate Limit Editor
3. ❌ Feature Catalog
4. ❌ Custom Role Builder
5. ⚠️ Permission Browser

### Phase 3: Tenant Admin Views (Medium Priority)
1. ⚠️ User Detail
2. ⚠️ Agent Detail
3. ❌ Integration Config
4. ❌ Tenant Role Config

### Phase 4: Infrastructure Admin (High Priority)
1. ❌ Redis Admin (rate limits)
2. ❌ Temporal Admin (workflows)
3. ❌ MCP Registry
4. ❌ All other infrastructure screens
