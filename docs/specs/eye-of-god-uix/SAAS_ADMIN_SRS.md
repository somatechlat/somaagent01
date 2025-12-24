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

### 4.3.1 Subscription Tier Builder (Full-Screen Composer)

**Route:** `/saas/subscriptions/builder`  
**Permission:** `saas_admin->configure_platform`

#### Overview

A **full-screen, drag-and-drop tier composition system** that enables SAAS admins to create and configure subscription tiers by dragging features from a catalog and customizing limits. All modals are **full-screen experiences** (100% viewport) for maximum configuration space.

#### Wireframe - Tier Builder

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│  ← Back to Tiers                          TIER BUILDER                    [Save Draft]  │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  ┌────────────────────────────────────────────────────────────┐  ┌────────────────────┐ │
│  │                                                            │  │  FEATURE CATALOG   │ │
│  │   TIER INFO                                                │  │  ────────────────  │ │
│  │   ─────────────────────────────────────────                │  │                    │ │
│  │   Name: [Professional_____________]                         │  │  Search features...│ │
│  │   Slug: [professional] (auto)                              │  │                    │ │
│  │   Description: [For growing teams with advanced needs___]  │  │  CORE              │ │
│  │                                                            │  │  ┌──────────────┐  │ │
│  │   Price: [$__299__]  Billing: [Monthly ▼]                  │  │  │  ◉ VOICE     │  │ │
│  │   ☐ Custom pricing  ☐ Usage-based add-on                   │  │  │  TTS & STT   │  │ │
│  │                                                            │  │  └──────────────┘  │ │
│  │   ─────────────────────────────────────────                │  │  ┌──────────────┐  │ │
│  │   ASSIGNED FEATURES (drop here)                            │  │  │  ◉ MEMORY    │  │ │
│  │                                                            │  │  │  SomaBrain   │  │ │
│  │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │  │  └──────────────┘  │ │
│  │   │   VOICE     │  │   MEMORY    │  │    MCP      │       │  │  ┌──────────────┐  │ │
│  │   │  ●●●●●      │  │  ●●●●○      │  │  ●●●○○      │       │  │  │  ◉ MCP       │  │ │
│  │   │  1000 min   │  │  100K items │  │  5 servers  │       │  │  │  Connections │  │ │
│  │   │  [Configure]│  │  [Configure]│  │  [Configure]│       │  │  └──────────────┘  │ │
│  │   └─────────────┘  └─────────────┘  └─────────────┘       │  │                    │ │
│  │                                                            │  │  AI CAPABILITIES   │ │
│  │   ┌─────────────┐  ┌─────────────┐                        │  │  ┌──────────────┐  │ │
│  │   │   VISION    │  │   MODELS    │   [+ Drop more]         │  │  │  ◉ VISION    │  │ │
│  │   │  ●●●○○      │  │  ●●●●●      │                        │  │  │  Image AI    │  │ │
│  │   │  100 img/d  │  │  All models │                        │  │  └──────────────┘  │ │
│  │   │  [Configure]│  │  [Configure]│                        │  │  ┌──────────────┐  │ │
│  │   └─────────────┘  └─────────────┘                        │  │  │  ◉ MODELS    │  │ │
│  │                                                            │  │  │  LLM Access  │  │ │
│  │   ─────────────────────────────────────────                │  │  └──────────────┘  │ │
│  │   BASE LIMITS                                              │  │                    │ │
│  │   Agents: [__20__]  Users: [__100__]  Storage: [__500 GB]  │  │  AUTOMATION        │ │
│  │                                                            │  │  ┌──────────────┐  │ │
│  │                                                            │  │  │  ◉ BROWSER   │  │ │
│  │                                                            │  │  │  Automation  │  │ │
│  │                                                            │  │  └──────────────┘  │ │
│  │                                                            │  │  ┌──────────────┐  │ │
│  │                                                            │  │  │  ◉ CODE EXEC │  │ │
│  │                                                            │  │  │  Sandbox     │  │ │
│  │                                                            │  │  └──────────────┘  │ │
│  │                                                            │  │  ┌──────────────┐  │ │
│  │                                                            │  │  │  ◉ TOOLS     │  │ │
│  │                                                            │  │  │  Extensions  │  │ │
│  │                                                            │  │  └──────────────┘  │ │
│  │                                                            │  │                    │ │
│  └────────────────────────────────────────────────────────────┘  └────────────────────┘ │
│                                                                                          │
│                                             [Cancel]  [Preview Tier]  [Publish Tier]     │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Feature Settings Modal - Full-Screen (Example: VOICE)

