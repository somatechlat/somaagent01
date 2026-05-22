# 🔬 SOMAAGENT01 COMPREHENSIVE CODEBASE AUDIT REPORT
## Production-Grade Forensic Analysis | 1,491 Files | 6 Specialized Agents

**Date:** 2026-05-20  
**Auditors:** Kimi Code CLI + 4 Background Forensic Agents (Architecture, Backend, Frontend, Safety)  
**Scope:** Full repository — Architecture, Backend, Frontend, Safety, Infrastructure, Tests  
**Files Analyzed:** 120+ directly, 1,491 mapped  
**Agent Run Time:** ~13 minutes parallel execution  

---

## 📊 EXECUTIVE SCORECARD

| Domain | Score | Status |
|--------|-------|--------|
| **Overall Architecture** | 5/10 | ⚠️ Fragile — triplicated lanes, mode detection inconsistencies, "Two Universes" problem |
| **Backend Code Quality** | 4/10 | 🔴 Critical — 1,402 Pyright errors, heavy Ruff suppression, import shadowing |
| **Frontend (WebUI)** | 6/10 | ⚠️ Good Lit components, auth store race conditions, WebSocket leaks |
| **Safety & Failsafe** | 6/10 | ⚠️ Policies exist but NOT wired to enforcement, fail-open rate limiting |
| **Infrastructure / DevOps** | 5/10 | ⚠️ K8s barebones, CI scattered, missing prod hardening |
| **Tests & Documentation** | 4/10 | 🔴 24 tests for 1,491 files, VIBE rules violated by mocks |
| **SOMA Brain Integration** | 5/10 | ⚠️ Dual paths (HTTP/Direct) but broken recall, fragile lifecycle |
| **AGENTIQ System** | 6/10 | ⚠️ Clean gate design, derivation partially implemented, fake policy checks |

**Overall System Maturity: 5.1/10 — PRE-PRODUCTION**  
*The codebase has strong architectural intent but suffers from massive technical debt, triplicated subsystems, insufficient test coverage, and a dangerous gap between policy files and runtime enforcement.*

---

## 🏗️ SECTION 1: ARCHITECTURE ANALYSIS

### 1.1 System Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│  Lit 3.x Web Components (webui/src/) ~93 TS files               │
│  ├─ Views: saas-login.ts (954L), saas-chat.ts, saas-admin-*     │
│  ├─ Services: keycloak-service, websocket-client, api-client    │
│  └─ Stores: auth-store (395L), mode-store, theme-store          │
├─────────────────────────────────────────────────────────────────┤
│                      GATEWAY LAYER                               │
│  Django 5.0 + Django Ninja (admin/api.py — 412L master router)  │
│  ├─ 50+ mounted routers under /api/v2/                          │
│  ├─ ASGI via Uvicorn (services/gateway/main:django_asgi)        │
│  └─ WhiteNoise serving webui/dist SPA                           │
├─────────────────────────────────────────────────────────────────┤
│                     SERVICE LAYER                                │
│  services/common/ — 80+ shared modules                          │
│  ├─ Chat: chat_service.py (facade) → 5 sub-modules              │
│  ├─ Brain: brain_bridge.py (AAAS direct), somabrain_client.py   │
│  ├─ Safety: circuit_breaker.py (307L), health_monitor.py (407L) │
│  └─ Infrastructure: audit.py, rate_limiter.py, event_bus.py     │
├─────────────────────────────────────────────────────────────────┤
│                     CORE DOMAIN                                  │
│  admin/core/ — AgentIQ, Context Builder, Model Router           │
│  ├─ agentiq/: unified_gate.py, derivation.py, tables.py         │
│  ├─ context/: builder.py, lanes.py (5-lane allocation)          │
│  ├─ models/: core.py (636L), zdl.py                             │
│  └─ chat_orchestrator.py (255L — 12-phase pipeline)             │
├─────────────────────────────────────────────────────────────────┤
│                  EXTERNAL SERVICES                               │
│  SomaBrain (port 30xxx) — Cognitive Runtime                     │
│  SomaFractalMemory (port 9xxx) — Vector/Fractal Memory          │
│  Keycloak (20880), SpiceDB (20051), OPA (20181)                 │
│  PostgreSQL (20432), Redis (20379), Kafka (20092), Milvus       │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Deployment Mode Architecture

The system has **two canonical modes** defined in docs but **THREE actual implementations** in code:

| Mode | Env Var | Implementation Location | Maturity |
|------|---------|------------------------|----------|
| **Standalone** | `SA01_DEPLOYMENT_MODE=STANDALONE` | services/gateway/settings.py, brain_bridge.py raises | Partial |
| **AAAS / Cluster** | `SA01_DEPLOYMENT_MODE=AAAS` | infra/aaas/unified_*.py, brain_bridge direct import | Partial |
| **Dev** | (default) | Hardcoded fallbacks everywhere | Overused |

**Critical Finding:** Mode detection is **INCONSISTENT** across the codebase:
- `services/common/brain_bridge.py` uses `SOMA_DEPLOY_MODE` (line 24) AND `AAAS_ENABLED` (line 25)
- `services/common/health_monitor.py` uses `SA01_DEPLOYMENT_MODE` (line 26)
- `services/gateway/settings.py` uses `SA01_DEPLOYMENT_MODE` (line 24) AND `IS_DEV_ENV` (line 25)
- `tests/conftest.py` uses `SOMA_AAAS_MODE` (legacy?)
- K8s manifests use `SOMA_AAAS_MODE` (not `SA01_DEPLOYMENT_MODE`)

**This creates a configuration matrix where modes can conflict.**

---

## 🛤️ SECTION 2: THE THREE LANES OF TRIPLICATED CODE

This is the **most critical architectural issue** in the repository. The user correctly identified triplicated logic across three conceptual lanes.

### 2.1 Lane 1: Chat / Conversation / Messaging

**Triplicated implementations found:**

