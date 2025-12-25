# SRS: Ultimate User Journey — From Platform Admin to End User

**Document ID:** SA01-SRS-USER-JOURNEYS-2025-12
**Purpose:** Complete user journey design for all personas with full settings catalog
**Status:** CANONICAL REFERENCE

---

## 1. Eight User Personas

| Persona | Code | Scope | Primary Screen | Key Permissions |
|---------|------|-------|----------------|-----------------|
| **SAAS Super Admin** | `saas_admin` | Platform | `/platform` | `*` (All) |
| **Tenant Admin** | `tenant_admin` | Tenant | `/admin` | `tenant:*`, `user:*`, `agent:*` |
| **Tenant Manager** | `tenant_manager` | Tenant | `/admin` | `user:create`, `agent:*` |
| **Agent Owner** | `agent_owner` | Agent | `/settings` | `agent:configure_*` |
| **Agent Operator** | `agent_operator` | Agent | `/chat` | `agent:start`, `agent:stop` |
| **Developer** | `developer` | Agent | `/dev/console` | DEV mode access |
| **Trainer** | `trainer` | Agent | `/trn/cognitive` | TRN mode access |
| **End User** | `user` | Agent | `/chat` | `conversation:*` |

---

## 2. Complete Settings Hierarchy

### 2.1 LLM Model Settings (Per-Agent)

| Setting | Type | Default | UI Route | Persona |
|---------|------|---------|----------|---------|
| **Chat Model** | | | | |
| `chat_model_provider` | String | `openrouter` | `/settings` | Agent Owner |
| `chat_model_name` | String | `openai/gpt-4.1` | `/settings` | Agent Owner |
| `chat_model_api_base` | URL | `` | `/settings` | Agent Owner |
| `chat_model_kwargs` | JSON | `{}` | `/settings` (advanced) | Agent Owner |
| `chat_model_ctx_length` | Integer | `100000` | `/settings` | Agent Owner |
| `chat_model_ctx_history` | Float | `0.7` | `/settings` | Agent Owner |
| `chat_model_vision` | Boolean | `true` | `/settings` | Agent Owner |
| `chat_model_rl_requests` | Integer | `0` | `/admin/settings` | Tenant Admin |
| `chat_model_rl_input` | Integer | `0` | `/admin/settings` | Tenant Admin |
| `chat_model_rl_output` | Integer | `0` | `/admin/settings` | Tenant Admin |
| **Utility Model** | | | | |
| `util_model_provider` | String | `openrouter` | `/settings` | Agent Owner |
| `util_model_name` | String | `openai/gpt-4.1-mini` | `/settings` | Agent Owner |
| `util_model_api_base` | URL | `` | `/settings` | Agent Owner |
| `util_model_ctx_length` | Integer | `100000` | `/settings` | Agent Owner |
| `util_model_ctx_input` | Float | `0.7` | `/settings` | Agent Owner |
| **Embedding Model** | | | | |
| `embed_model_provider` | String | `huggingface` | `/settings` | Agent Owner |
| `embed_model_name` | String | `sentence-transformers/all-MiniLM-L6-v2` | `/settings` | Agent Owner |
| `embed_model_api_base` | URL | `` | `/settings` | Agent Owner |
| **Browser Model** | | | | |
| `browser_model_provider` | String | `openrouter` | `/settings` | Agent Owner |
| `browser_model_name` | String | `openai/gpt-4.1` | `/settings` | Agent Owner |
| `browser_model_vision` | Boolean | `true` | `/settings` | Agent Owner |
| `browser_http_headers` | JSON | `{}` | `/settings` (advanced) | Agent Owner |

### 2.2 Memory Settings (Per-Agent)

