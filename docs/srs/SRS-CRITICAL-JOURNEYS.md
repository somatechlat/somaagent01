# SRS: Critical Use Case Journeys — Implementation Specification

**Document ID:** SA01-SRS-CRITICAL-JOURNEYS-2025-12
**Purpose:** Complete implementation specification for 10 critical SAAS use cases
**Stack:** AgentSkin (Lit 3.x) + Django Ninja + Django ORM
**Status:** READY FOR IMPLEMENTATION

---

## 1. Technology Stack Requirements

### 1.1 Frontend (AgentSkin)

| Technology | Version | Purpose |
|------------|---------|---------|
| Lit | 3.x | Web Components |
| Vaadin Router | 1.x | SPA Routing |
| CSS Variables | - | Design Tokens |

### 1.2 Backend (Pure Django)

| Technology | Version | Purpose |
|------------|---------|---------|
| Django | 5.x | Framework |
| Django Ninja | 1.x | REST API |
| Django ORM | - | Database |
| PostgreSQL | 16.x | Database |

### 1.3 VIBE Compliance

- ✅ NO FastAPI
- ✅ NO SQLAlchemy
- ✅ NO Alembic
- ✅ Pure Django migrations
- ✅ Lit for all frontend components

---

## 2. Use Case 1: Platform Health Dashboard

### 2.1 User Story

```
AS A SAAS Administrator
I WANT TO view real-time health of all infrastructure services
SO THAT I can monitor platform status and respond to issues
```

### 2.2 UI Component

**File:** `webui/src/views/platform-metrics.ts`

```typescript
// Component: saas-platform-metrics
// Route: /platform/metrics
// Parent: saas-layout

Sections:
- ServiceHealthGrid (12 service cards)
- LatencyChart (p50/p95/p99 histograms)
- TokenUsagePanel (LLM token consumption)
- SlaComplianceTable (SLA violation counts)
- CircuitBreakerStatus (circuit states)
```

### 2.3 Django Ninja API

**File:** `admin/observability/api.py`

| Endpoint | Method | Response |
|----------|--------|----------|
| `/api/v2/observability/health` | GET | All service health status |
| `/api/v2/observability/metrics/summary` | GET | Aggregated metrics snapshot |
| `/api/v2/observability/latency` | GET | Latency percentiles |
| `/api/v2/observability/sla` | GET | SLA compliance data |

### 2.4 ORM Models

**File:** `admin/observability/models.py`

```python
class ServiceHealth(models.Model):
    service_name = models.CharField(max_length=100, unique=True)
    status = models.CharField(choices=HealthStatus.choices)
    last_check = models.DateTimeField(auto_now=True)
    latency_ms = models.IntegerField(null=True)
    details = models.JSONField(default=dict)
```

### 2.5 Flow Diagram

```
User opens /platform/metrics
    │
    ├─→ saas-platform-metrics.ts loads
    │
    ├─→ API call: GET /api/v2/observability/health
    │       └─→ Django Ninja handler
    │           └─→ Check each service (pg, redis, temporal, etc.)
    │           └─→ Return aggregated health
    │
    ├─→ API call: GET /api/v2/observability/metrics/summary
    │       └─→ Query Prometheus metrics
    │       └─→ Return formatted data
    │
    └─→ Render dashboard with real-time data
```

---

## 3. Use Case 2: Rate Limit Configuration

### 3.1 User Story

```
AS A SAAS Administrator
I WANT TO visually configure API rate limits
SO THAT I can prevent abuse without editing code
```

### 3.2 UI Component

**File:** `webui/src/views/ratelimit-editor.ts`

```typescript
// Component: saas-ratelimit-editor
// Route: /platform/infrastructure/redis/ratelimits

Sections:
- RateLimitTable (list all limits)
- EditModal (form for editing)
- TierOverridesTab (per-tier overrides)
- AuditTrailPanel (recent changes)
```

### 3.3 Django Ninja API

**File:** `admin/infrastructure/api/ratelimits.py`

