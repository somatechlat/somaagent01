# Chat & LLM Integration Deployment Plan

**Date**: 2026-01-14 | **Status**: Ready for Review

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Lit 3.x)                          │
│       webui/src/views/saas-chat.ts (1265 lines)                     │
│       ↓ WebSocket /ws/v2/chat                                        │
├─────────────────────────────────────────────────────────────────────┤
│                         WEBSOCKET LAYER                              │
│       services/websocket-client.ts (245 lines)                      │
│       ↓ JSON Messages                                                │
├─────────────────────────────────────────────────────────────────────┤
│                         DJANGO BACKEND                               │
│   ┌───────────────────────────────────────────────────────────────┐ │
│   │ admin/chat/api/chat.py (15KB)                                 │ │
│   │   ├── create_conversation()                                    │ │
│   │   ├── list_conversations()                                     │ │
│   │   └── send_message() → ChatService                            │ │
│   └───────────────────────────────────────────────────────────────┘ │
│                              ↓                                       │
│   ┌───────────────────────────────────────────────────────────────┐ │
│   │ services/common/chat_service.py (1150 lines)                  │ │
│   │   ├── AgentIQ Governor → LanePlan                             │ │
│   │   ├── ContextBuilder → Built Context                          │ │
│   │   └── LLM Invoke → Stream Response                            │ │
│   └───────────────────────────────────────────────────────────────┘ │
│                              ↓                                       │
│   ┌───────────────────────────────────────────────────────────────┐ │
│   │ admin/llm/services/litellm_client.py (1492 lines)             │ │
│   │   ├── get_chat_model() → LangChain LLM                        │ │
│   │   ├── get_api_key() → Vault lookup                            │ │
│   │   └── ChatGenerationResult → Streaming chunks                 │ │
│   └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Inventory

| Component | File | Lines | Status |
|-----------|------|-------|--------|
| Chat UI | `webui/src/views/saas-chat.ts` | 1265 | ✅ Complete |
| WebSocket Client | `webui/src/services/websocket-client.ts` | 245 | ✅ Complete |
| Chat API | `admin/chat/api/chat.py` | ~400 | ✅ Complete |
| Chat Models | `admin/chat/models.py` | 154 | ✅ Complete |
| ChatService | `services/common/chat_service.py` | 1150 | ✅ Complete |
| **AgentIQ Governor** | `admin/agents/services/agentiq_governor.py` | 878 | ✅ Complete |
| Context Builder | `admin/agents/services/context_builder.py` | ~700 | ✅ Complete |
| Confidence Scorer | `admin/agents/services/confidence_scorer.py` | ~350 | ✅ Complete |
| Run Receipt | `admin/agents/services/run_receipt.py` | ~300 | ✅ Complete |
| LiteLLM Client | `admin/llm/services/litellm_client.py` | 1492 | ✅ Complete |
| LLM Models | `admin/llm/models.py` | ~60 | ✅ Complete |

---

## 3. Integration Requirements

### 3.1 LLM Provider Configuration

| Provider | Env Var | Vault Path | Status |
|----------|---------|------------|--------|
| OpenAI | `OPENAI_API_KEY` | `secret/soma/openai` | ⚠️ Configure |
| OpenRouter | `OPENROUTER_API_KEY` | `secret/soma/openrouter` | ⚠️ Configure |
| Anthropic | `ANTHROPIC_API_KEY` | `secret/soma/anthropic` | ⚠️ Configure |
| Groq | `GROQ_API_KEY` | `secret/soma/groq` | Optional |

### 3.2 Django Settings Required

```python
# services/gateway/settings.py
SOMABRAIN_URL = "http://localhost:9696"       # ✅ Configured
SOMAFRACTALMEMORY_URL = "http://localhost:10101"  # ✅ Configured
SOMA_MEMORY_API_TOKEN = "<from_vault>"        # ⚠️ Configure
```

### 3.3 AgentIQ Feature Flag

```bash
# Enable AgentIQ Governor
SA01_ENABLE_AGENTIQ_GOVERNOR=true  # Default: false
```

---

## 4. Deployment Checklist

### Step 1: Verify SaaS Stack Running
```bash
docker ps --filter name=somastack --format "{{.Names}}: {{.Status}}"
# Required: postgres, redis, milvus, kafka, minio - all healthy
```

### Step 2: Configure LLM API Key
```bash
# Option A: Environment variable
export OPENROUTER_API_KEY="sk-or-..."

# Option B: Vault (production)
vault kv put secret/soma/openrouter api_key="sk-or-..."
```

### Step 3: Update GlobalDefaults (LLM Models)
```python
# admin/saas/models/profiles.py - GlobalDefault.defaults["models"]
# Already configured with openrouter/minimax-01
```

### Step 4: Run WebUI
```bash
cd webui && npm install && npm run dev
# Access: http://localhost:5173
```

### Step 5: Test Chat Flow
1. Navigate to `/chat`
2. Select agent
3. Send message
4. Verify streaming response

---

## 5. AgentIQ Governor Details

| Component | Purpose |
|-----------|---------|
| **AIQ Score** | Predicts response quality (0-100) |
| **Lane Plan** | Budgets tokens across 6 lanes |
| **Degradation Levels** | L0-L4 based on AIQ thresholds |
| **Tool K** | Dynamic tool selection limit |

### 6 Lanes:
1. `system_policy` - System prompt + OPA policies
2. `history` - Conversation history
3. `memory` - SomaBrain retrieved context
4. `tools` - Tool definitions
5. `tool_results` - Tool execution results
6. `buffer` - Safety buffer

---

## 6. Known Issues to Fix

| Issue | File | Action |
|-------|------|--------|
| WebSocket endpoint missing | N/A | Implement Django Channels consumer |
| Chat API auth | `chat.py` | Verify bearer token handling |
| LLM key loading | `litellm_client.py` | Verify Vault integration |
| Streaming not wired | `chat_service.py` | Returns iterator, needs WS relay |

---

## 7. Next Steps

1. **Configure LLM API Key** in Vault or ENV
2. **Start WebUI** and verify Chat UI loads
3. **Test REST API** via curl to `/api/v1/chat/conversations`
4. **Implement WebSocket consumer** for streaming (if missing)
5. **Enable AgentIQ** via feature flag for production
