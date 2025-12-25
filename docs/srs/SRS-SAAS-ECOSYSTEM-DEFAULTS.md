# SRS: Eye of God — Ecosystem Defaults & Catalogs

**Document ID:** SA01-SRS-ECOSYSTEM-DEFAULTS-2025-12
**Persona:** 🔴 SAAS SysAdmin (God Mode)
**Focus:** The "Physics" of the Platform Universe (Catalogs & Inheritance)
**Status:** CANONICAL DESIGN

---

## 1. The "Catalog" Philosophy

The Eye of God does not just manage tenants; it manages the **Catalogs of Reality** from which tenants are constructed.

**The Golden Rule of Inheritance:**
Everything is defined at the **Platform (God)** level first.
→ **Tenants** select a subset of the Platform Catalog.
→ **Agents** select a subset of the Tenant Catalog.

---

## 2. The Five Great Catalogs

The SAAS Admin manages these five global registries. No entity can exist if it is not first defined here.

### 2.1 🧠 The Model Registry (`/saas/settings/models`)
Defines the AI brains available to the system.

| Model ID | Provider | Context Window | Use Case | Cost/1K Tokens |
|----------|----------|----------------|----------|----------------|
| `gpt-4o` | OpenAI | 128k | Reasoning | $0.005 |
| `claude-3-sonnet` | Anthropic | 200k | Coding | $0.003 |
| `somabrain-v1` | Internal | 32k | Memory Ops | $0.000 |
| `llama-3-70b` | Groq | 8k | Fast Chat | $0.001 |

**Permissions:** `platform:manage_models`
**Settings:**
*   `global_enabled`: bool (Kill switch)
*   `tier_availability`: List[Tier] (e.g., GPT-4 only for Enterprise)

### 2.2 🛠 The Tool Registry (`/saas/settings/tools`)
Defines the capabilities agents can possess.

| Tool ID | Category | Risk Level | Description |
|---------|----------|------------|-------------|
| `web_browser` | Research | Medium | Puppeteer browsing |
| `code_interpreter` | Compute | High (Sandboxed) | Python execution |
| `jira_integration` | Productivity | Low | Ticket management |
| `postgres_connector` | Database | Critical | Direct DB access |

**Permissions:** `platform:manage_tools`
**Settings:**
*   `requires_approval`: bool (Must admin approve run?)
*   `configuration_schema`: JSONSchema (Required inputs)

### 2.3 🗣 The Voice Registry (`/saas/settings/voices`)
Defines the personalities for TTS availability.

| Voice ID | Provider | Gender | Style |
|----------|----------|--------|-------|
| `alloy` | OpenAI | Neutral | Crisp |
| `shimmer` | OpenAI | Female | Expressive |
| `rachel` | ElevenLabs | Female | Professional |
| `batman` | Custom | Male | Deep/Gravelly |

### 2.4 🛡 The Permission Catalog (`/saas/permissions/catalog`)
(Derived from `admin/permissions/granular.py`)
This is non-editable (code-defined) but **viewable** and **attachable**.

*   `tenant:create`
*   `tenant:suspend`
*   `agent:configure_personality`
*   ... (45+ items)

### 2.5 📦 The Compliance Registry (`/saas/settings/compliance`)
Defines regulatory frameworks tenants can enable.

*   **HIPAA:** Enforces 365-day retention, encryption-at-rest, PII redaction.
*   **GDPR:** Enforces "Right to be Forgotten", EU data residency.
*   **SOC2:** Enforces Audit Logging `verbose` mode.

---

## 3. The Recursive Settings Schema

We define a *Single Source of Truth* schema for settings that flows down.

### 3.1 The Schema (Pseudocode)

```typescript
interface EcosystemSettings {
  // 1. COMPUTE
  compute: {
    default_model: string;            // Default for new agents
    allowed_models: string[];         // Whitelist
    max_tokens_per_req: number;       // Hard limit
    context_window_limit: number;     // Hard limit
  };

  // 2. BEHAVIOR
  behavior: {
    safety_filter_level: 'low'|'med'|'high';
    allow_nefarious_prompts: boolean; // For "Red Teaming" tenants
    system_prompt_prefix: string;     // Forced prefix
  };

  // 3. RETENTION (Memory)
  memory: {
    max_vectors_per_agent: number;
    retention_days: number;
    pruning_strategy: 'fifo'|'relevance';
  };
}
```

