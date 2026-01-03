cannot# SRS: SomaAgent01 — Complete Feature & Settings Catalog

**Document ID:** SA01-SRS-FEATURE-CATALOG-2025-12
**Purpose:** Definitive inventory of ALL features, settings, quotas, limits, and their management interfaces.
**Status:** CANONICAL REFERENCE

---

## 1. System Architecture Summary

| Layer | Module Count | Description |
|-------|--------------|-------------|
| **Platform (SAAS)** | 26 | Multi-tenant infrastructure, billing, tiers |
| **Core Services** | 168 | Agent runtime, LLM, memory, tools |
| **Cognitive (SomaBrain)** | 9 | Neuromodulators, sleep cycles, adaptation |
| **Voice** | 19 | STT (Whisper), TTS (Kokoro), real-time voice |
| **Permissions** | 10 | RBAC, granular permissions, SpiceDB |

**Total Django Apps:** 62

---

## 2. Management Interface Map

### 2.1 WHERE Settings Are Managed

| Interface | Purpose | Route |
|-----------|---------|-------|
| **Django Admin** | Database models, superuser access | `/django-admin/` |
| **SAAS Custom UI** | Platform Admin (tenant/tier management) | `/saas/*`, `/platform/*` |
| **Tenant Custom UI** | Tenant Admin (users/agents/billing) | `/admin/*` |
| **Agent Custom UI** | Agent Owner (config/personality/tools) | `/agent/*`, `/settings/*` |
| **API Only** | Programmatic access, no UI | `/api/v2/*` |

---

## 3. Roles & Permissions Management

### 3.1 Predefined Roles (9 Total)

| Role | Scope | Management Location |
|------|-------|---------------------|
| `saas_super_admin` | Platform | Django Admin + `/platform/roles` |
| `tenant_admin` | Tenant | `/platform/tenants/:id/users` |
| `tenant_manager` | Tenant | `/admin/users` |
| `agent_owner` | Agent | `/admin/agents/:id/users` |
| `agent_operator` | Agent | `/admin/agents/:id/users` |
| `user` | Tenant | `/admin/users` |
| `viewer` | Tenant | `/admin/users` |
| `billing_admin` | Tenant | `/admin/users` |
| `security_auditor` | Tenant | `/admin/users` |

### 3.2 Granular Permissions (45+ Permissions, 12 Resources)

| Resource | Permissions | Management Location |
|----------|-------------|---------------------|
| `platform` | manage, read_metrics, manage_billing, manage_features, impersonate | **Django Admin ONLY** |
| `tenant` | create, read, update, delete, suspend, manage_subscription, view_billing, manage_users | `/platform/tenants` |
| `user` | create, read, update, delete, assign_roles, revoke_roles, reset_password, manage_mfa, view_activity | `/admin/users` |
| `agent` | create, read, update, delete, start, stop, configure_personality, configure_tools, view_logs, export | `/admin/agents` |
| `conversation` | create, read, update, delete, send_message, view_history, export, search | `/chat/*` (runtime) |
| `memory` | read, create, update, delete, search, export, configure_retention | `/memory/*` + `/admin/settings` |
| `tool` | read, execute, create, update, delete, approve | `/admin/agents/:id/tools` |
| `file` | upload, read, delete, share | `/files/*` (runtime) |
| `apikey` | create, read, revoke, rotate | `/admin/settings/api-keys` |
| `integration` | create, read, update, delete, sync | `/admin/settings/integrations` |
| `audit` | read, export, configure_retention | `/admin/audit` + `/platform/audit` |
| `backup` | create, read, restore, delete, configure_schedule | **Django Admin ONLY** |
| `billing` | view_invoices, view_usage, manage_payment, view_subscription, change_plan | `/admin/billing` |
| `voice` | voice_persona:*, voice_session:*, voice_model:* | `/voice/*` + `/platform/voice/*` |

### 3.3 Custom Role Builder

**Route:** `/platform/roles` (SAAS Admin) or `/admin/settings/roles` (Tenant Admin)
**Capabilities:**
- Create custom roles with selected granular permissions
- Assign roles to users
- Inherit from predefined roles