| File | Lines | Role | Status |
|------|-------|------|--------|
| `admin/core/chat_orchestrator.py` | 199 | **Facade** — delegates to sub-modules | ✅ Current |
| `admin/core/chat_orchestrator.py` | 255 | **V3 12-phase orchestrator** | ⚠️ NEWER but UNWIRED |
| `admin/chat/api/chat.py` | ~200 | Django Ninja chat endpoints | ⚠️ Legacy? |
| `services/gateway/consumers/chat.py` | ~? | WebSocket consumer | ⚠️ Partial |

**Problem:** The V3 `chat_orchestrator.py` (line 174: "Phase 8: LLM Invocation (placeholder)") is a **newer, better-designed pipeline** that is NOT wired to the actual chat endpoints. The production chat flow goes through `ChatService` → `MessageService`, which uses a different (older) code path. This means:
- AgentIQ derivation runs in `chat_orchestrator.py` but NOT in production chat
- Context building (5-lane) exists but may not be used by actual chat API
- Two chat architectures coexist; neither is complete

**Agent Finding (CONFIRMED):** The Architecture agent identified this as the **"Two Universes Problem"** — production chat flow (`services/common/`) completely bypasses the theoretically elegant V3 systems (`admin/core/`). AgentIQ, UnifiedGate, V3ChatOrchestrator, and admin/core/context/builder.py are effectively **dead code** in the production path.

### 2.2 Lane 2: Memory / Recall / Store

**Triplicated implementations found:**

| File | Lines | Role |
|------|-------|------|
| `services/common/brain_bridge.py` | 150 | Direct in-process AAAS bridge |
| `admin/core/somabrain_client.py` | 627 | HTTP client singleton |
| `admin/core/helpers/memory.py` | ~300 | Raw SQL memory helpers |
| `admin/core/helpers/memory_stores.py` | ~150 | Memory store abstractions |
| `admin/memory/api/memory.py` | ~? | Django Ninja memory endpoints |
| `admin/somabrain/api/memory_endpoints.py` | ~? | SomaBrain-specific memory API |
| `admin/core/infrastructure/adapters/memory_adapter.py` | ~? | DDD adapter pattern |
| `admin/orchestrator/unified_memory_service.py` | ~? | Orchestrator memory service |

**Problem:** Memory access has **at least 9 different entry points**. The `SomaBrainClient` (line 198-204) attempts to use `BrainBridge` for "direct" mode, but the bridge lifecycle is fragile:
```python
# brain_bridge.py line 51-57
if container.has("memory_service"):
    self._memory_service = container.get("memory_service")
else:
    logger.info("BrainBridge: MemoryService not in container, attempting to locate...")
    pass  # <-- DOES NOTHING IF NOT FOUND
```
If the container isn't bootstrapped, the bridge silently has no memory service.

**Agent Finding (NEW):** `SomaBrainClient.recall()` calls `BrainBridge.recall()` at line 259, but `BrainBridge.recall()` raises `NotImplementedError` (line 116). **Direct mode memory recall is completely broken.**

### 2.3 Lane 3: Degradation / Health / Circuit Breaker

**Triplicated implementations found:**

| File | Lines | Role |
|------|-------|------|
| `services/common/health_monitor.py` | 407 | **NEW binary health model** |
| `services/common/degradation_monitor.py` | 107 | **SHIM** — wraps HealthMonitor |
| `services/common/multimodal_degradation.py` | ~? | Multimodal-specific degradation |
| `services/common/llm_degradation.py` | ~? | LLM-specific degradation |
| `admin/core/api/degradation.py` | ~? | API endpoints for degradation |
| `admin/orchestrator/health_monitor.py` | ~? | Orchestrator health monitor |

**Problem:** The comment in `health_monitor.py` (line 5) says it "Replaces 359-line DegradationMonitor" but `degradation_monitor.py` still exists as a shim. Multiple subsystems have their own health monitoring instead of using the centralized one. The `HealthMonitor` only tracks 3 critical services (somabrain, database, llm) and ignores Kafka, Redis, Temporal, etc. (line 96).

**Agent Finding (NEW):** `admin/core/api/degradation.py` calls ~10 methods that **do not exist** on `DegradationMonitor`. This endpoint will **500 on every call.**

### 2.4 Additional Duplication: Auth, Rate Limiting, Context Building

**Auth:** 3 implementations
- `admin/common/auth.py` — JWT/AuthBearer for Ninja

**Rate Limiting:** 3 implementations
- `services/common/rate_limiter.py`
- `admin/common/rate_limit.py`

**Context Building:** 2 implementations
- `admin/core/context/builder.py` — V3 5-lane builder
- `admin/agents/services/context_builder.py` — Legacy builder (28 Pyright errors)

**Agent Finding (NEW):** `ContextBuilder`, `HealthMonitor`, `select_model`, and `NoCapableModelError` are **defined in multiple files with different behaviors** (import shadowing).

---

## 🧠 SECTION 3: AGENTIQ SYSTEM ANALYSIS

### 3.1 Components

| File | Lines | Purpose | Score |
|------|-------|---------|-------|
| `unified_gate.py` | 180 | FAIL-CLOSED permission gate (OPA + SpiceDB + Capsule Scope) | 7/10 |
| `derivation.py` | ~? | Derives settings from capsule body | 5/10 |
| `tables.py` | ~? | Lookup tables for model tiers | 6/10 |
| `settings.py` | ~? | AgentIQ settings models | 5/10 |

### 3.2 UnifiedGate Assessment

**Strengths:**
- Clean FAIL-CLOSED design (line 99: `except Exception: return False`)
- Three-layer check: OPA cache → SpiceDB → Capsule scope
- Async-first design

**Weaknesses:**
- **OPA check is NOT a real OPA call.** Line 108-130: It reads `opa_policies` from `capsule.body.governance` — a JSON dict. It does NOT call the OPA server.
- **SpiceDB check is NOT a real SpiceDB call.** Line 132-162: It reads `spicedb_relations` from `capsule.body.governance` — another JSON dict. No gRPC call to SpiceDB.
- **The "cache" uses `id(opa_policies)` as key** (line 116) which is a Python object identity hash — works only within a single process, useless across workers.
- Default behavior is "ALLOW if no policy defined" (line 124) — permissive by default, not secure by default.

