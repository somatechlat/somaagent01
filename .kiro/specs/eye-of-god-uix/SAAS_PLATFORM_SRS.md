# Eye of God SAAS Platform — Software Requirements Specification

## IEEE 830 / ISO/IEC/IEEE 29148:2018 Compliant

---

## Document Control

| Field | Value |
|-------|-------|
| **Document ID** | SA01-SAAS-PLATFORM-SRS-2025-12 |
| **Version** | 2.0 |
| **Date** | 2025-12-22 |
| **Status** | CANONICAL |
| **Classification** | Internal |
| **Author** | SomaAgent Development Team |
| **Approvers** | Technical Lead, Product Owner |

### Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-21 | Dev Team | Initial SAAS Admin SRS |
| 2.0 | 2025-12-22 | Dev Team | Full platform SRS with auth flows, mode selection, infrastructure |

---

## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification (SRS) defines the complete requirements for the **Eye of God SAAS Platform** — a multi-tenant enterprise AI agent management system. It covers:

- Multi-tenant architecture
- Authentication and authorization flows
- God Mode (SAAS Admin) capabilities
- Tenant isolation and quota management
- Infrastructure requirements
- UI/UX specifications

### 1.2 Scope

**System Name:** Eye of God SAAS Platform

**Product Features:**
- Multi-tenant AI agent deployment platform
- Hierarchical permission system (Platform → Tenant → Agent)
- Real-time voice interaction (AgentVoiceBox integration)
- Fractal memory system (SomaBrain integration)
- Enterprise billing and quota management

**Out of Scope:**
- Mobile native applications (future phase)
- On-premise deployment (cloud-only for V1)

### 1.3 Definitions and Acronyms

| Term | Definition |
|------|------------|
| **God Mode** | SAAS Super Administrator access level with platform-wide visibility |
| **Tenant** | Enterprise customer organization with isolated resources |
| **Agent** | AI assistant instance deployed within a tenant |
| **SpiceDB** | Google Zanzibar-based authorization system |
| **MRR** | Monthly Recurring Revenue |

### 1.4 References

| Document | ID |
|----------|-----|
| UI Architecture | SA01-EOG-UI-ARCH-2025-12 |
| Design Document | SA01-EOG-DES-2025-12 |
| SAAS Admin SRS | SA01-SAAS-SRS-2025-12 |

---

## 2. Overall Description

