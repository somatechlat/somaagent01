# SRS: SAAS Platform Admin (God Mode)

**Document ID:** SA01-SRS-SAAS-ADMIN-2025-12  
**Role:** 🔴 SAAS SysAdmin  
**Permission:** `platform->manage`  
**Routes:** `/saas/*`

---

## 1. Screens

### 1.1 Platform Dashboard (`/saas`)

**Purpose:** Overview of entire SaaS platform

**Elements:**
| Element | Type | Description |
|---------|------|-------------|
| Total Tenants | Stat Card | Count with growth % |
| Total Users | Stat Card | All users across tenants |
| MRR | Stat Card | Monthly Recurring Revenue |
| Uptime | Stat Card | Platform uptime % |
| Tenants by Tier | Bar Chart | Distribution |
| System Health | Status Grid | All services |
| Recent Activity | Timeline | Platform events |

**API:**
```
GET /api/v2/saas/stats
GET /api/v2/saas/health
GET /api/v2/saas/activity
```

---

### 1.2 Tenant List (`/saas/tenants`)

**Purpose:** Manage all tenants

**Elements:**
| Element | Type | Actions |
|---------|------|---------|
| Search | Input | Filter by name/email |
| Status Filter | Dropdown | All/Active/Suspended/Pending |
| Tier Filter | Dropdown | Free/Starter/Team/Enterprise |
| Tenant Row | Table | Name, Email, Tier, Users, Agents, Status, Actions |
| Actions | Menu | View, Edit, Suspend, Delete, Impersonate |

**Edge Cases:**
| Scenario | System Response |
|----------|-----------------|
| Delete tenant with active subscriptions | ⚠️ "Cancel subscription first via Lago" |
| Delete tenant with active agents | ⚠️ "This will delete X agents. Confirm?" |
| Suspend tenant with active sessions | ⚠️ "X active sessions will be terminated" |
| Impersonate audit | ✅ Log impersonation to audit trail |

**API:**
```
GET /api/v2/saas/tenants?status=&tier=&search=
DELETE /api/v2/saas/tenants/{id}
POST /api/v2/saas/tenants/{id}/suspend
POST /api/v2/saas/tenants/{id}/impersonate
```

---

### 1.3 Create Tenant (`/saas/tenants/new`)

**Purpose:** Create new tenant

**Form Fields:**
| Field | Type | Validation |
|-------|------|------------|
| Organization Name | Text | Required, 2-100 chars |
| Slug | Text | Required, lowercase, unique |
| Owner Email | Email | Required, valid format |
| Subscription Tier | Select | Free/Starter/Team/Enterprise |
| Initial Agent Name | Text | Optional |
| Send Welcome Email | Toggle | Default: On |

**Edge Cases:**
| Scenario | System Response |
|----------|-----------------|
| Slug already exists | ❌ "Slug 'acme' is already taken" |
| Invalid email format | ❌ "Please enter a valid email" |
| Email already owner | ⚠️ "User already owns another tenant. Continue?" |
| Lago unavailable | ⚠️ "Billing service down. Create without subscription?" |

**API:**
```
POST /api/v2/saas/tenants
{
  "name": "Acme Corp",
  "slug": "acme",
  "owner_email": "admin@acme.com",
  "subscription_tier": "team",
  "initial_agent_name": "Support-AI",
  "send_welcome_email": true
}
```

---

### 1.4 Subscription Tiers (`/saas/subscriptions`)

**Purpose:** Configure pricing tiers

**Tier Configuration:**
| Tier | Max Agents | Max Users | Tokens/Month | Storage | Price |
|------|------------|-----------|--------------|---------|-------|
| Free | 1 | 3 | 100K | 1 GB | $0 |
| Starter | 3 | 10 | 1M | 10 GB | $49/mo |
| Team | 10 | 50 | 10M | 100 GB | $199/mo |
| Enterprise | Custom | Custom | Custom | Custom | Custom |

**Edge Cases:**
| Scenario | System Response |
|----------|-----------------|
| Reduce tier limits | ⚠️ "X tenants exceed new limits. Grandfather?" |
| Delete tier with tenants | ❌ "Cannot delete tier with active tenants" |
| Lago sync fails | ⚠️ "Changes saved locally. Sync to Lago failed." |

**API:**
```
GET /api/v2/saas/subscriptions
PUT /api/v2/saas/subscriptions/{tier_id}
POST /api/v2/saas/subscriptions/{tier_id}/sync-lago
```

---

### 1.5 Platform Health (`/saas/health`)

**Purpose:** Monitor all services

**Services Monitored:**
| Service | Check Type | Healthy Threshold |
|---------|------------|-------------------|
| PostgreSQL | Connection | < 50ms |
| Redis | Ping | < 10ms |
| Kafka | Producer test | < 100ms |
| Milvus | Collection list | < 200ms |
| Temporal | Namespace check | < 100ms |
| Keycloak | JWKS fetch | < 500ms |
| SomaBrain | /health | < 200ms |
| Lago | /health | < 500ms |

**Degradation Handling:**
| Scenario | System Response |
|----------|-----------------|
| SomaBrain down | 🟡 "Memory service degraded. Session-only mode active." |
| Kafka down | 🔴 "Event streaming down. Outbox queueing active." |
| Keycloak down | 🔴 "Auth service down. No new logins possible." |
| Lago down | 🟡 "Billing sync paused. Cached data shown." |

**API:**
```
GET /api/v2/saas/health
GET /api/v2/saas/health/{service}
POST /api/v2/saas/health/{service}/restart
```

---

## 2. User Journey Flow

```mermaid
flowchart TD
    A[Login as SAAS Admin] --> B[/saas Dashboard]
    
    B --> C{Action?}
    
    C -->|Manage Tenants| D[/saas/tenants]
    D --> E[Create Tenant]
    D --> F[Edit Tenant]
    D --> G[Suspend Tenant]
    D --> H[Delete Tenant]
    D --> I[Impersonate]
    
    C -->|Configure Billing| J[/saas/subscriptions]
    J --> K[Edit Tier Limits]
    J --> L[Sync to Lago]
    
    C -->|View Revenue| M[/saas/billing]
    M --> N[Generate Report]
    
    C -->|Monitor Health| O[/saas/health]
    O --> P{Service Down?}
    P -->|Yes| Q[View Degradation Details]
    P -->|No| R[All Systems Healthy]
    
    I --> S[Redirected as Tenant Admin]
    S --> T[Banner: "Impersonating ACME"]
    T --> U[Exit Impersonation]
    U --> B
```

---

## 3. Error Handling

| Error Code | Scenario | User Message | Recovery Action |
|------------|----------|--------------|-----------------|
| 400 | Invalid input | "Please fix the errors below" | Highlight fields |
| 401 | Session expired | "Session expired. Please login again." | Redirect /login |
| 403 | Not SAAS admin | "Access denied" | Redirect /admin |
| 404 | Tenant not found | "Tenant not found" | Back to list |
| 409 | Conflict | "Slug already exists" | Suggest alternatives |
| 429 | Rate limit | "Too many requests. Wait X seconds." | Show countdown |
| 500 | Server error | "Something went wrong. Try again." | Retry button |
| 503 | Service down | "Service temporarily unavailable" | Show status page |

---

## 4. Accessibility Requirements

- All forms keyboard navigable
- ARIA labels on all controls
- 4.5:1 contrast ratio
- Focus indicators visible
- Screen reader announcements for dynamic content
- Reduced motion support

---

**Next:** [SRS-TENANT-ADMIN.md](./SRS-TENANT-ADMIN.md)
