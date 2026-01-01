# CANONICAL USER JOURNEYS SRS

**Document ID:** SA01-SRS-JOURNEYS-2025-12
**Version:** 1.0
**Created:** 2025-12-24
**Status:** CANONICAL — Single Source of Truth

> **SUPERCEDES:** USER_JOURNEYS.md (to be deleted after review)

---

## 1. Overview

This SRS defines **ALL user journeys** for SomaAgent01 with:
- Screen flows for each journey
- API endpoints per journey
- **Degradation handling** for each journey (reusable patterns)
- Error states and recovery

---

## 2. User Personas

| Persona | Role | Access Level |
|---------|------|--------------|
| **End User** | Regular user | Tenant-scoped |
| **Tenant Admin** | Manages tenant | Tenant admin |
| **Platform Admin** | Super admin (God Mode) | Platform-wide |
| **API Consumer** | External integration | API token |
| **Agent** | AI agent (system) | System-level |

---

## 3. Degradation Context

**Every journey reads from centralized DegradationMonitor:**

```python
# Available in all journeys via dependency injection
class JourneyContext:
    somabrain_available: bool
    llm_available: bool
    voice_available: bool
    storage_available: bool
    current_llm_model: str  # May be fallback
    degradation_messages: List[str]  # User-visible warnings
```

---

## 4. Journey: UC-01 Chat with AI Agent

### 4.1 Screen Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ SCREEN: Chat View                                               │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────┐  ┌────────────────────────────────────────────┐ │
│ │ Sidebar     │  │ Chat Panel                                 │ │
│ │ [Conv 1]    │  │ Agent: How can I help you today?           │ │
│ │ [Conv 2]    │  │ User: Analyze this document                │ │
│ │ [+ New]     │  │ Agent: [Streaming response...]             │ │
│ │             │  ├────────────────────────────────────────────┤ │
│ │ ⚠ Degraded  │  │ [📎] Type message...            [🎤] [➤]  │ │
│ └─────────────┘  └────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Flow

1. User opens Chat View
2. **[DEGRADATION CHECK]** Check DegradationMonitor status
3. User types message
4. Message → Gateway → Kafka → Conversation Worker
5. **[DEGRADATION: SomaBrain]** If unavailable → use session context only
6. Worker calls LLM **[DEGRADATION: LLM]** → use fallback if primary down
7. Streaming response → SSE → UI
8. **[ZDL]** Memory stored via OutboxMessage → eventual SomaBrain sync

### 4.3 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v2/chat/messages` | Send message |
| GET | `/api/v2/chat/conversations` | List conversations |
| GET | `/api/v2/chat/messages/{conv_id}` | Get messages |

### 4.4 Degradation Handling

| Dependency | Status | User Experience |
|------------|--------|-----------------|
| SomaBrain | DOWN | ⚠ "Limited memory mode" - session only |
| LLM Primary | DOWN | Transparent fallback (no message) |
| LLM All | DOWN | ❌ "AI temporarily unavailable" |
| Kafka | DOWN | Messages queued via Outbox |

---

## 5. Journey: UC-02 Create New Conversation

### 5.1 Screen Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ MODAL: New Conversation                                         │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Conversation Title: [________________]                       │ │
│ │                                                              │ │
│ │ Agent: [CustomerSupport01 ▼]                                │ │
│ │                                                              │ │
│ │ Memory Mode: ○ Session Only  ● Persistent                   │ │
│ │                                                              │ │
│ │                    [Cancel] [Create Conversation]            │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Flow

1. User clicks "+ New Conversation"
2. Modal opens with agent selection
3. User selects agent and memory mode
4. **[ZDL]** Conversation created in DB via transaction
5. UI navigates to new conversation

### 5.3 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v2/chat/conversations` | Create conversation |
| GET | `/api/v2/agents` | List available agents |

### 5.4 Degradation Handling

| Dependency | Status | User Experience |
|------------|--------|-----------------|
| Database | DOWN | ❌ "Cannot create conversation" |
| SomaBrain | DOWN | ✓ Create allowed, memory mode forced to session |

---

## 6. Journey: UC-03 Upload File to Agent

### 6.1 Screen Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ SCREEN: Chat View - File Upload                                 │
├─────────────────────────────────────────────────────────────────┤
│ ┌────────────────────────────────────────────────────────────┐  │
│ │ Drop files here or click to browse                         │  │
│ │                                                             │  │
│ │ ┌──────────────────────────────────────────────────────┐   │  │
│ │ │ 📄 report.pdf (2.3 MB)                               │   │  │
│ │ │ ████████████████░░░░░░░░░░░░░░░░░░ 65%               │   │  │
│ │ └──────────────────────────────────────────────────────┘   │  │
│ │                                                             │  │
│ │ ⚠ Storage degraded - upload will be queued                │  │
│ └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Flow

