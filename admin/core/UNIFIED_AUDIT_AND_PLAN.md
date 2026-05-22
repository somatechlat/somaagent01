# SOMA Agent 01 — UNIFIED AUDIT & ACTION PLAN

> Comprehensive audit covering: Security, Degradation/Resilience, Infrastructure Integration, Architecture Integrity
> Date: 2026-05-20
> Status: Analysis Complete — awaiting approval to execute

---

## EXECUTIVE SUMMARY

The codebase has **real, production-grade infrastructure** (Kafka, Redis, PostgreSQL, Keycloak) and **sophisticated resilience patterns** (circuit breakers, transactional outbox, binary health model), but there are **critical integration gaps** where the infrastructure is either:

1. **Configured but unused** (Milvus, MinIO, etcd, Grafana — defined in docker-compose, never connected by app code)
2. **Referenced but undefined** (Temporal, SpiceDB, Prometheus — code expects them, no docker-compose service)
3. **Broken at integration points** (Django signals never emitted, outbox publisher not deployed, Kafka workers missing from supervisord)
4. **Degradation logic is fragmented** (HealthMonitor detects degradation, SimpleGovernor knows what to do, but V3ChatOrchestrator never consults either)

**The system CAN work without SomaBrain** (chat continues, PostgreSQL trace is saved), but it **CANNOT work without LLM** (circuit breaker causes hard failure instead of degraded response). The user's requirement — "agent works 100% without Brain, just no cognitive functions" — is **80% implemented but missing the LLM degradation path and the orchestrator-to-health-monitor wiring**.

---

## SECTION 1: SECURITY FIXES (COMPLETED)

| # | Issue | Status |
|---|-------|--------|
| S-01 | SQLite fallback eliminated | ✅ DONE |
| S-02 | UnifiedGate fail-closed | ✅ DONE |
| S-03 | Rate limiter fail-closed | ✅ DONE |
| S-04 | JWT verify_aud configurable | ✅ DONE |
| S-05 | Impersonation secret externalized | ✅ DONE |
| S-06 | Missing await on decode_token | ✅ DONE |
| S-07 | Development policy gated | ✅ DONE |
| S-08 | BrainBridge.recall() fixed | ✅ DONE |
| S-09 | SomaBrainClient circuit breaker | ✅ DONE |
| S-10 | Session config Redis-backed | ✅ DONE |
| S-11 | Placeholder code eliminated (multimodal, billing, capsules, quality, users) | ✅ DONE |
| S-12 | ALLOW_INSECURE_AUTH_BYPASS removed | ✅ DONE |

---

## SECTION 2: DEGRADATION & RESILIENCE GAPS

### 2.1 Critical Gaps (P0)

| # | Gap | Impact | Current State | Required Fix |
|---|-----|--------|---------------|--------------|
| D-01 | **V3ChatOrchestrator does NOT consult HealthMonitor** | Degraded mode is never entered in chat pipeline | Orchestrator has circuit breakers but no health awareness | Wire `get_health_monitor().is_degraded()` into `process_turn()` and `stream_turn()` |
| D-02 | **SimpleGovernor is NOT wired into V3ChatOrchestrator** | Token budgets never adjust for degradation | Governor exists with normal/degraded budgets, but orchestrator ignores it | Replace hardcoded budgets with `SimpleGovernor.allocate_budget(degraded=...)` |
| D-03 | **LLM circuit breaker causes HARD FAILURE** | Chat dies completely if LLM is down | `ServiceUnavailableError` propagates to user | Catch LLM circuit breaker → return degraded-mode response (local model or cached response) |
| D-04 | **DegradationMonitor API is BROKEN** | `/degradation` endpoint crashes | References non-existent methods on shim | Fix `admin/core/api/degradation.py` to use `HealthMonitor` API |
| D-05 | **ConversationWorker uses broken DegradationMonitor** | Worker crashes on degradation check | Accesses `degradation_monitor.components` which doesn't exist | Update to use `HealthMonitor` |
| D-06 | **SomaBrain memory ops have NO transaction lane in chat path** | Memories lost when Brain is down | `PendingMemory` exists but is unwired from chat orchestrator | Wire `MemorySyncService` into `_store_turn()` and `_store_episodic_bg()` |
| D-07 | **EventPublisher in-memory buffer loses events on flush failure** | Observability events lost | 3 retries then `RuntimeError`, buffer cleared | Persist failed events to `SensorOutbox` before raising |
| D-08 | **DLQ consumer crashes on import** | `os.environ.kafka` syntax error | File is completely broken | Fix to read env vars correctly |
| D-09 | **Audit publisher singleton is broken** | `get_durable_publisher` missing | Import error on every audit publish call | Fix or remove the broken singleton |
| D-10 | **Memory replicator crashes on import** | `os.environ.service` syntax error | File is completely broken | Fix to read env vars correctly |