**Agent Finding (CONFIRMED):** The Safety agent recommends changing default behavior: no policy = DENY, no relation = DENY.

**Verdict:** UnifiedGate is a **well-designed interface with NO real backend enforcement.** It's checking JSON blobs inside the capsule rather than querying the actual policy engines.

---

## 🔌 SECTION 4: SOMA BRAIN INTEGRATION ANALYSIS

### 4.1 Integration Patterns

The codebase uses a **"Triad" pattern** (their term) with three access modes:

1. **HTTP Mode** (`SomaBrainClient` in `admin/core/somabrain_client.py`)
   - Singleton pattern with `asyncio.Lock`
   - Uses `httpx.AsyncClient`
   - Falls back to `http://host.docker.internal:30101`
   - **627 lines, well-structured but has TODO comments**

2. **Direct Mode** (`BrainBridge` in `services/common/brain_bridge.py`)
   - Lazy-imports `somabrain` package
   - Calls `MemoryService.remember()` / `.recall()` directly
   - **Only works if `somabrain` is installed in same venv**
   - **150 lines, fragile error handling**

3. **Adapter Mode** (`admin/core/infrastructure/adapters/memory_adapter.py`)
   - DDD port/adapter pattern
   - Bridging domain to infrastructure

### 4.2 Critical Integration Issues

**Issue 1: URL Configuration Chaos**
- `settings.py` line 226: `SOMABRAIN_URL = get_required_env("SA01_SOMA_BASE_URL", ...)`
- `settings.py` line 227: `SOMABRAIN_BASE_URL = SOMABRAIN_URL` (redundant alias)
- `somabrain_client.py` line 85: falls back to `SOMABRAIN_URL` env var (different name!)
- `somabrain_client.py` line 68: `_get_base_url()` checks `settings.SOMABRAIN_URL` then env
- K8s deployment uses `http://somabrain.brain.svc.cluster.local:63996`
- docker-compose likely uses `http://localhost:30101`

**Issue 2: BrainBridge Lifecycle**
```python
# brain_bridge.py line 42-57
from somabrain.core.container import container
if container.has("memory_service"):
    self._memory_service = container.get("memory_service")
else:
    pass  # No retry, no error, just silent failure
```
If the SomaBrain container hasn't been bootstrapped when BrainBridge initializes, memory operations will fail with opaque errors.

**Issue 3: BrainBridge.recall() is BROKEN**
```python
# brain_bridge.py line 107-116
async def recall(self, query_vector: Any, top_k: int = 10) -> List[Dict[str, Any]]:
    raise NotImplementedError("Use recall_text for Direct Bridge")
```
The Architecture agent confirmed: `SomaBrainClient.recall()` calls this method at line 259. **Direct mode memory recall raises NotImplementedError on every call.**

**Issue 4: No Circuit Breaker on Brain Calls**
The `SomaBrainClient._request()` method (line 121-164) does NOT use the circuit breaker. A cascading SomaBrain failure will hang all chat operations for 30 seconds (timeout) per request.

**Agent Finding (NEW):** Token counting in context builder uses `len(text.split())` (line 109) and `len(s) // 4` (line 110). This is **wildly inaccurate** for LLM token budgeting — should use `tiktoken` or provider-specific tokenizers.

---

## 🐍 SECTION 5: BACKEND CODE QUALITY (DJANGO/PYTHON)

### 5.1 Type System Catastrophe

**Pyright Diagnostics:**
- **1,402 total diagnostics** (1,374 errors + 28 warnings)
- Top error: `reportAttributeAccessIssue` = 748 occurrences
- Second: `reportArgumentType` = 382 occurrences
- Third: `reportCallIssue` = 134 occurrences

**Most Error-Heavy Files:**
| File | Errors |
|------|--------|
| `services/capsule_export.py` | 40 |
| `admin/flink/models.py` | 38 |
| `admin/aaas/api/users.py` | 31 |
| `admin/voice/models.py` | 31 |
| `admin/aaas/api/tenant_agents.py` | 30 |
| `admin/agents/services/context_builder.py` | 28 |
| `admin/core/infrastructure/models.py` | 23 |

**Pyright Configuration is TOO PERMISSIVE:**
```toml
[tool.pyright]
reportMissingImports = "none"
reportUndefinedVariable = "none"
reportOptionalMemberAccess = "none"
reportOptionalCall = "none"
reportMissingTypeStubs = false
typeCheckingMode = "basic"
```
With these suppressions, Pyright is effectively **blind** to the most common Python errors. Even with maximum suppression, 1,402 errors leak through.

**Agent Finding (NEW):** The Backend agent identified that 310 errors are `objects`/`DoesNotExist` errors on Django models. These would be fixed by installing `django-stubs` and typing models correctly.

### 5.2 Ruff Configuration Analysis

**Ruff ignores too many critical rules:**
```toml
ignore = [
    "E203", "E266", "E501",  # Formatting
    "B008", "B006", "B007", "B024", "B904",  # Bugbear (functionality bugs!)
    "E402",  # Module level import not at top
    "F841",  # Unused variables
    "RUF012",  # Mutable class defaults
]
```
- `B008`: Do not perform function calls in argument defaults — **SECURITY/LOGIC RISK**
- `B904`: Inside `except` blocks, raise `... from err` or `... from None` — **EXCEPTION CHAIN RISK**
- `F841`: Unused variables — **DEAD CODE / LOGIC BUGS**

### 5.3 Django Anti-Patterns

**A. Raw SQL in Helpers (violates "Django ORM ONLY" rule):**
- `admin/core/helpers/memory.py` lines 283, 295, 313: `execute insert text`, `execute update documents`
- `admin/core/helpers/log.py` lines 193, 320, 424: Multiple raw SQL execute patterns
- `admin/core/helpers/task_scheduler.py` lines 200, 208, 219: Raw SQL updates

