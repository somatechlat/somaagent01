# SRS: Deep Dive — SAAS Tenant Creation & Administration Journey

**Document ID:** SA01-SRS-TENANT-CREATION-2025-12
**Persona:** 🔴 SAAS SysAdmin (God Mode)
**Focus:** The "Moment of Creation" & "Architecting Defaults"
**Status:** CANONICAL DESIGN

---

## 1. Executive Summary & Philosophy

Creation is not just a form; it is the **instantiation of a universe** for a customer. When the SAAS Admin creates a tenant, they are defining the physical and logical boundaries of that tenant's existence.

**The "Perfect Flow" Philosophy:**
1.  **Templates over Inputs:** Admins should rarely start from scratch. Use "Blueprints" (e.g., "Enterprise HIPAA Blueprint").
2.  **Cascading Defaults:** Decisions made at the Platform level cascade to Tenant, then to Agent.
3.  **Validation at the Source:** Checks for slug uniqueness, domain availability, and resource quotas happen in real-time.

---

## 2. The User Journey: "Genesis"

### 2.1 High-Level Flow Chart

```mermaid
graph TD
    Start([🔴 Admin Initiates Creation]) --> Method{Creation Method}
    
    Method -->|Wizard| Wizard[🚀 Comparison Wizard]
    Method -->|Clone| Clone[🐑 Clone Existing Tenant]
    Method -->|Blueprint| Blueprint[📄 Use Blueprint]
    
    subgraph "Phase 1: Identity & Infrastructure"
        Wizard --> Step1[Basic Info & Slug]
        Step1 --> Step2[Region & Data Residency]
        Step2 --> Step3[Domain & Whitelisting]
    end
    
    subgraph "Phase 2: Commercial & Limits"
        Step3 --> Step4[Subscription Tier Selection]
        Step4 --> Step5[Quota Overrides]
        Step5 --> Step6[Billing Entity (Lago)]
    end
    
    subgraph "Phase 3: The 'Soul' (Defaults)"
        Step6 --> Step7[Default Agent Persona]
        Step7 --> Step8[Model Whitelist]
        Step8 --> Step9[Feature Flag Toggles]
    end
    
    Blueprint --> Review[🔍 Final Reviews]
    Clone --> Review
    Step9 --> Review
    
    Review --> Commit[⚡ PROVISION SYSTEM]
    
    Commit --> DB[Create DB Schema/Row]
    Commit --> Keycloak[Realm/Client Setup]
    Commit --> SpiceDB[Write Root Permissions]
    Commit --> Lago[Create Customer/Sub]
    Commit --> Email[Send 'sysadmin' Invite]
    
    Commit --> Success([✨ Tenant Live])
```

---

## 3. UI Screen Specifications

### 3.1 Screen 1: The "Genesis" Modal (Multi-step Wizard)

**Route:** `/saas/tenants/new` (Full Screen Overlay)

#### Step 1: Identity & Compliance

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CREATE NEW TENANT (Step 1 of 4)                                     [Esc]  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. IDENTITY             2. PLAN               3. DEFAULTS       4. REVIEW  │
│  ●●●●○                   ○                     ○                 ○          │
│                                                                             │
│  Organization Name *                                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ Acme Health Solutions                                                 │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Tenant Slug (URL Namespace) *                                              │
│  ┌──────────────────────────────┐ ┌──────────────────────────────────────┐  │
│  │ https://app.soma.ai/tenant/  │ │ acme-health                          │  │
│  └──────────────────────────────┘ └──────────────────────────────────────┘  │
│                                     ✅ Available                             │
│                                                                             │
│  Data Residency (Region) *                                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ 🇺🇸 US-East (N. Virginia) - Standard                                 ▼ │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│  ℹ️ Determines where Postgres and Vector DB shards are physically located.   │
│                                                                             │
│  Compliance Frameworks (affects retention & auditing)                       │
│  ☐ GDPR (EU)   ☑ HIPAA (US Healthcare)   ☐ SOC2 (Audit Heavy)               │
│                                                                             │
│  Private Domain White-labeling (Enterprise)                                 │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ console.acme-health.com                                               │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│  ⚠️ Requires DNS CNAME verification later.                                   │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  [Cancel]                                                   [Next: Plan →]  │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Step 3: Inherited Defaults (The "Soul")

