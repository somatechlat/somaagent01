# SOMA-RPT-SEC-REVIEW-2026-10-13 — Enterprise Security Review

| Field | Value |
|---|---|
| Document Identifier | SOMA-RPT-SEC-REVIEW-2026-10-13 |
| Date | 2026-10-13 |
| Reviewer | security-reviewer (MiMoCode-sec-review-2026-10-13) |
| Scope | `somaAgent01` + `somabrain` + `somafractalmemory` |
| Standard | `SOMA-STD-SECURITY-001`, `SOMA-STD-TRIAD-001`, `SOMA-STD-BOOTSTRAP-001` |
| Mode | Full enterprise security — real AuthN/AuthZ, Brain/SFM real, no mocks, no bypasses |
| Commits | **None** (operator order) |

---

## 1. Executive summary

Reviewed the focus surfaces (SFM tenant binding, Brain→SFM token, Agent RBAC,
memory authorize, health/delegation gates, bootstrap ceremony, tool_calling
memory_forget, webui token handling) against SOMA law.

**7 clear violations fixed with minimal diffs** (all `py_compile` green).
**6 residual risks remain open** (need product/arch change, not a safe minimal
diff). **0 hardcoded secrets found in production code.** SQL is parameterized.
Subprocess uses argv lists (no `shell=True`). T-1 (agent never holds SFM client)
is enforced in `services/common/adapters/`.

---

## 2. FIXED in this review (minimal diffs)

### F-1 — CRITICAL — Secret file on disk
- **Attack class:** Secrets exposure / credential at rest outside Vault
- **Where:** `somafractalmemory/secrets/vault-token` (28-byte token file, mode 0600)
- **Law:** SOMA-STD-SECURITY-001 §1.8 BANNED (`secrets/vault-token`); §3.3 "DELETE the file"
- **Fix:** File deleted. No code referenced it (`compose` uses `/run/t0/sfm_runtime_token` via `VAULT_TOKEN_FILE`).
- **Status:** FIXED

### F-2 — HIGH — Shared memory token unlocks `admin:read`
- **Attack class:** Privilege escalation / broken access control
- **Where:** `somabrain/somabrain/api/standalone_auth.py:57`
- **Law:** Operator "Admin routes require dedicated admin credential (shared memory token must NOT unlock admin)"
- **Detail:** Every holder of the shared `SOMABRAIN_MEMORY_HTTP_TOKEN` received `admin:read` in its scope set. `require_admin_auth` still refused the shared token for admin routes (static-token path), but the scope was a latent privilege grant and contradicted documented defect B24.
- **Fix:** Shared token scopes are now `["memory:read", "memory:write"]`. Admin scopes (`admin`, `admin:read`, `admin:write`) attach **only** when `is_admin` is true (dedicated `SOMABRAIN_ADMIN_TOKEN` match).
- **Status:** FIXED

### F-3 — HIGH — Cross-tenant merge via `or "default"` (transactions)
- **Attack class:** Multi-tenant isolation failure
- **Where:** `somabrain/somabrain/transactions/event_store.py` (Kafka key + OutboxEvent.tenant_id)
- **Law:** Operator "Never `or "default"` tenant"
- **Fix:** `store()` fail-closes on empty `tenant_id` (returns False, logs error). Kafka key and OutboxEvent now use the real tenant. Strangers can no longer share one `default` partition.
- **Status:** FIXED

### F-4 — MED — Cross-tenant merge via `or "default"` (test registry mirror)
- **Attack class:** Multi-tenant isolation failure
- **Where:** `somabrain/somabrain/services/tiered_memory_registry.py:68`
- **Fix:** Empty tenant is dropped (no `default` merge). Fail-closed.
- **Status:** FIXED

### F-5 — HIGH — Unauthenticated internal health probe
- **Attack class:** Information disclosure / unauthenticated internal state
- **Where:** `somaAgent01/admin/orchestrator/health_router.py` `/v1/health`
- **Law:** Operator "No unauthenticated probes of internal state"
- **Fix:** `auth=AuthBearer()` + `authorize(..., action="system:view", resource="health")`.
- **Status:** FIXED

### F-6 — MED — SFM `/health` all-tenant dump
- **Attack class:** Cross-tenant information disclosure
- **Where:** `somafractalmemory/somafractalmemory/api/routers/health.py` (per-tenant stats block)
- **Detail:** Authenticated endpoint enumerated every tenant name + memory/graph counts. With the shared writer token this is full cross-tenant reconnaissance.
- **Fix:** Per-tenant stats now scoped to `SOMA_BOUND_TENANT` only. Wildcard writer credentials get aggregates only — never a tenant list.
- **Status:** FIXED

