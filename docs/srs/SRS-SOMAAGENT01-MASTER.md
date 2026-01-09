# SomaAgent01 — Master Technical Specification
## ISO/IEC 25010 Compliant Documentation

| Document ID | SRS-SOMAAGENT01-MASTER-001 |
|-------------|---------------------------|
| Version | 1.0.0 |
| Date | 2026-01-02 |
| Status | APPROVED |
| Classification | Internal - Engineering |

---

# TABLE OF CONTENTS

1. [Scope](#1-scope)
2. [Architecture Overview](#2-architecture-overview)
3. [Subsystem Catalog](#3-subsystem-catalog)
4. [API Reference](#4-api-reference)
5. [Data Models](#5-data-models)
6. [Integration Points](#6-integration-points)
7. [Migration Audit](#7-migration-audit)
8. [7-Persona Deep Analysis](#8-7-persona-deep-analysis)
9. [Action Items](#9-action-items)
10. [Verification Procedures](#10-verification-procedures)

---

# 1. SCOPE

## 1.1 Purpose
Complete technical specification for SomaAgent01, the execution layer of the SOMA cognitive stack.

## 1.2 System Overview
- **Project:** SomaAgent01
- **Framework:** Django 5.1 + Django Ninja 1.3
- **Database:** PostgreSQL via Django ORM
- **Message Queue:** Apache Kafka
- **Cache:** Redis
- **Orchestration:** Temporal

## 1.3 Compliance Status
| Metric | Value |
|--------|-------|
| SQLAlchemy imports | **0** |
| FastAPI imports | **0** |
| VIBE Compliance | **98%** |
| Total Files | 500+ |
| Total Directories | 71 |

---

# 2. ARCHITECTURE OVERVIEW

## 2.1 Stack Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SOMA COGNITIVE STACK                               │
├─────────────────────────────────────────────────────────────────────────────┤
│   SomaAgent01 (Port 20xxx)          ─── Execution Layer                     │
│   ├── AgentContext._process_chain   ─── Recursive agent hierarchy           │
│   ├── AgentIQGovernor               ─── 6-lane token budgeting              │
│   ├── ContextBuilder                ─── LLM context construction            │
│   ├── ConversationWorkerImpl        ─── Kafka-driven message processing     │
│   └── BrainMemoryFacade             ─── DIRECT MEMORY BRIDGE (<0.1ms)       │
│                          │          (In-Process Call)                        │
│                          ▼                                                   │
│   SomaBrain (Port 30xxx)            ─── Cognitive Runtime (Hybrid)          │
│                          │          (Direct Hook)                            │
│                          ▼                                                   │
│   SomaFractalMemory (Port 9xxx)     ─── Storage Layer (Raw SQL Access)      │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 2.2 Core Components

| Component | File | Lines | Purpose |
|-----------|------|-------|---------|
| AgentContext | `agents/services/agent_context.py` | 246 | Agent hierarchy delegation |
| AgentIQGovernor | `agents/services/agentiq_governor.py` | 872 | Token budgeting |
| ContextBuilder | `agents/services/context_builder.py` | 649 | LLM context construction |
| DegradationMonitor | `services/common/degradation_monitor.py` | 925 | Health monitoring |
| SessionManager | `admin/common/session_manager.py` | 300 | Redis session store |
| ChatService | `services/common/chat_service.py` | 800 | Chat orchestration |

## 2.3 AgentIQ Governor - 6-Lane Token Budgeting

| Lane | Purpose | Default % | Critical % |
|------|---------|-----------|------------|
| system_policy | System prompt + OPA | 15% | 70% |
| history | Conversation history | 25% | 0% |
| memory | SomaBrain context | 25% | 0% |
| tools | Tool definitions | 20% | 0% |
| tool_results | Previous outputs | 10% | 0% |
| buffer | Safety margin (min 200) | 5% | 30% |

**AIQ Score Formula:**
```
AIQ = 0.4 × context_quality + 0.3 × tool_relevance + 0.3 × budget_efficiency
```

---

# 3. SUBSYSTEM CATALOG

## 3.1 Admin Directory (61 subdirectories)

| Subsystem | Files | Status | Purpose |
|-----------|-------|--------|---------|
| agents/ | 24 | ✅ Complete | Agent services and delegation |
| auth/ | 5 | ✅ Complete | Authentication, MFA, invitations |
| billing/ | 3 | ✅ Complete | Lago integration |
| chat/ | 5 | ✅ Complete | Conversation models |
| core/ | 180 | ✅ Complete | Infrastructure, helpers, commands |
| conversations/ | 2 | ✅ Complete | Conversation API (Django ORM) |
| sessions/ | 2 | ✅ Complete | Session API (Redis) |
| saas/ | 32 | ✅ Complete | Multi-tenant SaaS |
| tools/ | 24 | ✅ Complete | Tool implementations |
| voice/ | 19 | ⚠️ 98% | WebSocket placeholder |
| (51 more) | - | ✅ Complete | Various domains |

## 3.2 Services Directory (10 subdirectories)

| Service | Files | Status | Purpose |
|---------|-------|--------|---------|
| common/ | 65 | ✅ Complete | Shared utilities |
| conversation_worker/ | 11 | ✅ Complete | Kafka consumer |
| delegation_gateway/ | 2 | ✅ Complete | Task delegation |
| delegation_worker/ | 2 | ✅ Complete | Worker processes |
| gateway/ | 14 | ✅ Complete | API gateway |
| tool_executor/ | 18 | ✅ Complete | Temporal worker |
| multimodal/ | 5 | ✅ Complete | Voice/vision |
| memory_replicator/ | 3 | ✅ Complete | Memory sync |

---

# 4. API REFERENCE

## 4.1 Sessions API (`sessions/api.py` - 446 lines)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/sessions/current` | GET | Current session info |
| `/sessions/current/refresh` | POST | Token rotation |
| `/sessions/current/logout` | POST | Logout current |
| `/sessions/users/{id}` | GET | List user sessions |
| `/sessions/users/{id}` | DELETE | Force logout |
| `/sessions/stats` | GET | Session statistics |
| `/sessions/security/terminate-all` | POST | Emergency logout |

## 4.2 Conversations API (`conversations/api.py` - 727 lines)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/conversations` | GET | List conversations |
| `/conversations` | POST | Start conversation |
| `/conversations/{id}` | GET | Get details |
| `/conversations/{id}/messages` | GET | List messages |
| `/conversations/{id}/messages` | POST | Send message |
| `/conversations/{id}/chat` | POST | Full chat cycle |
| `/conversations/search` | POST | Search conversations |

---

# 5. DATA MODELS

## 5.1 Chat Models (`chat/models.py`)

```python
class Conversation(models.Model):
    id = models.UUIDField(primary_key=True)
    agent_id = models.UUIDField()
    user_id = models.UUIDField()
    tenant_id = models.UUIDField()
    title = models.CharField(max_length=255, null=True)
    status = models.CharField(max_length=50)  # active, ended, archived
    message_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Message(models.Model):
    id = models.UUIDField(primary_key=True)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    role = models.CharField(max_length=50)  # user, assistant, system, tool
    content = models.TextField()
    metadata = models.JSONField(null=True)
    token_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
```

---

# 6. INTEGRATION POINTS

## 6.1 SomaBrain Integration

```python
# ContextBuilder → SomaBrain (Direct Mode)
from soma_core.memory_client import BrainMemoryFacade

# 1. Memory Operations (Direct <0.1ms)
facade = BrainMemoryFacade.get_instance()
snippets = await facade.recall(query, top_k=5)

# 2. Cognitive Operations (HTTP via SomaClient)
from admin.core.somabrain_client import SomaBrainClient
client = SomaBrainClient.get()
reward = await client.publish_reward(session_id, "thumbs_up", 1.0)
```

## 6.2 Environment Variables

| Variable | Purpose |
|----------|---------|
| `SA01_DB_DSN` | PostgreSQL connection |
| `SA01_REDIS_URL` | Redis connection |
| `SA01_KAFKA_BOOTSTRAP_SERVERS` | Kafka brokers |
| `SA01_TEMPORAL_HOST` | Temporal server |
| `SA01_SOMA_BASE_URL` | SomaBrain endpoint |
| `SA01_OPA_URL` | OPA policy engine |

---

# 7. MIGRATION AUDIT

## 7.1 Compliance Matrix

| Category | Files | SQLAlchemy | FastAPI | Placeholders | Score |
|----------|-------|------------|---------|--------------|-------|
| admin/* | 61 dirs | 0 | 0 | 2 | 97% |
| services/* | 10 dirs | 0 | 0 | 0 | 100% |
| **TOTAL** | 71 dirs | **0** | **0** | **2** | **98%** |

## 7.2 Anti-Pattern Scan

| Pattern | Occurrences | Status |
|---------|-------------|--------|
| SQLAlchemy imports | 0 | ✅ CLEAN |
| FastAPI imports | 0 | ✅ CLEAN |
| FIXME comments | 0 | ✅ CLEAN |
| HACK comments | 0 | ✅ CLEAN |
| XXX markers | 0 | ✅ CLEAN |
| Raw psycopg2 | 0 | ✅ CLEAN |

---

# 8. 7-PERSONA DEEP ANALYSIS

## 8.1 PhD Developer (Architecture)
- `cursor.execute("SELECT 1")` uses Django's `connection.cursor()` ✅
- Pattern is VIBE-compliant for health probes

## 8.2 Security Auditor (Credentials)
| Pattern | Count | Location | Status |
|---------|-------|----------|--------|
| Hardcoded passwords | 0 | - | ✅ |
| Hardcoded API keys | 0 | - | ✅ |
| `example.com` | 19 | Tests only | ✅ |

## 8.3 DevOps Engineer (Configuration)
- 75+ localhost fallbacks - ALL use `os.environ.get()` pattern ✅
- **3 hardcoded URLs found (LOW severity):**

| File | Line | Issue |
|------|------|-------|
| `admin/orchestrator/api.py` | 32 | TEMPORAL_HOST hardcoded |
| `admin/billing/lago_client.py` | 26 | Lago URL hardcoded |
| `admin/voice/api.py` | 310 | WebSocket URL hardcoded |

## 8.4 QA Lead (Test Coverage)
- Test fixtures use env vars with fallbacks ✅
- No mocks in production code ✅

## 8.5 PM (Feature Gaps)
| Feature | File | Status |
|---------|------|--------|
| Voice WebSocket streaming | `voice/api.py:299-303` | Placeholder |
| SaaS TenantSettings | `saas/api/settings.py:43` | Comment only |

---

# 9. ACTION ITEMS

## 9.1 Required Implementations

| ID | Item | Priority | Effort |
|----|------|----------|--------|
| REQ-001 | Voice WebSocket consumer | HIGH | 2 days |
| REQ-002 | SaaS TenantSettings model | MEDIUM | 0.5 days |
| REQ-003 | Hardcoded URL fixes | LOW | 0.1 days |

## 9.2 Total Implementation Effort

| Item | Days |
|------|------|
| Voice WebSocket | 2.0 |
| SaaS Settings Model | 0.5 |
| Hardcoded URL Fixes | 0.1 |
| **TOTAL** | **2.6 days** |

---

# 10. VERIFICATION PROCEDURES

```bash
# 1. Django compliance check
python manage.py check --deploy

# 2. Anti-pattern verification
grep -r "from sqlalchemy\|from fastapi" admin/ services/ --include="*.py" | wc -l
# Expected: 0

# 3. Run test suite
python manage.py test

# 4. Migration status
python manage.py showmigrations
```

---

# APPENDIX A: FILE REFERENCE

| File | Lines | Purpose |
|------|-------|---------|
| `agents/services/agentiq_governor.py` | 872 | Token budgeting |
| `agents/services/agent_context.py` | 246 | Agent hierarchy |
| `agents/services/context_builder.py` | 649 | LLM context |
| `services/common/degradation_monitor.py` | 925 | Health monitoring |
| `services/common/chat_service.py` | 800 | Chat orchestration |
| `sessions/api.py` | 446 | Session management |
| `conversations/api.py` | 727 | Conversation API |

---

**END OF DOCUMENT**

*SRS-SOMAAGENT01-MASTER-001 v1.0.0*