When user clicks **[Configure]** on a feature card → **FULL SCREEN** modal opens:

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│  ← Back to Tier Builder              VOICE CONFIGURATION                  Professional  │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│   ┌─────────────────────────────────────────┐   ┌─────────────────────────────────────┐ │
│   │  USAGE LIMITS                           │   │  LIVE PREVIEW                       │ │
│   │  ─────────────────────────────────      │   │  ─────────────────────────────────  │ │
│   │                                         │   │                                     │ │
│   │  Monthly Voice Minutes                  │   │   ┌───────────────────────────┐    │ │
│   │  ┌─────────────────────────────────┐   │   │   │  Voice Assistant Active   │    │ │
│   │  │  1000                           │   │   │   │  ─────────────────────    │    │ │
│   │  └─────────────────────────────────┘   │   │   │  "Hello, how can I help   │    │ │
│   │  ○ Unlimited  ● Limited  ○ Disabled     │   │   │   you today?"             │    │ │
│   │                                         │   │   │                           │    │ │
│   │  Concurrent Calls                       │   │   │   [Play Sample]           │    │ │
│   │  ┌─────────────────────────────────┐   │   │   │                           │    │ │
│   │  │  5                              │   │   │   └───────────────────────────┘    │ │
│   │  └─────────────────────────────────┘   │   │                                     │ │
│   │                                         │   │   Estimated Cost: ~$50/mo          │ │
│   │  Max Recording Length (minutes)         │   │   Based on avg usage               │ │
│   │  ┌─────────────────────────────────┐   │   │                                     │ │
│   │  │  30                             │   │   └─────────────────────────────────────┘ │
│   │  └─────────────────────────────────┘   │                                          │
│   │                                         │   ┌─────────────────────────────────────┐ │
│   └─────────────────────────────────────────┘   │  ENFORCEMENT POLICY                 │ │
│                                                  │  ─────────────────────────────────  │ │
│   ┌─────────────────────────────────────────┐   │                                     │ │
│   │  TTS PROVIDERS (Text-to-Speech)         │   │  Backend: AgentVoiceBox             │ │
│   │  ─────────────────────────────────      │   │  Metric: lago.voice_minutes         │ │
│   │                                         │   │  Policy: spicedb.voice_quota        │ │
│   │  ☑ Local TTS (Free, basic quality)      │   │                                     │ │
│   │  ☑ ElevenLabs (Premium voices)          │   │  [View Policy Definition]           │ │
│   │  ☑ OpenAI TTS (Natural voices)          │   │                                     │ │
│   │  ☐ Azure Cognitive (Enterprise)         │   │  When limit exceeded:               │ │
│   │  ☐ Google Cloud TTS (Wavenet)           │   │  ○ Block  ● Soft limit  ○ Alert     │ │
│   │                                         │   │                                     │ │
│   └─────────────────────────────────────────┘   └─────────────────────────────────────┘ │
│                                                                                          │
│   ┌─────────────────────────────────────────┐   ┌─────────────────────────────────────┐ │
│   │  STT PROVIDERS (Speech-to-Text)         │   │  VOICE CLONING                      │ │
│   │  ─────────────────────────────────      │   │  ─────────────────────────────────  │ │
│   │                                         │   │                                     │ │
│   │  ☑ OpenAI Whisper (Most accurate)       │   │  ● Disabled  ○ Enabled              │ │
│   │  ☑ Local Whisper (Offline capable)      │   │                                     │ │
│   │  ☐ Google Speech (Streaming)            │   │  Max Custom Voices: [___3___]       │ │
│   │  ☐ Azure Speech (Real-time)             │   │                                     │ │
│   │                                         │   │  Cloning Method:                    │ │
│   └─────────────────────────────────────────┘   │  [ElevenLabs Instant Clone ▼]       │ │
│                                                  │                                     │ │
│   ┌─────────────────────────────────────────┐   └─────────────────────────────────────┘ │
│   │  QUALITY SETTINGS                       │                                          │
│   │  ─────────────────────────────────      │                                          │ │
│   │                                         │                                          │ │
│   │  Output Quality:                        │                                          │ │
│   │  ○ Standard (fastest, 22kHz)            │                                          │ │
│   │  ● High (balanced, 44kHz)               │                                          │ │
│   │  ○ Ultra (slowest, 48kHz lossless)      │                                          │ │
│   │                                         │                                          │ │
│   └─────────────────────────────────────────┘                                          │
│                                                                                          │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                [Cancel]                    [Apply to Tier]               │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Feature Settings Modals (All Full-Screen)

| Feature | Modal Contents | Backend Integration |
|---------|----------------|---------------------|
| **VOICE** | Limits, TTS/STT Providers, Quality, Cloning | `AgentVoiceBox`, Lago `voice_minutes` |
| **MEMORY** | Entries limit, Retention, Embedding model, Capabilities | `SomaBrain`, PostgreSQL |
| **MCP** | Client/Server toggle, Max connections, Allowed servers list | MCP Registry, SpiceDB |
| **VISION** | Images/day, Providers (OpenAI, Anthropic, Google), Resolution | Lago `vision_requests` |
| **MODELS** | Model catalog with tier access toggle per model | `saas.models` table |
| **BROWSER** | Sessions, Timeout, Allowed domains, Sandbox level | Browser Automation Service |
| **CODE EXEC** | Languages, Memory limit, CPU time, Allowed packages | Code Sandbox Service |
| **TOOLS** | Tool catalog with enable/disable per tool | `saas.tools` table |
| **DELEGATION** | Max delegate agents, Inter-agent communication | Agent Orchestrator |

#### API Endpoints (Tier Builder)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v2/saas/tiers` | GET | List all subscription tiers |
| `/api/v2/saas/tiers` | POST | Create new tier |
| `/api/v2/saas/tiers/{id}` | GET | Get tier with all feature configs |
| `/api/v2/saas/tiers/{id}` | PUT | Update tier |
| `/api/v2/saas/tiers/{id}` | DELETE | Delete tier |
| `/api/v2/saas/tiers/{id}/features` | GET | Get features assigned to tier |
| `/api/v2/saas/tiers/{id}/features/{feature}` | PUT | Update feature config for tier |
| `/api/v2/saas/features/catalog` | GET | List all available features |
| `/api/v2/saas/features/{feature}/schema` | GET | Get schema for feature settings |
| `/api/v2/saas/features/{feature}/defaults` | GET | Get default settings |
| `/api/v2/saas/features/{feature}/providers` | GET | List available providers |