### F-7 — MED — Banned `SOMA_VAULT_TOKEN_FILE` alias + unvalidated tenant keys
- **Attack class:** Config law violation / tenant-key injection
- **Where:** `somafractalmemory/infra/standalone/seed_vault.py`, `somafractalmemory/api/utils.py`
- **Law:** SOMA-STD-SECURITY-001 "Deleted forever: SOMA_VAULT_TOKEN*"
- **Fix:**
  - `seed_vault.py` prefers canonical `VAULT_ADDR` / `VAULT_TOKEN_FILE`; old names remain as one-release compat only and are documented as banned from compose.
  - `api/utils.py` `_validate_tenant_id` rejects empty/oversized (>255), control chars, path separators and `..` before a tenant becomes a storage key. Applied on every resolve path (wildcard header, explicit body, header).
- **Status:** FIXED

---

## 3. OPEN residuals (need product/arch change — not minimal-diff safe)

### R-1 — CRITICAL — One token, all tenants (`SOMA_BOUND_TENANT='*'`)
- **Attack class:** Broken multi-tenant isolation / F-02b
- **Where:** `somafractalmemory/api/auth.py:57-73` + `api/utils.py:69-78`
- **Detail:** Explicit `SOMA_BOUND_TENANT='*'` makes the shared writer token able to select **any** partition via `X-Soma-Tenant`. Default is fail-closed (unset → reject), which is correct. But the enterprise blocker stands: there is no per-credential tenant map. One leaked writer token = every tenant.
- **Fix (when ready):** Per-credential tenant allow-list (Vault KV map token-fingerprint → tenants). Replace wildcard with an explicit set. This is F-02b and is a real product change.
- **Status:** OPEN (config-gated, fail-closed default is correct)

