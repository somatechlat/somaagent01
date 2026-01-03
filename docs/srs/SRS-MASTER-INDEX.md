# SRS: Master Index — Complete System Specification

**Document ID:** SA01-SRS-MASTER-INDEX-2025-12
**Purpose:** Consolidate ALL SRS documents with complete UI registry and implementation parameters
**Status:** CANONICAL MASTER REFERENCE

---

## 1. Document Registry

| SRS Document | Focus | Screens | Settings |
|--------------|-------|---------|----------|
| `SRS-ARCHITECTURE.md` | System layers | - | - |
| `SRS-INFRASTRUCTURE-ADMIN.md` | Service administration | 12 | 50+ |
| `SRS-INFRASTRUCTURE-JOURNEYS.md` | Admin user flows | - | - |
| `SRS-SEED-DATA.md` | Default data | - | 78 permissions |
| `SRS-USER-JOURNEYS.md` | All persona flows | 48 | 60+ |
| `SRS-MULTIMODAL.md` | Image/Diagram/Screenshot | 4 | 15+ |
| `SRS-METRICS-DASHBOARDS.md` | Observability UI | 10 | 60 metrics |
| `SRS-FEATURE-CATALOG.md` | Feature mapping | - | 62 modules |
| `SRS-SETTINGS-TREE.md` | Settings hierarchy | - | 100+ |
| `SRS-SAAS-TENANT-CREATION.md` | Tenant wizard | 5 | 20+ |
| `SRS-SAAS-ECOSYSTEM-DEFAULTS.md` | Platform physics | - | Catalogs |
| `SRS-SAAS-INTEGRATIONS.md` | External services | 8 | 30+ |
| `SRS-SAAS-AGENT-MARKETPLACE.md` | Marketplace | 6 | 15+ |
| `SRS-SAAS-VISUAL-INFRASTRUCTURE.md` | Topology view | 1 | - |
| `SRS-SAAS-INFRASTRUCTURE-DEFAULTS.md` | MCP registry | 4 | 20+ |

---

## 2. Complete UI View Registry (66 Screens)

### 2.1 Platform Admin (SAAS SysAdmin) — 28 Screens

| Route | Component | Priority | Status |
|-------|-----------|----------|--------|
| **DASHBOARD** | | | |
| `/platform` | `platform-dashboard.ts` | P0 | ✅ |
| **TENANTS** | | | |
| `/platform/tenants` | `tenant-list.ts` | P0 | ✅ |
| `/platform/tenants/:id` | `tenant-detail.ts` | P0 | ✅ |
| `/platform/tenants/create` | `tenant-wizard.ts` | P0 | ⚠️ |
| **TIERS & BILLING** | | | |
| `/platform/subscriptions` | `subscription-tiers.ts` | P0 | ✅ |
| `/platform/subscriptions/:id` | `tier-detail.ts` | P0 | ⚠️ |
| `/platform/subscriptions/:id/quotas` | `tier-quotas.ts` | P1 | ❌ |
| `/platform/billing` | `platform-billing.ts` | P1 | ⚠️ |
| **PERMISSIONS & ROLES** | | | |
| `/platform/permissions` | `saas-permissions.ts` | P0 | ⚠️ |
| `/platform/roles` | `saas-admin-roles-list.ts` | P1 | ✅ |
| `/platform/roles/create` | `role-builder.ts` | P1 | ❌ |
| **FEATURES** | | | |
| `/platform/features` | `feature-catalog.ts` | P1 | ❌ |
| `/platform/models` | `model-catalog.ts` | P1 | ❌ |
| **AUDIT** | | | |
| `/platform/audit` | `platform-audit.ts` | P1 | ⚠️ |
| **INFRASTRUCTURE** | | | |
| `/platform/infrastructure` | `infrastructure-dashboard.ts` | P0 | ❌ |
| `/platform/infrastructure/database` | `database-admin.ts` | P1 | ❌ |
| `/platform/infrastructure/redis` | `redis-admin.ts` | P0 | ❌ |
| `/platform/infrastructure/redis/ratelimits` | `ratelimit-editor.ts` | P0 | ❌ |
| `/platform/infrastructure/temporal` | `temporal-admin.ts` | P1 | ❌ |
| `/platform/infrastructure/qdrant` | `qdrant-admin.ts` | P1 | ❌ |
| `/platform/infrastructure/auth` | `keycloak-admin.ts` | P1 | ❌ |
| `/platform/infrastructure/billing` | `lago-admin.ts` | P1 | ❌ |
| `/platform/infrastructure/somabrain` | `somabrain-admin.ts` | P1 | ❌ |
| `/platform/infrastructure/voice` | `voice-admin.ts` | P1 | ❌ |
| `/platform/infrastructure/mcp` | `mcp-registry.ts` | P1 | ❌ |
| `/platform/infrastructure/storage` | `storage-admin.ts` | P2 | ❌ |
| `/platform/infrastructure/email` | `email-admin.ts` | P2 | ❌ |
| **METRICS & OBSERVABILITY** | | | |
| `/platform/metrics` | `platform-metrics.ts` | P0 | ❌ |
| `/platform/metrics/llm` | `llm-metrics.ts` | P1 | ❌ |
| `/platform/metrics/tools` | `tool-metrics.ts` | P1 | ❌ |
| `/platform/metrics/memory` | `memory-metrics.ts` | P1 | ❌ |
| `/platform/metrics/sla` | `sla-dashboard.ts` | P1 | ❌ |