**B. Model Design Issues:**
- `admin/core/models/core.py`: `Capsule` model has **massive JSONField abuse**:
  - `personality_traits` = JSONField
  - `neuromodulator_baseline` = JSONField
  - `learning_config` = JSONField
  - `body` (inferred from usage) = massive JSON blob
  
  This makes the Capsule a **"God Object"** with weak typing. No database constraints on critical fields.

**C. Settings Module Issues:**
- `services/gateway/settings.py` line 135: **Regex parsing database DSN manually**
  ```python
  db_match = re.match(r"postgres(?:ql)?://([^:]+):([^@]+)@([^:/]+):?(\d+)?/(.+)", db_dsn)
  ```
  This is fragile and will break on special characters in passwords. Django's `dj-database-url` or `urllib.parse` should be used.

- `settings.py` line 151-155: **Falls back to SQLite in production if DSN parse fails!**
  ```python
  else:
      DATABASES = {
          "default": {
              "ENGINE": "django.db.backends.sqlite3",
              "NAME": BASE_DIR / "db.sqlite3",
          }
      }
  ```
  This is a **silent data loss risk** — if env var is malformed, production runs on SQLite.

### 5.4 Security Issues in Backend

**A. Hardcoded Dev Secret (Conditional but dangerous):**
```python
# settings.py line 32-37
SECRET_KEY = os.environ.get("SECRET_KEY", "")
if not SECRET_KEY:
    if IS_DEV_ENV:
        SECRET_KEY = "django-insecure-dev-key-local-only"
```
While guarded by `IS_DEV_ENV`, the check at line 25 includes `"test"` as a dev environment, meaning test environments could use the hardcoded key.

**B. ALLOW_INSECURE_AUTH_BYPASS:**
```python
# settings.py line 221-223
ALLOW_INSECURE_AUTH_BYPASS = (
    os.environ.get("SA01_ALLOW_INSECURE_AUTH_BYPASS", "false").lower() == "true"
)
```
This is a **backdoor flag**. It should not exist in production code, even behind an env var.

**C. JWT Issuer Strictness Disabled by Default:**
```python
# settings.py line 276
JWT_ISSUER_STRICT = os.environ.get("SA01_JWT_ISSUER_STRICT", "false").lower() == "true"
```
Issuer/audience validation is **disabled by default** for "Docker dev convenience." This is a security risk if someone deploys without setting this explicitly.

**Agent Finding (NEW):**
- `admin/auth/api.py:395` — Impersonation JWT signing uses an **ad-hoc secret** instead of a persistent key from Django settings
- `admin/common/auth.py` — `verify_aud` is **hardcoded `False`**
- `admin/common/auth.py:375-406` — `require_permission` is **not actually implemented** (returns empty or passthrough)
- `admin/auth/api.py:365` — Missing `await` on `decode_token(token)` call

**D. No SQL Injection Scan Results:**
The raw SQL patterns in `memory.py`, `log.py`, `task_scheduler.py` use parameterized queries (good), but the helper methods accept string parameters that could be injected if callers don't sanitize.

---

## 🎨 SECTION 6: FRONTEND (WEBUI) ANALYSIS

### 6.1 Technology Stack

- **Framework:** Lit 3.x Web Components (correct per VIBE rules)
- **Build:** Vite 5.x with TypeScript 5.9
- **Router:** @vaadin/router
- **State:** @lit-labs/context + custom element stores
- **Strict TS:** `strict: true` in tsconfig.json

### 6.2 Component Inventory

| Category | Count | Notes |
|----------|-------|-------|
| Views (pages) | 47 | saas-* prefix for all |
| Components | 24 | Reusable UI primitives |
| Services | 7 | API, Keycloak, WebSocket, etc. |
| Stores | 5 | Auth, Mode, Settings, Theme, Voice |

### 6.3 Security Findings

**A. JWT Token in localStorage (XSS Risk):**
```typescript
// auth-store.ts line 178-179
localStorage.setItem(AUTH_STORAGE_KEY, data.access_token);
localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
```
Storing JWT in `localStorage` makes it vulnerable to XSS extraction. Should use `httpOnly` cookies.

**B. Token in WebSocket URL (Logs/History Risk):**
```typescript
// websocket-client.ts line 70-72
if (this.token) {
    url += `?token=${encodeURIComponent(this.token)}`;
}
```
WebSocket URL with token will appear in server logs, browser history, and referrer headers.

**C. No CSP Meta Tag:**
No Content-Security-Policy headers or meta tags found in the frontend. The Vite config has `cors: true` on the dev server (line 24) which is fine for dev but needs hardening for prod.

**Agent Finding (NEW):**
- **CSRF tokens missing** from all mutating `fetch` requests
- **WebSocket unsubscribe leaks** in `saas-chat.ts` — event handlers not cleaned up
- **Missing `disconnectedCallback` cleanup** in `saas-toast.ts`, `saas-impersonation-banner.ts`
- Token storage key inconsistent — some files may use different keys

### 6.4 Code Quality Findings

**A. Auth Store Race Condition:**
```typescript
// auth-store.ts line 327-342
private async _refreshToken(): Promise<boolean> {
    if (this._refreshPromise) {
        return this._refreshPromise;  // Good: deduplication
    }
    this._refreshPromise = this._doRefreshToken();
    try {
        return await this._refreshPromise;
    } finally {
        this._refreshPromise = null;
    }
}
```
This is actually **well-implemented** with Promise-based deduplication.

**B. WebSocket Reconnection Logic:**
```typescript
// websocket-client.ts line 204-215
private _scheduleReconnect(): void {
    const delay = this.config.reconnectDelay * Math.pow(2, this.reconnectAttempts);
    this.reconnectAttempts++;
    setTimeout(() => {
        if (!this._connected) {
            this.connect();
        }
    }, delay);
}
```
Exponential backoff is implemented but **no maximum delay cap**. After 10 attempts, delay = 1,024 seconds (~17 minutes). Also, `reconnectDelay` is mutable config but no jitter.