1. User drags file to chat or clicks attach
2. **[DEGRADATION CHECK]** Check storage status
3. If TUS available → resumable upload
4. ClamAV scans file (SCAN_PENDING → AVAILABLE)
5. File stored in storage provider
6. **[DEGRADATION: Storage]** If unavailable → queue via Outbox
7. File reference added to message

### 6.3 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v2/uploads/init` | Initialize TUS upload |
| PATCH | `/api/v2/uploads/{id}` | Resume upload chunk |
| GET | `/api/v2/uploads/{id}/status` | Check scan status |

### 6.4 Degradation Handling

| Dependency | Status | User Experience |
|------------|--------|-----------------|
| Storage Primary | DOWN | ⚠ "Using backup storage" |
| Storage All | DOWN | ⚠ "Upload queued for later" |
| ClamAV | DOWN | Files held in SCAN_PENDING |

---

## 7. Journey: UC-04 Voice Chat

### 7.1 Screen Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ SCREEN: Voice Mode Active                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                    ┌────────────────────┐                      │
│                    │   ●  ●  ●  ●  ●    │ ← Audio Visualizer  │
│                    └────────────────────┘                      │
│                                                                 │
│              "Please search for Python tutorials"               │
│                                                                 │
│              [🎤 Listening...]  or  [🔊 Speaking...]           │
│                                                                 │
│              ⚠ Voice in fallback mode                          │
│                                                                 │
│                    [End Voice Session]                          │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Flow

1. User clicks microphone button
2. **[DEGRADATION CHECK]** Check TTS/STT availability
3. VAD detects speech end
4. Audio → STT **[DEGRADATION: STT]** → use fallback
5. Text → Chat flow (UC-01)
6. Response → TTS **[DEGRADATION: TTS]** → use fallback
7. Audio plays to user

### 7.3 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| WebSocket | `/ws/voice` | Real-time audio stream |
| POST | `/api/v2/voice/transcribe` | STT |
| POST | `/api/v2/voice/synthesize` | TTS |

### 7.4 Degradation Handling

| Dependency | Status | User Experience |
|------------|--------|-----------------|
| TTS Primary | DOWN | ⚠ "Voice in fallback mode" + browser TTS |
| STT Primary | DOWN | ⚠ "Voice in fallback mode" + browser STT |
| All Voice | DOWN | ❌ Voice disabled, text-only mode |

---

## 8. Journey: UC-05 View/Manage Memories

### 8.1 Screen Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ SCREEN: Memory Dashboard                                        │
├─────────────────────────────────────────────────────────────────┤
│ [Search memories...]                    [Filters ▼] [Export]   │
│                                                                 │
│ ⚠ SomaBrain offline - showing cached memories                  │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Memory Graph Visualization                                  │ │
│ │     [Node]──────[Node]──────[Node]                         │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ Recent Memories (cached):                                       │
│ │ "Project deadline is Dec 31" | [View] [Delete]              │ │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 Flow

1. User opens Memory Dashboard
2. **[DEGRADATION CHECK]** Check SomaBrain status
3. If available → load from SomaBrain `/memory/recall`
4. **[DEGRADATION: SomaBrain]** If down → show cached/pending
5. User can search, filter, delete
6. **[ZDL]** Deletions queued via Outbox if SomaBrain down

### 8.3 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v2/memory/search` | Semantic search |
| GET | `/api/v2/memory/recent` | Recent memories |
| DELETE | `/api/v2/memory/{id}` | Delete memory |
| GET | `/api/v2/memory/pending` | Pending sync count |

### 8.4 Degradation Handling

| Dependency | Status | User Experience |
|------------|--------|-----------------|
| SomaBrain | DOWN | ⚠ "Showing cached memories" |
| Graph viz | N/A | Falls back to list view |

---

## 9. Journey: UC-06 Configure Agent