### 2.2 Tenant Admin — 16 Screens

| Route | Component | Priority | Status |
|-------|-----------|----------|--------|
| **DASHBOARD** | | | |
| `/admin` | `tenant-dashboard.ts` | P0 | ✅ |
| **USERS** | | | |
| `/admin/users` | `user-list.ts` | P0 | ✅ |
| `/admin/users/:id` | `user-detail.ts` | P0 | ⚠️ |
| `/admin/users/invite` | `user-invite.ts` | P1 | ❌ |
| **AGENTS** | | | |
| `/admin/agents` | `agent-list.ts` | P0 | ✅ |
| `/admin/agents/:id` | `agent-detail.ts` | P0 | ⚠️ |
| `/admin/agents/create` | `agent-create.ts` | P0 | ⚠️ |
| **USAGE & BILLING** | | | |
| `/admin/usage` | `tenant-usage.ts` | P0 | ❌ |
| `/admin/billing` | `tenant-billing.ts` | P1 | ⚠️ |
| **AUDIT** | | | |
| `/admin/audit` | `tenant-audit.ts` | P1 | ⚠️ |
| **SETTINGS** | | | |
| `/admin/settings` | `tenant-settings.ts` | P1 | ⚠️ |
| `/admin/settings/api-keys` | `api-keys.ts` | P1 | ⚠️ |
| `/admin/settings/integrations` | `integrations.ts` | P2 | ❌ |
| `/admin/settings/roles` | `tenant-roles.ts` | P2 | ❌ |
| **METRICS** | | | |
| `/admin/metrics` | `tenant-metrics.ts` | P0 | ❌ |
| `/admin/metrics/agents` | `agent-metrics.ts` | P1 | ❌ |

### 2.3 Agent User — 12 Screens

| Route | Component | Priority | Status |
|-------|-----------|----------|--------|
| **CHAT** | | | |
| `/chat` | `chat-view.ts` | P0 | ✅ |
| `/chat/:conversationId` | `chat-view.ts` | P0 | ✅ |
| **MEMORY** | | | |
| `/memory` | `memory-browser.ts` | P0 | ✅ |
| `/memory/:id` | `memory-detail.ts` | P1 | ⚠️ |
| **SETTINGS** | | | |
| `/settings` | `agent-settings.ts` | P0 | ✅ |
| `/settings/models` | `model-settings.ts` | P0 | ❌ |
| `/settings/memory` | `memory-settings.ts` | P1 | ⚠️ |
| `/settings/voice` | `voice-settings.ts` | P1 | ⚠️ |
| `/settings/tools` | `tool-settings.ts` | P1 | ⚠️ |
| `/settings/multimodal` | `multimodal-settings.ts` | P1 | ❌ |
| **PROFILE** | | | |
| `/profile` | `user-profile.ts` | P1 | ⚠️ |

### 2.4 Developer Mode — 4 Screens

| Route | Component | Priority | Status |
|-------|-----------|----------|--------|
| `/dev/console` | `debug-console.ts` | P1 | ⚠️ |
| `/dev/mcp` | `mcp-inspector.ts` | P1 | ⚠️ |
| `/dev/logs` | `log-viewer.ts` | P2 | ❌ |
| `/dev/metrics` | `dev-metrics.ts` | P1 | ❌ |

### 2.5 Trainer Mode — 2 Screens

| Route | Component | Priority | Status |
|-------|-----------|----------|--------|
| `/trn/cognitive` | `cognitive-panel.ts` | P1 | ⚠️ |
| `/trn/memory` | `memory-trainer.ts` | P2 | ❌ |