#### Database Schema (Tier Builder Extension)

```sql
-- Feature Catalog
CREATE TABLE saas_features (
    id VARCHAR(50) PRIMARY KEY,  -- 'voice', 'memory', 'mcp', etc.
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    icon VARCHAR(50),
    settings_schema JSONB,  -- JSON Schema for settings
    default_settings JSONB,
    is_active BOOLEAN DEFAULT TRUE
);

-- Tier-Feature Assignments
CREATE TABLE saas_tier_features (
    tier_id UUID REFERENCES subscription_tiers(id),
    feature_id VARCHAR(50) REFERENCES saas_features(id),
    is_enabled BOOLEAN DEFAULT TRUE,
    settings JSONB,  -- Override settings for this tier
    PRIMARY KEY (tier_id, feature_id)
);

-- Feature Providers
CREATE TABLE saas_feature_providers (
    id VARCHAR(50) PRIMARY KEY,
    feature_id VARCHAR(50) REFERENCES saas_features(id),
    name VARCHAR(100) NOT NULL,
    config_schema JSONB,
    is_active BOOLEAN DEFAULT TRUE
);
```

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

## 9. Complete CRUD UI Screens

### 9.1 Models Catalog (CRUD)

**Route:** `/platform/models`  
**Permission:** `platform->configure_platform`

#### Wireframe - Models List

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [Sidebar]  │ Model Catalog                               [+ Add Model]     │
│            │─────────────────────────────────────────────────────────────────│
│            │ 🔍 Search...     [Provider ▼] [Type ▼] [Status ▼]              │
│            │                                                                 │
│            │ CHAT MODELS                                                     │
│            │ ┌───────────────────────────────────────────────────────────┐ │
│            │ │ Model          Provider  Context  Vision  Status  Actions │ │
│            │ │ ─────────────────────────────────────────────────────────│ │
│            │ │ gpt-4o         OpenAI    128K     ✓       🟢      [···]  │ │
│            │ │ gpt-4o-mini    OpenAI    128K     ✓       🟢      [···]  │ │
│            │ │ claude-3-opus  Anthropic 200K     ✓       🟢      [···]  │ │
│            │ │ claude-3-sonn  Anthropic 200K     ✓       🟢      [···]  │ │
│            │ │ gemini-pro     Google    2M       ✓       🟢      [···]  │ │
│            │ └───────────────────────────────────────────────────────────┘ │
│            │                                                                 │
│            │ EMBEDDING MODELS                                                │
│            │ ┌───────────────────────────────────────────────────────────┐ │
│            │ │ Model              Provider  Dims   Status  Actions       │ │
│            │ │ ─────────────────────────────────────────────────────────│ │
│            │ │ text-embed-3-sm    OpenAI    1536   🟢      [···]         │ │
│            │ │ text-embed-3-lg    OpenAI    3072   🟢      [···]         │ │
│            │ └───────────────────────────────────────────────────────────┘ │
└────────────┴─────────────────────────────────────────────────────────────────┘
```

#### Model CRUD Operations

| Operation | Button | Modal Fields | API |
|-----------|--------|--------------|-----|
| **Create** | `+ Add Model` | Provider, Model ID, Type, Context Length, Has Vision, Rate Limits | `POST /api/v2/saas/models` |
| **Read** | Row click | Full model details panel | `GET /api/v2/saas/models/{id}` |
| **Update** | `[···] → Edit` | All editable fields | `PUT /api/v2/saas/models/{id}` |
| **Delete** | `[···] → Delete` | Confirmation modal | `DELETE /api/v2/saas/models/{id}` |
| **Toggle** | `[···] → Enable/Disable` | None | `PATCH /api/v2/saas/models/{id}/status` |

#### Add Model Modal

```
┌─────────────────────────────────────────────────────────┐
│  Add Model to Catalog                                ✕  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Provider *                                             │
│  ┌─────────────────────────────────────────────────┐   │
│  │ OpenAI                                      ▼   │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Model ID *                                             │
│  ┌─────────────────────────────────────────────────┐   │
│  │ gpt-4o-2024-11-20                               │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Display Name *                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ GPT-4o (Nov 2024)                               │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Type *                                                 │
│  ○ Chat Model  ○ Embedding Model  ○ Utility Model      │
│                                                         │
│  Context Window *          Max Output Tokens            │
│  ┌──────────────────┐      ┌──────────────────┐        │
│  │ 128000           │      │ 16384            │        │
│  └──────────────────┘      └──────────────────┘        │
│                                                         │
│  Capabilities                                           │
│  ☑ Vision (Image Input)                                │
│  ☑ Function Calling                                    │
│  ☐ JSON Mode                                           │
│                                                         │
│  Rate Limits                                            │
│  RPM (Requests/Min) *      TPM (Tokens/Min)            │
│  ┌──────────────────┐      ┌──────────────────┐        │
│  │ 500              │      │ 30000            │        │
│  └──────────────────┘      └──────────────────┘        │
│                                                         │
│  Tier Availability                                      │
│  ☑ Enterprise  ☑ Team  ☐ Starter  ☐ Free              │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  [Cancel]                              [Add Model]      │
└─────────────────────────────────────────────────────────┘
```

---

### 9.2 Roles & Permissions Catalog (CRUD)

**Route:** `/platform/roles`  
**Permission:** `platform->configure_platform`

#### Wireframe - Roles List

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [Sidebar]  │ Roles & Permissions                        [+ Create Role]    │
│            │─────────────────────────────────────────────────────────────────│
│            │ [Platform Roles] [Tenant Roles] [Agent Roles]                  │
│            │                                                                 │
│            │ PLATFORM ROLES (SAAS Admin only)                               │
│            │ ┌───────────────────────────────────────────────────────────┐ │
│            │ │ Role               Users   Permissions        Actions     │ │
│            │ │ ─────────────────────────────────────────────────────────│ │
│            │ │ 👑 saas_superadmin 2       ALL (45)            [View]     │ │
│            │ │ 🛡️ saas_support    5       12 permissions      [Edit]     │ │
│            │ │ 📊 saas_billing    3       8 permissions       [Edit]     │ │
│            │ └───────────────────────────────────────────────────────────┘ │
│            │                                                                 │
│            │ TENANT ROLES (Template for all tenants)                        │
│            │ ┌───────────────────────────────────────────────────────────┐ │
│            │ │ Role          Modes    Permissions          Actions       │ │
│            │ │ ─────────────────────────────────────────────────────────│ │
│            │ │ 👑 sysadmin   ALL      Full tenant control   [🔒 System] │ │
│            │ │ 🛡️ admin      ADM,STD  User/agent mgmt       [Edit]      │ │
│            │ │ 👨‍💻 developer  DEV,STD  Dev tools, debug      [Edit]      │ │
│            │ │ 🎓 trainer    TRN,STD  Cognitive params      [Edit]      │ │
│            │ │ 👤 member     STD      Chat, memory, tools   [Edit]      │ │
│            │ │ 👁️ viewer     RO       Read-only access      [Edit]      │ │
│            │ └───────────────────────────────────────────────────────────┘ │
└────────────┴─────────────────────────────────────────────────────────────────┘
```