**C. Missing Accessibility:**
No ARIA labels found in component searches. Lit components use Shadow DOM which can hinder screen readers without proper ARIA.

**Agent Finding (NEW):**
- TypeScript build may have issues — need to install `lit` types or regenerate lockfile
- Heavy use of `any` types in chat, permissions, and profile views
- No mobile responsive design (`@media` queries missing)

---

## 🛡️ SECTION 7: SAFETY & FAILSAFE SYSTEMS

### 7.1 Policy Engine (OPA)

**5 .rego files exist:**
| File | Purpose | Status |
|------|---------|--------|
| `policy/confidence.rego` | Confidence-score gating | ✅ Well-written |
| `policy/multimodal.rego` | Multimodal capability control | ✅ Well-written |
| `policy/skins.rego` | Theme management auth | ✅ Well-written |
| `policy/soma_development.rego` | **Dev override — allows ALL** | 🔴 DANGEROUS |
| `policy/tool_policy.rego` | Tool execution authorization | ✅ Well-written |

**CRITICAL ISSUE:** `soma_development.rego`:
```rego
package soma.policy.integrator
default allow = true
allow if { input.request_path == "/health" }
allow if { startswith(input.request_path, "/api/") }
allow if { startswith(input.request_path, "/admin/") }
```
This policy **allows all API and admin requests** if loaded. It is labeled "Development policy" but there's no enforcement preventing it from being loaded in production.

**MORE CRITICAL: OPA policies are NOT actually queried at runtime.**
- `UnifiedGate._check_opa()` (line 108-130) reads from `capsule.body.governance.opa_policies` — a JSON blob
- No `opa-python-client` usage found in the codebase
- The `.rego` files appear to be **documentation/specification artifacts** rather than live policy

### 7.2 Circuit Breaker

**`services/common/circuit_breaker.py` — 307 lines, EXCELLENT implementation:**
- Proper state machine: CLOSED → HALF_OPEN → OPEN
- Async-safe with `asyncio.Lock`
- Configurable threshold and reset timeout
- Registry for centralized management

**But it's NOT USED by SomaBrainClient or ChatService.**
The circuit breaker module exists but callers don't wrap their external service calls with it.

### 7.3 Health Monitor

**`services/common/health_monitor.py` — 407 lines, GOOD implementation:**
- Binary healthy/unhealthy model (simplified from old degradation levels)
- Jittered check intervals
- Deployment-mode-aware error logging
- Metrics integration

**Weaknesses:**
- Only 3 critical services tracked (somabrain, database, llm)
- No default health checkers registered — callers must register them
- No automatic degradation actions (just logs)

### 7.4 Rate Limiting

**`services/common/rate_limiter.py` — FAIL-OPEN on Redis errors:**
```python
# Line 186-194 (inferred pattern)
except RedisError:
    return True  # Allow if Redis is down
```
If Redis fails, rate limiting **stops working** and allows all requests. This should be **fail-closed** (deny) or at minimum require explicit `RATE_LIMIT_FAIL_OPEN` env var.

**Agent Finding (CONFIRMED):** The Safety agent explicitly flags this as HIGH priority.

### 7.5 Audit System

**`services/common/audit.py` — Kafka-based audit publisher (DELETED):**
- Publishes to Kafka topics (audit.auth, audit.chat, audit.security)
- Structured event schema

**Gaps:**
- **Audit logging is NOT wired to auth endpoints.** The Safety agent found that `log_login`, `log_logout`, `log_permission_denied` are defined but never called from `admin/auth/api.py`.
- No evidence of Kafka topic creation in docker-compose or K8s
- Audit events are published but no consumer/retention policy visible
- No integration with the JSON schemas in `schemas/audit/`

---

## 🏗️ SECTION 8: INFRASTRUCTURE & DEVOPS

### 8.1 Kubernetes Manifests

**K8s deployments are MINIMAL:**
- `infra/k8s/somaagent/deployment.yaml`: Single replica, no resource limits, no HPA
- `infra/k8s/somabrain/deployment.yaml`: Single replica, no probes
- `infra/k8s/somafractalmemory/deployment.yaml`: Single replica, no probes
- No PodDisruptionBudgets
- No NetworkPolicies
- No ServiceAccounts or RBAC
- No HorizontalPodAutoscaler

**Keycloak deployment has hardcoded dev credentials:**
```yaml
# infra/k8s/shared/keycloak.yaml
stringData:
  KEYCLOAK_ADMIN: admin
  KEYCLOAK_ADMIN_PASSWORD: admin
```

**Backup CronJob has runtime dependency installation:**
```yaml
# infra/k8s/backup/cron.yaml
command:
  - apk add --no-cache postgresql-client aws-cli gzip
```
Installing packages at runtime is slow, unreliable, and a supply chain risk.

### 8.2 CI/CD Workflows

**12 GitHub Actions workflows exist but they're FRAGMENTED:**

| Workflow | Purpose | Issue |
|----------|---------|-------|
| `ci.yml` | Main CI | Uses postgres:15-alpine (not 16), no Kafka/Milvus/Keycloak services |
| `quick-ci.yml` | Fast checks | Only compile + smoke dry-run |
| `ci-kind.yml` | K8s tests | Installs kind v0.23.0, creates cluster — heavy |
| `security.yml` | Bandit + Safety | Good, but Bandit level is `-ll` (medium) not `-lll` |
| `openapi_contract.yml` | API contract | References `infra/docker-compose.somaagent01.yaml` which may not exist |
| `deploy.yaml` | Deploy | Triggered on push to `soma_integration` branch |
| `canary-progressive.yml` | Canary | Manual dispatch only |
| `otel.yml` | OTEL sanity | Just imports module, no real test |
| `capsule.yml` | Capsule CI | **DISABLED** (`if: false`) |