### 9.1 Screen Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ SCREEN: Agent Configuration                                    │
├─────────────────────────────────────────────────────────────────┤
│ Agent: CustomerSupport01                                        │
│ [General]  [Capabilities]  [Memory]  [Permissions]             │
│                                                                 │
│ LLM Model: [GPT-4o ▼] ⚠ Currently using fallback              │
│ Temperature: [0.7 ────●──────]                                  │
│ Max Tokens: [4096]                                              │
│                                                                 │
│ Capabilities:                                                   │
│ ☑ Web Search    ☑ Code Execution                              │
│ ☐ File Upload   ☑ Memory Access                                │
│                                                                 │
│                               [Cancel] [Save Agent]            │
└─────────────────────────────────────────────────────────────────┘
```

### 9.2 Flow

1. Tenant Admin opens Agent Configuration
2. **[DEGRADATION CHECK]** Show current LLM status
3. Admin configures model, capabilities
4. **[ZDL]** Config saved via transaction
5. Changes apply to future conversations

### 9.3 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v2/agents` | List agents |
| POST | `/api/v2/agents` | Create agent |
| PUT | `/api/v2/agents/{id}` | Update agent |
| GET | `/api/v2/agents/{id}/capabilities` | Get capabilities |

### 9.4 Degradation Handling

| Dependency | Status | User Experience |
|------------|--------|-----------------|
| Database | DOWN | ❌ Cannot save configuration |
| LLM | FALLBACK | ⚠ "Model X currently unavailable" |

---

## 10. Journey: UC-07 Manage Users (Tenant Admin)

### 10.1 Screen Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ SCREEN: User Management (Tenant Admin)                         │
├─────────────────────────────────────────────────────────────────┤
│ [+ Invite User]  [Bulk Import]                    [Search... ] │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ User              │ Role        │ Status    │ Actions      │ │
│ ├─────────────────────────────────────────────────────────────┤ │
│ │ john@company.com  │ Admin       │ ✓ Active  │ [Edit] [Del] │ │
│ │ jane@company.com  │ User        │ ✓ Active  │ [Edit] [Del] │ │
│ │ bob@company.com   │ User        │ ⏳ Pending │ [Resend]     │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ Tenant Quota: 25/50 users                                       │
└─────────────────────────────────────────────────────────────────┘
```

### 10.2 Flow

1. Tenant Admin opens User Management
2. View list of tenant users
3. Can invite new user (email sent)
4. Can change roles (Admin/User)
5. Can deactivate/delete users
6. **[ZDL]** All changes via transactions

### 10.3 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v2/tenants/{id}/users` | List users |
| POST | `/api/v2/tenants/{id}/users/invite` | Invite user |
| PUT | `/api/v2/tenants/{id}/users/{uid}` | Update role |
| DELETE | `/api/v2/tenants/{id}/users/{uid}` | Remove user |

### 10.4 Degradation Handling

| Dependency | Status | User Experience |
|------------|--------|-----------------|
| Keycloak | DOWN | ❌ Cannot invite/modify users |
| Email | DOWN | ⚠ "Invite queued" |

---

## 11. Journey: UC-08 View Usage/Billing

### 11.1 Screen Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ SCREEN: Usage & Billing                                         │
├─────────────────────────────────────────────────────────────────┤
│ Current Plan: PRO ($99/mo)                    [Upgrade Plan]   │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Usage This Month                                            │ │
│ │                                                             │ │
│ │ API Calls:     ████████████████░░░░ 15,234 / 20,000        │ │
│ │ Tokens Used:   ██████████░░░░░░░░░░ 1.2M / 2M              │ │
│ │ Storage:       ████░░░░░░░░░░░░░░░░ 2.1 GB / 10 GB         │ │
│ │ Agents:        ██████████████████░░ 9 / 10                 │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ Billing History:                                                │
│ │ Dec 2024 | $99.00 | Paid    │                                │
│ │ Nov 2024 | $99.00 | Paid    │                                │
└─────────────────────────────────────────────────────────────────┘
```

### 11.2 Flow

1. User opens Usage & Billing
2. Load usage metrics from Lago
3. Display current plan and limits
4. Show billing history
5. User can upgrade/downgrade plan

### 11.3 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v2/saas/usage` | Current usage |
| GET | `/api/v2/saas/subscription` | Plan details |
| GET | `/api/v2/saas/invoices` | Billing history |
| POST | `/api/v2/saas/subscription/change` | Change plan |

### 11.4 Degradation Handling

| Dependency | Status | User Experience |
|------------|--------|-----------------|
| Lago | DOWN | ⚠ "Billing data unavailable" + cached |

---

## 12. Journey: UC-09 Create Tenant (Platform Admin)

### 12.1 Screen Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ SCREEN: Create Tenant (GOD MODE)                                │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Company Name:  [________________________]                   │ │
│ │ Domain:        [________].somaagent.io                     │ │
│ │ Admin Email:   [________________________]                   │ │
│ │                                                             │ │
│ │ Plan: ○ Free  ○ Pro  ● Enterprise                          │ │
│ │                                                             │ │
│ │ Initial Limits:                                             │ │
│ │ Users: [100]  Agents: [50]  Storage: [100] GB              │ │
│ │                                                             │ │
│ │                    [Cancel] [Create Tenant]                 │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 12.2 Flow