| Setting | Type | Default | UI Route | Persona |
|---------|------|---------|----------|---------|
| `memory_recall_enabled` | Boolean | `true` | `/settings` | Agent Owner |
| `memory_recall_delayed` | Boolean | `false` | `/settings` | Agent Owner |
| `memory_recall_interval` | Integer | `3` | `/settings` | Agent Owner |
| `memory_recall_history_len` | Integer | `10000` | `/settings` | Agent Owner |
| `memory_recall_memories_max_search` | Integer | `12` | `/settings` | Agent Owner |
| `memory_recall_solutions_max_search` | Integer | `8` | `/settings` | Agent Owner |
| `memory_recall_memories_max_result` | Integer | `5` | `/settings` | Agent Owner |
| `memory_recall_solutions_max_result` | Integer | `3` | `/settings` | Agent Owner |
| `memory_recall_similarity_threshold` | Float | `0.7` | `/settings` | Agent Owner |
| `memory_recall_query_prep` | Boolean | `true` | `/settings` | Agent Owner |
| `memory_recall_post_filter` | Boolean | `true` | `/settings` | Agent Owner |
| `memory_memorize_enabled` | Boolean | `true` | `/settings` | Agent Owner |
| `memory_memorize_consolidation` | Boolean | `true` | `/settings` | Agent Owner |
| `memory_memorize_replace_threshold` | Float | `0.9` | `/settings` | Agent Owner |

### 2.3 Voice/Speech Settings (Per-Agent)

| Setting | Type | Default | UI Route | Persona |
|---------|------|---------|----------|---------|
| `stt_model_size` | Enum | `base` | `/settings/voice` | Agent Owner |
| `stt_language` | String | `en` | `/settings/voice` | Agent Owner |
| `stt_silence_threshold` | Float | `0.3` | `/settings/voice` | Agent Owner |
| `stt_silence_duration` | Integer (ms) | `1000` | `/settings/voice` | Agent Owner |
| `stt_waiting_timeout` | Integer (ms) | `2000` | `/settings/voice` | Agent Owner |
| `speech_provider` | String | `browser` | `/settings/voice` | Agent Owner |
| `speech_realtime_enabled` | Boolean | `false` | `/settings/voice` | Agent Owner |
| `speech_realtime_model` | String | `gpt-4o-realtime-preview` | `/settings/voice` | Agent Owner |
| `speech_realtime_voice` | String | `verse` | `/settings/voice` | Agent Owner |
| `speech_realtime_endpoint` | URL | OpenAI | `/settings/voice` | Agent Owner |
| `tts_kokoro` | Boolean | `false` | `/settings/voice` | Agent Owner |

### 2.4 MCP & A2A Settings (Per-Agent)

| Setting | Type | Default | UI Route | Persona |
|---------|------|---------|----------|---------|
| `mcp_servers` | JSON | `{}` | `/settings/tools` | Agent Owner |
| `mcp_client_init_timeout` | Integer | `10` | `/admin/settings` | Tenant Admin |
| `mcp_client_tool_timeout` | Integer | `120` | `/admin/settings` | Tenant Admin |
| `mcp_server_enabled` | Boolean | `false` | `/settings` | Agent Owner |
| `mcp_server_token` | String | `` | Auto-generated | System |
| `a2a_server_enabled` | Boolean | `false` | `/settings` | Agent Owner |

### 2.5 Agent Profile Settings

| Setting | Type | Default | UI Route | Persona |
|---------|------|---------|----------|---------|
| `agent_profile` | String | `agent0` | `/admin/agents/:id` | Tenant Admin |
| `agent_memory_subdir` | String | `default` | `/admin/agents/:id` | Tenant Admin |
| `agent_knowledge_subdir` | String | `custom` | `/admin/agents/:id` | Tenant Admin |

### 2.6 RFC/Shell Settings