#### Role Edit Modal - Permission Matrix

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Edit Role: Developer                                                    ✕  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Role Name *              Role Code (read-only)                             │
│  ┌──────────────────┐     ┌──────────────────┐                             │
│  │ Developer        │     │ developer   [🔒] │                             │
│  └──────────────────┘     └──────────────────┘                             │
│                                                                             │
│  Agent Modes Allowed                                                        │
│  ☑ STD (Standard)  ☑ DEV (Developer)  ☐ TRN  ☐ ADM  ☐ RO                  │
│                                                                             │
│  PERMISSION MATRIX                                            [Select All] │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ CHAT & MEMORY                                                       │   │
│  │ ────────────────────────────────────────────────────────────────── │   │
│  │ ☑ chat:send              Send chat messages                        │   │
│  │ ☑ chat:view_history      View conversation history                 │   │
│  │ ☑ memory:read            Read from SomaBrain                       │   │
│  │ ☑ memory:write           Write to SomaBrain                        │   │
│  │ ☐ memory:delete          Delete memories                           │   │
│  │ ☐ memory:export          Export memory data                        │   │
│  │                                                                     │   │
│  │ TOOLS                                                               │   │
│  │ ────────────────────────────────────────────────────────────────── │   │
│  │ ☑ tools:execute          Execute approved tools                    │   │
│  │ ☑ tools:code_exec        Execute code snippets                     │   │
│  │ ☑ tools:browser          Use browser agent                         │   │
│  │ ☑ tools:debug            Access debug tools                        │   │
│  │ ☐ tools:configure        Configure tool settings                   │   │
│  │                                                                     │   │
│  │ SETTINGS                                                            │   │
│  │ ────────────────────────────────────────────────────────────────── │   │
│  │ ☑ settings:view          View settings (read-only)                 │   │
│  │ ☐ settings:edit          Edit settings                             │   │
│  │ ☐ settings:api_keys      Manage API keys                           │   │
│  │                                                                     │   │
│  │ ADMIN (disabled for non-admin roles)                               │   │
│  │ ────────────────────────────────────────────────────────────────── │   │
│  │ ☐ admin:users            Manage tenant users        [🔒 ADM only] │   │
│  │ ☐ admin:agents           Manage agents              [🔒 ADM only] │   │
│  │ ☐ admin:billing          View/manage billing        [🔒 ADM only] │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  [Cancel]                                              [Save Changes]       │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Complete Permission List

| Category | Permission | Description | Default Roles |
|----------|------------|-------------|---------------|
| **Chat** | `chat:send` | Send messages | ALL except RO |
| | `chat:view_history` | View history | ALL |
| | `chat:export` | Export conversations | admin+ |
| **Memory** | `memory:read` | Read SomaBrain | ALL |
| | `memory:write` | Write to memory | ALL except RO |
| | `memory:delete` | Delete memories | sysadmin, admin |
| | `memory:export` | Export memory | sysadmin |
| **Tools** | `tools:execute` | Run tools | ALL except RO |
| | `tools:code_exec` | Execute code | member+ |
| | `tools:browser` | Browser agent | member+ |
| | `tools:debug` | Debug mode | developer+ |
| | `tools:configure` | Configure tools | admin+ |
| **Voice** | `voice:input` | Voice input | ALL except RO |
| | `voice:output` | Voice output | ALL |
| | `voice:configure` | Voice settings | admin+ |
| **Settings** | `settings:view` | View settings | ALL |
| | `settings:edit` | Edit settings | admin+ |
| | `settings:api_keys` | Manage API keys | sysadmin |
| | `settings:models` | Configure models | admin+ |
| **Admin** | `admin:users` | User management | admin+ |
| | `admin:agents` | Agent management | admin+ |
| | `admin:billing` | Billing access | sysadmin |
| | `admin:audit` | View audit log | admin+ |
| **Cognitive** | `cognitive:view` | View params | trainer+ |
| | `cognitive:edit` | Edit params | trainer, sysadmin |
| | `cognitive:reset` | Reset adaptation | sysadmin |

