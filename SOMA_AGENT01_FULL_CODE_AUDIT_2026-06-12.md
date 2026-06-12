> **NOTE TO USER:** This is a code-level audit. No code was changed; documentation was updated to remove references to deleted/legacy modules.

# SomaAgent01 — Full Code Audit & Documentation Contrast

**Date:** 2026-06-12  
**Scope:** Full codebase audit (code, not just docs); contrast with `AGENT.md`, `README.md`, `DEPLOYMENT_PLAN.md`, SRS files, and historical audit reports.  
**Method:** 6 specialized forensic agents inspected actual source files, plus manual verification.

---

## Executive Scorecard

| Domain | Grade | Status |
|--------|-------|--------|
| Architecture | C+ | V3 orchestrator is real and wired; worker bypasses it; many services are stubs |
| Authentication | C | Backdoors removed; JWT solid; RBAC endpoints lie about permissions; frontend stores token in localStorage |
| Authorization | C | `UnifiedGate` makes real OPA/SpiceDB calls; RBAC API endpoints are stubs returning `allowed: true` |
| SomaBrain / Memory Integration | D+ | Shape exists but runtime is miswired; packages missing; mocks incompatible; MemoryPort unused |
| Web UI / UX | D | Cannot chat: no agent selector, wrong WebSocket URL, agent list returns empty, workspace chat is mock |
| Production Readiness | D | App cannot start due to monkeypatch; migrations out of sync; K8s incomplete; env templates missing vars |
| Database / Models | D | Migrations out of sync; raw SQL in health checks; `asyncpg` still declared; docs inventory stale |
| Documentation Accuracy | D | Major drift corrected in this session; historical reports now carry snapshot warnings |

**Overall: D+ — Pre-production; cannot be deployed or used for chat without concentrated fixes.**

---

## 1. Architecture & Chat Pipeline

### What the code actually shows

- **55 admin apps** exist; **50** expose `api.py`; **5** are missing/empty (`apikeys`, `secrets`, `billing` has only webhooks, `features` not mounted, `llm` no router).
- **V3 orchestrator** (`admin/core/chat_orchestrator.py`) is actively used by:
  - `admin/chat/api/chat.py` (REST)
  - `services/gateway/consumers/chat.py` (WebSocket)
  - `services/common/chat_service.py` (test wrapper)
- **Conversation worker** (`services/conversation_worker/main.py`) uses a **separate pipeline** via `ProcessMessageUseCase` + `GenerateResponseUseCase`; it never imports V3.
- `admin/core/application/__init__.py` imports `dto`, which does **not exist**, breaking package-level imports.
- `services/common/chat/` modules are **deleted**; docs references removed.
- `services/common/model_router.py` is **deleted**; only `admin/core/model_router.py` remains.
- Many `services/common/*` modules are stubs (`health_monitor`, `event_bus`, `publisher`, `model_profiles`, several stores).

### Documentation mismatches fixed
- Removed references to `services/common/chat/*` from `violations.md`, `docs/reports/DEEP_REPO_ANALYSIS.md` (via snapshot note), `docs/tasks/AGENT_HANDOFF_SOMAAGENT01.md`.
- Updated `AGENT.md` to describe the real 2-pipeline state.

---

## 2. Authentication & Authorization

### Verified fixed in code
- `ALLOW_INSECURE_AUTH_BYPASS` **removed** from production code.
- `DEV_MODE = false` in `webui/src/main.ts`.
- Account lockout implemented (`admin/common/account_lockout.py`).
- PKCE implemented (`admin/common/pkce.py`, `admin/auth/api_oauth.py`).
- `UnifiedGate` makes real OPA/SpiceDB calls.
- Rate limiter is **fail-closed** on Redis errors.

### Still broken
- **RBAC check endpoints return `allowed: true` unconditionally**
  - `admin/permissions/api.py:320-342`
  - `admin/permissions/granular.py:391-422`
- **MFA is non-functional**: all mutating endpoints raise `ServiceUnavailableError`.
- **Password reset/change non-functional**: no persistence; `/change` is unauthenticated and ignores current password.
- **Registration is a no-op**: returns success without creating user.
- **Frontend stores JWT in `localStorage`**, contradicting documented httpOnly-cookie model.
- **`saas-auth-provider` context implemented but never mounted.**
- **`RoleRequired`/`TenantRequired` return `None`**, causing 401 instead of 403.
- **OPA data path mismatch**: client queries `/v1/data/soma/allow`, Rego packages are `soma.policy`, etc.

---

## 3. SomaBrain & Memory Integration

### Verified in code
- `BrainBridge.recall()` is implemented for direct and HTTP modes.
- `MemoryPort` protocol exists but is **not adopted** by production adapters.

### Broken paths
- **`somabrain` and `somafractalmemory` packages are NOT installed** in `.venv`.
- **`BrainBridge` direct mode raises `RuntimeError`** when package missing.
- **Three incompatible HTTP dialects**:
  - `BrainBridge` uses `/api/recall`, `/api/remember`
  - `SomaBrainClient` uses `/memory/remember`, `/memory/recall`, `/v1/context/evaluate`
  - Mocks use `/api/v1/agents/{id}/chat`
- **Mocks are endpoint-incompatible** with production clients.
- **Streaming chat omits SFM fallback** (`admin/core/chat_orchestrator.py:622-628`).
- **`MemoryServiceProtocol` is the accidental production contract**, not `MemoryPort`.
- **`get_memory_service()` uses legacy `SOMA_AAAS_MODE`** instead of canonical `DeploymentMode`.
- **Default URLs wrong**: `SomaBrainClient` falls back to `host.docker.internal:30101`; docs claim `63996`/`9696`.