### 2.1 Product Perspective

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EYE OF GOD SAAS PLATFORM                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         PRESENTATION LAYER                              │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │ │
│  │  │  Web UI      │  │  Desktop     │  │  CLI         │                  │ │
│  │  │  (Lit 3.x)   │  │  (Tauri)     │  │  (Ratatui)   │                  │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│                           HTTPS/WSS (Connection Pool)                        │
│                                    ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                          API GATEWAY LAYER                              │ │
│  │  ┌──────────────────────────────────────────────────────────────────┐  │ │
│  │  │              Django Ninja API (Port 8020)                         │  │ │
│  │  │  /api/v2/saas/*     Platform Administration                       │  │ │
│  │  │  /api/v2/auth/*     Authentication & Sessions                     │  │ │
│  │  │  /api/v2/admin/*    Tenant Administration                         │  │ │
│  │  │  /api/v2/agents/*   Agent Management                              │  │ │
│  │  │  /api/v2/chat/*     Conversation                                  │  │ │
│  │  │  /ws/v2/*           Real-time WebSocket                           │  │ │
│  │  └──────────────────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                       AUTHORIZATION LAYER                               │ │
│  │  ┌──────────────────────────────────────────────────────────────────┐  │ │
│  │  │                    SpiceDB (Port 50051)                           │  │ │
│  │  │  Platform → Tenant → Agent → User Permission Graph                │  │ │
│  │  └──────────────────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                          DATA LAYER                                     │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │ │
│  │  │  PostgreSQL  │  │  Redis       │  │  Kafka       │                  │ │
│  │  │  (Primary)   │  │  (Cache/WS)  │  │  (Events)    │                  │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                      INTEGRATION LAYER                                  │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │ │
│  │  │  SomaBrain   │  │AgentVoiceBox │  │  LLM APIs    │                  │ │
│  │  │  (Memory)    │  │  (Voice)     │  │  (OpenAI/+)  │                  │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 User Classes and Characteristics

| User Class | Description | Access Level |
|------------|-------------|--------------|
| **SAAS Super Admin** | Platform operators (God Mode) | Full platform access |
| **Tenant SysAdmin** | Organization owners | Full tenant access |
| **Tenant Admin** | Organization administrators | Tenant management |
| **Agent Admin** | Agent-level administrators | Agent configuration |
| **Developer** | Technical users | DEV mode access |
| **Trainer** | AI trainers | TRN mode access |
| **User** | Standard users | STD mode access |
| **Viewer** | Read-only users | RO mode access |

### 2.3 Operating Environment

| Component | Specification |
|-----------|---------------|
| **Cloud Provider** | AWS/GCP/Azure (Kubernetes) |
| **Container Runtime** | Docker + K8s |
| **Database** | PostgreSQL 15+ |
| **Cache** | Redis 7+ |
| **Message Queue** | Kafka 3+ |
| **Auth Service** | SpiceDB (Zanzibar) |
| **Billing Service** | Lago (Open Source) |

### 2.4 Infrastructure Stack (Complete)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        INFRASTRUCTURE LAYER                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      CORE SERVICES                                   │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │    │
│  │  │  Django API  │  │  SomaBrain   │  │AgentVoiceBox │               │    │
│  │  │  (Port 8020) │  │  (Port 8030) │  │  (Port 8035) │               │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    PLATFORM SERVICES (Always Present)                │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │    │
│  │  │   SpiceDB    │  │    Lago      │  │   Keycloak   │               │    │
│  │  │  (Auth/RBAC) │  │  (Billing)   │  │   (SSO)      │               │    │
│  │  │  Port 50051  │  │  Port 3000   │  │  Port 8080   │               │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      DATA SERVICES                                   │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │    │
│  │  │  PostgreSQL  │  │    Redis     │  │    Kafka     │               │    │
│  │  │  (Primary)   │  │  (Cache/WS)  │  │  (Events)    │               │    │
│  │  │  Port 5432   │  │  Port 6379   │  │  Port 9092   │               │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    EXTERNAL INTEGRATIONS                             │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │    │
│  │  │  LLM APIs    │  │   Stripe     │  │   SendGrid   │               │    │
│  │  │  (OpenAI/+)  │  │  (Payments)  │  │  (Email)     │               │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2.5 Lago Billing System Integration

### 2.5.1 Lago Overview

Lago is an open-source usage-based billing platform that handles:
- Usage event ingestion
- Metrics aggregation  
- Pricing and packaging
- Invoicing
- Payment collection

**Reference:** https://www.getlago.com/

### 2.5.2 Lago 5-Step Billing Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        LAGO BILLING WORKFLOW                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. USAGE INGESTION                                                          │
│     └── Agent sends events: tokens_used, api_calls, storage_bytes           │
│                                                                              │
│  2. METRICS AGGREGATION                                                      │
│     └── Lago aggregates: COUNT, SUM, MAX, LATEST, WEIGHTED_SUM              │
│                                                                              │
│  3. PRICING & PACKAGING                                                      │
│     └── Plans: Free, Starter, Team, Enterprise (with overages)              │
│                                                                              │
│  4. INVOICING                                                                │
│     └── Automatic invoice generation at billing period end                  │
│                                                                              │
│  5. PAYMENTS                                                                 │
│     └── Integration with Stripe, PayPal, or manual collection               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.5.3 Billable Metrics for SomaAgent

| Metric Code | Type | Description | Unit |
|-------------|------|-------------|------|
| `tokens_input` | SUM | LLM input tokens | tokens |
| `tokens_output` | SUM | LLM output tokens | tokens |
| `api_calls` | COUNT | API requests made | calls |
| `storage_bytes` | LATEST | Storage used | bytes |
| `voice_minutes` | SUM | Voice processing time | minutes |
| `agents_active` | MAX | Peak active agents | agents |
| `users_active` | MAX | Peak active users | users |
| `memories_stored` | COUNT | Memory writes | memories |

### 2.5.4 Lago API Integration

| Lago Entity | Eye of God Mapping | Description |
|-------------|-------------------|-------------|
| Customer | Tenant | One Lago customer per tenant |
| Subscription | Tenant.subscription | Active plan subscription |
| Plan | Subscription Tier | Free/Starter/Team/Enterprise |
| Billable Metric | Usage Metrics | Token/API/Storage tracking |
| Invoice | Billing → Invoices | Monthly billing documents |
| Wallet | Prepaid Credits | Token pre-purchase |
| Coupon | Discounts | Promotional pricing |

### 2.5.5 Eye of God ↔ Lago Flow

```
┌──────────────────────┐         ┌──────────────────────┐
│    Eye of God UI     │         │        Lago          │
│   (Billing Admin)    │         │   (Billing Engine)   │
├──────────────────────┤         ├──────────────────────┤
│                      │         │                      │
│  Create Tenant ──────┼────────▶│  Create Customer     │
│                      │         │                      │
│  Assign Plan ────────┼────────▶│  Create Subscription │
│                      │         │                      │
│  View Usage ◀────────┼─────────│  Return Metrics      │
│                      │         │                      │
│  View Invoices ◀─────┼─────────│  Return Invoices     │
│                      │         │                      │
│  Apply Coupon ───────┼────────▶│  Apply Coupon        │
│                      │         │                      │
│  Add Credits ────────┼────────▶│  Top-up Wallet       │
│                      │         │                      │
└──────────────────────┘         └──────────────────────┘
         │                                 │
         │                                 │
         ▼                                 ▼
┌──────────────────────┐         ┌──────────────────────┐
│    SomaAgent Core    │         │   Payment Provider   │
│   (Usage Events)     │         │     (Stripe)         │
├──────────────────────┤         ├──────────────────────┤
│                      │         │                      │
│  Chat Request ───────┼────────▶│  Lago sends events   │
│  Voice Call ─────────┼────────▶│  to Stripe for       │
│  Memory Write ───────┼────────▶│  payment collection  │
│                      │         │                      │
└──────────────────────┘         └──────────────────────┘
```

### 2.5.6 Lago UI in Eye of God

| View | Lago API Used | Description |
|------|---------------|-------------|
| Billing Dashboard | GET /analytics | Revenue charts, MRR |
| Tenant Billing | GET /customers/{id} | Tenant subscription & usage |
| Invoices | GET /invoices | Invoice list with download |
| Plans | GET /plans | Plan configuration |
| Usage | GET /billable_metrics | Real-time usage tracking |
| Wallets | GET /wallets | Prepaid credit balances |
| Coupons | GET/POST /coupons | Discount management |

---

### 2.6 Design Constraints

| Constraint | Rationale |
|------------|-----------|
| Multi-tenancy isolation | Enterprise security requirement |
| WebSocket for real-time | Voice latency requirements |
| SpiceDB for auth | Google Zanzibar model for scale |
| Lit 3.x for UI | Web Components for reusability |

---

## 3. System Features

### 3.1 Authentication System

#### 3.1.1 Login Flow

**FR-AUTH-001:** System shall provide email/password authentication  
**FR-AUTH-002:** System shall support OAuth2 providers (Google, GitHub, Microsoft)  
**FR-AUTH-003:** System shall issue JWT tokens with 24h expiration  
**FR-AUTH-004:** System shall support token refresh mechanism  

#### 3.1.2 Mode Selection Flow (God Mode Users)

**FR-AUTH-010:** After login, SAAS admins shall see mode selection screen  
**FR-AUTH-011:** Mode selection shall offer two options:
  - Platform Mode (God View)
  - Tenant Entry (Select tenant to impersonate)

**FR-AUTH-012:** Tenant Entry shall allow role selection (SysAdmin/Admin/User)  
**FR-AUTH-013:** Regular users shall bypass mode selection, entering their tenant directly  

```
Login Flow Diagram:

[Login Page] 
    │
    ▼
[Authenticate]
    │
    ├── IF role == SAAS_ADMIN
    │       │
    │       ▼
    │   [Mode Selection Screen]
    │       ├── Platform Mode → [Platform Dashboard]
    │       └── Enter Tenant → [Select Tenant] → [Tenant UI]
    │
    └── ELSE
            │
            ▼
        [Tenant UI] (User's assigned tenant)
```

#### 3.1.3 Session Management

**FR-AUTH-020:** Session shall store: user_id, tenant_id, entry_mode, role  
**FR-AUTH-021:** Session shall support runtime tenant switching (God users only)  
**FR-AUTH-022:** Session shall create audit log on tenant entry  

### 3.2 Multi-Tenancy System

#### 3.2.1 Tenant Isolation

**FR-TENANT-001:** Each tenant shall have isolated database schema/partition  
**FR-TENANT-002:** API requests shall require X-Tenant-ID header (except platform APIs)  
**FR-TENANT-003:** WebSocket connections shall be tenant-scoped  
**FR-TENANT-004:** File storage shall be tenant-isolated (S3 buckets/prefixes)  

#### 3.2.2 Tenant Lifecycle

**FR-TENANT-010:** SAAS admin shall create tenants with:
  - Name, slug, owner email, subscription tier

**FR-TENANT-011:** Tenants shall have states: pending, active, suspended, deleted  
**FR-TENANT-012:** Suspended tenants shall have read-only access  
**FR-TENANT-013:** Deleted tenants shall have 30-day recovery window  

### 3.3 Subscription & Quota System

#### 3.3.1 Subscription Tiers

**FR-SUB-001:** System shall support tiered subscriptions:

| Tier | Max Agents | Max Users | Tokens/Month | Storage | Price |
|------|------------|-----------|--------------|---------|-------|
| Free | 1 | 3 | 100K | 1 GB | $0 |
| Starter | 3 | 10 | 1M | 10 GB | $49/mo |
| Team | 10 | 50 | 10M | 100 GB | $199/mo |
| Enterprise | Unlimited | Unlimited | Custom | Custom | Custom |

**FR-SUB-002:** System shall enforce quota limits before resource creation  
**FR-SUB-003:** System shall send alerts at 80% and 100% quota usage  

### 3.4 Permission System (SpiceDB)

#### 3.4.1 Permission Schema

**FR-PERM-001:** Permissions shall follow hierarchy:
```
platform → tenant → agent → resource
```

**FR-PERM-002:** Permission checks shall occur at:
  - API Gateway (route-level)
  - Service Layer (action-level)
  - UI (component-level visibility)

#### 3.4.2 SpiceDB Relations

```zed
definition platform {}

definition saas_admin {
    relation platform: platform
    permission manage_tenants = platform
    permission view_billing = platform
    permission configure_platform = platform
}

definition tenant {
    relation sysadmin: user
    relation admin: user
    relation developer: user
    relation trainer: user
    relation member: user
    relation viewer: user
    relation subscription: subscription_tier
    
    permission manage = sysadmin
    permission administrate = sysadmin + admin
    permission develop = administrate + developer
    permission train = administrate + trainer
    permission use = develop + train + member
    permission view = use + viewer
}

definition agent {
    relation tenant: tenant
    relation owner: user
    relation admin: user
    relation developer: user
    relation trainer: user
    relation user: user
    relation viewer: user
    
    permission configure = owner + admin
    permission activate_dev = configure + developer
    permission activate_trn = configure + trainer
    permission interact = activate_dev + activate_trn + user
    permission observe = interact + viewer
}
```

### 3.5 UI System

#### 3.5.1 Platform UI (God Mode)

**FR-UI-001:** Platform Dashboard shall display:
  - Total tenants, agents, users
  - MRR and billing metrics
  - System health status
  - Recent activity feed

**FR-UI-002:** Tenants view shall display:
  - Tenant list with search/filter
  - Quota usage per tenant
  - Actions: Create, Enter, Suspend, Delete

**FR-UI-003:** Billing view shall display:
  - Revenue charts
  - Subscription breakdown
  - Invoice history

#### 3.5.2 Tenant UI (All Roles)

**FR-UI-010:** Same UI components for all roles  
**FR-UI-011:** Components shall hide based on permissions  
**FR-UI-012:** Actions shall disable based on permissions  

#### 3.5.3 Tenant Switcher

**FR-UI-020:** Header shall include tenant switcher (God users only)  
**FR-UI-021:** Switcher shall show: Platform option + tenant list  
**FR-UI-022:** Switching shall preserve current view when possible  

---

## 4. External Interface Requirements

### 4.1 User Interfaces

| Screen | Route | Description |
|--------|-------|-------------|
| Login | `/login` | Email/password auth |
| Mode Selection | `/select-mode` | God user mode selection |
| Platform Dashboard | `/platform` | SAAS admin dashboard |
| Tenants | `/platform/tenants` | Tenant management |
| Billing | `/platform/billing` | Revenue & invoices |
| Chat | `/chat` | Agent conversation |
| Memory | `/memory` | SomaBrain browser |
| Settings | `/settings` | User/agent settings |

### 4.2 API Interfaces

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v2/auth/login` | POST | User authentication |
| `/api/v2/auth/mode-select` | POST | Set entry mode (God users) |
| `/api/v2/saas/tenants` | GET/POST | Tenant CRUD |
| `/api/v2/saas/tenants/{id}/enter` | POST | Enter tenant (impersonate) |
| `/api/v2/admin/users` | GET/POST | Tenant user management |
| `/api/v2/agents` | GET/POST | Agent CRUD |

### 4.3 Hardware Interfaces

N/A (Cloud-native, no hardware dependencies)

### 4.4 Software Interfaces

| System | Interface | Purpose |
|--------|-----------|---------|
| SomaBrain | REST/gRPC | Fractal memory |
| AgentVoiceBox | WebSocket | Real-time voice |
| OpenAI/Anthropic | REST | LLM completions |
| Stripe/Paddle | REST | Billing integration |
| SpiceDB | gRPC | Authorization |

---

## 5. Non-Functional Requirements

### 5.1 Performance

| Metric | Requirement |
|--------|-------------|
| API Latency (p95) | < 200ms |
| Page Load | < 2s |
| WebSocket Latency | < 50ms |
| Voice Round-trip | < 500ms |
| Concurrent Users | 10,000+ per tenant |

### 5.2 Security

| Requirement | Implementation |
|-------------|----------------|
| Encryption at Rest | AES-256 |
| Encryption in Transit | TLS 1.3 |
| Password Storage | bcrypt (cost 12) |
| Session Tokens | JWT (RS256) |
| API Auth | Bearer tokens |
| RBAC | SpiceDB (Zanzibar) |

### 5.3 Scalability

| Component | Strategy |
|-----------|----------|
| API | Horizontal pod scaling (K8s HPA) |
| Database | Read replicas, sharding |
| Cache | Redis Cluster |
| WebSocket | Sticky sessions + Redis Pub/Sub |

### 5.4 Availability

| Metric | Target |
|--------|--------|
| Uptime | 99.9% |
| RTO | 1 hour |
| RPO | 15 minutes |

---

## 6. Implementation Priority

| Phase | Features | Timeline |
|-------|----------|----------|
| **Phase 1** | Login, Auth, Tenant CRUD, Basic UI | Week 1-2 |
| **Phase 2** | Mode Selection, Quota Enforcement, Agent CRUD | Week 3-4 |
| **Phase 3** | Billing Integration, Usage Tracking | Week 5-6 |
| **Phase 4** | Voice Integration, Memory Integration | Week 7-8 |
| **Phase 5** | Analytics, Advanced Admin | Week 9-10 |

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| Eye of God | The admin console UI for SomaAgent |
| God Mode | SAAS Super Admin access level |
| SomaBrain | Fractal memory system |
| AgentVoiceBox | Real-time voice processing system |
| SpiceDB | Zanzibar-based authorization database |
| Tenant | An enterprise customer organization |

---

**Document Status:** CANONICAL — Ready for Implementation