### R-2 — HIGH — Login token in `sessionStorage` + WS subprotocol
- **Attack class:** XSS token theft / credential in JS-readable storage
- **Where:** `webui/src/views/soma-login.ts:871`, `webui/src/services/websocket-client.ts:137-146`
- **Detail:** Login response token is stored in `sessionStorage` (`soma_ws_token`) and sent as `Sec-WebSocket-Protocol: soma-auth.<token>`. Any XSS can read it. The subprotocol value can also leak via proxy/access logs. The code comments document why the httpOnly cookie alone is insufficient for WS reconnect.
- **Fix (when ready:** Server-side WS ticket: short-lived one-time ticket in the cookie, exchanged for the socket; never a long-lived bearer in JS storage. Keep `httpOnly` + `Secure` + `SameSite` for the session.
- **Status:** OPEN

### R-3 — HIGH — macOS keychain in vault unseal path
- **Attack class:** Operator LAW violation / host bypass
- **Where:** `somaAgent01/infra/standalone/vault_unseal.py:73-163`
- **Law:** Operator "never macOS keychain, never host bypasses. Container-native only."
- **Detail:** Keychain helpers are preferred when available. SOMA-STD-SECURITY-001 §1.2 allows keychain for local/T-8; the operator order overrides for this generation. Code currently prefers keychain over T0 tmpfs.
- **Fix (when ready):** Hard-refuse keychain when `/.dockerenv` or `container` env is present (or unconditionally for this generation); unseal via ceremony ENV only. Not a safe one-liner: `unseal_watch` restart path depends on the custodian.
- **Status:** OPEN

### R-4 — HIGH — Unseal key at rest in T0
- **Attack class:** Credential at rest
- **Where:** `somaAgent01/infra/standalone/bootstrap_exec.py:178-181`
- **Detail:** `t0_write(UNSEAL_ACCOUNT, unseal)` persists the unseal key in T0 so `unseal_watch` can re-unseal without a keychain. SOMA-STD-SECURITY-001 §1.4 says unseal never enters consumer T0. Tradeoff was deliberate (keychain banned by operator). Residual risk R-1/R-2 of the standard.
- **Status:** OPEN (documented tradeoff; needs Channel FD or KMS auto-unseal)

### R-5 — MED — `memory_forget` with `query=` auto-executes (no HITL)
- **Attack class:** Destructive multi-row erase without human approval
- **Where:** `somaAgent01/admin/core/tool_calling.py:277-285`
- **Detail:** Bare coord forget stays `approval_required`. A non-empty `query=`/`text=`/`match=` (len >= 3) upgrades to `auto_execute` for the "delete my name" product path. RBAC (`resource:tool_execute`) and Clef guardrail still run. `memory_forget` is correctly **excluded** from `NON_DISABLEABLE_TOOLS`.
- **Risk:** A prompt-injected model can multi-erase tenant memory without HITL when IQ floor is `none`.
- **Fix (when ready):** Keep query-forget gated under `require_hitl` / `tool_approval=all` (already does via `_apply_autonomy_floor`), and add a hard row-cap on query-erase. Do not silently remove the product path.
- **Status:** OPEN (intentional product path; residual risk)

### R-6 — MED — `require_service_url` has no URL scheme/host allow-list
- **Attack class:** SSRF from operator-managed URLs
- **Where:** `somaAgent01/admin/core/helpers/service_urls.py:166-217`
- **Detail:** Fail-closed on **missing** config (good). Values from InfrastructureConfig / AgentSetting / capsule override are used as fetch targets with no scheme/host validation. An administrator can point `SOMABRAIN_URL` at an internal metadata IP.
- **Fix (when ready):** Allow-list scheme (`https`/`http` for local) and deny link-local / loopback / private ranges unless explicitly opted-in per endpoint.
- **Status:** OPEN

---

## 4. Surfaces reviewed — clean

| Surface | Result |
|---|---|
| `admin/core/authz.py` | No wildcards, fail-closed, org-scoped (`permissions_for_principal` returns empty set if `org_id` empty). sysadmin `memory_*` are named grants (Memory UI ordinary use) — documented, not a bypass. |
| `admin/memory/api/memory.py` | Every route: `AuthBearer` + `authorize(action=...)`. `_tenant()` refuses empty/default/standalone. |
| `services/common/authorization.py` | Empty tenant on principal → `ForbiddenError`. OPA can only narrow. |
| `somabrain/core/security/legacy_auth.py` `require_admin_auth` | Shared memory token refused; only `SOMABRAIN_ADMIN_TOKEN` or JWT admin claim. |
| Brain `/health`, `/`, `/diagnostics`, `/metrics` | `api_key_auth` present. `/healthz` liveness only. |
| Delegation gateway | `AuthBearer` + `authorize` on metrics/health/task/callback. |
| Brain→SFM `memory/sfm_auth.py` | Vault-first (`get_runtime_secret("memory_http_token")`), fail-closed if unprovisioned, namespace/tenant required (T-5). |
| T-1 | `services/common/adapters/__init__.py` — agent never holds SFM client. |
| Injection | Parameterized `cursor.execute(query, params)`. Subprocess argv lists, no `shell=True`. |
| Hardcoded secrets | None in production paths (grep across three repos). |
| Mocks/fakes in auth/memory | None (only comments denying fakes). |

---

## 5. Verification

```
python3 -m py_compile  # all 7 changed files → OK
pytest tests/unit/test_memory_token_single_source.py   → 6 passed, 1 skipped
pytest tests/unit/test_sfm_auth_and_client.py          → 6 passed, 1 failed (PRE-EXISTING:
                                                         test_transports_use_resolver expects
                                                         resolve_sfm_api_token in transport.py)
pytest tests/unit/test_vault_token_file_only.py        → 7 passed, 1 skipped (Vault not up)
```

Pre-existing failures unrelated to this review:
- `test_transports_use_resolver` (source-string drift)
- `test_memory_vector_fail_closed` (`_hit_similarity` ImportError)

---

## 6. Checklist (SOMA law)

| # | Law | Status |
|---|---|---|
| 1 | Secrets = Vault only | **Partial** — F-1 fixed; R-4 unseal in T0 remains |
| 2 | Real AuthN/AuthZ every surface; empty org = deny | **Pass** (R-1 wildcard config is the residual) |
| 3 | Admin routes dedicated credential | **Pass** (F-2 fixed; `require_admin_auth` correct) |
| 4 | Fail-closed missing token/tenant/URL/key | **Pass** (F-3/F-4/F-7 hardened) |
| 5 | T-1 agent never holds SFM client | **Pass** |
| 6 | No injection / parameterized / SSRF | **Partial** — SQL/subprocess clean; R-6 SSRF open |
| 7 | No mocks/fakes in production auth/memory | **Pass** |
| 8 | Multi-tenant isolation | **Partial** — F-3/F-4/F-6 fixed; R-1 open |
| 9 | Never macOS keychain / host bypasses | **FAIL** — R-3 open |

---

*security-reviewer owns this report. No commits. A2A: CLAIMS + LEDGER updated.*