### Documentation updated
- `docs/srs/SRS-SOMABRAIN-INTEGRATION.md` traceability now points to `aaas/brain.py` and `admin/core/somabrain_client.py`.
- `docs/srs/SRS-CHAT-FLOW-MASTER.md` updated similarly.
- `docs/tasks/TASK-RLM-ENGINE.md` updated to remove `admin/agents/services/brain_bridge.py` reference.

---

## 4. Web UI / UX

### Verdict: cannot chat

1. Login stores token in `localStorage`.
2. `/chat` calls `/agents` → backend **always returns empty array**.
3. No agent selector rendered.
4. WebSocket connects to `/ws/v2/chat` (no `agent_id`) → backend closes with **4004**.
5. `/workspace` uses `saas-chat-workspace`, which returns a hardcoded placeholder.

### Other issues
- `keycloak-service.ts` hardcoded to `localhost:20880`.
- `google-auth-service.ts` hardcoded a real-looking Client ID.
- `saas-auth-provider` dead code.
- Vite dev server does not proxy `/ws/`.

---

## 5. Production Readiness

### Test results
- `pytest tests/unit/`: 14 passed, 6 skipped
- `pytest tests/`: 52 passed, 69 skipped, **4 failed**
  - 2 connection-refused docker proofs
  - 2 `browser-use monkeypatch is not implemented` failures

### Startup blockers
- **`admin.llm.services` cannot be imported** due to `browser_use_monkeypatch.apply()` raising `RuntimeError`.
- **Migrations out of sync** for `admin/aaas` and `admin/core`.

### Deployment issues
- `webui/nginx.conf` proxies to non-existent `somaagent-django:8020`.
- K8s manifests incomplete (missing env vars, secrets, probes, limits).
- Prometheus `/metrics` route missing on gateway.
- Env templates missing `SA01_SOMA_BASE_URL`, `VAULT_ADDR`, `MILVUS_HOST`.

### TODO count
Actual repository count (excluding `.venv`, `node_modules`, `.git`):
- TODO: 60, FIXME: 8, NotImplementedError: 25, XXX: 72, HACK: 8 = **173 total**
- AGENT.md claim of "8,030+ TODO/FIXME" is **false**.

---

## 6. Database / Models

### Migration status
`makemigrations --check --dry-run` wants to create:
- `admin/aaas/migrations/0004_platformconfig_delete_globaldefault_and_more.py`
- `admin/core/migrations/0008_asset_delegationtask_executionrecord_modelprofile_and_more.py`

### Issues
- `GlobalDefault` → `PlatformConfig` rename unresolved.
- `AuditLog` moved from `admin.core` to `admin.aaas` without data migration.
- `admin/core/infrastructure/models.py` models **not registered** in `admin.core.models`.
- `admin/integrations/models.py` app not in `INSTALLED_APPS`.
- Raw SQL in `admin/aaas/api/health.py`, `admin/core/api/health.py`, `admin/core/infrastructure/health_checker.py`.
- `asyncpg` still declared in `pyproject.toml` despite VIBE rule and commit claim.
- `AGENT.md` model inventory updated to match actual models.

---

## 7. Documentation Changes Made

### Canonical docs updated
- `AGENT.md` — OPA/SpiceDB runtime status, rate limiter fail-closed, auth issues fixed, chat architecture corrected to 2 pipelines, BrainBridge.recall() status, data model inventory, gaps updated.
- `README.md` — security issues struck through and marked fixed, limitations table updated, new frontend blockers added.
- `DEPLOYMENT_PLAN.md` — maturity/security scores, broken/missing list, short-term actions marked done, WebUI image added.

### Historical reports preserved with warnings
- `SOMA_AGENT01_COMPREHENSIVE_AUDIT_REPORT.md`
- `VIOLATIONS_FULL_AUDIT_2026-05-28.md`
- `docs/reports/DEEP_REPO_ANALYSIS.md`

### Legacy references removed/updated
- `violations.md` — removed `services/common/chat/*` and `services/common/model_router.py` references.
- `docs/tasks/TASK-RLM-ENGINE.md` — removed `admin/agents/services/brain_bridge.py` reference.
- `docs/tasks/AGENT_HANDOFF_SOMAAGENT01.md` — added historical snapshot warning.
- `docs/srs/SRS-SOMABRAIN-INTEGRATION.md` — traceability updated from `services/common/brain_bridge.py` to `aaas/brain.py` + `admin/core/somabrain_client.py`.
- `docs/srs/SRS-CHAT-FLOW-MASTER.md` — same traceability update.
- `docs/srs/SRS-650-LINE-SOVEREIGNTY.md` — marked `admin/conversations/api.py` decomposition as N/A (deleted).

---

## 8. Top 10 Critical Blockers (All Domains)

1. **`browser_use_monkeypatch` crashes app startup** — chat/LLM path unusable.
2. **Uncommitted Django migrations** — deployments will fail.
3. **RBAC endpoints return `allowed: true` unconditionally** — authorization bypass.
4. **Frontend cannot chat** — no agent selector, wrong WebSocket URL, agent list stubbed empty.
5. **`somabrain`/`somafractalmemory` packages missing** — AAAS direct mode broken.
6. **Frontend stores JWT in `localStorage`** — contradicts security model.
7. **MFA non-functional** — all endpoints fail-closed without persistence.
8. **SomaBrain HTTP dialects incompatible** — clients and mocks don't agree on endpoints.
9. **K8s manifests incomplete** — no probes, secrets, limits, namespaces.
10. **Conversation worker bypasses V3 orchestrator** — two divergent chat pipelines.

---

## 9. What Was NOT Changed

- No Python/TypeScript code was modified.
- No migrations generated.
- No tests run that wrote state.
- Historical audit reports were not rewritten; they were given snapshot warnings.

---

End of audit.
