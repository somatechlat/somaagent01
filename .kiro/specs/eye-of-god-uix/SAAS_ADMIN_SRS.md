# Eye of God SAAS Admin — Software Requirements Specification

## Document Control

| Field | Value |
|-------|-------|
| **Document ID** | SA01-SAAS-SRS-2025-12 |
| **Version** | 1.0 |
| **Date** | 2025-12-22 |
| **Status** | DRAFT |
| **Classification** | CANONICAL |

---

## 1. Executive Summary

The Eye of God SAAS Admin UI provides enterprise-level administration for multi-tenant SomaAgent deployments. It enables SAAS operators to manage **Tenants**, enforce **Quotas**, configure **Subscriptions**, and delegate administration to tenant-level and agent-level users.

**Key Capabilities:**
- Tenant lifecycle management (create, suspend, delete)
- Subscription tiers with quota enforcement
- Hierarchical permission model (SAAS → Tenant → Agent)
- Agent deployment limits and resource allocation
- Billing integration and usage tracking

---

## 2. Permission Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SAAS PLATFORM LEVEL                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ SAAS Super Admin (God Mode)                                          │   │
│  │  • Create/Delete Tenants                                             │   │
│  │  • Set Subscription Tiers                                            │   │
│  │  • View All Usage/Billing                                            │   │
│  │  • Platform-wide Feature Flags                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TENANT LEVEL (e.g., SomaTechDev)                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Tenant SysAdmin                                                      │   │
│  │  • Manage Tenant Users                                               │   │
│  │  • Create/Configure Agents (within quota)                            │   │
│  │  • View Tenant Billing                                               │   │
│  │  • Tenant-wide Settings                                              │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ Tenant Admin                                                         │   │
│  │  • Manage Agent Admins                                               │   │
│  │  • Configure Agent Defaults                                          │   │
│  │  • View Audit Logs                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AGENT LEVEL (e.g., SomaAgent01)                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Agent Owner         • Full control of this specific agent           │   │
│  │ Agent Admin         • Manage agent settings, models, tools          │   │
│  │ Agent Developer     • DEV mode access, debugging                    │   │
│  │ Agent Trainer       • TRN mode, cognitive parameter tuning          │   │
│  │ Agent User          • Standard interaction (STD mode)               │   │
│  │ Agent Viewer        • Read-only access (RO mode)                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. SpiceDB Permission Schema Extension

```zed
// SAAS Platform Level
definition platform {}

definition saas_admin {
    relation platform: platform
    
    permission manage_tenants = platform
    permission view_billing = platform
    permission configure_platform = platform
}

// Tenant Level (extended)
definition tenant {
    relation sysadmin: user          // Tenant owner/super admin
    relation admin: user             // Tenant administrators
    relation developer: user         // Developers with DEV access
    relation trainer: user           // Trainers with TRN access
    relation member: user            // Regular users
    relation viewer: user            // Read-only users
    
    // Subscription limits
    relation subscription: subscription_tier
    
    // Computed permissions
    permission manage = sysadmin
    permission administrate = sysadmin + admin
    permission develop = sysadmin + admin + developer
    permission train = sysadmin + admin + trainer
    permission use = sysadmin + admin + developer + trainer + member
    permission view = sysadmin + admin + developer + trainer + member + viewer
    
    // Agent management
    permission create_agent = sysadmin + admin
    permission delete_agent = sysadmin
}

// Subscription Tier (NEW)
definition subscription_tier {
    relation owner: tenant
    
    // Limits stored as relation metadata
    // max_agents: int
    // max_users: int
    // max_tokens_per_month: int
    // max_storage_gb: int
}

// Agent Level (NEW)
definition agent {
    relation tenant: tenant
    relation owner: user              // Agent owner (full control)
    relation admin: user              // Agent admins
    relation developer: user          // Agent developers
    relation trainer: user            // Agent trainers
    relation user: user               // Agent users
    relation viewer: user             // Agent viewers
    
    // Mode permissions
    permission activate_adm = owner + admin
    permission activate_dev = owner + admin + developer
    permission activate_trn = owner + admin + trainer
    permission activate_std = owner + admin + developer + trainer + user
    permission activate_ro = owner + admin + developer + trainer + user + viewer
    
    // Agent configuration
    permission configure = owner + admin
    permission view_settings = owner + admin + developer + trainer
}
```

---

## 4. UI Views Specification