| Setting | Type | Default | UI Route | Persona |
|---------|------|---------|----------|---------|
| `rfc_auto_docker` | Boolean | `true` | Django Admin | SAAS Admin |
| `rfc_url` | String | `localhost` | Django Admin | SAAS Admin |
| `rfc_password` | String | `` | Django Admin | SAAS Admin |
| `rfc_port_http` | Integer | `55080` | Django Admin | SAAS Admin |
| `rfc_port_ssh` | Integer | `55022` | Django Admin | SAAS Admin |
| `shell_interface` | String | `local` | Django Admin | SAAS Admin |

---

## 3. LLM Model Registry (Platform Catalog)

### 3.1 Model Configuration Fields

| Field | Type | Description | Managed At |
|-------|------|-------------|------------|
| `name` | String | Model identifier (e.g., `gpt-4o`) | `/platform/models` |
| `model_type` | Enum | `chat` or `embedding` | `/platform/models` |
| `provider` | String | Provider name (e.g., `openai`, `anthropic`) | `/platform/models` |
| `api_base` | URL | Custom API endpoint | `/platform/models` |
| `ctx_length` | Integer | Context window size | `/platform/models` |
| `limit_requests` | Integer | Rate limit: requests | `/platform/models` |
| `limit_input` | Integer | Rate limit: input tokens | `/platform/models` |
| `limit_output` | Integer | Rate limit: output tokens | `/platform/models` |
| `vision` | Boolean | Supports vision/images | `/platform/models` |
| `kwargs` | JSON | Additional parameters | `/platform/models` |
| `is_active` | Boolean | Available for use | `/platform/models` |

### 3.2 Default Model Seed Data

| Provider | Models |
|----------|--------|
| **OpenAI** | gpt-4o, gpt-4o-mini, gpt-4-turbo, o1, o1-mini |
| **Anthropic** | claude-3-5-sonnet, claude-3-opus, claude-3-haiku |
| **OpenRouter** | openai/gpt-4.1, anthropic/claude-3.5-sonnet |
| **Google** | gemini-2.0-flash, gemini-pro |
| **HuggingFace** | sentence-transformers/all-MiniLM-L6-v2 (embed) |

---

## 4. Complete User Journeys

### Journey 1: SAAS Admin — Platform Setup (Day 0)

```
SAAS Admin logs in
    │
    ├─→ /platform (Dashboard)
    │       └─ View: Tenant count, Revenue, Health status
    │
    ├─→ /platform/infrastructure (Health Check)
    │       └─ Verify: All 12 services healthy
    │
    ├─→ /platform/subscriptions (Tier Setup)
    │       └─ Action: Configure Free/Starter/Team/Enterprise tiers
    │       └─ Action: Set quotas and feature gates
    │
    ├─→ /platform/models (Model Catalog)
    │       └─ Action: Register LLM providers (OpenAI, Anthropic keys)
    │       └─ Action: Assign models to tiers
    │
    ├─→ /platform/infrastructure/redis/ratelimits
    │       └─ Action: Configure global rate limits
    │
    └─→ /platform/tenants/create (First Tenant)
            └─ Action: Create first tenant, assign to tier
```

### Journey 2: SAAS Admin — Daily Operations

```
SAAS Admin opens /platform
    │
    ├─→ Check: Dashboard metrics (Tenants, Agents, Revenue)
    │
    ├─→ /platform/infrastructure
    │       └─ Check: All services healthy?
    │       └─ If degraded → Investigate specific service
    │
    ├─→ /platform/audit
    │       └─ Review: Recent platform events
    │
    └─→ /platform/tenants
            └─ Handle: Support tickets, tenant issues
```

### Journey 3: Tenant Admin — Onboarding New Organization

```
Tenant Admin receives invite email
    │
    ├─→ /login (Keycloak)
    │
    ├─→ /admin (Tenant Dashboard)
    │       └─ View: Quota usage, Agent count
    │
    ├─→ /admin/users (Invite Team)
    │       └─ Action: Invite users with roles
    │
    ├─→ /admin/agents/create (First Agent)
    │       └─ Action: Name, Model, Features
    │
    └─→ /admin/settings/api-keys
            └─ Action: Add OpenAI/Anthropic API keys
```

