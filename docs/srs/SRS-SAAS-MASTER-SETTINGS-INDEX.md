# SRS: SAAS Platform Administration — Master Settings Index

**Document ID:** SA01-SRS-MASTER-SETTINGS-INDEX-2025-12
**Persona:** Platform Administrator (SAAS SysAdmin)
**Focus:** Complete Inventory of Administrable Settings
**Status:** CANONICAL REFERENCE

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PLATFORM LEVEL                                    │
│  (Global Catalogs, Default Policies, Infrastructure Connections)            │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────┐   ┌───────────────────────────┐              │
│  │         TENANT A          │   │         TENANT B          │   ...        │
│  │  (Tenant Settings,        │   │  (Inherited + Overridden) │              │
│  │   User Management)        │   │                           │              │
│  ├───────────────────────────┤   ├───────────────────────────┤              │
│  │  ┌─────────┐ ┌─────────┐  │   │  ┌─────────┐ ┌─────────┐  │              │
│  │  │ Agent 1 │ │ Agent 2 │  │   │  │ Agent 3 │ │ Agent 4 │  │              │
│  │  └─────────┘ └─────────┘  │   │  └─────────┘ └─────────┘  │              │
│  └───────────────────────────┘   └───────────────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Platform-Level Settings (SAAS SysAdmin)

| Category | Route | Settings | SRS Document |
|----------|-------|----------|--------------|
| **Model Catalog** | `/saas/settings/models` | LLM providers, model IDs, cost per token, tier availability | `SRS-SAAS-ECOSYSTEM-DEFAULTS.md` |
| **Tool Catalog** | `/saas/settings/tools` | Tool registry, risk levels, sandboxing rules | `SRS-SAAS-ECOSYSTEM-DEFAULTS.md` |
| **Voice Catalog** | `/saas/settings/voices` | TTS voices, cloning policies | `SRS-SAAS-AGENT-MARKETPLACE-AND-VOICE.md` |
| **Permission Catalog** | `/saas/permissions` | Granular permissions (45+), role templates | `SRS-PERMISSION-MATRIX.md` |
| **Compliance Frameworks** | `/saas/settings/compliance` | HIPAA, GDPR, SOC2 toggles | `SRS-SAAS-ECOSYSTEM-DEFAULTS.md` |
| **MCP Server Registry** | `/saas/infrastructure/mcp` | Registered MCP servers (mandatory/optional) | `SRS-SAAS-INFRASTRUCTURE-DEFAULTS.md` |
| **Integrations** | `/saas/settings/integrations` | Lago, Keycloak, SMTP, LLM provider keys | `SRS-SAAS-INTEGRATIONS.md` |
| **Subscription Tiers** | `/saas/subscriptions` | Tier definitions, feature gates, quotas | `SRS-EYE-OF-GOD-COMPLETE.md` |
| **Marketplace** | `/saas/marketplace` | Agent templates, monetization rules | `SRS-SAAS-AGENT-MARKETPLACE-AND-VOICE.md` |
| **Global Defaults** | `/saas/settings/defaults` | Compute, Memory, Safety defaults | `SRS-SAAS-ECOSYSTEM-DEFAULTS.md` |
| **Visual Topology** | `/saas/infrastructure/topology` | Node-based infrastructure visualization | `SRS-SAAS-VISUAL-INFRASTRUCTURE.md` |

---

## 3. Tenant-Level Settings (Tenant SysAdmin)

| Category | Route | Settings | Inherited From |
|----------|-------|----------|----------------|
| **General** | `/admin/settings/general` | Org name, contact email, timezone | N/A |
| **Branding** | `/admin/settings/branding` | Logo, theme colors, custom domain | Platform Defaults |
| **Security** | `/admin/settings/security` | MFA requirement, session timeout, IP allowlist | Platform Auth Config |
| **API Keys** | `/admin/settings/api-keys` | Tenant-scoped API keys | Platform Key Format |
| **Webhooks** | `/admin/settings/webhooks` | Outbound event URLs | N/A |
| **Model Whitelist** | `/admin/settings/models` | Allowed models (subset of Platform) | Platform Model Catalog |
| **Tool Whitelist** | `/admin/settings/tools` | Allowed tools (subset of Platform) | Platform Tool Catalog |
| **MCP Servers** | `/admin/settings/mcp` | Enabled MCP servers (subset of Platform) | Platform MCP Registry |
| **Quota Usage** | `/admin/billing` | Token, storage, agent, user counts | Tier Limits |