### 2.6 Authentication — 4 Screens

| Route | Component | Priority | Status |
|-------|-----------|----------|--------|
| `/login` | `login-page.ts` | P0 | ✅ |
| `/logout` | `logout-page.ts` | P0 | ✅ |
| `/register` | `register-page.ts` | P1 | ⚠️ |
| `/forgot-password` | `forgot-password.ts` | P2 | ⚠️ |

---

## 3. Infrastructure Settings (All Configurable Parameters)

### 3.1 PostgreSQL Settings

| Parameter | Type | Default | UI Route |
|-----------|------|---------|----------|
| `POSTGRES_HOST` | String | `localhost` | `/platform/infrastructure/database` |
| `POSTGRES_PORT` | Integer | `5432` | `/platform/infrastructure/database` |
| `POSTGRES_USER` | String | - | `/platform/infrastructure/database` |
| `POSTGRES_DB` | String | - | `/platform/infrastructure/database` |
| `POSTGRES_POOL_SIZE` | Integer | `20` | `/platform/infrastructure/database` |
| `POSTGRES_MAX_OVERFLOW` | Integer | `10` | `/platform/infrastructure/database` |
| `POSTGRES_CONN_TIMEOUT` | Integer | `30` | `/platform/infrastructure/database` |

### 3.2 Redis Settings

| Parameter | Type | Default | UI Route |
|-----------|------|---------|----------|
| `REDIS_URL` | URL | `redis://localhost:6379` | `/platform/infrastructure/redis` |
| `REDIS_MAX_CONNECTIONS` | Integer | `100` | `/platform/infrastructure/redis` |
| `REDIS_TTL_DEFAULT` | Integer | `3600` | `/platform/infrastructure/redis` |
| `RATELIMIT_API_CALLS` | Integer | `1000` | `/platform/infrastructure/redis/ratelimits` |
| `RATELIMIT_LLM_TOKENS` | Integer | `100000` | `/platform/infrastructure/redis/ratelimits` |
| `RATELIMIT_VOICE_MINUTES` | Integer | `60` | `/platform/infrastructure/redis/ratelimits` |
| `RATELIMIT_POLICY` | Enum | `HARD` | `/platform/infrastructure/redis/ratelimits` |

### 3.3 Temporal Settings

| Parameter | Type | Default | UI Route |
|-----------|------|---------|----------|
| `TEMPORAL_HOST` | String | `temporal:7233` | `/platform/infrastructure/temporal` |
| `TEMPORAL_NAMESPACE` | String | `default` | `/platform/infrastructure/temporal` |
| `TEMPORAL_TASK_QUEUE` | String | `soma-tasks` | `/platform/infrastructure/temporal` |
| `TEMPORAL_WORKFLOW_TIMEOUT` | Integer | `3600` | `/platform/infrastructure/temporal` |
| `TEMPORAL_ACTIVITY_TIMEOUT` | Integer | `300` | `/platform/infrastructure/temporal` |
| `TEMPORAL_RETRY_MAX` | Integer | `3` | `/platform/infrastructure/temporal` |

### 3.4 Qdrant Settings

| Parameter | Type | Default | UI Route |
|-----------|------|---------|----------|
| `QDRANT_HOST` | String | `qdrant:6333` | `/platform/infrastructure/qdrant` |
| `QDRANT_GRPC_PORT` | Integer | `6334` | `/platform/infrastructure/qdrant` |
| `QDRANT_COLLECTION_PREFIX` | String | `soma_` | `/platform/infrastructure/qdrant` |
| `QDRANT_VECTOR_SIZE` | Integer | `384` | `/platform/infrastructure/qdrant` |
| `QDRANT_DISTANCE` | Enum | `Cosine` | `/platform/infrastructure/qdrant` |

### 3.5 Keycloak Settings

| Parameter | Type | Default | UI Route |
|-----------|------|---------|----------|
| `KEYCLOAK_URL` | URL | - | `/platform/infrastructure/auth` |
| `KEYCLOAK_REALM` | String | `master` | `/platform/infrastructure/auth` |
| `KEYCLOAK_CLIENT_ID` | String | - | `/platform/infrastructure/auth` |
| `KEYCLOAK_CLIENT_SECRET` | Secret | - | `/platform/infrastructure/auth` |

### 3.6 Lago Settings

