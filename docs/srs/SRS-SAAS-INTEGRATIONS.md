# SRS: Eye of God — Platform Integrations & Connections

**Document ID:** SA01-SRS-PLATFORM-INTEGRATIONS-2025-12
**Persona:** 🔴 SAAS SysAdmin (God Mode)
**Focus:** Managing External Nerves (Billing, Auth, Email, LLM)
**Status:** CANONICAL DESIGN

---

## 1. The "Integration Hub" Philosophy

The Eye of God must control its external dependencies. Hardcoded environment variables are for initialization, but **Runtime Configuration** allows the SAAS Admin to rotate keys, switch providers, and debug connections without redeployment.

**Location:** `/saas/settings/integrations`

---

## 2. Core Integration Modules

### 2.1 💰 Billing & Plans (Lago)
**Route:** `/saas/settings/integrations/lago`

#### Connection Settings
| Setting | Type | Description |
|---------|------|-------------|
| `lago_api_url` | URL | e.g., `https://api.getlago.com/v1` |
| `lago_api_key` | Secret | The master API key |
| `webhook_secret` | Secret | For verifying incoming events |
| `sync_frequency` | Enum | `Real-time`, `Daily` |

#### Plan Synchronization Flow (The User's Request)
**Route:** `/saas/subscriptions` (The Tier Builder)

When a SAAS Admin creates/updates a Tier in Eye of God, they must decide the "Source of Truth".

**Scenario A: Eye of God → Lago (Push)**
1.  Admin creates "Enterprise Tier" in `/saas/subscriptions/new`.
2.  Defines Price: $499/mo.
3.  Click **[Save & Sync to Lago]**.
4.  System:
    *   Creates Plan in DB.
    *   POSTs definition to Lago API.
    *   Stores `lago_plan_id` mapping.

**Scenario B: Lago → Eye of God (Pull)**
1.  Admin clicks **[Import from Lago]**.
2.  System fetches all Plans from Lago.
3.  Admin maps Lago Plan "Ent-2025" to Soma Validated Tier "Enterprise".

### 2.2 🔐 Authentication (Keycloak/SSO)
**Route:** `/saas/settings/integrations/auth`

The SAAS Admin manages the **Keycloak Master Realm** connection here.

#### Connection Settings
| Setting | Type | Description |
|---------|------|-------------|
| `keycloak_url` | URL | e.g., `https://auth.soma.ai` |
| `admin_client_id` | String | `admin-cli` or `soma-admin` |
| `admin_client_secret` | Secret | Super admin credentials |

#### Identity Provider (IdP) Management
**Route:** `/saas/settings/auth`
Allows adding "Social Logins" that apply Platform-wide.
*   **Google OAuth:** Client ID / Secret.
*   **GitHub OAuth:** Client ID / Secret.
*   **Enterprise SAML (Okta/Azure):** XML Metadata URL (Only enabled for Enterprise Tenants via dynamic configuration).

### 2.3 📧 Communication (SMTP/Resend/Twilio)
**Route:** `/saas/settings/integrations/email`

#### SMTP Configuration
| Setting | Type | Description |
|---------|------|-------------|
| `smtp_host` | Hostname | e.g., `smtp.resend.com` |
| `smtp_port` | Port | `587` |
| `smtp_user` | String | `apikey` |
| `smtp_pass` | Secret | ... |
| `default_from` | Email | `no-reply@soma.ai` |

**Test Action:** `[Send Test Email]` button to verify connection immediately.

---

## 3. UI Specifications

### 3.1 Screen: Integration Dashboard (`/saas/settings/integrations`)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🔴 PLATFORM INTEGRATIONS                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌────────────────────┐ │
│  │ 💰 Lago (Billing)    │  │ 🔐 Keycloak (Auth)   │  │ 📧 SMTP (Email)    │ │
│  │ Status: ✅ Connected │  │ Status: ✅ Connected │  │ Status: ⚠️ Error   │ │
│  │ Last 24h: 45 events  │  │ User Sync: Active    │  │ Timeout (5s)       │ │
│  │ [Configure]          │  │ [Configure]          │  │ [Configure]        │ │
│  └──────────────────────┘  └──────────────────────┘  └────────────────────┘ │
│                                                                             │
│  ┌──────────────────────┐  ┌──────────────────────┐                         │
│  │ 🤖 OpenAI (LLM)      │  │ ☁️ AWS S3 (Storage)  │                         │
│  │ Status: ✅ Connected │  │ Status: ✅ Connected │                         │
│  │ [Configure]          │  │ [Configure]          │                         │
│  └──────────────────────┘  └──────────────────────┘                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Screen: Plan Syncer (`/saas/subscriptions`)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🔴 SUBSCRIPTION TIERS                                  [+ New Tier] [Sync]  │
├─────────────────────────────────────────────────────────────────────────────┤
│  Sync Status: ✅ Synchronized with Lago (10 mins ago)                       │
│                                                                             │
│  TIER NAME      LAGO CODE      PRICE       SYNC     ACTIONS                 │
│  Free           free_v1        $0.00       ✅       [Edit]                  │
│  Starter        starter_24     $29.00      ✅       [Edit]                  │
│  Pro            pro_24_q4      $99.00      ⚠️ Diff  [Resolve]               │
│                                                                             │
│  -------------------------------------------------------------------------  │
│  ⚠️ 'Pro' Tier has local changes not pushed to Lago.                        │
│     [Push to Lago]  [Revert to Lago Version]                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. User Journey: "The Broken Billing Connection"

**Scenario:** The Lago API Key was rotated, breaking the connection.
1.  **Alert:** Admin sees "Billing System Unreachable" on Dashboard.
2.  **Action:** Navigates to `/saas/settings/integrations`.
3.  **Observation:** Lago card shows `Status: ❌ 401 Unauthorized`.
4.  **Fix:** Clicks [Configure]. Enters new `lago_api_key`.
5.  **Test:** Clicks [Test Connection].
6.  **Result:** `✅ Connected. Org: SomaTech`. Saved. System resumes billing events.

---

## 5. Security & Permission Implications

*   **View Integrations:** `platform:view_settings`
*   **Edit Secrets:** `platform:manage_settings` (Requires Re-Auth/Sudo mode)
*   **Sync Plans:** `platform:manage_billing`

**Secret Storage:**
*   Secrets are **NEVER** returned in the API `GET` response (masked as `*******`).
*   Secrets are encrypted at rest in the `integration_secrets` table.