| Endpoint | Method | Response |
|----------|--------|----------|
| `/api/v2/infrastructure/ratelimits` | GET | All rate limit policies |
| `/api/v2/infrastructure/ratelimits/{key}` | PUT | Update rate limit |
| `/api/v2/infrastructure/ratelimits` | POST | Create new limit |
| `/api/v2/infrastructure/ratelimits/{key}` | DELETE | Delete limit |

### 3.4 ORM Models

**File:** `admin/infrastructure/models.py`

```python
class RateLimitPolicy(models.Model):
    key = models.CharField(max_length=100, unique=True)
    limit = models.IntegerField()
    window_seconds = models.IntegerField()
    policy = models.CharField(choices=EnforcementPolicy.choices)
    tier_overrides = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### 3.5 Flow Diagram

```
Admin opens /platform/infrastructure/redis/ratelimits
    │
    ├─→ API call: GET /api/v2/infrastructure/ratelimits
    │       └─→ RateLimitPolicy.objects.all()
    │       └─→ Return list
    │
    ├─→ Admin clicks "Edit" on api_calls
    │       └─→ Modal opens with form
    │
    ├─→ Admin changes limit from 1000 to 2000
    │
    ├─→ Admin clicks "Save"
    │       └─→ API call: PUT /api/v2/infrastructure/ratelimits/api_calls
    │           └─→ Update ORM model
    │           └─→ Push to Redis: SET ratelimit:config:api_calls
    │           └─→ Create audit log entry
    │           └─→ Return success
    │
    └─→ Table refreshes with new value
```

---

## 4. Use Case 3: Tenant Usage Dashboard

### 4.1 User Story

```
AS A Tenant Administrator
I WANT TO view usage metrics for my organization
SO THAT I can monitor consumption and plan capacity
```

### 4.2 UI Component

**File:** `webui/src/views/tenant-usage.ts`

```typescript
// Component: saas-tenant-usage
// Route: /admin/usage

Sections:
- QuotaProgressBars (API calls, tokens, images, voice)
- UsageByAgentTable (breakdown by agent)
- CostEstimatePanel (estimated invoice)
- UsageTrendChart (30-day trend)
```

### 4.3 Django Ninja API

**File:** `admin/saas/api/usage.py`

| Endpoint | Method | Response |
|----------|--------|----------|
| `/api/v2/tenants/{id}/usage` | GET | Current period usage |
| `/api/v2/tenants/{id}/usage/agents` | GET | Per-agent breakdown |
| `/api/v2/tenants/{id}/usage/costs` | GET | Cost estimates |
| `/api/v2/tenants/{id}/usage/history` | GET | Historical usage |

### 4.4 ORM Models

**File:** `admin/saas/models/usage.py`

```python
class UsageRecord(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, null=True)
    metric_type = models.CharField(max_length=50)
    quantity = models.BigIntegerField()
    period_start = models.DateField()
    period_end = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
```

---

## 5. Use Case 4: Agent Model Configuration

### 5.1 User Story

```
AS AN Agent Owner
I WANT TO configure which LLM models my agent uses
SO THAT I can optimize for cost/quality tradeoffs
```

### 5.2 UI Component

**File:** `webui/src/views/model-settings.ts`

```typescript
// Component: saas-model-settings
// Route: /settings/models

Sections:
- ChatModelSelector (dropdown with model list)
- UtilityModelSelector (dropdown)
- EmbeddingModelSelector (dropdown)
- BrowserModelSelector (dropdown)
- AdvancedSettings (temperature, ctx_length)
```

### 5.3 Django Ninja API

**File:** `admin/agents/api/config.py`

| Endpoint | Method | Response |
|----------|--------|----------|
| `/api/v2/agents/{id}/config/models` | GET | Current model config |
| `/api/v2/agents/{id}/config/models` | PUT | Update model config |
| `/api/v2/models/available` | GET | Available models for tier |

### 5.4 Flow Diagram

```
Agent Owner opens /settings/models
    │
    ├─→ API call: GET /api/v2/agents/{id}/config/models
    │       └─→ Return current chat/util/embed/browser models
    │
    ├─→ API call: GET /api/v2/models/available
    │       └─→ Filter by tier permissions
    │       └─→ Return available models
    │
    ├─→ Owner selects "Claude 3.5 Sonnet" for chat
    │
    ├─→ Owner clicks "Save"
    │       └─→ API call: PUT /api/v2/agents/{id}/config/models
    │           └─→ Validate tier allows this model
    │           └─→ Update AgentSettings ORM
    │           └─→ Return success
    │
    └─→ Show confirmation toast