---

### 9.3 Feature Flags Management (CRUD)

**Route:** `/platform/flags`  
**Permission:** `platform->configure_platform`

#### Wireframe

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [Sidebar]  │ Feature Flags                              [+ Create Flag]    │
│            │─────────────────────────────────────────────────────────────────│
│            │ [Global] [Per-Tier] [Per-Tenant]                               │
│            │                                                                 │
│            │ GLOBAL FEATURE FLAGS                                           │
│            │ ┌───────────────────────────────────────────────────────────┐ │
│            │ │ Flag                    Description          Status       │ │
│            │ │ ─────────────────────────────────────────────────────────│ │
│            │ │ sse_enabled             SSE streaming         🟢 ON [···] │ │
│            │ │ embeddings_ingest       Embedding pipeline    🟢 ON [···] │ │
│            │ │ semantic_recall         SomaBrain recall      🟢 ON [···] │ │
│            │ │ audio_support           Voice subsystem       🟡 OFF[···] │ │
│            │ │ browser_support         Browser agent         🟢 ON [···] │ │
│            │ │ code_exec               Code execution        🟢 ON [···] │ │
│            │ │ vision_support          Image analysis        🟢 ON [···] │ │
│            │ │ mcp_client              MCP connections       🟢 ON [···] │ │
│            │ │ mcp_server              MCP server mode       🟡 OFF[···] │ │
│            │ │ voice_local             Local Whisper/Kokoro  🟢 ON [···] │ │
│            │ │ voice_agentvoicebox     AgentVoiceBox         🟡 OFF[···] │ │
│            │ │ delegation              Agent delegation      🟢 ON [···] │ │
│            │ └───────────────────────────────────────────────────────────┘ │
│            │                                                                 │
│            │ PER-TIER OVERRIDES                                             │
│            │ ┌───────────────────────────────────────────────────────────┐ │
│            │ │ Tier        Overrides                     Actions         │ │
│            │ │ ─────────────────────────────────────────────────────────│ │
│            │ │ Free        audio_support=OFF, browser=OFF [Configure]    │ │
│            │ │ Starter     mcp_server=OFF                 [Configure]    │ │
│            │ │ Team        (inherits global)              [Configure]    │ │
│            │ │ Enterprise  (all enabled)                  [Configure]    │ │
│            │ └───────────────────────────────────────────────────────────┘ │
└────────────┴─────────────────────────────────────────────────────────────────┘
```

---

### 9.4 API Keys Management (CRUD)

**Route:** `/platform/api-keys`  
**Permission:** `platform->configure_platform`

#### Wireframe

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [Sidebar]  │ Platform API Keys                          [+ Add Key]        │
│            │─────────────────────────────────────────────────────────────────│
│            │ ⚠️ These are platform-wide API keys. Tenant keys are separate.│
│            │                                                                 │
│            │ LLM PROVIDERS                                                   │
│            │ ┌───────────────────────────────────────────────────────────┐ │
│            │ │ Provider       Key                      Status   Actions  │ │
│            │ │ ─────────────────────────────────────────────────────────│ │
│            │ │ 🟢 OpenAI      sk-proj-****...8x9K      Valid    [···]    │ │
│            │ │ 🟢 Anthropic   sk-ant-****...JKL2       Valid    [···]    │ │
│            │ │ 🟢 Google      AIzaSy****...mnop        Valid    [···]    │ │
│            │ │ 🟡 Groq        gsk_****...qrst          Exp.5d   [···]    │ │
│            │ │ ⚪ Mistral     (not configured)         —        [Add]    │ │
│            │ └───────────────────────────────────────────────────────────┘ │
│            │                                                                 │
│            │ SERVICES                                                        │
│            │ ┌───────────────────────────────────────────────────────────┐ │
│            │ │ Service        Key                      Status   Actions  │ │
│            │ │ ─────────────────────────────────────────────────────────│ │
│            │ │ 🟢 Serper      ****...xyz               Valid    [···]    │ │
│            │ │ 🟢 Lago        lago_****...abc          Valid    [···]    │ │
│            │ │ ⚪ Stripe      (not configured)         —        [Add]    │ │
│            │ └───────────────────────────────────────────────────────────┘ │
│            │                                                                 │
└────────────┴─────────────────────────────────────────────────────────────────┘
```

---

## 10. Shared Component Catalog

### 10.1 Reusable Components (AgentSkin Pattern)

All components follow the `saas-*` naming convention and are built with Lit 3.x.