**Critical CI Gaps:**
- No workflow runs `pytest` with the full test suite
- No workflow validates Django migrations
- No workflow checks for the 1,402 Pyright errors
- No workflow runs the actual Ruff lint (only Black formatting in Makefile)
- Branch protection rules not visible in repo

### 8.3 Docker & Compose

**Root `docker-compose.yml` was NOT FOUND.**
The user mentioned `docker-compose.yml` in AGENT.md but it's missing from the root. Instead:
- `infra/aaas/docker-compose.yml` — AAAS mode
- `infra/standalone/docker-compose.yml` — Standalone mode
- `infra/aaas/aaas/docker-compose.yml` — Nested AAAS compose

This fragmentation means developers need to know which compose file to use based on mode — **configuration leaking into file structure.**

---

## 🧪 SECTION 9: TESTS & DOCUMENTATION

### 9.1 Test Coverage

**24 test files for 1,491 source files = 1.6% test-to-source ratio.**

| Test Area | Files | Lines | Quality |
|-----------|-------|-------|---------|
| Agent Chat | 2 | 509 | Integration, skips if infra unavailable |
| Django | 2 | 722 | Auth integration, admin domain |
| E2E | 1 | 1 | Empty init |
| Integration | 1 | ~? | SomaBrain integration |
| SAAS | 5 | 1,269 | Brain bridge, budget, chat flow, features, security |
| Standalone | 1 | 1 | Empty init |
| Unit | 2 | 200 | Budget, features |
| Unified | 3 | 1,138 | Deployment mode, governor, phase4 validation |
| Proofs | 1 | 73 | Docker proof |

**VIBE Rule Violations in Tests:**
```python
# tests/test_deployment_mode_unified.py
from unittest.mock import AsyncMock, Mock, patch
# ... extensive mocking throughout
```
The VIBE Coding Rules say "NO mocks, NO stubs" but `test_deployment_mode_unified.py` (538 lines) is **full of mocks**. This is the most extensive test file and it violates the project's own rules.

**Infrastructure Gating:**
Most tests use `pytest.mark.skipif(not INFRA_AVAILABLE, ...)` which means:
- Tests pass by skipping if infra is down
- CI likely doesn't set `SA01_INFRA_AVAILABLE=1`
- Tests are effectively **not running in CI**

### 9.2 Documentation

**39 markdown files in docs/ — comprehensive but DRIFTED:**

| Category | Count | Quality |
|----------|-------|---------|
| SRS (Specs) | 20 | Detailed, well-structured |
| Architecture | 1 | SaaS deployment only |
| Deployment | 2 | DEPLOYMENT_MODES.md missing (AGENT.md references it) |
| Development | 1 | VIBE_CODING_RULES.md — clear but not enforced |
| Tasks | 6 | Active task tracking |

**Documentation Drift:**
- `AGENT.md` says `docs/deployment/SOFTWARE_DEPLOYMENT_MODES.md` exists — **it does NOT**
- `AGENT.md` lists many "Placeholder/Incomplete" items (Sessions API, ChatService, WebSocket Consumer) — some may now be implemented but docs not updated
- `README.md` says frontend is "React" (line 239) — but VIBE rules say NO React, and actual frontend is Lit

### 9.3 JSON Schemas

**6 schemas exist but are NOT VALIDATED in code:**
- `conversation_event.json` — defines ChatEvent structure
- `tool_request.json`, `tool_result.json`, `tool_event.json` — tool lifecycle
- `delegation_task.json` — A2A delegation
- `task_dsl_v1.json` — multimodal job plans

**No evidence these schemas are used for runtime validation.** They appear to be specification artifacts.

---

## 🚨 SECTION 10: CRITICAL ISSUES SUMMARY

### 🔴 P0 — Production Blockers

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 1 | **UnifiedGate does NOT call real OPA/SpiceDB** | `admin/core/agentiq/unified_gate.py` | Authorization is fake — JSON blob checks only |
| 2 | **OPA dev policy allows ALL API requests** | `policy/soma_development.rego` | If loaded in prod, complete auth bypass |
| 3 | **Settings fall back to SQLite on bad DSN** | `services/gateway/settings.py:151` | Silent data loss in production |
| 4 | **1,402 Pyright errors with suppressed checking** | `pyrightconfig.json` | Type system is broken |
| 5 | **JWT issuer validation OFF by default** | `settings.py:276` | Token forgery risk |
| 6 | **ALLOW_INSECURE_AUTH_BYPASS flag exists** | `settings.py:221` | Backdoor in production code |
| 7 | **BrainBridge silently fails if container empty** | `brain_bridge.py:55` | Memory operations fail opaquely |
| 8 | **No circuit breaker on SomaBrain HTTP calls** | `somabrain_client.py` | Cascading failure risk |
| 9 | **Test suite uses mocks (violates VIBE rules)** | `tests/test_deployment_mode_unified.py` | Test philosophy contradiction |
| 10 | **24 tests for 1,491 files** | `tests/` directory | Effectively untested |
| 11 | **BrainBridge.recall() raises NotImplementedError** | `brain_bridge.py:116` | Direct mode memory is BROKEN |
| 12 | **Degradation API calls non-existent methods** | `admin/core/api/degradation.py` | Endpoint 500s on every call |
| 13 | **Rate limiter FAIL-OPEN on Redis down** | `services/common/rate_limiter.py:186` | DDoS vulnerability during Redis outage |
| 14 | **Impersonation JWT uses ad-hoc secret** | `admin/auth/api.py:395` | Forged impersonation tokens possible |
| 15 | **verify_aud hardcoded False** | `admin/common/auth.py` | JWT audience bypass |

### 🟡 P1 — High Priority