### 4.1 SAAS Super Admin Dashboard

**Route:** `/saas/dashboard`  
**Permission:** `saas_admin->manage_tenants`

**Features:**
- Platform overview (total tenants, users, agents)
- Revenue/billing summary
- System health metrics
- Feature flag management

---

### 4.2 Tenant Management

**Route:** `/saas/tenants`  
**Permission:** `saas_admin->manage_tenants`

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Tenant unique identifier |
| `name` | string | Organization name |
| `slug` | string | URL-safe identifier |
| `subscription_tier` | enum | free/starter/team/enterprise |
| `status` | enum | active/suspended/pending |
| `created_at` | datetime | Creation timestamp |
| `owner_email` | string | Primary contact |

**Actions:**
- Create Tenant (modal form)
- Edit Tenant Settings
- Suspend/Reactivate Tenant
- Delete Tenant (with confirmation)
- Impersonate Tenant (for support)

---

### 4.3 Subscription Tiers

**Route:** `/saas/subscriptions`  
**Permission:** `saas_admin->configure_platform`

| Tier | Max Agents | Max Users | Tokens/Month | Storage | Price |
|------|------------|-----------|--------------|---------|-------|
| **Free** | 1 | 3 | 100K | 1 GB | $0 |
| **Starter** | 3 | 10 | 1M | 10 GB | $49/mo |
| **Team** | 10 | 50 | 10M | 100 GB | $199/mo |
| **Enterprise** | Unlimited | Unlimited | Custom | Custom | Custom |

**Actions:**
- Edit tier limits
- Create custom tiers
- Assign tier to tenant

---

### 4.4 Tenant Users (within Tenant Admin)

**Route:** `/admin/users`  
**Permission:** `tenant->administrate`

**User Roles:**
- `sysadmin` - Tenant owner, full control
- `admin` - Administrative access
- `developer` - DEV mode access
- `trainer` - TRN mode access
- `member` - Standard access
- `viewer` - Read-only access

**Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | User identifier |
| `email` | string | Email address |
| `name` | string | Display name |
| `role` | enum | User role within tenant |
| `status` | enum | active/invited/suspended |
| `last_active` | datetime | Last activity |

---

### 4.5 Agent Management

**Route:** `/admin/agents`  
**Permission:** `tenant->create_agent`

**Agent Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Agent identifier |
| `name` | string | Agent name |
| `slug` | string | URL-safe identifier |
| `status` | enum | running/stopped/error |
| `owner_id` | UUID | Agent owner user |
| `chat_model` | string | Primary LLM model |
| `memory_enabled` | bool | SomaBrain integration |
| `voice_enabled` | bool | AgentVoiceBox integration |
| `created_at` | datetime | Creation timestamp |

**Actions:**
- Create Agent (within tenant quota)
- Configure Agent Settings
- Start/Stop Agent
- Delete Agent
- Transfer Ownership

**Quota Enforcement:**
```
if tenant.agent_count >= tenant.subscription.max_agents:
    raise QuotaExceededError("Agent limit reached for subscription tier")
```

---

### 4.6 Agent-Level User Management

**Route:** `/agent/{agent_id}/users`  
**Permission:** `agent->configure`

**Agent Roles:**
- `owner` - Full control (single user)
- `admin` - Agent configuration
- `developer` - DEV mode access
- `trainer` - TRN mode access
- `user` - Standard interaction
- `viewer` - Read-only

---

## 5. API Endpoints

### 5.1 SAAS Admin APIs

```
# Tenant Management
GET    /api/v2/saas/tenants                  # List tenants
POST   /api/v2/saas/tenants                  # Create tenant
GET    /api/v2/saas/tenants/{id}             # Get tenant
PUT    /api/v2/saas/tenants/{id}             # Update tenant
DELETE /api/v2/saas/tenants/{id}             # Delete tenant
POST   /api/v2/saas/tenants/{id}/suspend     # Suspend tenant
POST   /api/v2/saas/tenants/{id}/activate    # Activate tenant

# Subscription Management
GET    /api/v2/saas/subscriptions            # List tiers
POST   /api/v2/saas/subscriptions            # Create tier
PUT    /api/v2/saas/tenants/{id}/subscription # Assign tier

# Usage & Billing
GET    /api/v2/saas/usage                    # Platform usage
GET    /api/v2/saas/tenants/{id}/usage       # Tenant usage
GET    /api/v2/saas/billing                  # Billing summary
```