This step is critical. It defines what the Tenant SysAdmin sees when *they* first log in.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CREATE NEW TENANT (Step 3 of 4)                                     [Esc]  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. IDENTITY             2. PLAN               3. DEFAULTS       4. REVIEW  │
│  ✓                       ✓                     ●●●●○             ○          │
│                                                                             │
│  🤖 Model Whitelist (Restrict what models this tenant can access)           │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ ☑ GPT-4o   ☑ Claude 3.5 Sonnet   ☐ Llama 3 (Local)                    │  │
│  │ ☑ SomaBrain v1 (Internal)                                             │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  🔐 Authentication Strictness                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ Enforce MFA for all users?            [ Yes / No ]                        │
│  │ Allow Social Login (Google/Github)?   [ Yes / No ]                        │
│  │ Session Timeout                       [ 4 hours ▼ ]                       │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  🎨 Default Branding (Can be overridden by Tenant Admin)                    │
│  Theme: [ Dark Modern ▼ ]    Accent Color: [ #00E5FF ]                      │
│                                                                             │
│  👥 Initial Admin User                                                      │
│  Email: [ admin@acme.com _________ ]  (Will receive magic link)             │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  [← Back]                                                 [Next: Review →]  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Deep Settings Architecture

We must expose every variable that controls a tenant's reality.

### 4.1 The Settings Schema (`tenant_settings` JSONB)

This schema lives in the `tenants` table but feeds into the UI for "Tenant Settings".

```json
{
  "branding": {
    "logo_url": "https://...",
    "favicon_url": "https://...",
    "primary_color": "#000000",
    "white_label_css": "/* custom override */", 
    "portal_title": "Acme AI Portal"
  },
  "compliance": {
    "hipaa_mode": true,
    "audit_level": "verbose", // 'minimal', 'standard', 'verbose'
    "data_retention_days": 365,
    "pii_redaction_enabled": true
  },
  "compute": {
    "default_model": "gpt-4o",
    "allowed_models": ["gpt-4o", "claude-3-opus"],
    "max_concurrent_agents": 50,
    "gpu_priority": "standard" // 'standard', 'high', 'dedicated'
  },
  "auth": {
    "sso_provider": "google-workspace",
    "sso_domain_lock": "acme.com",
    "mfa_enforced": true,
    "password_policy": "nist-800-63b"
  },
  "features": {
    "enable_voice": true,
    "enable_vision": true,
    "enable_code_interpreter": false, // Sandbox risk
    "enable_web_browsing": true
  }
}
```

---

## 5. User Journeys & Edge Cases

### 5.1 Journey: "The Enterprise Conflict"
**Scenario:** Admin tries to create "Nike" but slug is taken.
1.  **Input:** Slug `nike`.
2.  **System:** Real-time check `GET /api/v2/saas/slug-check?q=nike`.
3.  **Response:** `409 Conflict`.
4.  **UI Feedback:** Red outline. Suggestion: `nike-inc`, `nike-global`.
5.  **Resolution:** Admin selects `nike-global`.

### 5.2 Journey: "The Provisioning Failure" (Rollback)
**Scenario:** Database created, but Lago billing fails.
1.  **Step:** `Step 4: Review` -> Click "Create".
2.  **Actions:**
    *   ✅ DB Schema created (transaction)
    *   ✅ SpiceDB Permissions written
    *   ❌ Lago API returns `503 Service Unavailable`.
3.  **System Behavior:**
    *   Catch Exception.
    *   **Rollback:** Delete SpiceDB tuples. Rollback DB transaction.
    *   **UI Feedback:** "Tenant creation failed at Billing step. System rolled back. Please try again."

---

## 6. Defaults Administration (`/saas/settings/defaults`)

A designated area where the God Mode admin defines "What is a default?".

### 6.1 "Global Blueprint" Screen

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🔴 Global Tenant Defaults                                       [Save All]  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  These settings apply to NEW tenants if no specific blueprint is selected.  │
│                                                                             │
│  Standard Subscription Tier   [ Free ]                                      │
│  Standard Region              [ US-East ]                                   │
│                                                                             │
│  Standard "Welcome" Email Template                                          │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ Subject: Welcome to SomaAgent, {{tenant_name}}!                       │  │
│  │ Body:                                                                 │  │
│  │ Hello {{admin_name}},                                                 │  │
│  │ Your AI infrastructure is ready: {{login_url}}                        │  │
│  │ ...                                                                   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Permission Implications

### 7.1 Creating the "Super Tenant" (God Mode within Tenant)
When a SAAS Admin creates a tenant, they inject a `sysadmin` user.
*   **SpiceDB Logic:**
    ```zed
    // The specific user invited gets the highest permission relation
    relation sysadmin: user
    permission manage = sysadmin
    ```
*   **Impersonation:** The SAAS Admin retains `platform->impersonate` permission, which allows them to effectively "become" this `sysadmin` at any time to debug configuration issues without asking for credentials.