### 3.2 Inheritance Logic

1.  **Platform Defaults:** The "Base Reality".
    *   `compute.allowed_models` = [`all`]
    *   `memory.retention_days` = 365

2.  **Tier Overrides:** (Applied on top of Platform)
    *   *Free Tier:* `memory.retention_days` = 7, `allowed_models` = [`gpt-3.5`]
    *   *Enterprise:* `memory.retention_days` = 3650

3.  **Tenant Configuration:** (Restricted by Tier)
    *   Tenant chooses: `default_model` = `claude-3-sonnet`

4.  **Agent Configuration:** (Restricted by Tenant)
    *   Agent specific: `system_prompt` += "You are a pirate."

---

## 4. UI: The Defaults Administration Flow

**Route:** `/saas/settings/defaults`

### 4.1 Screen: Global Defaults Editor

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🔴 GLOBAL DEFAULTS (The DNA of SomaAgent)                      [Save DNA]   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [Navigation: Compute | Memory | Safety | Billing | Auth]                   │
│                                                                             │
│  🧠 COMPUTE DEFAULTS                                                        │
│  The baseline for every agent unless overridden.                            │
│                                                                             │
│  Default Model ID           [ gpt-4o                 ▼ ]                    │
│  Fallback Model ID          [ llama-3-70b            ▼ ]                    │
│                                                                             │
│  Global Context Limit       [ 128,000 ] tokens                              │
│  Global Max Output          [ 4,096   ] tokens                              │
│                                                                             │
│  🛡 SAFETY & ALIGNMENT                                                      │
│  Global Ban List (Regex)    [ (password|keys|secret) ]                      │
│  PII Auto-Redaction         [ Enabled  ▼ ]                                  │
│                                                                             │
│  💾 MEMORY & VECTORS                                                        │
│  Default Embedding Model    [ text-embedding-3-small ▼ ]                    │
│  Vector DB Shard Size       [ 1024 ] MB                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. User Journey: "The New Model Rollout"

**Objective:** Add "GPT-5" to the platform and restrict it to Enterprise.

1.  **Integration:** DevOps adds adapter code for GPT-5.
2.  **Registration:** God Mode Admin goes to `/saas/settings/models`.
    *   Click "Add Model" -> Select "OpenAI/GPT-5".
    *   Set **Base Cost**: $0.05/1k.
3.  **Availability:**
    *   Toggle `Global Enabled` = **True**.
    *   Section `Tier Availability`: Check `Enterprise` ONLY.
4.  **Propagation:**
    *   Enterprise Tenant Admins now see "GPT-5" in their whitelist dropdown.
    *   Free Tenant Admins do NOT see it.

---

## 6. Permission Governance (SpiceDB/ORM Mapping)

### 6.1 The "Role Templates" (`/saas/roles`)

Admins define the standard roles that tenants start with.

*   **Standard Roles:**
    1.  `TenantAdmin` (All access within tenant)
    2.  `AgentOperator` (Can run agents, cannot delete)
    3.  `Viewer` (Read-only)

*   **Custom Role Policy:**
    *   Setting: `allow_custom_roles` (bool).
    *   If `True`: Tenant Admins can mix/match granular permissions.
    *   If `False`: They must use the Standard Roles.

### 6.2 The "God View" of Permissions (`/saas/permissions`)
The missing screen! This is a **Matrix Explorer**.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🔴 PERMISSION MATRIX EXPLORER                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  Subject: [ User: admin@acme.com ▼ ]    Resource: [ Agent: SalesBot ▼ ]    │
│                                                                             │
│  Result: ✅ ALLOWED                                                         │
│                                                                             │
│  Trace:                                                                     │
│  1. User `admin@acme.com` has role `TenantAdmin` on `Tenant: Acme`.         │
│  2. `TenantAdmin` includes permission `agent:*`.                            │
│  3. `agent:*` includes `agent:view_logs`.                                   │
│                                                                             │
│  [ Check Another ]                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```