### Journey 4: Agent Owner — Configure Agent

```
Agent Owner opens /settings
    │
    ├─→ Models Tab
    │       └─ Select: Chat model (GPT-4o)
    │       └─ Select: Utility model (GPT-4o-mini)
    │       └─ Configure: Temperature, context length
    │
    ├─→ Memory Tab
    │       └─ Toggle: Enable/disable memory
    │       └─ Configure: Recall settings
    │
    ├─→ Voice Tab (if tier allows)
    │       └─ Toggle: Enable voice
    │       └─ Select: Voice persona
    │
    ├─→ Tools Tab
    │       └─ Enable: Available tools
    │       └─ Configure: MCP servers
    │
    └─→ Personality Tab
            └─ Edit: System prompt
            └─ Configure: Behavior settings
```

### Journey 5: Developer — Debug Agent

```
Developer switches to DEV mode
    │
    ├─→ /dev/console
    │       └─ View: Real-time logs (LLM, Tools, Memory)
    │       └─ Filter: By level (DEBUG/INFO/WARN/ERROR)
    │
    ├─→ /dev/mcp
    │       └─ View: Connected MCP servers
    │       └─ Test: Execute tool manually
    │       └─ Inspect: Request/response JSON
    │
    └─→ /settings (with DEV access)
            └─ View: Advanced configuration
            └─ Export: Agent data
```

### Journey 6: Trainer — Tune Cognition

```
Trainer switches to TRN mode
    │
    ├─→ /trn/cognitive
    │       └─ Adjust: Neuromodulator sliders
    │           ├─ Dopamine (0.0-0.8)
    │           ├─ Serotonin (0.0-1.0)
    │           ├─ Norepinephrine (0.0-0.1)
    │           └─ Acetylcholine (0.0-0.5)
    │
    │       └─ Action: Trigger sleep cycle
    │       └─ Action: Reset adaptation
    │
    └─→ /memory (with TRN access)
            └─ Review: Memory consolidation results
            └─ Edit: Memory tags
```

### Journey 7: End User — Daily Chat

```
End User logs in
    │
    ├─→ /chat
    │       └─ View: Conversation list
    │       └─ Action: Start new conversation
    │       └─ Action: Send messages
    │       └─ Action: Use voice input (if enabled)
    │
    ├─→ /memory (if permitted)
    │       └─ View: Agent's memories about user
    │       └─ Search: Past conversations
    │
    └─→ /profile
            └─ Edit: Display name, avatar
            └─ Configure: Theme, notifications
```

---

## 5. Settings Visibility Matrix

| Setting Category | SAAS Admin | Tenant Admin | Agent Owner | Developer | Trainer | User |
|------------------|------------|--------------|-------------|-----------|---------|------|
| Platform Config | ✅ EDIT | ❌ | ❌ | ❌ | ❌ | ❌ |
| Infrastructure | ✅ EDIT | ❌ | ❌ | ❌ | ❌ | ❌ |
| Rate Limits | ✅ EDIT | 👁️ VIEW | ❌ | ❌ | ❌ | ❌ |
| Tier Quotas | ✅ EDIT | 👁️ VIEW | ❌ | ❌ | ❌ | ❌ |
| Model Catalog | ✅ EDIT | 👁️ VIEW | 👁️ VIEW | 👁️ VIEW | ❌ | ❌ |
| Tenant Settings | ✅ EDIT | ✅ EDIT | ❌ | ❌ | ❌ | ❌ |
| Agent Config | ✅ EDIT | ✅ EDIT | ✅ EDIT | 👁️ VIEW | ❌ | ❌ |
| Memory Settings | ✅ EDIT | ✅ EDIT | ✅ EDIT | 👁️ VIEW | 👁️ VIEW | ❌ |
| Voice Settings | ✅ EDIT | ✅ EDIT | ✅ EDIT | 👁️ VIEW | ❌ | ❌ |
| Cognitive Params | ✅ EDIT | ❌ | ❌ | ❌ | ✅ EDIT | ❌ |
| User Profile | ✅ EDIT | ✅ EDIT | ✅ EDIT | ✅ EDIT | ✅ EDIT | ✅ EDIT |