---

## 4. Quota & Limit Settings

### 4.1 Tier-Level Quotas (Managed via `/platform/subscriptions`)

| Quota | Field | Default (Starter) | Management |
|-------|-------|-------------------|------------|
| Max Agents | `max_agents` | 1 | Tier Builder UI |
| Max Users per Agent | `max_users_per_agent` | 5 | Tier Builder UI |
| Monthly Voice Minutes | `max_monthly_voice_minutes` | 60 | Tier Builder UI |
| Monthly API Calls | `max_monthly_api_calls` | 1000 | Tier Builder UI |
| Storage (GB) | `max_storage_gb` | 1.0 | Tier Builder UI |

### 4.2 Feature Settings per Tier

| Feature Code | Category | Billable | Management |
|--------------|----------|----------|------------|
| `memory` | Core | Yes | Tier Builder |
| `voice` | Communication | Yes | Tier Builder |
| `mcp` | Extensibility | No | Tier Builder |
| `browser_agent` | Capabilities | No | Tier Builder |
| `code_execution` | Capabilities | No | Tier Builder |
| `file_upload` | Core | Yes | Tier Builder |
| `export` | Data | No | Tier Builder |

---

## 5. Agent-Level Settings (60+ Settings)

### 5.1 Chat Model Settings

| Setting Key | Type | Management Location |
|-------------|------|---------------------|
| `chat_model_provider` | String | `/settings` or Django Admin |
| `chat_model_name` | String | `/settings` |
| `chat_model_api_base` | URL | `/settings` |
| `chat_model_temperature` | Float (0-2) | `/settings` |
| `chat_model_ctx_length` | Integer | `/settings` |
| `chat_model_ctx_history` | Float (0-1) | `/settings` |
| `chat_model_vision` | Boolean | `/settings` |
| `chat_model_rl_requests` | Integer (rate limit) | Django Admin |
| `chat_model_rl_input` | Integer (rate limit) | Django Admin |
| `chat_model_rl_output` | Integer (rate limit) | Django Admin |

### 5.2 Memory Settings

| Setting Key | Type | Management Location |
|-------------|------|---------------------|
| `memory_recall_enabled` | Boolean | `/settings` |
| `memory_recall_delayed` | Boolean | `/settings` |
| `memory_recall_interval` | Integer | `/settings` |
| `memory_recall_history_len` | Integer | `/settings` |
| `memory_recall_memories_max_search` | Integer | `/settings` |
| `memory_recall_solutions_max_search` | Integer | `/settings` |
| `memory_recall_memories_max_result` | Integer | `/settings` |
| `memory_recall_solutions_max_result` | Integer | `/settings` |
| `memory_recall_similarity_threshold` | Float | `/settings` |
| `memory_memorize_enabled` | Boolean | `/settings` |
| `memory_memorize_consolidation` | Boolean | `/settings` |
| `memory_memorize_replace_threshold` | Float | `/settings` |

### 5.3 Voice/Speech Settings

| Setting Key | Type | Management Location |
|-------------|------|---------------------|
| `stt_model_size` | Enum (tiny/base/...) | `/settings` |
| `stt_language` | String (ISO) | `/settings` |
| `stt_silence_threshold` | Float | `/settings` |
| `stt_silence_duration` | Integer (ms) | `/settings` |
| `speech_provider` | String | `/settings` |
| `speech_realtime_enabled` | Boolean | `/settings` |
| `speech_realtime_model` | String | `/settings` |
| `speech_realtime_voice` | String | `/settings` |
| `tts_kokoro` | Boolean | `/settings` |

### 5.4 MCP Settings

| Setting Key | Type | Management Location |
|-------------|------|---------------------|
| `mcp_servers` | JSON | `/settings` + `/dev/mcp` |
| `mcp_client_init_timeout` | Integer | Django Admin |
| `mcp_client_tool_timeout` | Integer | Django Admin |
| `mcp_server_enabled` | Boolean | `/settings` |

---

## 6. Cognitive (SomaBrain) Settings

### 6.1 Neuromodulator Parameters

