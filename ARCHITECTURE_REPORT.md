# ⚠️ SOMA COLLECTIVE ARCHITECTURE REPORT & STABILIZATION ASSESSMENT ⚠️

**Date:** 2024-01-13  
**Project:** somaAgent01  
**Analyst Role:** PhD-level Architect & Security Auditor  
**Status:** 🔴 CRITICAL STABILIZATION REQUIRED

---

## 1. EXECUTIVE SUMMARY

The `somaAgent01` codebase is a **Django 5.1.4 + Django Ninja** monolith attempting to support a microservices-style architecture. While the technology stack aligns with modern standards (Django, Redis, Kafka, Temporal), the architectural implementation suffers from **severe code duplication**, **lax security defaults**, and **spaghetti routing**.

**Stop all feature development immediately.** The codebase is currently in a "High-Risk Pre-Alpha" state, not Production Readiness.

---

## 2. CRITICAL SECURITY FINDINGS (Vulnerabilities)

### 🔴 CRITICAL-01: Insecure Default Secret Key
**File:** `services/gateway/settings/base.py:44`
```python
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-dev-key-change-in-prod")
```
*   **Risk:** If `SECRET_KEY` is omitted in production (common in Docker/K8s secrets mounting), the application defaults to a hardcoded string. This allows attackers to forge sessions and potentially remote code execution via pickle serialization.
*   **Impact:** Complete application compromise.
*   **Fix:** Application must crash immediately if `SECRET_KEY` is missing. No defaults.

### 🔴 CRITICAL-02: Runtime Cryptographic Material Generation
**File:** `admin/core/helpers/vault_adapter.py:18`
```python
key = os.environ.get("SA01_CRYPTO_FERNET_KEY")
material = key.encode() if isinstance(key, str) and key else Fernet.generate_key()
```
*   **Risk:** If `SA01_CRYPTO_FERNET_KEY` is missing, a new key is generated *at runtime*. If the process restarts or scales horizontally (multiple pods), data encrypted previously becomes **permanently unrecoverable**.
*   **Impact:** Permanent data loss for secrets/encrypted fields.
*   **Fix:** Require the env var explicitly. Crash if missing.

### 🟠 HIGH-03: Secret Persistence on Disk
**File:** `admin/core/helpers/secrets.py`
*   **Risk:** The `SecretsManager` writes to `tmp/secrets.env`. If the `tmp` directory is served by the web server or exposed in logs, sensitive credentials are leaked.
*   **Fix:** Use strictly in-memory storage or HashiCorp Vault (as implied by the module name, but not fully implemented).

---

## 3. ARCHITECTURAL FLAWS & DUPLICATION

### 3.1 The "Gateway" vs "Orchestrator" Confusion
There are two ASGI entry points fighting for control:
1.  **`services/gateway/`**: The intended API gateway. Uses `admin/api.py` for Django Ninja routes.
2.  **`admin/orchestrator/main.py`**: A standalone ASGI server that wraps *other* services (Gateway, Memory, Cache) inside a `SomaOrchestrator` class.

**The Problem:** Why is the Orchestrator an HTTP server wrapping the Gateway? This suggests an architectural misunderstanding.
*   **Correct Pattern:** `Gateway` handles HTTP. `Orchestrator` handles internal workflows (Tempo/Async). They should not be nested in a single process wrapper.

### 3.2 Service Discovery vs. Hardcoding
**File:** `services/gateway/settings/service_registry.py`
*   **Observation:** Excellent implementation. Uses `dataclass` and environment variables.
*   **Contradiction:** `admin/core/helpers/secrets.py` uses a custom `tmp/secrets.env` parser.
*   **Duplication:** The system has `env_config.py` (Service Registry) and `secrets.py` (Secret Manager). These should be unified into a single Secrets/Config provider (likely Vault).

### 3.3 API Route Explosion (Spaghetti API)
**File:** `admin/api.py`
*   **Observation:** 70+ routers are imported and mounted in a single file.
*   **Risk:** Import overhead is massive. `importlib` style loading is missing.
*   **Duplication:** Routes like `/permissions` are mounted twice (line 235 and line 253).
*   **Legacy Indicators:** Comments mention "MIGRATION POSTURE" and "FastAPI replaced", implying this is a fresh port. However, the sheer volume of endpoints (including `/billing`, `/webhooks`, `/scheduling`) suggests these were split out monolithically without proper domain separation.