| Component | Path | Usage | Props |
|-----------|------|-------|-------|
| `saas-data-table` | `components/data-table.ts` | All list views | `columns`, `data`, `sortable`, `filterable` |
| `saas-modal` | `components/modal.ts` | All CRUD modals | `title`, `open`, `size` |
| `saas-form-field` | `components/form-field.ts` | All form inputs | `label`, `type`, `required`, `error` |
| `saas-select` | `components/select.ts` | All dropdowns | `options`, `value`, `searchable` |
| `saas-toggle` | `components/toggle.ts` | Feature flags, settings | `checked`, `disabled`, `label` |
| `saas-stat-card` | `components/stat-card.ts` | Dashboard metrics | `title`, `value`, `trend`, `icon` |
| `saas-quota-bar` | `components/quota-bar.ts` | Usage indicators | `used`, `max`, `label` |
| `saas-status-badge` | `components/status-badge.ts` | Status indicators | `status`, `size` |
| `saas-action-menu` | `components/action-menu.ts` | Row actions | `items` |
| `saas-confirm-dialog` | `components/confirm-dialog.ts` | Dangerous actions | `title`, `message`, `confirmText` |
| `saas-toast` | `components/toast.ts` | Notifications | `message`, `type`, `duration` |
| `saas-sidebar` | `components/sidebar.ts` | Navigation | `items`, `activeRoute` |
| `saas-header` | `components/header.ts` | Top bar | `user`, `tenant` |

### 10.2 Voice Settings Component (Shared)

**Component:** `saas-voice-settings`  
**Used by:** Agent Settings, Tenant Settings, Platform Settings

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Voice & Speech Settings                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Voice Provider *                                                           │
│  ○ Local Voice (Whisper + Kokoro)                                          │
│    On-device processing, full privacy, ~300ms latency                       │
│                                                                             │
│  ○ AgentVoiceBox (External Service)                                        │
│    Cloud processing, lower latency (~150ms), requires network               │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  [IF Local Selected]                                                        │
│                                                                             │
│  STT Engine               STT Model Size                                    │
│  ┌──────────────────┐     ┌──────────────────┐                             │
│  │ Whisper      ▼   │     │ base         ▼   │                             │
│  └──────────────────┘     └──────────────────┘                             │
│  Models: tiny (39M), base (74M), small (244M), medium (769M), large (1.5G) │
│                                                                             │
│  TTS Engine               TTS Voice                                         │
│  ┌──────────────────┐     ┌──────────────────┐                             │
│  │ Kokoro       ▼   │     │ am_onyx      ▼   │                             │
│  └──────────────────┘     └──────────────────┘                             │
│                                                                             │
│  TTS Speed                                                                  │
│  Slow ─────────●───────── Fast                                             │
│       0.5x     1.0x       2.0x                                              │
│                                                                             │
│  VAD Threshold (Voice Activity Detection)                                   │
│  Less Sensitive ──────●────── More Sensitive                                │
│                  0.5                                                        │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  [IF AgentVoiceBox Selected]                                                │
│                                                                             │
│  AgentVoiceBox Server URL *                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ https://voice.mycompany.com                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  API Token *                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ••••••••••••••••••••••••                                [Show] [Test]│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  Audio Devices                                                              │
│                                                                             │
│  Input Device (Microphone)                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Built-in Microphone (Default)                                   ▼   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Output Device (Speaker)                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Built-in Speakers (Default)                                     ▼   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  [Test Microphone]  [Test Speaker]                                          │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  [Reset to Defaults]                                   [Save Settings]      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 10.3 Catalog Manager Abstraction (Universal Dual-Panel Pattern)

A **universal reusable component** for all complex admin catalog management. This abstraction enables drag-and-drop composition with full-screen configuration modals.

#### Pattern Overview

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                         CATALOG MANAGER (Base Component)                              │
├──────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│   LEFT PANEL (Source)                           RIGHT PANEL (Target/Config)           │
│   ┌───────────────────────────┐                ┌────────────────────────────────┐    │
│   │  AVAILABLE ITEMS          │                │  ASSIGNED / CONFIGURED          │    │
│   │  ─────────────────────    │                │  ─────────────────────────      │    │
│   │                           │                │                                 │    │
│   │  [Search...]              │   DRAG →→→    │  [Drop zone / Configuration]    │    │
│   │                           │                │                                 │    │
│   │  ┌─────────────────────┐  │                │                                 │    │
│   │  │  Draggable Card 1   │──┼────────────→   │                                 │    │
│   │  └─────────────────────┘  │                │                                 │    │
│   │  ┌─────────────────────┐  │                │  Click item → Opens Full-Screen │    │
│   │  │  Draggable Card 2   │  │                │  Configuration Modal            │    │
│   │  └─────────────────────┘  │                │                                 │    │
│   │  ┌─────────────────────┐  │                │                                 │    │
│   │  │  Draggable Card 3   │  │                │                                 │    │
│   │  └─────────────────────┘  │                │                                 │    │
│   │                           │                │                                 │    │
│   │  Categories/Filters       │                │                                 │    │
│   │  ─────────────────────    │                │                                 │    │
│   │  ○ All  ● Core  ○ AI      │                └────────────────────────────────┘    │
│   │                           │                                                       │
│   └───────────────────────────┘                                                       │
│                                                                                       │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

#### Component Architecture

| Component | Type | Description |
|-----------|------|-------------|
| `<catalog-manager>` | Full-screen page | Master orchestrator |
| `<catalog-panel>` | Sidebar panel | Left: Searchable, filterable, draggable items |
| `<catalog-item>` | Draggable card | Draggable feature/item card |
| `<target-panel>` | Drop zone | Right: Drop target + assigned items |
| `<assigned-item>` | Clickable card | Opens full-screen modal on click |
| `<fullscreen-config-modal>` | Full-screen modal | 100% viewport configuration |