### 2.2 Degradation Architecture — How It SHOULD Work

```
User Request
    ↓
V3ChatOrchestrator.process_turn()
    ↓
[NEW] Check HealthMonitor.is_degraded()
    ↓
If degraded:
    - Use SimpleGovernor.degraded_budget
    - Skip memory recall (use PostgreSQL history only)
    - Disable tools
    - Use LLM fallback chain (or cached response if all down)
    - Queue SomaBrain memory ops to PendingMemory
    - Continue chat normally
    ↓
If healthy:
    - Use SimpleGovernor.normal_budget
    - Full memory recall
    - Tools enabled
    - Direct SomaBrain memory store
    ↓
Return ChatResult (always, never hard-fail)
```

### 2.3 Existing Resilience Patterns (Keep & Wire)

| Pattern | Status | Location |
|---------|--------|----------|
| Circuit Breaker | ✅ Working | `services/common/circuit_breaker.py` |
| Binary Health Model | ✅ Working | `services/common/health_monitor.py` |
| Token Budget Governor | ✅ Exists, unwired | `services/common/simple_governor.py` |
| Transactional Outbox (Kafka) | ✅ Working, unwired from hot path | `admin/core/models/zdl.py` + `publish_outbox.py` |
| Sensor Outbox (SomaBrain) | ✅ Working, unwired from hot path | `admin/core/sensors/outbox.py` + `sync_worker.py` |
| PendingMemory Queue | ✅ Exists, unwired | `admin/core/models/zdl.py` + `sync_memories.py` |
| LLM Fallback Chain | ✅ Working | `services/common/llm_degradation.py` |
| ZDL (Zero Data Loss) | ✅ Models exist | `OutboxMessage`, `DeadLetterMessage`, `IdempotencyRecord` |

---

## SECTION 3: INFRASTRUCTURE INTEGRATION GAPS

### 3.1 Service Matrix: Docker-Compose vs Code vs Reality

| Service | In Compose | In Code | Actually Used | Status | Action |
|---------|-----------|---------|---------------|--------|--------|
| **PostgreSQL** | ✅ All 3 | ✅ Django ORM | ✅ Yes | Working | None |
| **Redis** | ✅ All 3 | ✅ Cache, sessions, channels, rate-limiter | ✅ Yes | Working | Add connection pooling |
| **Kafka** | ✅ AAAS only | ✅ event_bus, publisher, workers | ✅ Yes | Working | Add topic provisioning, fix broken workers |
| **Keycloak** | ✅ All 3 | ✅ JWT auth | ✅ Yes | Working | None |
| **Vault** | ✅ All 3 | ✅ Secret manager | ⚠️ Partial | Silent failure | Fail-fast in prod |
| **OPA** | ✅ AAAS/aaas only | ✅ Policy adapter | ✅ Yes | Broken in simple AAAS | Add to simple AAAS compose |
| **Milvus** | ✅ AAAS only | ❌ No pymilvus client | ❌ No | Dead weight | Remove OR wire up |
| **MinIO** | ✅ AAAS/aaas only | ❌ No S3 client pointing to it | ❌ No | Dead weight | Remove OR wire up |
| **etcd** | ✅ AAAS/aaas only | ❌ Never referenced | ❌ No | Dead weight | Remove (Milvus only) |
| **Temporal** | ❌ None | ✅ Workers, settings | ❌ No service | Broken | Add to AAAS compose |
| **SpiceDB** | ❌ None | ✅ Client, permissions API | ❌ No service | Broken | Add to AAAS compose |
| **Prometheus** | ❌ None | ✅ Metrics endpoint | ⚠️ No scraper | Orphaned metrics | Add to compose or document |
| **Grafana** | ❌ None | ❌ Not referenced | ❌ No | Not needed | Remove from .env.example |

