# SRS: Unified Infrastructure Administration Architecture

**Document ID:** SA01-SRS-INFRASTRUCTURE-ADMIN-2025-12
**Purpose:** Define how ALL system components are administered through unified UI
**Status:** CANONICAL REFERENCE

---

## 1. The Complete System

This is NOT just Django. This is a **distributed system** with multiple services:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PLATFORM ADMIN UI (Custom Lit)                         │
│                           /platform/infrastructure/*                        │
│                                                                             │
│   Unified interface to view, configure, and monitor ALL services            │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────────
│                        DJANGO NINJA API LAYER                               │
│                                                                             │
│   /api/v2/infrastructure/*  - Unified API for all services                  │
│   /api/v2/ratelimit/*       - Rate limit configuration                      │
│   /api/v2/health/*          - Health checks for all services                │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────────┐
          │                         │                             │
          ▼                         ▼                             ▼
┌─────────────────┐     ┌─────────────────┐           ┌─────────────────┐
│   PostgreSQL    │     │     Redis       │           │    Temporal     │
│   (Primary DB)  │     │   (Cache/RL)    │           │   (Workflows)   │
└─────────────────┘     └─────────────────┘           └─────────────────┘
          │                         │                             │
          ▼                         ▼                             ▼
┌─────────────────┐     ┌─────────────────┐           ┌─────────────────┐
│    Qdrant       │     │    Keycloak     │           │      Lago       │
│   (Vectors)     │     │     (Auth)      │           │   (Billing)     │
└─────────────────┘     └─────────────────┘           └─────────────────┘
          │                         │                             │
          ▼                         ▼                             ▼
┌─────────────────┐     ┌─────────────────┐           ┌─────────────────┐
│   SomaBrain     │     │    Whisper      │           │     Kokoro      │
│   (Memory)      │     │     (STT)       │           │     (TTS)       │
└─────────────────┘     └─────────────────┘           └─────────────────┘
```

---

## 2. Service Inventory (ALL Administrable)

| Service | Purpose | Admin Route | Config Source |
|---------|---------|-------------|---------------|
| **PostgreSQL** | Primary database | `/platform/infrastructure/database` | Django Settings |
| **Redis** | Cache, Rate Limiting, Sessions | `/platform/infrastructure/redis` | UI + ORM |
| **Temporal** | Workflow orchestration | `/platform/infrastructure/temporal` | UI + ORM |
| **Qdrant** | Vector embeddings | `/platform/infrastructure/qdrant` | UI + ORM |
| **Keycloak** | Authentication/SSO | `/platform/infrastructure/auth` | UI + ORM |
| **Lago** | Billing/Subscriptions | `/platform/infrastructure/billing` | UI + ORM |
| **SomaBrain** | Cognitive Memory | `/platform/infrastructure/somabrain` | UI + ORM |
| **Whisper** | Speech-to-Text | `/platform/infrastructure/voice/stt` | UI + ORM |
| **Kokoro** | Text-to-Speech | `/platform/infrastructure/voice/tts` | UI + ORM |
| **MCP Servers** | Tool Extensions | `/platform/infrastructure/mcp` | UI + ORM |
| **S3/MinIO** | Object Storage | `/platform/infrastructure/storage` | UI + ORM |
| **SMTP** | Email Delivery | `/platform/infrastructure/email` | UI + ORM |

---

## 3. Rate Limiting Administration (Redis)

### 3.1 Current State (Code-Based)

```python
# admin/ratelimit/api.py - Currently defined in code
RATE_LIMITS = {
    "api_calls": {"limit": 1000, "window": 3600},  # 1000/hour
    "voice_minutes": {"limit": 60, "window": 86400},  # 60/day
}
```

### 3.2 Target State (UI-Based Administration)

**Route:** `/platform/infrastructure/redis/ratelimits`

**UI Screen:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Infrastructure > Redis > Rate Limits                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Global Rate Limits                                    [+ Add New]  │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │  KEY                    LIMIT     WINDOW      POLICY    ACTIONS    │   │
│  │  ─────────────────────────────────────────────────────────────────  │   │
│  │  api_calls              1000      1 hour      HARD      [Edit]     │   │
│  │  voice_minutes          60        24 hours    SOFT      [Edit]     │   │
│  │  llm_tokens             100000    24 hours    SOFT      [Edit]     │   │
│  │  file_uploads           50        1 hour      HARD      [Edit]     │   │
│  │  memory_queries         500       1 hour      SOFT      [Edit]     │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Per-Tier Overrides                                                 │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │  TIER          api_calls   voice_min   llm_tokens   file_uploads   │   │
│  │  ───────────────────────────────────────────────────────────────    │   │
│  │  Free          100         0           10000        10             │   │
│  │  Starter       1000        60          100000       50             │   │
│  │  Team          10000       500         1000000      500            │   │
│  │  Enterprise    Unlimited   Unlimited   Unlimited    Unlimited      │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Live Metrics (Real-time from Redis)                                │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │  Current Usage    ████████░░░░░░░░  52% of limit                   │   │
│  │  Active Keys      1,247                                            │   │
│  │  Blocked Requests 23 (last hour)                                   │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Data Model for Rate Limits

```python
# admin/ratelimit/models.py (NEW)
class RateLimitPolicy(models.Model):
    key = models.CharField(max_length=100, unique=True)  # 'api_calls'
    limit = models.IntegerField()  # 1000
    window_seconds = models.IntegerField()  # 3600
    policy = models.CharField(choices=['HARD', 'SOFT', 'WARN'])
    applies_to = models.CharField(choices=['GLOBAL', 'TIER', 'TENANT', 'AGENT'])
    tier = models.ForeignKey(SubscriptionTier, null=True)  # For tier overrides
    tenant = models.ForeignKey(Tenant, null=True)  # For tenant overrides

# API endpoint reads from ORM, writes to Redis
```

---

## 4. Temporal Workflow Administration

**Route:** `/platform/infrastructure/temporal`

**UI Screen:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Infrastructure > Temporal                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Connection Status: 🟢 Connected (temporal:7233)                            │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Active Workflows                                                   │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │  WORKFLOW              COUNT    RUNNING   PENDING   FAILED         │   │
│  │  ────────────────────────────────────────────────────────────────── │   │
│  │  tenant-provisioning   45       2         1         0              │   │
│  │  sleep-cycle           128      5         0         0              │   │
│  │  memory-consolidation  89       12        3         1              │   │
│  │  usage-sync            500      0         0         2              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Workflow Settings                                    [Save]        │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │  Default Timeout:        [300] seconds                              │   │
│  │  Retry Policy:           [3] attempts                               │   │
│  │  Backoff Multiplier:     [2.0]                                      │   │
│  │  Max Concurrent:         [100] workflows                            │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Complete Infrastructure Dashboard

**Route:** `/platform/infrastructure`

**UI Screen:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Platform > Infrastructure                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  OVERALL STATUS: 🟢 All Systems Operational                                 │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ PostgreSQL   │  │    Redis     │  │   Temporal   │  │   Qdrant     │    │
│  │ 🟢 Healthy   │  │ 🟢 Healthy   │  │ 🟢 Healthy   │  │ 🟢 Healthy   │    │
│  │ 45ms latency │  │ 2ms latency  │  │ 5 workflows  │  │ 1.2M vectors │    │
│  │ [Manage →]   │  │ [Manage →]   │  │ [Manage →]   │  │ [Manage →]   │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  Keycloak    │  │    Lago      │  │  SomaBrain   │  │   Voice      │    │
│  │ 🟢 Healthy   │  │ 🟢 Healthy   │  │ 🟡 Degraded  │  │ 🟢 Healthy   │    │
│  │ 3 realms     │  │ $12.4K MRR   │  │ 85% memory   │  │ Whisper+Kokoro│   │
│  │ [Manage →]   │  │ [Manage →]   │  │ [Manage →]   │  │ [Manage →]   │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ MCP Servers  │  │   Storage    │  │    Email     │  │ Rate Limits  │    │
│  │ 🟢 12 active │  │ 🟢 S3 Ready  │  │ 🟢 SMTP OK   │  │ 🟢 Normal    │    │
│  │ [Manage →]   │  │ [Manage →]   │  │ [Manage →]   │  │ [Manage →]   │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. How Each Service is Administered

| Service | View Status | Configure | Monitor | Rate Limit |
|---------|-------------|-----------|---------|------------|
| **PostgreSQL** | Connection, latency | Pool size, timeout | Query stats | N/A |
| **Redis** | Memory, keys | TTL defaults | Hit/miss rate | **YES - VISUAL** |
| **Temporal** | Workflow counts | Timeout, retry | Running/failed | Per-workflow |
| **Qdrant** | Vector count | Collection config | Query latency | Per-collection |
| **Keycloak** | Realm count | Realm settings | Auth failures | Login rate |
| **Lago** | Revenue, subs | Plan sync | Invoice status | N/A |
| **SomaBrain** | Memory usage | Retention, sleep | Consolidation | Per-agent |
| **Whisper** | Latency | Model size | Transcription rate | Voice minutes |
| **Kokoro** | Latency | Voice selection | Synthesis rate | Voice minutes |
| **MCP Servers** | Active count | Server registry | Tool calls | Per-server |
| **S3/MinIO** | Usage, objects | Bucket policy | Upload rate | Storage quota |
| **SMTP** | Queue status | Connection | Delivery rate | Emails/hour |

---

## 7. Implementation Architecture

### 7.1 New Django App: `infrastructure`

```
admin/infrastructure/
├── __init__.py
├── api.py              # Django Ninja endpoints for all services
├── models.py           # RateLimitPolicy, ServiceConfig, etc.
├── services/
│   ├── redis_admin.py      # Redis configuration commands
│   ├── temporal_admin.py   # Temporal client wrapper
│   ├── qdrant_admin.py     # Qdrant admin operations
│   ├── keycloak_admin.py   # Keycloak admin API
│   └── lago_admin.py       # Lago admin API
└── health.py           # Health check aggregator
```

### 7.2 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v2/infrastructure` | GET | All service statuses |
| `/api/v2/infrastructure/{service}` | GET | Service detail |
| `/api/v2/infrastructure/{service}/config` | GET, PUT | Service config |
| `/api/v2/infrastructure/ratelimits` | GET, POST, PUT | Rate limit policies |
| `/api/v2/infrastructure/health` | GET | Aggregated health |

### 7.3 Frontend Components

| Component | Route | Purpose |
|-----------|-------|---------|
| `infrastructure-dashboard.ts` | `/platform/infrastructure` | Overview |
| `redis-admin.ts` | `/platform/infrastructure/redis` | Redis config |
| `temporal-admin.ts` | `/platform/infrastructure/temporal` | Workflows |
| `ratelimit-editor.ts` | `/platform/infrastructure/redis/ratelimits` | Rate limits |

---

## 8. Rate Limit Flow (Visual Configuration)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   1. Admin opens /platform/infrastructure/redis/ratelimits                  │
│                                                                             │
│   2. UI loads current limits from Django ORM (RateLimitPolicy model)        │
│                                                                             │
│   3. Admin changes "api_calls" limit from 1000 to 2000                      │
│                                                                             │
│   4. UI calls: PUT /api/v2/infrastructure/ratelimits/api_calls              │
│      Body: { "limit": 2000, "window_seconds": 3600, "policy": "HARD" }      │
│                                                                             │
│   5. Django Ninja endpoint:                                                 │
│      a) Updates RateLimitPolicy in PostgreSQL                               │
│      b) Updates Redis key: SET ratelimit:config:api_calls {...}             │
│      c) Publishes event to invalidate cached limits                         │
│                                                                             │
│   6. All Django processes pick up new limit immediately                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Summary: Unified Administration

**Everything is administrable from ONE interface:**

| What | Where | How |
|------|-------|-----|
| Tenants, Users, Agents | `/platform/tenants` | Custom UI → API → ORM |
| Tiers, Features, Quotas | `/platform/subscriptions` | Custom UI → API → ORM |
| Rate Limits | `/platform/infrastructure/redis` | Custom UI → API → ORM → Redis |
| Workflow Settings | `/platform/infrastructure/temporal` | Custom UI → API → ORM → Temporal |
| Auth Realms | `/platform/infrastructure/auth` | Custom UI → API → Keycloak Admin |
| Billing Plans | `/platform/infrastructure/billing` | Custom UI → API → Lago Admin |
| Voice Config | `/platform/infrastructure/voice` | Custom UI → API → ORM |
| MCP Servers | `/platform/infrastructure/mcp` | Custom UI → API → ORM |
| Storage | `/platform/infrastructure/storage` | Custom UI → API → S3 Admin |