| Parameter | Range | Management Location |
|-----------|-------|---------------------|
| Dopamine | 0.0 - 0.8 | `/trn/cognitive` (Trainer Mode) |
| Serotonin | 0.0 - 1.0 | `/trn/cognitive` |
| Norepinephrine | 0.0 - 0.1 | `/trn/cognitive` |
| Acetylcholine | 0.0 - 0.5 | `/trn/cognitive` |

### 6.2 Sleep Cycle Settings

| Setting | Type | Management Location |
|---------|------|---------------------|
| `duration_minutes` | Integer | `/trn/cognitive` |
| `consolidate_memory` | Boolean | `/trn/cognitive` |

---

## 7. Integration Settings

| Integration | Settings | Management Location |
|-------------|----------|---------------------|
| **Lago (Billing)** | API URL, API Key, Webhook Secret | `/saas/settings/integrations` |
| **Keycloak (Auth)** | URL, Realm, Client ID, Client Secret | `/saas/settings/integrations` |
| **SMTP (Email)** | Host, Port, User, Pass, From Address | `/saas/settings/integrations` |
| **OpenAI** | API Key | `/admin/settings/api-keys` |
| **Anthropic** | API Key | `/admin/settings/api-keys` |
| **Google Vertex** | Project ID, Credentials JSON | `/admin/settings/api-keys` |
| **Whisper (STT)** | URL, Model Size | `/saas/settings/integrations` |
| **Kokoro (TTS)** | URL | `/saas/settings/integrations` |
| **Qdrant (Vectors)** | URL, API Key | Django Admin |
| **S3/MinIO (Storage)** | Endpoint, Bucket, Credentials | Django Admin |

---

## 8. Feature to UI Screen Mapping

| Feature | Platform Admin | Tenant Admin | Agent Owner | User |
|---------|----------------|--------------|-------------|------|
| Tier Management | `/platform/subscriptions` | - | - | - |
| Tenant CRUD | `/platform/tenants` | - | - | - |
| User Management | `/platform/tenants/:id/users` | `/admin/users` | - | - |
| Agent CRUD | `/platform/tenants/:id/agents` | `/admin/agents` | - | - |
| Agent Config | - | `/admin/agents/:id` | `/settings` | - |
| Role Assignment | `/platform/roles` | `/admin/users` | - | - |
| Permission Browser | `/platform/permissions` | - | - | - |
| Billing | `/platform/billing` | `/admin/billing` | - | - |
| Audit Log | `/platform/audit` | `/admin/audit` | - | - |
| MCP Inspector | - | - | `/dev/mcp` | - |
| Cognitive Panel | - | - | `/trn/cognitive` | - |
| Chat | - | - | `/chat` | `/chat` |
| Memory Browser | - | - | `/memory` | `/memory` |
| Voice | - | - | `/voice/*` | `/voice/*` |

---

## 9. Summary: Management Location Decision Tree

```
WHERE is this setting managed?

1. Is it Platform-wide (Tiers, Integrations, Global Catalogs)?
   → `/saas/*` or `/platform/*` (SAAS Custom UI)

2. Is it Tenant-specific (Users, Agents, Billing)?
   → `/admin/*` (Tenant Custom UI)

3. Is it Agent-specific (Personality, Tools, Memory)?
   → `/settings` or `/agent/*` (Agent Custom UI)

4. Is it Infrastructure (Database, Cache, Secrets)?
   → Django Admin (`/django-admin/`)

5. Is it Rate Limits or Low-level Config?
   → Django Admin OR Environment Variables
```

---

## 10. NOT YET EXPOSED IN UI (API Only)

| Feature | API Endpoint | Needs UI? |
|---------|--------------|-----------|
| Custom Role Builder | `POST /api/v2/permissions/roles` | **YES** - `/platform/roles/create` |
| Permission Grant | `POST /api/v2/permissions/grants` | **YES** - `/platform/permissions` |
| Backup Management | `/api/v2/backup/*` | **YES** - `/platform/backups` |
| MCP Server Registration | `/api/v2/tools/mcp/*` | **YES** - `/platform/mcp` |
| Feature Catalog | `/api/v2/features/*` | **YES** - `/platform/features` |