### 3.2 Kafka — Real but Fragmented

**What works:**
- `aiokafka` event bus with real producer/consumer
- Transactional outbox pattern (Postgres → Kafka)
- Management commands for workers (`run_conversation_worker`, `run_tool_executor`, `publish_outbox`)
- Multiple publisher call sites

**What's broken:**
- **DLQ consumer** crashes on import (`os.environ.kafka`)
- **Audit publisher** crashes on import (missing `get_durable_publisher`)
- **Memory replicator** crashes on import (`os.environ.service`)
- **Topics NOT auto-created** (`KAFKA_AUTO_CREATE_TOPICS_ENABLE=false`)
- **No topic provisioning** in code or deployment scripts
- **Kafka workers NOT in supervisord** — production Docker deployment won't run consumers
- **Three different Kafka libraries** (`aiokafka`, `kafka-python`, `confluent-kafka`)

**What's bypassed:**
- Main chat API (`POST /chat/messages`) calls `V3ChatOrchestrator.process_turn()` directly — **never publishes to Kafka**
- WebSocket consumer calls `V3ChatOrchestrator.stream_turn()` directly — **never publishes to Kafka**
- Django signals (`memory_created`, `conversation_message`, `tool_executed`) have receivers but are **never emitted**

### 3.3 Redis — Working but Unpooled

**What works:**
- Django Cache backend (RedisCache)
- Django Channels (RedisChannelLayer)
- SessionManager (user sessions with TTL)
- Rate limiter (sliding window with Lua)
- Budget limits (`cache.incr`)
- Health checks

**What's broken:**
- **No connection pooling** — every module calls `redis.from_url()` with zero pool options
- **No shared Redis client factory** — 6+ modules each reinvent singleton pattern
- **`max_connections: 20`** in config loader is a phantom — never applied

### 3.4 Event Bus — Infrastructure Theater on the Hot Path

The system has **built a fully functional Kafka event bus, transactional outbox, DLQ, and sync workers** — but the **main chat flow bypasses all of it**.

| Layer | Status |
|-------|--------|
| Django Signals | Receivers exist, **never triggered** |
| OutboxMessage (PostgreSQL) | Written by signals (never), read by `publish_outbox` command |
| Kafka Producer | Real, but hot path doesn't call it |
| Kafka Consumer | Real, but nothing publishes to consumed topics |
| SensorOutbox | Real, but only `ConversationSensor` uses it (management command only) |

**The chat flow today:**
```
HTTP API / WebSocket → V3ChatOrchestrator.process_turn() → LLM → Response
                            ↓
                    Direct SomaBrainClient.remember() (best effort)
```

**The intended event-driven flow (not active):**
```
HTTP API → Django Signal → OutboxMessage → Kafka → ConversationWorker → SomaBrain
```

---

## SECTION 4: SOMABRAIN & SOMAFRACTALMEMORY STATUS

### 4.1 Source Code Location

| Component | Location | Status |
|-----------|----------|--------|
| **SomaAgent01** (this repo) | `/Users/.../somaAgent01` | ✅ Full codebase |
| **SomaBrain** | `../somabrain` (sibling directory) | ⚠️ External repo, not in this project |
| **SomaFractalMemory** | `../somafractalmemory` (sibling directory) | ⚠️ External repo, not in this project |

### 4.2 Docker Integration

| Mode | Dockerfile | How Brain/Memory Are Included |
|------|-----------|------------------------------|
| **AAAS Unified** | `infra/aaas/Dockerfile` | `COPY ../somabrain /app/somabrain` (requires sibling repo) |
| **AAAS Multi-Process** | `infra/aaas/aaas/Dockerfile` | `COPY ../somabrain /app/somabrain` + Rust builder stage |
| **Standalone** | `infra/standalone/Dockerfile` | No Brain/Memory |

**To build the AAAS Docker image, you need:**
```
parent/
├── somaAgent01/     ← this repo
├── somabrain/       ← external repo (required for build)
└── somafractalmemory/ ← external repo (required for build)
```

### 4.3 Runtime Modes