#### Use Cases (Same Abstraction, Different Data)

| Use Case | Left Panel (Catalog) | Right Panel (Target) | Full-Screen Modal |
|----------|---------------------|---------------------|-------------------|
| **Tier Builder** | Features (Voice, Memory, MCP...) | Tier composition canvas | Feature settings |
| **Agent Config** | Tools, Models, Features | Agent capabilities | Tool/Model settings |
| **Role Editor** | Permissions catalog | Role permission set | Permission rules |
| **MCP Manager** | Available MCP servers | Connected servers | Server config |
| **Model Catalog** | All LLM models | Enabled for tenant | Model settings & limits |
| **Tool Registry** | All available tools | Active tools | Tool configuration |
| **Webhook Manager** | Event types | Active webhooks | Webhook config |
| **Theme Builder** | UI components | Theme preview | Component styling |

#### Component Usage Examples

**Tier Builder:**
```html
<catalog-manager
  catalog-source="/api/v2/saas/features/catalog"
  target-source="/api/v2/saas/tiers/{tierId}/features"
  modal-component="feature-settings-modal"
  mode="compose"
></catalog-manager>
```

**Agent Tool Configuration:**
```html
<catalog-manager
  catalog-source="/api/v2/tools/registry"
  target-source="/api/v2/agents/{agentId}/tools"
  modal-component="tool-settings-modal"
  mode="assign"
></catalog-manager>
```

**Role Permission Editor:**
```html
<catalog-manager
  catalog-source="/api/v2/permissions/catalog"
  target-source="/api/v2/roles/{roleId}/permissions"
  modal-component="permission-rules-modal"
  mode="assign"
></catalog-manager>
```

#### Props

| Prop | Type | Description |
|------|------|-------------|
| `catalog-source` | string | API endpoint for catalog items |
| `target-source` | string | API endpoint for assigned items |
| `modal-component` | string | Custom element name for config modal |
| `mode` | 'compose' \| 'assign' | Composition vs assignment mode |
| `searchable` | boolean | Enable search in catalog |
| `filterable` | boolean | Enable category filters |
| `max-items` | number | Maximum assignable items |

---

## 11. Element-Level Permissions

### 11.1 UI Element Visibility by Role

| Element | saas_admin | sysadmin | admin | developer | trainer | member | viewer |
|---------|------------|----------|-------|-----------|---------|--------|--------|
| **Sidebar - Platform** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Sidebar - Admin** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Sidebar - Billing** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Dashboard - MRR** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Dashboard - Agents** | ✅ | ✅ | ✅ | ✅ | ✅ | 👁️ | 👁️ |
| **Users - Invite** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Users - Delete** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Agents - Create** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Agents - Delete** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Settings - API Keys** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Settings - Models** | ✅ | ✅ | ✅ | 👁️ | 👁️ | 👁️ | 👁️ |
| **Cognitive Panel** | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |
| **Voice Configure** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Chat Send** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Memory Delete** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |

Legend: ✅ Full Access | 👁️ View Only | ❌ Hidden

### 11.2 SpiceDB Check Pattern

```typescript
// Frontend: Check permission before rendering
async function canRender(element: string, resource: string): Promise<boolean> {
  const result = await permStore.check({
    subject: `user:${currentUser.id}`,
    resource: resource,
    permission: elementPermissionMap[element]
  });
  return result.allowed;
}

// Usage in Lit component
render() {
  return html`
    ${this.canDelete ? html`<button @click=${this.handleDelete}>Delete</button>` : nothing}
  `;
}
```

---

## 12. Dashboard Specifications by Role