| Parameter | Type | Default | UI Route |
|-----------|------|---------|----------|
| `LAGO_API_URL` | URL | - | `/platform/infrastructure/billing` |
| `LAGO_API_KEY` | Secret | - | `/platform/infrastructure/billing` |
| `LAGO_WEBHOOK_SECRET` | Secret | - | `/platform/infrastructure/billing` |

### 3.7 SomaBrain Settings

| Parameter | Type | Default | UI Route |
|-----------|------|---------|----------|
| `SOMABRAIN_URL` | URL | - | `/platform/infrastructure/somabrain` |
| `SOMABRAIN_RETENTION_DAYS` | Integer | `365` | `/platform/infrastructure/somabrain` |
| `SOMABRAIN_SLEEP_INTERVAL` | Integer | `21600` | `/platform/infrastructure/somabrain` |
| `SOMABRAIN_CONSOLIDATION` | Boolean | `true` | `/platform/infrastructure/somabrain` |

### 3.8 Voice Settings

| Parameter | Type | Default | UI Route |
|-----------|------|---------|----------|
| `WHISPER_URL` | URL | - | `/platform/infrastructure/voice` |
| `WHISPER_MODEL` | Enum | `base` | `/platform/infrastructure/voice` |
| `KOKORO_URL` | URL | - | `/platform/infrastructure/voice` |
| `KOKORO_VOICE` | String | `af_nicole` | `/platform/infrastructure/voice` |

### 3.9 MCP Settings

| Parameter | Type | Default | UI Route |
|-----------|------|---------|----------|
| `MCP_INIT_TIMEOUT` | Integer | `10` | `/platform/infrastructure/mcp` |
| `MCP_TOOL_TIMEOUT` | Integer | `120` | `/platform/infrastructure/mcp` |
| `MCP_SERVERS` | JSON | `{}` | `/platform/infrastructure/mcp` |

### 3.10 Storage Settings

| Parameter | Type | Default | UI Route |
|-----------|------|---------|----------|
| `S3_ENDPOINT` | URL | - | `/platform/infrastructure/storage` |
| `S3_ACCESS_KEY` | Secret | - | `/platform/infrastructure/storage` |
| `S3_SECRET_KEY` | Secret | - | `/platform/infrastructure/storage` |
| `S3_BUCKET` | String | - | `/platform/infrastructure/storage` |

### 3.11 Email Settings

| Parameter | Type | Default | UI Route |
|-----------|------|---------|----------|
| `SMTP_HOST` | String | - | `/platform/infrastructure/email` |
| `SMTP_PORT` | Integer | `587` | `/platform/infrastructure/email` |
| `SMTP_USER` | String | - | `/platform/infrastructure/email` |
| `SMTP_PASSWORD` | Secret | - | `/platform/infrastructure/email` |
| `SMTP_FROM` | Email | - | `/platform/infrastructure/email` |

### 3.12 Prometheus/Metrics Settings

| Parameter | Type | Default | UI Route |
|-----------|------|---------|----------|
| `PROMETHEUS_URL` | URL | `prometheus:20090` | `/platform/metrics` |
| `GRAFANA_URL` | URL | `grafana:20030` | `/platform/metrics` |
| `METRICS_RETENTION_DAYS` | Integer | `30` | `/platform/metrics` |
| `ALERT_WEBHOOK_URL` | URL | - | `/platform/metrics/sla` |

---

## 4. Implementation Summary

### Statistics

| Category | Count |
|----------|-------|
| **Total UI Screens** | 66 |
| - Implemented | 12 |
| - Partial | 20 |
| - Missing | 34 |
| **Total Settings** | 100+ |
| **Total Permissions** | 78 |
| **Total Metrics** | 60+ |
| **Total SRS Documents** | 15 |

### Priority Matrix

| Priority | Screens | Focus |
|----------|---------|-------|
| **P0** | 18 | Core functionality |
| **P1** | 28 | Extended features |
| **P2** | 20 | Advanced features |

---

## 5. Implementation Order

### Phase 1: Core Infrastructure (P0)
1. `/platform/infrastructure` - Service health dashboard
2. `/platform/infrastructure/redis/ratelimits` - Rate limit editor
3. `/platform/metrics` - Metrics dashboard
4. `/admin/usage` - Tenant usage view
5. `/admin/metrics` - Tenant metrics

### Phase 2: Extended Admin (P1)
6. All remaining infrastructure screens
7. All metrics deep-dive screens
8. Feature catalog management
9. Model catalog management

### Phase 3: Full Feature Set (P2)
10. Advanced settings
11. Developer metrics
12. Trainer mode
13. Marketplace