```

---

## 6. Use Case 5: Infrastructure Service Health

### 6.1 User Story

```
AS A SAAS Administrator
I WANT TO view detailed status of each infrastructure service
SO THAT I can troubleshoot issues
```

### 6.2 UI Component

**File:** `webui/src/views/infrastructure-dashboard.ts`

```typescript
// Component: saas-infrastructure-dashboard
// Route: /platform/infrastructure

Sections:
- ServiceGrid (12 clickable cards)
- ServiceDetailPanel (when card clicked)
- RecentAlertsPanel
- QuickActionsBar
```

### 6.3 Django Ninja API

**File:** `admin/infrastructure/api/health.py`

| Endpoint | Method | Response |
|----------|--------|----------|
| `/api/v2/infrastructure/health` | GET | All services health |
| `/api/v2/infrastructure/{service}/health` | GET | Single service detail |
| `/api/v2/infrastructure/{service}/config` | GET | Service configuration |
| `/api/v2/infrastructure/{service}/config` | PUT | Update config |

---

## 7. Use Case 6: Multimodal Settings

### 7.1 User Story

```
AS AN Agent Owner
I WANT TO enable/disable multimodal capabilities
SO THAT I can control what content types my agent can generate
```

### 7.2 UI Component

**File:** `webui/src/views/multimodal-settings.ts`

```typescript
// Component: saas-multimodal-settings
// Route: /settings/multimodal

Sections:
- CapabilityToggles (image, diagram, screenshot)
- ProviderSettings (DALLE, Mermaid, Playwright)
- VisionSettings (input image processing)
```

### 7.3 Django Ninja API

| Endpoint | Method | Response |
|----------|--------|----------|
| `/api/v2/agents/{id}/multimodal` | GET | Current multimodal config |
| `/api/v2/agents/{id}/multimodal` | PUT | Update multimodal config |

---

## 8. Use Case 7: Tier Quota Management

### 8.1 User Story

```
AS A SAAS Administrator
I WANT TO configure quotas for each subscription tier
SO THAT I can enforce usage limits
```

### 8.2 UI Component

**File:** `webui/src/views/tier-quotas.ts`

```typescript
// Component: saas-tier-quotas
// Route: /platform/subscriptions/:id/quotas

Sections:
- CoreQuotasForm (agents, users, storage)
- ApiQuotasForm (calls, tokens, voice)
- MultimodalQuotasForm (images, diagrams, screenshots)
- EnforcementPolicyRadio (HARD/SOFT/NONE)
```

### 8.3 Django Ninja API

| Endpoint | Method | Response |
|----------|--------|----------|
| `/api/v2/tiers/{id}/quotas` | GET | Current tier quotas |
| `/api/v2/tiers/{id}/quotas` | PUT | Update tier quotas |

---

## 9. Use Case 8: Real-Time Developer Metrics

### 9.1 User Story

```
AS A Developer
I WANT TO see real-time metrics for my agent's requests
SO THAT I can debug performance issues
```

### 9.2 UI Component

**File:** `webui/src/views/dev-metrics.ts`

```typescript
// Component: saas-dev-metrics
// Route: /dev/metrics

Sections:
- ThinkingPipelineBreakdown (stage latencies)
- LLMCallDetails (tokens, latency, cost)
- ToolExecutionList (recent tool calls)
- LiveRefreshToggle
```

### 9.3 Django Ninja API

| Endpoint | Method | Response |
|----------|--------|----------|
| `/api/v2/agents/{id}/metrics/realtime` | GET | Latest request metrics |
| `/api/v2/agents/{id}/metrics/thinking` | GET | Thinking stage breakdown |

---

## 10. Use Case 9: Permission Browser

### 10.1 User Story

```
AS A SAAS Administrator
I WANT TO browse all permissions and their role assignments
SO THAT I can understand and manage access control
```

### 10.2 UI Component

**File:** `webui/src/views/saas-permissions.ts` (EXISTS)

```typescript
// Component: saas-permissions
// Route: /platform/permissions