1. Platform Admin opens Create Tenant
2. Fills tenant details and plan
3. **[ZDL]** Transaction:
   - Create Tenant in DB
   - Create in Keycloak
   - Create subscription in Lago
   - Create SpiceDB relationships
4. Send welcome email to admin

### 12.3 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v2/saas/tenants` | Create tenant |
| POST | `/api/v2/saas/tenants/{id}/subscription` | Assign plan |

### 12.4 Degradation Handling

| Dependency | Status | User Experience |
|------------|--------|-----------------|
| Keycloak | DOWN | ❌ Cannot create tenant |
| Lago | DOWN | ⚠ Tenant created, billing pending |
| SpiceDB | DOWN | ❌ Cannot create tenant |

---

## 13. Journey: UC-10 Suspend/Activate Tenant

### 13.1 Screen Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ SCREEN: Tenant Detail (GOD MODE)                                │
├─────────────────────────────────────────────────────────────────┤
│ Tenant: Acme Corp                           Status: ✓ Active   │
│                                                                 │
│ [Suspend Tenant] [Delete Tenant] [Export Data]                 │
│                                                                 │
│ ⚠ Suspending will:                                             │
│ • Block all user logins                                         │
│ • Stop all agent conversations                                  │
│ • Pause billing                                                 │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Confirm suspend Acme Corp?                                  │ │
│ │ Reason: [Payment failed________________]                    │ │
│ │                         [Cancel] [Confirm Suspend]          │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 13.2 Flow

1. Admin views tenant detail
2. Clicks Suspend
3. Confirmation with reason
4. **[ZDL]** Transaction:
   - Update tenant status
   - Invalidate all sessions
   - Update Keycloak
   - Notify tenant admin via email

### 13.3 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v2/saas/tenants/{id}/suspend` | Suspend |
| POST | `/api/v2/saas/tenants/{id}/activate` | Reactivate |

---

## 14. Journey: UC-11 Manage Subscriptions

### 14.1 Screen Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ SCREEN: Subscription Management (GOD MODE)                      │
├─────────────────────────────────────────────────────────────────┤
│ Tenant: Acme Corp                                               │
│                                                                 │
│ Current Plan: Pro ($99/mo)                                      │
│ Billing Cycle: Monthly (renews Jan 1, 2025)                    │
│                                                                 │
│ Change Plan:                                                    │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ ○ Free ($0)     ● Pro ($99)     ○ Enterprise (Custom)      │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ Override Limits:                                                │
│ Users: [50]  Agents: [15]  Storage: [25] GB                    │
│                                                                 │
│                    [Cancel] [Save Changes]                      │
└─────────────────────────────────────────────────────────────────┘
```

### 14.2 Flow

1. Admin opens subscription for tenant
2. Can change plan tier
3. Can override limits
4. **[ZDL]** Update Lago subscription
5. Prorated charges calculated

### 14.3 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v2/saas/tenants/{id}/subscription` | Get subscription |
| PUT | `/api/v2/saas/tenants/{id}/subscription` | Update |
| POST | `/api/v2/saas/tenants/{id}/subscription/override` | Custom limits |

---

## 15. Journey: UC-12 View Platform Metrics

### 15.1 Screen Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ SCREEN: Platform Dashboard (GOD MODE)                           │
├─────────────────────────────────────────────────────────────────┤
│ ⚠ 2 services degraded                      [View Health Map]   │
│                                                                 │
│ Platform Metrics (Real-time)                                    │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Total Tenants: 127 (+5 this week)                          │ │
│ │ Active Users: 2,340                                         │ │
│ │ Total Agents: 892                                           │ │
│ │ MRR: $45,600 (+$2,100)                                     │ │
│ │                                                             │ │
│ │ API Calls (24h): 1.2M                                       │ │
│ │ Error Rate: 0.02%                                           │ │
│ │ P99 Latency: 245ms                                          │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ Service Health:                                                 │
│ │ ✓ Gateway    ✓ Database    ⚠ SomaBrain    ✓ Kafka          │
└─────────────────────────────────────────────────────────────────┘
```

### 15.2 Flow

1. Admin opens Platform Dashboard
2. Real-time metrics from Prometheus
3. **[DEGRADATION]** Service health status visible
4. Can drill down to individual services
5. Alerts for degraded components

### 15.3 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v2/saas/metrics/summary` | Platform summary |
| GET | `/api/v2/saas/metrics/health` | Service health |
| GET | `/api/v2/saas/metrics/realtime` | SSE real-time |