**Detailed in:** `SRS-TENANT-ADMIN.md`

---

## 4. Agent-Level Settings (Agent Owner/Tenant Admin)

| Category | Settings | Inherited From |
|----------|----------|----------------|
| **Identity** | Name, Slug, Description, Avatar | N/A |
| **Chat Model** | Primary model, fallback model, temperature, max tokens | Tenant Model Whitelist |
| **Memory** | Enabled/Disabled, retention days, embedding model | Tenant Memory Policy |
| **Voice** | Enabled/Disabled, voice ID, speed, persona config | Tenant Voice Settings |
| **Tools** | Enabled tools (from whitelist), custom MCP configs | Tenant Tool Whitelist |
| **System Prompt** | Agent personality, instructions | N/A |
| **Safety** | PII redaction, content filters | Platform Safety + Tenant Override |
| **Turn Detection** | VAD threshold, silence duration | Default values |
| **Features** | Browser agent, code execution, MCP mode | Tier Feature Gates |
| **Access** | Assigned users, per-user modes (STD/DEV/TRN) | Tenant User Roster |

**Detailed in:** `SRS-AGENT-USER.md`

---

## 5. User-Level Settings (Self-Service)

| Category | Settings | Scope |
|----------|----------|-------|
| **Profile** | Display name, avatar, email (read-only) | Per-User |
| **Authentication** | MFA setup, password change, linked accounts | Per-User |
| **Notifications** | Email preferences, in-app alerts | Per-User |
| **UI Preferences** | Theme (dark/light), language | Per-User |

---

## 6. Server & Service Inventory (Administrable Infrastructure)

| Service | Admin Route | Configuration |
|---------|-------------|---------------|
| **PostgreSQL** | `/saas/infrastructure/database` | Connection string (env), pool size |
| **Redis** | `/saas/infrastructure/cache` | Connection string, TTL defaults |
| **Keycloak** | `/saas/settings/integrations/auth` | URL, Admin Client ID, Client Secret |
| **Lago (Billing)** | `/saas/settings/integrations/billing` | API URL, API Key, Webhook Secret |
| **OpenAI** | `/saas/settings/integrations/llm` | API Key |
| **Anthropic** | `/saas/settings/integrations/llm` | API Key |
| **Google Vertex** | `/saas/settings/integrations/llm` | Project ID, Credentials JSON |
| **Whisper (STT)** | `/saas/settings/integrations/voice` | URL, Model Size |
| **Kokoro (TTS)** | `/saas/settings/integrations/voice` | URL |
| **Qdrant (Vectors)** | `/saas/infrastructure/vectors` | URL, API Key |
| **SMTP** | `/saas/settings/integrations/email` | Host, Port, User, Pass, From Address |
| **S3 / MinIO** | `/saas/infrastructure/storage` | Endpoint, Bucket, Credentials |
| **MCP Servers** | `/saas/infrastructure/mcp` | Per-server configs (Local/Remote) |

---

## 7. Gap Analysis (Remaining Work)

| Area | Status | Notes |
|------|--------|-------|
| Platform Dashboard | ✅ Exists | `SRS-EYE-OF-GOD-COMPLETE.md` |
| Tenant Management | ✅ Exists | `SRS-SAAS-TENANT-CREATION.md` |
| Model Catalog UI | ⚠️ Partial | SRS exists, UI not implemented |
| Tool Catalog UI | ⚠️ Partial | SRS exists, UI not implemented |
| MCP Registry UI | ⚠️ Partial | SRS exists, UI not implemented |
| Permission Browser UI | ⚠️ Partial | Frontend created, not tested |
| Visual Topology UI | ⚠️ Partial | SRS exists, UI not implemented |
| Agent Marketplace UI | ⚠️ Partial | SRS exists, UI not implemented |
| Voice Studio UI | ⚠️ Partial | SRS exists, UI not implemented |
| Integration Hub UI | ⚠️ Partial | SRS exists, UI not implemented |