### 12.1 SAAS Super Admin Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Platform Overview                                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│  │   124    │ │  4,502   │ │ $24.5K   │ │  99.9%   │ │    2     │         │
│  │ Tenants  │ │ Agents   │ │   MRR    │ │ Uptime   │ │ 🔴Alerts │         │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘         │
│                                                                             │
│  Revenue Trend        │  Tenant Distribution  │  System Health             │
│  ┌────────────────────┤  ┌────────────────────┤  ┌─────────────────────    │
│  │ 📈 Chart           │  │ 🥧 Pie by Tier     │  │ API: 🟢 45ms            │
│  └────────────────────┤  └────────────────────┤  │ DB:  🟢 12ms            │
│                       │                       │  │ Redis: 🟢 2ms           │
│                       │                       │  │ LLM: 🟢 350ms           │
│                       │                       │  └─────────────────────    │
│                                                                             │
│  Recent Activity        │  Top Tenants by Usage                             │
│  ┌──────────────────────┤  ┌──────────────────────────────────────────     │
│  │ Acme: tenant.create  │  │ 1. Acme Corp      4.2M tokens                  │
│  │ Globex: quota.warn   │  │ 2. TechStart      3.8M tokens                  │
│  │ ...                  │  │ 3. Globex Inc     2.1M tokens                  │
│  └──────────────────────┤  └──────────────────────────────────────────     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 12.2 Tenant SysAdmin Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Acme Corporation — Dashboard                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│  │   5/10   │ │  12/50   │ │  4.2M    │ │  45GB    │ │  $199    │         │
│  │ Agents   │ │ Users    │ │ Tokens   │ │ Storage  │ │ /month   │         │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘         │
│                                                                             │
│  Your Agents                                   User Activity               │
│  ┌────────────────────────────────────────┐   ┌────────────────────────   │
│  │ 🤖 Support-AI    🟢 Running  [Manage] │   │ Jane: 234 messages       │
│  │ 🤖 Sales-Bot     🟡 Stopped  [Start]  │   │ Bob: 156 messages        │
│  │ 🤖 Research-AI   🟢 Running  [Manage] │   │ Alice: 89 messages       │
│  └────────────────────────────────────────┘   └────────────────────────   │
│                                                                             │
│  Token Usage This Month    │  Quick Actions                                │
│  ┌─────────────────────────┤  ┌──────────────────────────────────────     │
│  │ 📊 4.2M / 10M (42%)     │  │ [+ Invite User] [+ Create Agent]          │
│  │ ████████░░░░░░░░░░░░   │  │ [📋 View Audit] [⚙️ Settings]              │
│  └─────────────────────────┤  └──────────────────────────────────────     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 12.3 Developer Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Developer Dashboard                                        [Mode: DEV]     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  My Agents                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────┐│
│  │ 🤖 Support-AI (developer access)                                      ││
│  │    Sessions: 45 today │ Errors: 2 │ Avg Latency: 320ms                ││
│  │    [Open Chat] [View Logs] [Debug Mode]                               ││
│  └────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│  Debug Console           │  Recent Errors                                  │
│  ┌───────────────────────┤  ┌──────────────────────────────────────────   │
│  │ > Tool execution logs │  │ ⚠️ 14:32 - Tool timeout (browser)          │
│  │ > API request/response│  │ ❌ 14:28 - LLM rate limit hit              │
│  │ > Memory operations   │  │ ⚠️ 14:15 - Memory write slow (>500ms)      │
│  └───────────────────────┤  └──────────────────────────────────────────   │
│                                                                             │
│  MCP Connections         │  Module SDK                                     │
│  ┌───────────────────────┤  ┌──────────────────────────────────────────   │
│  │ 🟢 filesystem         │  │ [📖 Documentation] [🧪 Playground]          │
│  │ 🟢 database           │  │ [📦 Component Library]                      │
│  │ 🟡 browser (unstable) │  │                                             │
│  └───────────────────────┤  └──────────────────────────────────────────   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 12.4 Trainer Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Trainer Dashboard                                          [Mode: TRN]     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Cognitive Status — Support-AI                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐│
│  │ ┌──────────────────────────────────────────────────────────────────┐ ││
│  │ │ NEUROMODULATOR LEVELS                                            │ ││
│  │ │                                                                  │ ││
│  │ │ Dopamine    ████████████░░░░░░░░░░░░░░░░░░  0.72  [Adjust]       │ ││
│  │ │ Serotonin   ██████████████░░░░░░░░░░░░░░░░  0.65  [Adjust]       │ ││
│  │ │ Norepineph  █████████░░░░░░░░░░░░░░░░░░░░░  0.48  [Adjust]       │ ││
│  │ │ Acetylchol  ██████████████████░░░░░░░░░░░░  0.81  [Adjust]       │ ││
│  │ └──────────────────────────────────────────────────────────────────┘ ││
│  └────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│  Adaptation Status       │  Training Actions                               │
│  ┌───────────────────────┤  ┌──────────────────────────────────────────   │
│  │ Learning Rate: 0.001  │  │ [🔄 Trigger Sleep Cycle]                    │
│  │ Adapt. Weights: 1.2   │  │ [🧹 Reset Adaptation]                       │
│  │ Last Consolidation:   │  │ [📊 Export Training Data]                   │
│  │   2 hours ago         │  │ [📈 View Learning Curves]                   │
│  └───────────────────────┤  └──────────────────────────────────────────   │
│                                                                             │
│  Training Sessions       │  Cognitive Metrics                              │
│  ┌───────────────────────┤  ┌──────────────────────────────────────────   │
│  │ Today: 45 interactions│  │ Confidence: 0.87 avg                        │
│  │ Corrections: 3        │  │ Response Quality: 4.2/5                     │
│  │ Positive: 89%         │  │ Hallucination Rate: 2.1%                    │
│  └───────────────────────┤  └──────────────────────────────────────────   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 12.5 Standard User Dashboard (Chat)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 💬 AI Chat                                             [+ New Chat]        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Recent Conversations                │  Chat Area                          │
│  ┌───────────────────────────────────┤  ┌──────────────────────────────    │
│  │ 📝 Server config help      Today  │  │                              │    │
│  │ 📝 Database optimization   Today  │  │  Welcome! How can I help?   │    │
│  │ 📝 Code review request     Yest.  │  │                              │    │
│  │ 📝 API documentation       Yest.  │  │                              │    │
│  │ ...                               │  │                              │    │
│  └───────────────────────────────────┤  │                              │    │
│                                      │  │                              │    │
│  Quick Actions                       │  │                              │    │
│  ┌───────────────────────────────────┤  │                              │    │
│  │ [🧠 Memory] [🔧 Tools]            │  │                              │    │
│  │ [⚙️ Settings] [🎨 Themes]         │  │                              │    │
│  └───────────────────────────────────┤  └──────────────────────────────    │
│                                      │                                     │
│                                      │  ┌────────────────────────────────┐│
│                                      │  │ + │ Write message...   🎤 │ ▲ │││
│                                      │  └────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

**Document Status:** CANONICAL — Complete with CRUD, Permissions, Dashboards  
**Revision:** 2.0 (2025-12-22)