| Mode | Brain Access | Memory Access | How It Works |
|------|-------------|---------------|--------------|
| **AAAS Single-Process** | Direct Python import | Direct Python import | `SOMA_SINGLE_PROCESS=true`, Brain/Memory imported as modules |
| **AAAS Multi-Process** | HTTP to `somabrain:9696` | HTTP to `somafractalmemory:10101` | Separate processes via supervisord |
| **Standalone** | None | None | Brain features disabled, chat uses PostgreSQL history only |
| **Dev** | HTTP to `localhost:9696` | HTTP to `localhost:10101` | Can connect to local Brain/Memory if running |

### 4.4 Starting SomaBrain & SomaFractalMemory

**Option A: Docker Compose (if sibling repos exist)**
```bash
cd infra/aaas/aaas
docker-compose up -d
# This starts: somabrain (gunicorn :9696), somafractalmemory (uvicorn :10101), somaagent (uvicorn :9000)
```

**Option B: Docker Compose (simple unified — single process)**
```bash
cd infra/aaas
docker-compose up -d
# This starts ONE container with Agent+Brain+Memory together
```

**Option C: Manual (if you have the sibling repos)**
```bash
# Terminal 1: Start SomaBrain
cd ../somabrain
python manage.py migrate
python manage.py runserver 0.0.0.0:9696

# Terminal 2: Start SomaFractalMemory
cd ../somafractalmemory
python manage.py migrate
python manage.py runserver 0.0.0.0:10101

# Terminal 3: Start SomaAgent01
cd somaAgent01
python manage.py migrate
python manage.py runserver 0.0.0.0:9000
```

**Option D: Standalone (no Brain/Memory)**
```bash
cd infra/standalone
docker-compose up -d
# Agent-only, chat works with PostgreSQL history
```

### 4.5 Critical Finding: Docker Compose Missing Workers

The `infra/aaas/aaas/docker-compose.yml` and `supervisord.conf` **do NOT start**:
- Kafka consumer workers
- Outbox publisher
- Memory sync worker
- Temporal worker

These must be started separately (or added to supervisord).

---

## SECTION 5: UNIFIED PRIORITIZED TODO LIST

### P0 — CRITICAL (Fix First)

| # | Item | Category | Effort |
|---|------|----------|--------|
| P0-D01 | Wire HealthMonitor into V3ChatOrchestrator | Degradation | Medium |
| P0-D02 | Wire SimpleGovernor into V3ChatOrchestrator token budgets | Degradation | Medium |
| P0-D03 | LLM circuit breaker → degraded response (not hard failure) | Degradation | Medium |
| P0-D04 | Wire MemorySyncService/PendingMemory into chat memory store | Degradation | Medium |
| P0-D05 | Fix DLQ consumer (`os.environ.kafka` crash) | Kafka | Small |
| P0-D06 | Fix audit publisher (missing `get_durable_publisher`) | Kafka | Small |
| P0-D07 | Fix memory replicator (`os.environ.service` crash) | Kafka | Small |
| P0-D08 | Fix DegradationMonitor API (`admin/core/api/degradation.py`) | Degradation | Small |
| P0-D09 | Fix ConversationWorker degradation check | Degradation | Small |
| P0-I01 | Add OPA to `infra/aaas/docker-compose.yml` | Infrastructure | Small |
| P0-I02 | Add Temporal + SpiceDB to `infra/aaas/aaas/docker-compose.yml` | Infrastructure | Medium |
| P0-I04 | Create shared Redis connection pool factory | Redis | Medium |
| P0-I05 | Add Kafka topic provisioning script | Kafka | Medium |
| P0-I06 | Add Kafka workers to supervisord.conf | Kafka | Small |

### P1 — HIGH (Fix Next)

| # | Item | Category | Effort |
|---|------|----------|--------|
| P1-D01 | Fix EventPublisher to persist failed events to SensorOutbox | Observability | Medium |
| P1-D02 | Add Milvus direct health check (not just via SomaBrain) | Health | Small |
| P1-D03 | PostgreSQL graceful degradation (read-only mode) | Resilience | Large |
| P1-D04 | Wire Django signals in chat orchestrator (or remove dead infrastructure) | Events | Medium |
| P1-I01 | Prune `.env.example` — remove dead variables | Config | Small |
| P1-I02 | Fix `openapi_contract.yml` CI workflow | CI/CD | Small |
| P1-I03 | Add Vault fail-fast in production mode | Security | Small |
| P1-I04 | Unify Kafka libraries (pick one: `aiokafka`) | Kafka | Medium |
| P1-I05 | Add Prometheus + Grafana to docker-compose | Observability | Medium |
| P1-I06 | Remove OR wire up Milvus/MinIO/etcd | Infrastructure | Medium |