---

## 16. Journey: UC-13 Tool Execution (Agent)

### 16.1 Flow Diagram

```
User: "Search for AI news"
        │
        ▼
┌─────────────────┐
│ LLM Response    │
│ tool: web_search│
└────────┬────────┘
         │
         ▼
┌─────────────────┐    ┌─────────────────┐
│ Tool Executor   │───▶│ OPA Policy      │
│                 │◀───│ Check           │
└────────┬────────┘    └─────────────────┘
         │ (if allowed)
         ▼
┌─────────────────┐
│ Execute Tool    │───▶ External API
│ Return Results  │
└────────┬────────┘
         │
         ▼
Agent: "Here are the AI news..."
```

### 16.2 Degradation Handling

| Dependency | Status | User Experience |
|------------|--------|-----------------|
| OPA | DOWN | ❌ Tool denied (fail-closed) |
| External API | DOWN | ⚠ "Tool X unavailable" |
| Kafka | DOWN | Tool request queued via Outbox |

---

## 17. Journey: UC-14 Store/Recall Memory (System)

### 17.1 Flow Diagram

```
Conversation ends
        │
        ▼
┌─────────────────────────────────────────────────┐
│ Memory Service                                   │
│                                                  │
│ 1. Check SomaBrain status                       │
│    └─▶ If AVAILABLE: POST /memory/remember     │
│    └─▶ If DOWN: Create PendingMemory record    │
│                                                  │
│ 2. IdempotencyRecord prevents duplicates        │
│                                                  │
│ 3. OutboxMessage ensures eventual delivery      │
└─────────────────────────────────────────────────┘
```

### 17.2 Degradation Handling

| Dependency | Status | Action |
|------------|--------|--------|
| SomaBrain | DOWN | Queue to PendingMemory |
| Database | DOWN | ❌ Critical failure |

---

## 18. Journey: UC-15 API Integration (External)

### 18.1 Flow Diagram

```
External System
        │
        ▼ API Key in Header
┌─────────────────────────────────────────────────┐
│ POST /api/v2/chat/completions                   │
│                                                  │
│ Request:                                         │
│ {                                                │
│   "messages": [{"role": "user", "content": ...}],│
│   "stream": true                                │
│ }                                                │
│                                                  │
│ Response (SSE):                                  │
│ data: {"delta": {"content": "..."}}             │
└─────────────────────────────────────────────────┘
```

### 18.2 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v2/chat/completions` | OpenAI-compatible |
| GET | `/api/v2/models` | List available models |
| POST | `/api/v2/embeddings` | Generate embeddings |

### 18.3 Degradation Handling

| Dependency | Status | API Response |
|------------|--------|--------------|
| LLM | DOWN | 503 + Retry-After header |
| Rate Limit | HIT | 429 + rate limit headers |
| Auth | INVALID | 401 Unauthorized |

---

## 19. Summary: Degradation by Journey

| Journey | SomaBrain | LLM | Voice | Storage | Kafka |
|---------|-----------|-----|-------|---------|-------|
| UC-01 Chat | Session-only | Fallback | N/A | N/A | Outbox |
| UC-02 New Conv | Session mode | N/A | N/A | N/A | Outbox |
| UC-03 Upload | N/A | N/A | N/A | Queue | Outbox |
| UC-04 Voice | N/A | Fallback | Fallback | N/A | Outbox |
| UC-05 Memory | Cached | N/A | N/A | N/A | Outbox |
| UC-06 Agent | N/A | Show status | N/A | N/A | Outbox |
| UC-07 Users | N/A | N/A | N/A | N/A | Outbox |
| UC-08 Billing | N/A | N/A | N/A | N/A | N/A |
| UC-09 Tenant | N/A | N/A | N/A | N/A | Outbox |
| UC-10 Suspend | N/A | N/A | N/A | N/A | Outbox |
| UC-11 Subscr | N/A | N/A | N/A | N/A | N/A |
| UC-12 Metrics | Show status | N/A | N/A | N/A | N/A |
| UC-13 Tool | N/A | N/A | N/A | N/A | Outbox |
| UC-14 Memory | PendingMemory | N/A | N/A | N/A | Outbox |
| UC-15 API | Session-only | Fallback | N/A | N/A | Outbox |

---

**Last Updated:** 2025-12-24
**Maintained By:** Architecture Team