### 5.2 Tenant Admin APIs

```
# User Management
GET    /api/v2/admin/users                   # List tenant users
POST   /api/v2/admin/users                   # Invite user
PUT    /api/v2/admin/users/{id}              # Update user
DELETE /api/v2/admin/users/{id}              # Remove user
PUT    /api/v2/admin/users/{id}/role         # Change role

# Agent Management
GET    /api/v2/admin/agents                  # List agents
POST   /api/v2/admin/agents                  # Create agent
GET    /api/v2/admin/agents/{id}             # Get agent
PUT    /api/v2/admin/agents/{id}             # Update agent
DELETE /api/v2/admin/agents/{id}             # Delete agent
POST   /api/v2/admin/agents/{id}/start       # Start agent
POST   /api/v2/admin/agents/{id}/stop        # Stop agent
```

### 5.3 Agent Admin APIs

```
# Agent Users
GET    /api/v2/agents/{id}/users             # List agent users
POST   /api/v2/agents/{id}/users             # Add user to agent
PUT    /api/v2/agents/{id}/users/{uid}/role  # Change agent role
DELETE /api/v2/agents/{id}/users/{uid}       # Remove from agent
```

---

## 6. UI Components Required

| Component | Path | Description |
|-----------|------|-------------|
| `eog-tenant-list` | `/saas/tenants` | Tenant grid with filters |
| `eog-tenant-form` | Modal | Create/edit tenant form |
| `eog-subscription-manager` | `/saas/subscriptions` | Tier configuration |
| `eog-quota-display` | Sidebar | Quota usage indicators |
| `eog-user-table` | `/admin/users` | User management table |
| `eog-role-selector` | Form | Role dropdown with descriptions |
| `eog-agent-grid` | `/admin/agents` | Agent cards with status |
| `eog-agent-form` | Modal | Create/configure agent |
| `eog-usage-chart` | Dashboard | Usage over time charts |

---

## 7. Database Schema

```sql
-- Subscription Tiers
CREATE TABLE subscription_tiers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(64) NOT NULL,
    slug VARCHAR(64) UNIQUE NOT NULL,
    max_agents INT NOT NULL DEFAULT 1,
    max_users INT NOT NULL DEFAULT 3,
    max_tokens_per_month BIGINT NOT NULL DEFAULT 100000,
    max_storage_bytes BIGINT NOT NULL DEFAULT 1073741824,
    price_cents INT NOT NULL DEFAULT 0,
    billing_interval VARCHAR(16) DEFAULT 'monthly',
    is_custom BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tenants
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(64) UNIQUE NOT NULL,
    subscription_tier_id UUID REFERENCES subscription_tiers(id),
    status VARCHAR(32) DEFAULT 'pending',
    owner_user_id UUID REFERENCES users(id),
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    suspended_at TIMESTAMPTZ
);

-- Tenant Users (junction)
CREATE TABLE tenant_users (
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(32) NOT NULL,
    invited_at TIMESTAMPTZ DEFAULT NOW(),
    accepted_at TIMESTAMPTZ,
    PRIMARY KEY (tenant_id, user_id)
);

-- Agents
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(64) NOT NULL,
    status VARCHAR(32) DEFAULT 'stopped',
    owner_user_id UUID REFERENCES users(id),
    config JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, slug)
);

-- Agent Users (junction)
CREATE TABLE agent_users (
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(32) NOT NULL,
    PRIMARY KEY (agent_id, user_id)
);

-- Usage Tracking
CREATE TABLE usage_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    agent_id UUID REFERENCES agents(id),
    user_id UUID REFERENCES users(id),
    metric_type VARCHAR(64) NOT NULL,
    value BIGINT NOT NULL,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 8. Implementation Priority

| Phase | Feature | Priority |
|-------|---------|----------|
| 1 | Tenant CRUD | HIGH |
| 1 | Subscription Tiers | HIGH |
| 1 | Tenant User Management | HIGH |
| 2 | Agent Quota Enforcement | HIGH |
| 2 | Agent CRUD | HIGH |
| 2 | Agent User Management | MEDIUM |
| 3 | Usage Tracking | MEDIUM |
| 3 | Billing Integration | MEDIUM |
| 4 | Platform Analytics | LOW |
| 4 | Custom Tier Builder | LOW |

---

**Document Status:** DRAFT — Awaiting Review