### 3.4 Duplicated Business Logic
*   **Policy:** `services/common/opa_policy_adapter.py` vs `admin/common/middleware.py`.
    *   The Adapter is used by workers.
    *   The Middleware is used by the Gateway.
    *   *Risk:* Logic divergence. If the Middleware allows a request, but the Worker's Adapter denies it (or vice versa), the system behaves unpredictably.
*   **Database:** `settings/base.py` parses DSN via Regex. Django handles DSN natively. This regex is fragile and duplicate logic.

---

## 4. CODE QUALITY & COMPLIANCE

### 4.1 Vibe Coding Rules Compliance
*   **Rule 1 (No Bullshit):** Mostly followed. Code is explicit.
*   **Rule 4 (Real Implementations):** **VIOLATED** in `base.py` (insecure default).
*   **Rule 6 (Complete Context):** **VIOLATED**. `admin/api.py` imports *everything* in the global scope. This causes massive initialization time and tight coupling.

### 4.2 Dependencies
*   `pyproject.toml` and `requirements.txt` are consistent.
*   **Issue:** `requirements.txt` contains both dev and prod tools. It should be split.
*   **Observation:** `browser-use`, `duckduckgo-search`, `kokoro` indicate heavy AI capabilities.

---

## 5. THE STABILIZATION & PRODUCTION READINESS PLAN

To stop the bleeding and take this to production, we must execute a **Code Freeze** and perform a **Stabilization Sprint**.

### Phase 1: Immediate Security Hardening (Do this NOW)
1.  **Patch `services/gateway/settings/base.py`**: Remove default `SECRET_KEY`. Make it `get_required_env`.
2.  **Patch `admin/core/helpers/vault_adapter.py`**: Remove `Fernet.generate_key()` fallback. Require `SA01_CRYPTO_FERNET_KEY`.
3.  **Audit `tmp/`**: Ensure `.gitignore` covers `tmp/` and that no web server serves this directory.

### Phase 2: Architecture Refactoring (The "Monolith" vs "Services" Decision)
*   **Decision Point:** Is this a Monolith or Microservices?
    *   *Current State:* Hybrid (Monolith Django + Folder of Services).
    *   *Recommendation:* **Full Monolith Migration**.
*   **Action:** Move `services/common/` logic into `admin/core/services/`.
*   **Action:** Move `services/conversation_worker/`, `services/tool_executor/` logic into Django Management Commands (`manage.py run_worker`).
*   **Why?** This simplifies deployment. You deploy one Django container. You spin up worker processes using `manage.py`.

### Phase 3: API Cleanup
1.  **Consolidate Routers:** Move router registration out of `admin/api.py`. Use Django's app structure. Each `admin/<app>/` should define its own router in `api.py` which is auto-discovered.
2.  **Remove `admin/orchestrator/main.py`:** The `Orchestrator` should be a class imported by the worker processes, not an HTTP server. Use Temporal.io for orchestration, not a custom HTTP wrapper.

### Phase 4: Secret Management
1.  **Delete `admin/core/helpers/secrets.py`** (or strictly isolate it for local dev only).
2.  **Enforce Vault:** Use the `ServiceRegistry` pattern to validate that `SA01_OPA_URL`, `SA01_DB_DSN`, etc., are present. Rely on HashiCorp Vault for runtime secret injection (K8s secrets -> Vault -> App).

---

## 6. ACTIONABLE CHECKLIST

- [ ] **SECURITY:** Remove `django-insecure-dev-key` default.
- [ ] **SECURITY:** Enforce `SA01_CRYPTO_FERNET_KEY` or remove encryption.
- [ ] **ARCHITECTURE:** Decide: Monolith vs Microservices. (Recommended: Monolith).
- [ ] **ARCHITECTURE:** Remove `services/gateway` directory, merge into root Django project.
- [ ] **ARCHITECTURE:** Remove `admin/orchestrator/main.py` (it's redundant overhead).
- [ ] **DUPLICATION:** Unify `services/common/opa_policy_adapter.py` into `admin/common/policy.py`.
- [ ] **CLEANUP:** Verify `admin/api.py` imports. Lazy-load heavy imports.

## 7. CONCLUSION

The codebase has **high potential** (Django 5, Ninja, solid dependency list) but is currently **unstable** due to architectural drift and "feature pile-up" (too many routers added too quickly).

**Immediate Action:** Apply the Security Hotfixes in Phase 1 immediately. Then, halt feature dev and execute Phase 2.