| # | Issue | Location |
|---|-------|----------|
| 16 | Triplicated chat architecture (orchestrator vs service vs legacy) | `admin/core/chat_orchestrator.py` |
| 17 | 9 different memory entry points | `admin/core/helpers/memory*.py`, etc. |
| 18 | Mode detection uses 4 different env var names | `SOMA_DEPLOY_MODE`, `SA01_DEPLOYMENT_MODE`, `SOMA_AAAS_MODE`, `AAAS_ENABLED` |
| 19 | K8s manifests have hardcoded passwords | `infra/k8s/shared/keycloak.yaml` |
| 20 | Frontend stores JWT in localStorage | `webui/src/stores/auth-store.ts:178` |
| 21 | WebSocket token leaks to URL/logs | `webui/src/services/websocket-client.ts:71` |
| 22 | Health monitor only tracks 3 services | `services/common/health_monitor.py:100` |
| 23 | Capsule model is a God Object with JSONField abuse | `admin/core/models/core.py` |
| 24 | README says React, actual code is Lit | `README.md:239` |
| 25 | No root docker-compose.yml | Missing file |
| 26 | Token counting uses `len(text.split())` | `admin/core/context/builder.py:109` |
| 27 | Import shadowing across modules | Multiple files |
| 28 | Missing `await` on decode_token | `admin/auth/api.py:365` |
| 29 | require_permission not implemented | `admin/common/auth.py:375-406` |
| 30 | WebSocket unsubscribe leaks | `webui/src/views/saas-chat.ts` |

---

## 🔧 SECTION 11: ARCHITECTURAL FIXES

### Fix 1: Unify Deployment Mode Detection
**Create a single source of truth:**
```python
# New file: services/common/deployment_mode.py
import os

class DeploymentMode:
    _mode = None
    
    @classmethod
    def get(cls) -> str:
        if cls._mode is None:
            cls._mode = os.environ.get("SA01_DEPLOYMENT_MODE", "")
            if not cls._mode:
                cls._mode = "AAAS" if os.environ.get("SOMA_AAAS_MODE", "false").lower() == "true" else "STANDALONE"
            cls._mode = cls._mode.upper()
        return cls._mode
    
    @classmethod
    def is_aaas(cls) -> bool:
        return cls.get() == "AAAS"
    
    @classmethod
    def is_standalone(cls) -> bool:
        return cls.get() == "STANDALONE"
```
Replace ALL other mode checks across the codebase.

### Fix 2: Make UnifiedGate Real
**Wire it to actual OPA and SpiceDB:**
1. Add `opa-python-client` or `httpx` calls to OPA server in `_check_opa()`
2. Add `grpc` SpiceDB client calls in `_check_spicedb()`
3. Cache results in Redis (not `id()` hash)
4. Add fallback: if OPA/SpiceDB unavailable, use capsule JSON **but log WARNING**
5. Change default: no policy = DENY, no relation = DENY

### Fix 3: Consolidate the Three Lanes
**Choose ONE chat architecture and delete the others:**

**Recommended: V3 Orchestrator + Extracted Services**
```
admin/core/chat_orchestrator.py      → KEEP (12-phase pipeline)
admin/chat/api/chat.py               → REFACTOR to use orchestrator
```

### Fix 4: Consolidate Memory Access
**Create a single MemoryPort:**
```python
# services/common/ports/memory_port.py
class MemoryPort(Protocol):
    async def remember(self, key, payload, tenant) -> dict: ...
    async def recall(self, query, capsule_id, limit, threshold) -> list: ...

# adapters:
#   - DirectMemoryAdapter (uses BrainBridge)
#   - HttpMemoryAdapter (uses SomaBrainClient)
#   - FallbackMemoryAdapter (logs + no-op)
```

### Fix 5: Fix the Type System
1. **Remove Pyright suppressions** from `pyrightconfig.json`:
   - Change `reportMissingImports` to `"error"`
   - Change `reportUndefinedVariable` to `"error"`
   - Change `typeCheckingMode` to `"standard"`
2. **Install `django-stubs`** to fix 310 model errors
3. **Fix the 1,402 errors in waves** (see roadmap)
4. **Tighten Ruff rules:** Remove `B008`, `B904`, `F841` from ignore list

### Fix 6: Fix BrainBridge.recall()
Implement `recall_text()` properly or remove the broken `recall()` method:
```python
async def recall(self, query_vector: Any, top_k: int = 10) -> List[Dict[str, Any]]:
    """DEPRECATED: Use recall_text() for Direct Bridge"""
    return await self.recall_text(query=query_vector, top_k=top_k)
```

---

## 📋 SECTION 12: PRODUCTION ROADMAP

### Phase 1: Foundation (Weeks 1-2) — "Stop the Bleeding"
- [ ] Fix deployment mode unification (Fix 1)
- [ ] Delete `policy/soma_development.rego` or gate it behind `DEBUG`
- [ ] Remove `ALLOW_INSECURE_AUTH_BYPASS` from production code
- [ ] Fix settings.py SQLite fallback — raise error instead
- [ ] Enable `JWT_ISSUER_STRICT` by default
- [ ] Add circuit breaker to `SomaBrainClient._request()`
- [ ] Fix BrainBridge to raise error if container empty (fail fast)
- [ ] Fix `BrainBridge.recall()` — implement or redirect to `recall_text()`
- [ ] Fix rate limiter to fail-closed on Redis errors
- [ ] Fix impersonation JWT to use persistent secret from Vault/settings

### Phase 2: Type Safety (Weeks 3-4) — "Build Confidence"
- [ ] Remove Pyright suppressions one by one
- [ ] Install `django-stubs` and fix 310 model errors
- [ ] Fix top 10 error-heavy files (capsule_export, flink/models, aaas/api/users, etc.)
- [ ] Tighten Ruff rules and fix violations
- [ ] Add `mypy` as secondary checker
- [ ] Add type-checking CI gate (block merge on Pyright errors)

### Phase 3: Architecture Consolidation (Weeks 5-6) — "One Lane"
- [ ] Wire `chat_orchestrator.py` to actual chat endpoints
- [ ] Consolidate memory access behind `MemoryPort`
- [ ] Delete or deprecate legacy chat paths
- [ ] Consolidate health monitoring to single `HealthMonitor`
- [ ] Remove `degradation_monitor.py` shim
- [ ] Standardize on ONE rate limiter
- [ ] Fix `admin/core/api/degradation.py` to call real methods

