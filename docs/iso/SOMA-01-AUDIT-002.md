# SOMA-01-AUDIT-002 — Code-Verified Deep Audit Report

## Document Control

| Field | Value |
|---|---|
| Document Title | SomaAgent01 Code-Verified Deep Audit Report |
| Document Identifier | SOMA-01-AUDIT-002 |
| Version | 2.0.0 |
| Date | 2026-06-15 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2026-12-28 |

## Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|

| 2.0.0 | 2026-09-28 | SomaTech Engineering | Brought under ISO document control. Prior status value `Active` is outside the closed set `Draft \| In Review \| Approved \| Obsolete`; normalised to `Draft` — no approver has signed this document. |
| 1.0.0 | 2025-12-30 | SomaTech Engineering | Initial audit |
| 1.1.0 | 2026-06-01 | SomaTech Engineering | Updated findings post-initial remediation |
| 2.0.0 | 2026-06-15 | SomaTech Engineering | Code-verified deep analysis; corrected audit findings; verified fixes with file:line references |

---

## Executive Scorecard

| Domain | Grade | Score | Notes |
|--------|-------|-------|-------|
| Architecture | B- | 70% | Sound dual-mode design; architectural debt in conversation-worker pipeline |
| Security | C+ | 60% | Key controls implemented (fail-closed rate limiter, real OPA/SpiceDB); authorization bypass remains |
| Backend | C | 50% | V3 orchestrator working; migrations out of sync; path dependency |
| Frontend | D | 35% | WebSocket routing broken; agent selector missing; chat flow blocked |
| Tests | D | 25% | 2.8% coverage (15 test files / 528+ source files); no CI/CD |
| Infrastructure | C- | 40% | Docker configs exist; K8s manifests incomplete; no CI/CD pipelines |
| **Overall** | **D+** | **~45%** | **Not production-ready; critical P0 issues remain** |

---

## 1. Code-Verified Fixes Since May 20 Audit

The following issues identified in the previous audit have been **verified as fixed** in the current codebase with specific file and line references.

### 1.1 SECRET_KEY Security

**File:** `services/gateway/settings.py` line 37

**Fix:** `SECRET_KEY` now uses `secrets.token_urlsafe(50)` for generation. In production (when `DEBUG=false`), if the key matches the old default value, a `ValueError` is raised preventing startup.

**Verification:** Code review confirmed no hardcoded default secret key persists.

### 1.2 SQLite Fallback Removal

**File:** `services/gateway/settings.py` line 142

**Fix:** No SQLite fallback exists. If `SA01_DB_DSN` is missing or malformed, a `ValueError` is raised with a descriptive message. The system will not silently fall back to SQLite.

**Verification:** Database configuration section explicitly rejects invalid DSNs.

### 1.3 Rate Limiter Fail-Closed

**File:** `services/common/rate_limiter.py` lines 186–196

**Fix:** On Redis connection error, the rate limiter returns `allowed=False` (fail-closed). Previously it returned `allowed=True` (fail-open), which would bypass rate limits during Redis outages.

**Verification:** Error handler in the rate limiter returns `(allowed=False, ...)` on Redis exceptions.

### 1.4 UnifiedGate Real Policy Engine Calls

**File:** `admin/core/agentiq/unified_gate.py` lines 130–207

**Fix:** `UnifiedGate` now makes real OPA HTTP calls via `PolicyClient` and real SpiceDB gRPC calls via `SpiceDBClient`. Previously, authorization checks inspected JSON blobs rather than calling the actual policy engines.

**Verification:** Code confirmed that `PolicyClient` (`services/common/policy_client.py`) makes HTTP POST to OPA and `SpiceDBClient` (`services/common/spicedb_client.py`) makes gRPC `CheckPermission` calls to SpiceDB.

### 1.5 BrainBridge.recall() Implementation

**File:** `aaas/brain.py` lines 132–161

**Fix:** `recall()` is now implemented for both direct (in-process) and HTTP modes. Previously it raised `NotImplementedError`.

**Verification:** Both code paths (direct `somabrain` import and HTTP fallback) execute recall operations.

### 1.6 JWT Audience Verification

**File:** `admin/common/auth.py` lines 195–210

**Fix:** `verify_aud` is now controlled by the `JWT_ISSUER_STRICT` environment variable (default: `true`). When strict mode is enabled, the JWT audience claim is validated against the expected audience.