---

## 6. Mode-Based UI Differences

| Mode | Available Features | Disabled Features |
|------|-------------------|-------------------|
| **STD (Standard)** | Chat, Memory browse, Settings view | Debug console, Cognitive panel |
| **DEV (Developer)** | + Debug console, + MCP inspector, + API logs | Cognitive panel |
| **TRN (Trainer)** | + Cognitive panel, + Memory edit | Debug console |
| **RO (Read-Only)** | View chat history, View memory | All write operations |
| **DGR (Degraded)** | Limited chat (session-only) | Memory, Voice, Tools |

---

## 7. Complete Navigation Map

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          MAIN NAVIGATION                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SAAS ADMIN          TENANT ADMIN         AGENT USER                        │
│  ────────────        ────────────         ──────────                        │
│  /platform           /admin               /chat                             │
│  ├─ /tenants         ├─ /users            ├─ /:conversationId               │
│  ├─ /subscriptions   ├─ /agents           ├─ /memory                        │
│  ├─ /permissions     ├─ /billing          ├─ /settings                      │
│  ├─ /roles           ├─ /audit            ├─ /profile                       │
│  ├─ /billing         ├─ /settings         │                                 │
│  ├─ /audit           │   ├─ /api-keys     │  DEV MODE                       │
│  ├─ /features        │   └─ /integrations │  ──────────                     │
│  │                   │                    │  /dev/console                   │
│  ├─ /infrastructure  │                    │  /dev/mcp                       │
│  │   ├─ /database    │                    │                                 │
│  │   ├─ /redis       │                    │  TRN MODE                       │
│  │   │   └─ /ratelimits                   │  ──────────                     │
│  │   ├─ /temporal    │                    │  /trn/cognitive                 │
│  │   ├─ /qdrant      │                    │                                 │
│  │   ├─ /auth        │                    │  AUTH                           │
│  │   ├─ /billing     │                    │  ──────────                     │
│  │   ├─ /somabrain   │                    │  /login                         │
│  │   ├─ /voice       │                    │  /logout                        │
│  │   ├─ /mcp         │                    │  /register                      │
│  │   └─ /storage     │                    │                                 │
│  │                   │                    │                                 │
│  └─ /models          │                    │                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Decision Tree: "Where Do I Configure X?"

```
START: What do you want to configure?
│
├─→ Platform-wide setting?
│       └─ YES → /platform/* (SAAS Admin only)
│
├─→ Subscription/Quota?
│       └─ YES → /platform/subscriptions (SAAS Admin only)
│
├─→ Rate Limit?
│       └─ YES → /platform/infrastructure/redis/ratelimits (SAAS Admin)
│
├─→ Infrastructure Service?
│       └─ YES → /platform/infrastructure/* (SAAS Admin)
│
├─→ Tenant-level setting?
│       └─ YES → /admin/settings (Tenant Admin)
│
├─→ User management?
│       └─ YES → /admin/users (Tenant Admin)
│
├─→ Agent creation/deletion?
│       └─ YES → /admin/agents (Tenant Admin)
│
├─→ Agent configuration?
│       └─ YES → /settings (Agent Owner)
│
├─→ Cognitive/Neuromodulators?
│       └─ YES → /trn/cognitive (Trainer)
│
├─→ Debug/Logs?
│       └─ YES → /dev/console (Developer)
│
└─→ Personal preferences?
        └─ YES → /profile (Self)
```

This is the **COMPLETE USER JOURNEY** covering all 8 personas, all 60+ settings, and all navigation paths.
