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

| Category | Route | Implementation | Settings | Code Reference |
|----------|-------|----------------|-----------|----------------|
| **Dashboard** | `/api/v2/saas/dashboard` | `admin/saas/api/dashboard.py:21` | Platform metrics, MRR, tenant counts | Real PostgreSQL queries |
| **Tenants** | `/api/v2/saas/tenants` | `admin/saas/api/tenants.py` | Full tenant CRUD, filters | `Tenant` model |
| **Users** | `/api/v2/saas/users` | `admin/saas/api/users.py` | User mgmt, invites, impersonation | `User`, `TenantUser` models |
| **Tiers** | `/api/v2/saas/tiers` | `admin/saas/api/tiers.py` | Subscription tiers, quotas | `SubscriptionTier` model |
| **Features** | `/api/v2/saas/features` | `admin/saas/api/features.py` | Feature catalog, providers | `SaasFeature`, `FeatureProvider` |
| **Settings** | `/api/v2/saas/settings` | `admin/saas/api/settings.py` | Platform-wide settings | Django Admin |
| **API Keys** | `/api/v2/saas/settings/api-keys` | `admin/saas/api/settings.py:26` | API key CRUD | `ApiKey` model |
| **Models** | `/api/v2/saas/settings/models` | `admin/saas/api/settings.py` | Model configuration | Platform model catalog |
| **Roles** | `/api/v2/saas/settings/roles` | `admin/saas/api/settings.py` | Role definitions | GlobalDefault._initial_defaults() |
| **SSO** | `/api/v2/saas/settings/sso` | `admin/saas/api/settings.py` | SSO config (Keycloak) | Keycloak integration |
| **Integrations** | `/api/v2/saas/integrations` | `admin/saas/api/integrations.py:149` | List all integrations | `IntegrationConfig` schema |
| **Billing** | `/api/v2/saas/billing` | `admin/saas/api/billing.py:26` | MRR, ARPU, invoices | Lago integration |
| **Audit** | `/api/v2/saas/audit` | `admin/saas/api/audit.py:91` | Audit log, export CSV | `AuditLog` model |
| **Health** | `/api/v2/saas/health` | `admin/saas/api/health.py` | Infrastructure health checks | Postgres, Redis, Kafka, etc. |

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

## 7. Implementation Details: GlobalDefault Model

The `GlobalDefault` model in `admin/saas/models/profiles.py` is the singleton that stores platform-wide default configurations.

### 7.1 Model Structure

```python
class GlobalDefault(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    defaults = models.JSONField(default=dict, help_text="Canonical default settings (models, roles, quotas)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "saas_global_defaults"
    ```

### 7.2 Initial Defaults (`_initial_defaults()`)

```python
@staticmethod
def _initial_defaults() -> Dict[str, Any]:
    return {
        "models": [
            {"id": "gpt-4o", "provider": "openai", "enabled": True},
            {"id": "claude-3-5-sonnet", "provider": "anthropic", "enabled": True},
        ],
        "roles": [
            {"id": "admin", "permissions": ["*"]},
            {"id": "member", "permissions": ["read"]},
        ],
        "dev_sandbox_defaults": {
            "max_agents": 2,
            "max_users": 1,
            "enable_code_interpreter": False,
            "enable_filesystem": False,
            "rate_limits_multiplier": 0.5,
        },
        "dev_live_defaults": {
            "max_agents": 10,
            "max_users": 5,
            "enable_code_interpreter": True,
            "enable_filesystem": True,
            "rate_limits_multiplier": 1.0,
        },
    }
```

### 7.3 Settings Resolution Priority

Settings are resolved in this exact order (fallback cascade):

1. **AgentSetting ORM** (`admin/core/models.py`) - Per-agent settings
2. **Environment Variables** - `SA01_CHAT_PROVIDER`, `SA01_CHAT_MODEL`, etc.
3. **Tenant Settings** (`TenantSettings` model) - Overrides for tenant
4. **Platform Defaults** (`GlobalDefault._initial_defaults()`) - Master blueprint
5. **Code Defaults** (`SettingsModel` in `settings_model.py`) - Ultimate fallback

Implemented in `admin/core/helpers/settings_defaults.py:get_default_settings()`.

---

## 8. Gap Analysis (Remaining Work)

| Area | Status | Notes |
|------|--------|-------|
| Platform Dashboard | ✅ Implemented | `admin/saas/api/dashboard.py` |
| Tenant Management | ✅ Implemented | `admin/saas/api/tenants.py` |
| User Management | ✅ Implemented | `admin/saas/api/users.py` |
| Tier Management | ✅ Implemented | `admin/saas/api/tiers.py` |
| Feature Catalog | ✅ Implemented | `admin/saas/api/features.py` |
| Platform Settings | ✅ Implemented | `admin/saas/api/settings.py` |
| Integration Management | ✅ Implemented | `admin/saas/api/integrations.py` |
| Billing Dashboard | ✅ Implemented | `admin/saas/api/billing.py` |
| Audit Log | ✅ Implemented | `admin/saas/api/audit.py` |
| Health Checks | ✅ Implemented | `admin/core/api/health.py` |
| Model Catalog UI | ⚠️ Partial | API exists (`/api/v2/saas/settings/models`), UI defined in SRS |
| Tool Catalog UI | ⚠️ Partial | API exists, UI defined in SRS |
| MCP Registry UI | ⚠️ Partial | API exists, UI defined in SRS |
| Permission Browser UI | ⚠️ Partial | API exists, UI defined in SRS |
| Visual Topology UI | ⚠️ Partial | SRS exists, UI not implemented |
| Agent Marketplace UI | ⚠️ Partial | SRS exists, UI not implemented |

**All backend APIs are fully implemented using Django Ninja with Pydantic schemas.**