**Verification:** Token decoding respects the `JWT_ISSUER_STRICT` flag.

### 1.7 Accurate Token Counting

**File:** `admin/core/chat_orchestrator.py` lines 52–59

**Fix:** The V3 chat orchestrator now uses `tiktoken` for accurate token counting instead of heuristic character-based estimation.

**Verification:** Import and usage of `tiktoken` confirmed in the orchestrator's token counting logic.

### 1.8 Circuit Breakers

**File:** `admin/core/chat_orchestrator.py` lines 149–152

**Fix:** Circuit breakers are now applied to both SomaBrain and LLM calls within the V3 orchestrator. This prevents cascade failures when downstream services are unavailable.

**Verification:** Circuit breaker checks confirmed before both SomaBrain recall and LLM invocation.

### 1.9 require_permission() Implementation

**File:** `admin/common/auth.py` lines 389–429

**Fix:** `require_permission()` is now implemented via `UnifiedGate`. Previously it was a stub that allowed all requests.

**Verification:** Function delegates to `UnifiedGate` for OPA + SpiceDB + Scope evaluation.

### 1.10 ALLOW_INSECURE_AUTH_BYPASS Removal

**File:** `services/gateway/settings.py` line 235–236

**Fix:** The `ALLOW_INSECURE_AUTH_BYPASS` setting has been removed entirely from the codebase. No references remain in settings or environment configuration.

**Verification:** Grep confirms zero occurrences of `ALLOW_INSECURE_AUTH_BYPASS` in the repository.

---

## 2. Remaining Issues

### 2.1 P0 — Critical (Blocks Production)

#### P0-001: Authorization Bypass in Permissions API

**File:** `admin/permissions/api.py` line 336

**Issue:** The permissions check endpoint returns `allowed: true` unconditionally, regardless of the actual permission state. This is a complete authorization bypass for any code path that relies on this endpoint.

**Risk:** Any client calling this endpoint receives an affirmative authorization response regardless of the user's actual permissions.

**Recommended Fix:** Replace the unconditional return with a call to `UnifiedGate` or `SpiceDBClient` to perform a real authorization check.

#### P0-002: WebSocket Routing Missing agent_id

**Files:** `services/gateway/urls.py` (routing.py) + `services/gateway/consumers/chat.py` line 136

**Issue:** The backend WebSocket consumer requires `agent_id` in the URL path (`/ws/chat/{agent_id}`), but the frontend WebSocket client does not include it. This makes the chat flow completely non-functional.

**Risk:** Real-time chat is broken for all users.

**Recommended Fix:** Update `webui/src/services/websocket-client.ts` to include `agent_id` in the WebSocket URL, and add an agent selector to the chat view (`webui/src/views/saas-chat.ts`).

#### P0-003: Django Migrations Out of Sync

**Files:** `admin/aaas/migrations/`, `admin/core/migrations/`

**Issue:** Django migrations are out of sync with the current model definitions for both `admin/aaas` and `admin/core` apps. Running `migrate` may fail or produce incorrect schema.

**Risk:** Deployment failures; data integrity issues.

**Recommended Fix:** Run `python manage.py makemigrations` and verify the generated migrations. Commit the migration files.

### 2.2 P1 — High (Must Fix Before Production)

#### P1-001: Zero CI/CD Pipelines

**Path:** No `.github/workflows/` directory exists.

**Issue:** No automated testing, linting, building, or deployment pipelines exist. All quality checks are manual.

**Risk:** Regressions are undetected; deployments are error-prone.

**Recommended Fix:** Create GitHub Actions workflows for: lint (ruff, pyright), test (pytest), build (Docker), and deploy.

#### P1-002: Test Coverage at 2.8%

**Files:** 15 test files vs. 528+ source files

**Issue:** Test coverage is critically low at approximately 2.8%. VIBE standard requires real infrastructure testing, but even the test files that exist provide minimal coverage.

**Risk:** High regression risk; inability to validate changes.

**Recommended Fix:** Prioritize integration tests for: authentication flow, chat orchestrator (V3), rate limiter, and UnifiedGate authorization.

#### P1-003: Path Dependency on somabrain

**File:** `pyproject.toml` line 21

**Issue:** `somabrain` is referenced as `../somabrain` path dependency. This is non-portable and will fail in CI/CD, Docker builds, and any environment where the sibling directory is not present.