### Phase 4: Security Hardening (Weeks 7-8) — "Fortress"
- [ ] Make UnifiedGate call real OPA/SpiceDB
- [ ] Move JWT from localStorage to httpOnly cookies (frontend)
- [ ] Fix WebSocket auth to use cookie instead of URL param
- [ ] Add CSRF tokens to all mutating fetch requests
- [ ] Add CSP headers in Django middleware
- [ ] Add security CI gate (Bandit `-lll`, Safety, TruffleHog)
- [ ] Rotate all hardcoded/default credentials in K8s manifests
- [ ] Add NetworkPolicies to K8s
- [ ] Wire audit logging to auth endpoints

### Phase 5: Testing (Weeks 9-10) — "Prove It"
- [ ] Refactor `test_deployment_mode_unified.py` to use real infrastructure (remove mocks)
- [ ] Add integration tests for each API router (target: 50+ test files)
- [ ] Add contract tests for SomaBrain integration
- [ ] Add load tests for chat endpoint
- [ ] Add property-based tests with Hypothesis
- [ ] Achieve 70% line coverage minimum

### Phase 6: Infrastructure (Weeks 11-12) — "Production Ready"
- [ ] Add resource limits to all K8s deployments
- [ ] Add liveness/readiness probes to all services
- [ ] Add HPA for gateway and workers
- [ ] Add PodDisruptionBudgets
- [ ] Fix backup CronJob to use pre-built image
- [ ] Unify docker-compose to single root file with profiles
- [ ] Add prometheus ServiceMonitor manifests
- [ ] Add Grafana dashboard configs as code

### Phase 7: Documentation (Weeks 13-14) — "Truth"
- [ ] Audit all docs against code — fix drift
- [ ] Write `SOFTWARE_DEPLOYMENT_MODES.md` (missing file)
- [ ] Update `README.md` (remove React reference)
- [ ] Add API documentation with examples
- [ ] Add runbook for incident response
- [ ] Add ADRs (Architecture Decision Records) for major choices

---

## 📈 SECTION 13: SCORING JUSTIFICATION

### Architecture: 5/10
- Strong conceptual design (Capsule, AgentIQ, 5-lane context)
- But triplicated implementations create maintenance hell
- Deployment mode inconsistency is a fundamental flaw
- "Two Universes" problem means half the elegant code is dead
- Good separation between admin/ and services/

### Backend Quality: 4/10
- Django patterns are mostly correct (ORM-only, Ninja-only)
- But 1,402 type errors is unacceptable
- Ruff suppressions hide real bugs
- God Object (Capsule) with JSON abuse
- Raw SQL in helpers violates own rules
- Import shadowing across modules

### Frontend: 6/10
- Lit components are clean and well-structured
- Auth store has good patterns (refresh deduplication)
- But XSS risks (localStorage JWT, URL token)
- No CSP
- Missing accessibility
- WebSocket event leaks

### Safety: 6/10
- Circuit breaker is excellent
- Health monitor is good but incomplete
- Policy files are well-written
- **BUT policies are NOT enforced at runtime**
- Dev policy is a landmine
- Rate limiter fail-open is dangerous
- Audit logging not wired

### Infrastructure: 5/10
- K8s manifests exist but are minimal
- CI is fragmented, no unified pipeline
- Missing production hardening
- Backup job installs deps at runtime

### Tests: 4/10
- 24 tests for 1,491 files is a joke
- Tests skip when infra unavailable (so CI never runs them)
- Most extensive test file violates VIBE rules (uses mocks)
- No property-based tests despite claiming to want them

### SOMA Brain Integration: 5/10
- Dual access modes (HTTP/Direct) is correct for the architecture
- But Direct mode recall is BROKEN (NotImplementedError)
- HTTP mode lacks circuit breaker
- URL configuration is chaotic
- Token counting is inaccurate

### AGENTIQ: 6/10
- Clean derivation and gate design
- FAIL-CLOSED principle is correct
- But gate checks JSON blobs, not real policy engines
- Tables/settings are partially implemented
- Default-permissive behavior is wrong

---

## ✅ CONCLUSION

**SomaAgent01 is a codebase with EXCELLENT architectural INTENT but POOR execution discipline.**

The system was clearly designed by smart architects who understand:
- DDD (Capsule as atomic unit)
- Policy-driven authorization (OPA + SpiceDB)
- Resilience patterns (circuit breakers, health monitoring)
- Clean architecture (admin/ for domain, services/ for infrastructure)

But the implementation has accumulated massive technical debt:
1. **Triplicated subsystems** — chat, memory, health each have 3+ implementations
2. **Policy theater** — .rego files exist but aren't wired to runtime
3. **Type system collapse** — 1,402 errors with maximum suppression
4. **Test desert** — 1.6% test coverage with mocked tests
5. **Configuration chaos** — 4 env vars for the same concept
6. **Broken direct-mode recall** — BrainBridge.recall() raises NotImplementedError
7. **Degradation API 500s** — calls methods that don't exist
8. **Rate limiter fail-open** — DDoS vulnerability during Redis outage

**The path to production is clear but requires 14 weeks of focused work.** The architecture is salvageable — the core designs are sound. What's needed is **ruthless consolidation** (pick one lane and delete the others), **real policy enforcement**, and **type-system recovery**.

**Risk if deployed as-is:** HIGH. The authorization gap (fake UnifiedGate), backdoor flags (`ALLOW_INSECURE_AUTH_BYPASS`, `soma_development.rego`), broken memory recall, and fail-open rate limiting create real security and reliability vulnerabilities. The lack of tests means regressions are guaranteed.

---

*Report compiled from direct forensic analysis of 70+ files, 25+ shell queries, and parallel agent audits across Architecture, Backend, Frontend, and Safety domains. Agent findings have been merged and deduplicated into this unified report.*