Sections:
- PermissionMatrix (resources x actions)
- RoleAssignmentTable
- AccessCheckerTool
```

---

## 11. Use Case 10: Tenant Creation Wizard

### 11.1 User Story

```
AS A SAAS Administrator
I WANT TO create a new tenant with guided steps
SO THAT I can onboard new organizations correctly
```

### 11.2 UI Component

**File:** `webui/src/views/tenant-wizard.ts`

```typescript
// Component: saas-tenant-wizard
// Route: /platform/tenants/create

Steps:
1. Basic Info (name, slug, admin email)
2. Tier Selection (select subscription tier)
3. Feature Overrides (enable/disable features)
4. API Keys (provision initial keys)
5. Review & Create
```

### 11.3 Django Ninja API

| Endpoint | Method | Response |
|----------|--------|----------|
| `/api/v2/tenants` | POST | Create tenant |
| `/api/v2/tenants/{id}/provision` | POST | Provision in Keycloak/Lago |

### 11.4 Flow Diagram

```
Admin opens /platform/tenants/create
    │
    ├─→ Step 1: Enter name, slug, admin email
    │
    ├─→ Step 2: Select tier from dropdown
    │       └─→ API: GET /api/v2/tiers
    │
    ├─→ Step 3: Toggle feature overrides
    │
    ├─→ Step 4: Configure initial API keys
    │
    ├─→ Step 5: Review all settings
    │
    ├─→ Click "Create Tenant"
    │       └─→ API: POST /api/v2/tenants
    │           └─→ Create Tenant in ORM
    │           └─→ Trigger Temporal workflow
    │               ├─→ Create Keycloak realm
    │               ├─→ Create Lago customer
    │               └─→ Provision resources
    │           └─→ Return tenant ID
    │
    └─→ Redirect to /platform/tenants/{id}
```

---

## 12. Component Architecture

### 12.1 Shared UI Components

| Component | Purpose | Used In |
|-----------|---------|---------|
| `saas-data-table` | Paginated tables | All list views |
| `saas-modal` | Modal dialogs | All edit forms |
| `saas-form-field` | Form inputs | All forms |
| `saas-toast` | Notifications | All views |
| `saas-metric-card` | Metric display | Dashboards |
| `saas-progress-bar` | Quota progress | Usage views |
| `saas-chart` | Charts | Metrics views |

### 12.2 API Client

**File:** `webui/src/api/client.ts`

```typescript
// Standard API client methods
- get<T>(path: string): Promise<T>
- post<T>(path: string, body: any): Promise<T>
- put<T>(path: string, body: any): Promise<T>
- delete(path: string): Promise<void>
```

---

## 13. Implementation Checklist

### Phase 1: Core Infrastructure (Week 1)

- [ ] Infrastructure Dashboard (`infrastructure-dashboard.ts`)
- [ ] Rate Limit Editor (`ratelimit-editor.ts`)
- [ ] Platform Metrics (`platform-metrics.ts`)
- [ ] Django `infrastructure` app with ORM models
- [ ] Django Ninja API endpoints for infrastructure

### Phase 2: User Dashboards (Week 2)

- [ ] Tenant Usage (`tenant-usage.ts`)
- [ ] Tenant Metrics (`tenant-metrics.ts`)
- [ ] Dev Metrics (`dev-metrics.ts`)
- [ ] Usage tracking ORM models
- [ ] Metrics aggregation API

### Phase 3: Configuration (Week 3)

- [ ] Model Settings (`model-settings.ts`)
- [ ] Multimodal Settings (`multimodal-settings.ts`)
- [ ] Tier Quotas (`tier-quotas.ts`)
- [ ] Agent config API updates

### Phase 4: Administration (Week 4)

- [ ] Tenant Wizard (`tenant-wizard.ts`)
- [ ] Permission Browser enhancements
- [ ] Full E2E testing