**Risk:** Build failures; developer onboarding friction.

**Recommended Fix:** Publish `somabrain` to a private PyPI registry or use a Git dependency URL. Make the import conditional for Standalone mode.

#### P1-004: RoleRequired Returns 401 Instead of 403

**File:** `admin/common/auth.py` line 277

**Issue:** `RoleRequired` returns `None` (resulting in HTTP 401 Unauthorized) when a user lacks the required role, instead of returning HTTP 403 Forbidden. This conflates authentication failure with authorization denial.

**Risk:** Client applications cannot distinguish between "not authenticated" and "not authorized."

**Recommended Fix:** Return an explicit 403 response when the user is authenticated but lacks the required role.

### 2.3 P2 — Medium (Should Fix)

#### P2-001: Hardcoded Docker Hostname

**File:** `aaas/brain.py` line 92

**Issue:** BrainBridge falls back to Docker hostname `somastack_aaas:9696` when no URL is configured. This is a hardcoded Docker networking assumption that will fail outside the specific Docker Compose setup.

**Recommended Fix:** Use environment variable resolution with no hardcoded fallback.

#### P2-002: Inconsistent Redis Environment Variable

**File:** `services/common/rate_limiter.py` line 67

**Issue:** The rate limiter uses `REDIS_URL` instead of the canonical `SA01_REDIS_URL` environment variable used by the rest of the system.

**Recommended Fix:** Update to use `SA01_REDIS_URL` for consistency.

#### P2-003: Regex-Based Tool Call Extraction

**File:** `admin/core/chat_orchestrator.py` line 750

**Issue:** Tool call extraction from LLM responses uses regex pattern matching rather than structured output parsing. This is fragile and may break with LLM response format changes.

**Recommended Fix:** Use the LLM's structured function-calling output format (tool_use / function_call) instead of regex extraction.

---

## 3. Risk Matrix

| ID | Issue | Severity | Likelihood | Risk Score | Category |
|----|-------|----------|------------|------------|----------|
| P0-001 | Authorization bypass in permissions API | Critical | Certain | 25 | Security |
| P0-002 | WebSocket routing broken | Critical | Certain | 25 | Functionality |
| P0-003 | Migrations out of sync | Critical | Likely | 20 | Data Integrity |
| P1-001 | Zero CI/CD | High | Certain | 20 | Process |
| P1-002 | 2.8% test coverage | High | Likely | 16 | Quality |
| P1-003 | Path dependency | High | Likely | 16 | Build |
| P1-004 | 401 instead of 403 | High | Likely | 12 | Security |
| P2-001 | Hardcoded hostname | Medium | Possible | 9 | Portability |
| P2-002 | Inconsistent env var | Medium | Possible | 9 | Configuration |
| P2-003 | Regex tool extraction | Medium | Possible | 8 | Reliability |

**Risk Score** = Severity (1–5) × Likelihood (1–5)

---

## 4. Recommendations

### 4.1 Immediate (Weeks 1–2)

| Priority | Action | Effort | Owner |
|----------|--------|--------|-------|
| P0-001 | Wire permissions API to UnifiedGate | 2 days | Backend |
| P0-002 | Fix WebSocket routing + add agent selector | 3 days | Frontend + Backend |
| P0-003 | Generate and commit migrations | 1 day | Backend |

### 4.2 Short-Term (Weeks 3–6)

| Priority | Action | Effort | Owner |
|----------|--------|--------|-------|
| P1-001 | Create CI/CD pipelines (lint, test, build) | 1 week | DevOps |
| P1-002 | Add integration tests for critical paths | 2 weeks | QA + Backend |
| P1-003 | Publish somabrain to private PyPI | 3 days | DevOps |
| P1-004 | Fix RoleRequired to return 403 | 1 day | Backend |

### 4.3 Medium-Term (Weeks 7–12)

| Priority | Action | Effort | Owner |
|----------|--------|--------|-------|
| P2-001 | Remove hardcoded hostname | 1 day | Backend |
| P2-002 | Standardize Redis env vars | 1 day | Backend |
| P2-003 | Replace regex tool extraction with structured output | 3 days | Backend |
| DEBT-001 | Consolidate conversation-worker with V3 | 2 weeks | Backend |
| DEBT-002 | Adopt MemoryPort in production adapters | 1 week | Backend |
| — | Complete K8s manifests | 2 weeks | DevOps |

---

End of Document