### P2 — MEDIUM

| # | Item | Category | Effort |
|---|------|----------|--------|
| P2-01 | Chat orchestrator test suite | Testing | Large |
| P2-02 | Context builder integration tests | Testing | Large |
| P2-03 | Tool execution timeout/deadline enforcement | Security | Medium |
| P2-04 | Metrics pipeline error handling | Observability | Medium |
| P2-05 | Audit logging on auth failures | Security | Medium |
| P2-06 | Kafka consumer auto-restart on failure | Kafka | Small |
| P2-07 | Outbox cleanup scheduled job | Maintenance | Small |
| P2-08 | Sensor outbox auto-scaling | Scaling | Medium |

### P3 — LOW / REFACTORING

| # | Item | Category | Effort |
|---|------|----------|--------|
| P3-01 | Memory system 9 entry points → single MemoryPort | Architecture | Large |
| P3-02 | Health/Degradation 8 implementations → single model | Architecture | Medium |
| P3-03 | Rate limiter 3 implementations → single limiter | Architecture | Medium |
| P3-04 | WebSocket token in query string → httpOnly cookie | Security | Medium |
| P3-05 | Frontend JWT in localStorage → httpOnly cookie | Security | Medium |
| P3-06 | Inconsistent error response formats | API | Medium |
| P3-07 | Missing OpenAPI schema annotations | API | Small |
| P3-08 | `admin/core/soma_client.py` vs `somabrain_client.py` clarify | Cleanup | Small |

---

## SECTION 6: RECOMMENDED EXECUTION ORDER

### Phase 1: Fix Broken Code (P0-D05 through P0-D09, P0-I01 through P0-I03)
**Goal:** Eliminate crashes on import and startup failures.
- Fix DLQ consumer, audit publisher, memory replicator
- Fix degradation API and conversation worker
- Add missing services to docker-compose
- Fix internal_token import

### Phase 2: Wire Degradation into Chat (P0-D01 through P0-D04)
**Goal:** Agent works 100% without SomaBrain, never hard-fails on LLM.
- Wire HealthMonitor + SimpleGovernor into V3ChatOrchestrator
- LLM circuit breaker → degraded response path
- Memory ops queue to PendingMemory when Brain down

### Phase 3: Infrastructure Hardening (P0-I04 through P0-I06, P1-I01 through P1-I06)
**Goal:** Every service in docker-compose is used; every code dependency has a service.
- Redis connection pooling
- Kafka topic provisioning + workers in supervisord
- Temporal + SpiceDB + Prometheus in compose
- Prune dead variables, fix CI

### Phase 4: Testing & Polish (P2-01 through P2-08, P3-01 through P3-08)
**Goal:** Production-ready with tests and clean architecture.

---

## APPENDIX: Key Files Reference

| File | Purpose |
|------|---------|
| `admin/core/chat_orchestrator.py` | 12-phase chat pipeline |
| `services/common/health_monitor.py` | Binary health model |
| `services/common/simple_governor.py` | Token budget allocation |
| `services/common/circuit_breaker.py` | Circuit breaker implementation |
| `admin/core/models/zdl.py` | Outbox, DeadLetter, PendingMemory, Idempotency |
| `services/common/event_bus.py` | Kafka event bus (aiokafka) |
| `admin/core/management/commands/publish_outbox.py` | Outbox → Kafka bridge |
| `admin/core/management/commands/sync_memories.py` | PendingMemory → SomaBrain sync |
| `services/common/llm_degradation.py` | LLM provider fallback chains |
| `services/common/degradation_monitor.py` | Legacy shim (broken API) |
| `infra/aaas/docker-compose.yml` | Simple AAAS compose |
| `infra/aaas/aaas/docker-compose.yml` | Full AAAS compose |
| `infra/aaas/aaas/supervisord.conf` | Production process manager |
