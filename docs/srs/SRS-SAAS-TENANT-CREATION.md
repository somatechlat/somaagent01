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

### 4.1 The Settings Architecture

Tenant settings are managed through two separate models following Django ORM best practices:

#### 4.1.1 `Tenant` Model (Identity & Billing)
**File:** `admin/saas/models/tenants.py:11-113`

The primary tenant model with fields for identity, subscriptions, and billing.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUIDField | Primary Key, Default: uuid.uuid4 | Tenant unique identifier |
| `name` | CharField | max_length=100 | Organization display name |
| `slug` | SlugField | max_length=100, Unique | URL-safe tenant identifier |
| `tier` | ForeignKey | To: SubscriptionTier, on_delete=PROTECT | Current subscription tier |
| `status` | CharField | Default: PENDING, choices: Active/Pending/Suspended/Terminated | Tenant lifecycle status |
| `keycloak_realm` | CharField | max_length=100, Blank | Keycloak realm for this tenant |
| `lago_customer_id` | CharField | max_length=100, Indexed, Blank | Lago billing customer ID |
| `lago_subscription_id` | CharField | max_length=100, Blank | Lago subscription external ID |
| `billing_email` | EmailField | Blank | Primary billing contact |
| `feature_overrides` | JSONField | Default: dict, Blank | Per-tenant feature configuration overrides |
| `metadata` | JSONField | Default: dict, Blank | Arbitrary metadata for integrations |
| `trial_ends_at` | DateTimeField | Null, Blank | When trial period ends |
| `created_at` | DateTimeField | Auto_now_add=True | Tenant creation timestamp |
| `updated_at` | DateTimeField | Auto_now=True | Last update timestamp |

**Indexes:** `slug`, `status`, `lago_customer_id`, `-created_at`

#### 4.1.2 `TenantSettings` Model (Configuration & Branding)
**File:** `admin/saas/models/profiles.py:140-239`

One-to-one extension with branding, security, and feature settings.

| Category | Field | Type | Default | Description |
|----------|-------|------|---------|-------------|
| **Primary Key** | `tenant` | OneToOneField | - | Link to Tenant model (CASCADE) |
| **Branding** | `logo_url` | URLField | "" | Custom logo URL |
| | `primary_color` | CharField | "#2563eb" | Primary brand color (hex) |
| | `accent_color` | CharField | "#3b82f6" | Accent brand color (hex) |
| | `custom_domain` | CharField | "" | White-label domain |
| **Security** | `mfa_policy` | CharField | "optional" | Choices: off/optional/required |
| | `sso_enabled` | BooleanField | false | SSO provider enabled |
| | `sso_config` | JSONField | dict | SSO provider configuration |
| | `session_timeout` | IntegerField | 30 | Session timeout in minutes |
| **Features** | `feature_overrides` | JSONField | dict | Feature overrides within tier limits |
| **SRS Compliance** | `compliance` | JSONField | dict | HIPAA/GDPR/SOC2 settings |
| | `compute` | JSONField | dict | Model and compute settings |
| | `auth` | JSONField | dict | Authentication and authorization |
| **Metadata** | `timezone` | CharField | "UTC" | Tenant timezone |
| | `language` | CharField | "en" | Default language code |
| **Timestamps** | `created_at` | DateTimeField | auto_now_add | Settings creation time |
| | `updated_at` | DateTimeField | auto_now | Last update time |

**Table:** `saas_tenant_settings`

#### 4.1.3 Example JSONB Schema for Flexible Fields

The JSONB fields (`feature_overrides`, `compliance`, `compute`, `auth`, `sso_config`) use this structure:

```json
{
  "feature_overrides": {
    "enable_voice": true,
    "enable_vision": true,
    "enable_code_interpreter": false,
    "enable_web_browsing": true,
    "max_concurrent_agents": 50,
    "gpu_priority": "standard"
  },
  "compliance": {
    "hipaa_mode": true,
    "audit_level": "verbose",
    "data_retention_days": 365,
    "pii_redaction_enabled": true
  },
  "compute": {
    "default_model": "gpt-4o",
    "allowed_models": ["gpt-4o", "claude-3-5-sonnet"],
    "temperature": 0.7,
    "max_tokens": 4096
  },
  "auth": {
    "sso_provider": "google-workspace",
    "sso_domain_lock": "acme.com",
    "mfa_enforced": true,
    "password_policy": "nist-800-63b"
  },
  "sso_config": {
    "provider": "saml",
    "entity_id": "https://sso.acme.com",
    "sso_url": "https://sso.acme.com/saml/sso",
    "slo_url": "https://sso.acme.com/saml/slo",
    "certificate": "-----BEGIN CERTIFICATE-----..."
  }
}
```

#### 4.1.4 Settings Resolution Priority

When retrieving settings for a tenant (via `admin/core/helpers/settings_defaults.py:37-89`):

```
1. TenantSettings.feature_overrides (highest priority)
2. Tenant.feature_overrides (fallback)
3. GlobalDefault._initial_defaults() (platform blueprint)
4. SettingsModel defaults (code-level defaults)
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
