# SOMA-RPT-SEC-CODE-DOCS-001 — Security Law / Standard vs Live Code Verification

## Document Control

| Field | Value |
|---|---|
| Document Title | Security Law & Standard vs Live Code Verification |
| Document Identifier | SOMA-RPT-SEC-CODE-DOCS-001 |
| Version | 1.0.0 |
| Date | 2026-10-13 |
| Status | Draft |
| Author | security-reviewer (somaAgent01) |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 · ISO 27001 (A.5–A.8) |
| Next Review | 2027-01-13 |
| Related | `SOMA-LAW-SECURITY-001` · `SOMA-STD-SECURITY-001` · `SOMA-STD-BOOTSTRAP-001` · `SOMA-RPT-SEC-VAULT-001` · `CLAUDE.md` |
| Source of truth | **Live code** (`infra/standalone/vault_*.py`, `vault-policies/*.hcl`, `services/common/vault_secrets.py`, `docker-compose.yml`, `admin/auth/*`). Docs yield to code (SEC-LAW-08). |
| Audience | Human Operator, security-reviewer, soma-vault-authority, A2A peers |
| Scope | `somaAgent01` standalone Vault bootstrap + auth fail-closed path |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-13 | security-reviewer (somaAgent01) | Full doc-vs-code matrix for Vault law, policies, T0 volume, fail-closed secrets, auth 503/200. GO with residual risks. Two doc mismatches fixed. |

---

> **Evidence rule:** every claim cites live code (`file:line`) or a dated operator observation. **No secret values appear in this document.** Code wins over docs.

---

## 1. Executive summary

| Area | Verdict |
|---|---|
| Orphan service tokens (`no_parent: True`) | **MATCH** — `vault_scoped_tokens.py:308` |
| 720h TTL (required, no default) | **MATCH** — `require_env("VAULT_TOKEN_TTL_HOURS")` + `.env:41` = 720 |
| Root never written to T0 | **MATCH** (guards) — `vault_scoped_tokens.py:150-155`, `vault_unseal.py:117-121`, `bootstrap_exec.py:69-70` |
| Root revoke after mint | **MATCH** — `auth/token/revoke-self` at `vault_scoped_tokens.py:354` |
| `vault-policies/*.hcl` least privilege (agent) | **MATCH** — read-only `secret/data/agent/credentials` + `api_keys` (+ metadata); no `sys/`; no write |
| `vault_secrets.py` fail-closed | **MATCH** — F-10/F-11 `VaultAuthError`; never returns `None` on auth failure |
| Compose `t0_agent` named volume | **MATCH** — `docker-compose.yml:57,140` (`standalone_t0_agent`, `/run/t0`) |
| Auth 503 / 200 behaviour | **MATCH** — pepper fail → 503; success → 200 |
| Secrets in `.env` / git | **MATCH** — topology only |
| brain-runtime policy vs LAW "read-only" | **MISMATCH (doc)** — live policy has write on `somabrain/*` |
| README root-in-T0 claim | **MISMATCH (doc)** — fixed in this pass |

**Overall: GO** for local/standalone operation. Residual risks (§5) are documented and ranked. No CRITICAL product-code change is required by this review.

---

## 2. Doc vs code verification matrix

Legend: **MATCH** = docs and code agree · **MISMATCH** = docs claim X, code does Y · **DOC-FIXED** = mismatch corrected in this pass · **LISTED** = large change, not applied here.

| # | Rule / claim (doc) | Doc source | Live code | Verdict |
|---|---|---|---|---|
| V-01 | Service tokens are orphans (`no_parent: True`) so root `revoke-self` does not kill them | LAW SEC-LAW-04 · BOOTSTRAP §3.4 · SECURITY 1.1.0 | `vault_scoped_tokens.py:305-308` `"no_parent": True` | **MATCH** |
| V-02 | TTL = `VAULT_TOKEN_TTL_HOURS`, required, **no default** (Rule 91) | LAW §2 · BOOTSTRAP §3.4 · SECURITY §1.3 | `vault_scoped_tokens.py:41-42,117` `require_env`; `bootstrap_exec.py:279`; `remint_ceremony.py:100` | **MATCH** |
| V-03 | This deploy TTL = **720h (30d)** | LAW §2 · BOOTSTRAP §3.4 · RPT-SEC-VAULT-001 | `infra/standalone/.env:41` `VAULT_TOKEN_TTL_HOURS=720` | **MATCH** |
| V-04 | Mint then **revoke root immediately** (`auth/token/revoke-self`) | LAW SEC-LAW-05 · ceremony step 8 | `vault_scoped_tokens.py:353-355` POST `auth/token/revoke-self` | **MATCH** |
| V-05 | **Never write Vault root to T0 / any disk** | LAW SEC-LAW-01 · BOOTSTRAP §2.1a · SECURITY §1.2 | `vault_scoped_tokens.py:150-155` refuses `ROOT_ACCOUNT`; `vault_unseal.py:117-121`; `bootstrap_exec.py:69-70` | **MATCH** (guards) |
| V-06 | Root for one-shot only: process env → keychain; never a repo file | LAW §2 · SECURITY §1.3 | `vault_scoped_tokens.py:228-266` `read_root_token()` | **MATCH** |
| V-07 | Service token paths: `/run/t0/agent_runtime_token`, `brain_runtime_token` | LAW §2 · CLAUDE.md item 7 | `vault_scoped_tokens.py:98-101` `SERVICE_TOKENS`; compose `VAULT_TOKEN_FILE=/run/t0/agent_runtime_token` (`docker-compose.yml:94`) | **MATCH** |
| V-08 | T0 custodian = Docker volume `standalone_t0_agent` (ext4), **not** tmpfs | LAW §2 · BOOTSTRAP §2.1a · CLAUDE.md item 7 | `docker-compose.yml:57` `t0_agent:` · `:140` `t0_agent:/run/t0:rw` | **MATCH** |
| V-09 | T0 write only if tmpfs **or** dedicated named volume; refuse ordinary dir / overlay / `/` | LAW §2.1 · BOOTSTRAP §2.1a | `vault_scoped_tokens.py:128-208` `_t0_custodian_allows` (mount table check) | **MATCH** |
| V-10 | Token file mode `0600` | LAW §2 | `vault_scoped_tokens.py:211,217` `0o600` | **MATCH** |
| V-11 | agent-runtime policy: read `secret/data/agent/credentials` + `api_keys` (+ metadata); no write; no `sys/` | LAW SEC-LAW-07 | `agent-runtime.hcl:14-44` | **MATCH** |
| V-12 | agent-runtime may `renew-self` / `lookup-self` only (token self-mgmt) | SECURITY §3.1 · BOOTSTRAP §3.1 | `agent-runtime.hcl:37-43` | **MATCH** |
| V-13 | brain-runtime: least privilege; no agent DB / keycloak secrets | SECURITY §1.5 · `brain-runtime.hcl` header | `brain-runtime.hcl:14-16` reads **whole** `secret/data/agent/credentials` (KV v2 doc-granular) | **PARTIAL** — documented in SECURITY §1.5 as accepted; header comment overclaims "just this key" |
| V-14 | Policies are **read-only KV v2** | LAW §2 "Policies … (read-only KV v2)" | `brain-runtime.hcl:19-25` grants `update/create/delete` on `somabrain/data/*` | **MISMATCH → DOC-FIXED** (LAW §2 wording) |
| V-15 | `vault_secrets.py` fail-closed: missing token / auth failure → `VaultAuthError`, never `None` | LAW SEC-LAW-06 · SECURITY §4.1 · BOOTSTRAP §2.7 | `vault_secrets.py:28-36,130-199,291-323` (F-10/F-11) | **MATCH** |
| V-16 | Root token name refused on every resolution path | SECURITY §1.2 · BOOTSTRAP §2.1a | `vault_secrets.py:50,163-171` `_ROOT_ACCOUNT_NAMES` | **MATCH** |
| V-17 | Pepper read-only at runtime; fail-closed if absent | SECURITY §1.6 · LAW SEC-LAW-06 | `admin/auth/identity.py:110-121` `_pepper()` raises if absent | **MATCH** |
| V-18 | Login with unconfigured identity → **HTTP 503** (not 200, not 500 with stack) | RPT-SEC-VAULT-001 I-1 · LAW §3 step 10 | `admin/auth/api.py:433-442` `ServiceUnavailableError` → `status_code = 503` (`admin/common/exceptions.py:231-234`) | **MATCH** |
| V-19 | Login success → **HTTP 200** + token | LAW ceremony step 10 | `admin/auth/api.py:522,653` `status=200` | **MATCH** |
| V-20 | `.env` = topology only; no secret values | LAW SEC-LAW-03 · BOOTSTRAP T-9 | `infra/standalone/.env` (hosts/ports/TTL only; comments name Vault keys) | **MATCH** |
| V-21 | No `secrets: file:` / `*_FILE` secret paths in compose | SECURITY §1.8 banned · BOOTSTRAP §3.6 | `docker-compose.yml` — no `secrets:` block; `VAULT_TOKEN_FILE` is a **path** to T0 token | **MATCH** |
| V-22 | `VAULT_TOKEN_TTL_HOURS` compose interpolation fail-closed (`:?`) | Rule 91 | `docker-compose.yml:97` `${VAULT_TOKEN_TTL_HOURS:?set VAULT_TOKEN_TTL_HOURS}` | **MATCH** |
| V-23 | Ceremony script mints orphans then revoke-self | LAW §3 · BOOTSTRAP §3.4 | `remint_ceremony.sh:86,112` · `remint_ceremony.py:125-134` | **MATCH** |
| V-24 | README custodian table: root may live in T0 for seeder | `infra/standalone/README.md:39` | Contradicts LAW SEC-LAW-01 + write guards | **MISMATCH → DOC-FIXED** |
| V-25 | T0 comments say "RAM tmpfs" while service mounts named volume | `docker-compose.yml:90` | Mount is `t0_agent` named volume | **LISTED** (stale comment; prior Δ-08; code-adjacent) |
| V-26 | SECURITY §1.5 policy table: brain denies write; agent `secret/data/agent/*` | SECURITY §1.5 | Live: brain **owns** `somabrain/*` write; agent is path-specific | **LISTED** (table rewrite = medium; live HCL is truth) |
| V-27 | `init_vault.py` / `seed_clef_vault.py` still **read** `T0_DIR/vault_root_token` as fallback | BOOTSTRAP "root never a custodian account" | `init_vault.py:68-73` · `seed_clef_vault.py:73` (read only; writers refuse) | **LISTED** (code residual; not a doc fix) |

---

## 3. Focused verification (requested rules)

### 3.1 `vault_scoped_tokens.py` — orphan · 720h · no root on disk

| Property | Code evidence | Doc claim | Status |
|---|---|---|---|
| `no_parent: True` | `:308` in `auth/token/create` body | LAW SEC-LAW-04 · BOOTSTRAP orphan rule | MATCH |
| `no_default_policy: True` | `:310` | BOOTSTRAP §3.4 | MATCH |
| TTL from `VAULT_TOKEN_TTL_HOURS` | `:117` `TOKEN_TTL = f"{TOKEN_TTL_HOURS}h"` | LAW §2 720h | MATCH |
| No coded default | `require_env` raises if unset (`:70-86`) | Rule 91 | MATCH |
| Root revoke after mint | `:354` | LAW SEC-LAW-05 | MATCH |
| Refuse `vault_root_token` write | `:150-155` | R-SEC-01 absolute | MATCH |
| Refuse non-custodian filesystem | `:179-204` | BOOTSTRAP §2.1a | MATCH |
| Never prints secret values | logs use policy/account/ttl only (`:323,355`) | LAW SEC-LAW-02 | MATCH |

### 3.2 `vault-policies/*.hcl`

| Policy | Grants (live) | Denies by omission | Doc alignment |
|---|---|---|---|
| `agent-runtime.hcl` | `read` `secret/data/agent/credentials`, `secret/data/agent/api_keys`, `api_keys/*`, metadata; `auth/token/renew-self` (`update`), `lookup-self` | `sys/*`, write, `auth/token/create`, other mounts | LAW SEC-LAW-07 **MATCH** |
| `brain-runtime.hcl` | `read` whole `secret/data/agent/credentials`; **own** `somabrain/data/*` (`read,update,create,delete`) + metadata; renew/lookup-self | `sys/*`, `auth/token/create`, `secret/data/agent/api_keys` | LAW §2 "read-only" **MISMATCH** (own-mount write is intentional service ownership) |

**Note:** KV v2 is document-granular. `brain-runtime.hcl:14-16` reading the whole agent credentials doc is a known least-privilege gap already called out in SECURITY §1.5. Not a new finding.

### 3.3 `services/common/vault_secrets.py` — fail-closed

| Behaviour | Evidence | Status |
|---|---|---|
| Auth/transport failure → `VaultAuthError` (never `None`) | `:291-323` | MATCH |
| Policy denial (403/401) named F-11; stop, do not widen | `:304-317` | MATCH |
| Missing token file / empty token fatal | `:172-188,190-199` | MATCH |
| Root account names refused | `:50,163-171` | MATCH |
| Genuine key absence → `None` only when Vault answered 404 | `:296-303` | MATCH |
| KV write merge-safe (read-modify-write whole map) | `:390-412` | MATCH |

### 3.4 Compose T0 volume

| Claim | Evidence | Status |
|---|---|---|
| Named volume `t0_agent` | `docker-compose.yml:57` | MATCH |
| Mounted at `/run/t0` rw on agent service | `:140` | MATCH |
| Separate `t0_postgres` for postgres consumer | `:58` | MATCH |
| `VAULT_TOKEN_FILE=/run/t0/agent_runtime_token` | `:94` | MATCH |
| Comments still say "RAM tmpfs custodian" | `:90` | LISTED (stale; volume is intentional §2.1a) |

### 3.5 Auth 503 / 200

| Path | Behaviour | Evidence | Status |
|---|---|---|---|
| Pepper / Vault unavailable | `ServiceUnavailableError("auth", "Identity service is not configured")` → **503** | `admin/auth/api.py:433-442`; `admin/common/exceptions.py:231-234` | MATCH |
| Successful login | `NinjaResponse(..., status=200)` | `admin/auth/api.py:522,653` | MATCH |
| Wrong password / unknown user | Uniform 401 (no oracle) | `admin/auth/api.py:380-383` contract | MATCH (documented) |
| Response never names secret store | comment + body omit Vault paths | `:434-435` | MATCH |

---

## 4. Security posture (summary)

| Control | State |
|---|---|
| Secrets at rest | Vault-only for application credentials; T0 holds **scoped** service tokens + unseal key (documented exception) |
| Secrets in git / `.env` | Clean (topology only) |
| Root lifecycle | One-shot mint → policy → orphan tokens → `revoke-self`; write guards refuse T0 root |
| Runtime identity | TTL-scoped policy-bound tokens (720h); F-10 stop-not-widen |
| Least privilege (agent) | Read-only credentials + api_keys; no `sys/` |
| Fail-closed auth | 503 when pepper/identity cannot be checked; 401 uniform for bad credentials |
| Audit | Named errors, no secret values in logs (mint path); Vault audit volume defined in compose |
| T0 custody | Named volume `standalone_t0_agent` (ext4) documented as §2.1a exception; production target KMS auto-unseal |

---

## 5. Residual risks (ranked)

| # | Risk | Sev | Mitigation / note |
|---|---|---|---|
| R-01 | T0 named volume is durable (ext4) — service tokens survive recreate; disk exposure if host is stolen | HIGH (local) | Documented §2.1a exception; 0600 `appuser`; production = KMS auto-unseal / tmpfs; tokens TTL 720h |
| R-02 | brain-runtime can read the **whole** `secret/data/agent/credentials` document (not just `memory_http_token`) | MED | SECURITY §1.5 already accepts or split to `secret/data/shared/*`; not silent |
| R-03 | `init_vault.py` / `seed_clef_vault.py` still **accept** a root token file in T0 as fallback if an operator left one | MED | Writers refuse root; residual is a **read** path. Prefer deleting T0 root reads (code change, out of scope here) |
| R-04 | Compose / README still describe T0 as "RAM tmpfs" in places | LOW | Stale comments (Δ-08); truth is LAW §2.1 + BOOTSTRAP §2.1a |
| R-05 | Unseal key 1-of-1 on local volume = single operator compromise | MED (local) | Prod: 3-of-5 / KMS auto-unseal (BOOTSTRAP §2.3) |
| R-06 | 720h token TTL is long; compromise window before natural expiry | MED | Renewable lease; F-10 on expiry; re-ceremony mints new orphan; consider shorter TTL + renew-self if ops allow |
| R-07 | Channel ENV secrets (postgres/keycloak) visible in `/proc/<pid>/environ` of PID1 | MED | Container UID isolation; core dumps off (BOOTSTRAP §2.5) |
| R-08 | `VAULT_SKIP_VERIFY` can disable TLS verify if operator sets it | LOW | Topology/ops control; do not set in non-local |

---

## 6. Documentation mismatches

### 6.1 Fixed in this pass (small)

| File | Change |
|---|---|
| `infra/standalone/README.md` | Root custodian row: **no longer** claims `vault_root_token` may sit in T0. Aligns with SEC-LAW-01 and write guards. |
| `docs/standards/SOMA-LAW-SECURITY-001.md` §2 | Policy line: agent read-only KV; brain owns `somabrain/*` (write allowed on own mount). Replaces blanket "read-only KV v2". |

### 6.2 Listed (not applied — medium/large or code-adjacent)

| Item | Why not fixed here |
|---|---|
| SECURITY §1.5 policy table rewrite (brain write grants; agent path list) | Table is normative across TRIAD seats — needs coordinated ACK |
| `docker-compose.yml` "RAM tmpfs custodian" comments | Code-adjacent comments; deferred with Δ-08 |
| Remove T0 root **read** fallbacks in `init_vault.py` / `seed_clef_vault.py` | Product code change; out of "docs only" scope |
| `brain-runtime.hcl` comment "just this key" vs whole-doc read | Policy comment cleanup with R-02 split |

---

## 7. GO / NO-GO

| Gate | Result |
|---|---|
| No secrets in code / git / `.env` | **PASS** |
| Root never written to disk (guards present) | **PASS** |
| Orphan tokens + revoke-self | **PASS** |
| Fail-closed secrets + auth 503 | **PASS** |
| Policies least-privilege for agent runtime | **PASS** |
| Docs match code on law-critical rules | **PASS** (two doc fixes applied; remainder listed) |
| Residual risks documented and ranked | **PASS** |

### **GO** — local/standalone Vault bootstrap and auth fail-closed path.

Conditions carried forward (not blockers for this GO):
1. Production must replace T0 volume custodian with KMS auto-unseal / tmpfs (R-01).
2. brain whole-document read (R-02) must be ACK'd or split before multi-tenant production.
3. T0 root **read** fallbacks (R-03) should be removed in a code pass.

---

## 8. Verification commands (re-run)

```bash
# orphan + revoke
grep -n 'no_parent\|revoke-self\|VAULT_TOKEN_TTL_HOURS' infra/standalone/vault_scoped_tokens.py

# no root write
grep -n 'ROOT_ACCOUNT\|vault_root_token' infra/standalone/vault_scoped_tokens.py infra/standalone/vault_unseal.py infra/standalone/bootstrap_exec.py

# policies
grep -n 'capabilities' infra/standalone/vault-policies/*.hcl

# fail-closed
grep -n 'VaultAuthError\|F-10\|F-11' services/common/vault_secrets.py

# compose T0
grep -n 't0_agent\|VAULT_TOKEN_FILE\|VAULT_TOKEN_TTL' infra/standalone/docker-compose.yml

# auth status
grep -n 'ServiceUnavailableError\|status=200\|status_code = 503' admin/auth/api.py admin/common/exceptions.py

# .env topology
grep -nE 'PASSWORD|SECRET|API_KEY' infra/standalone/.env || echo 'no secret keys in .env'
```

---

*security-reviewer owns this report. Code is the only source of truth. No secret values are recorded here.*

*End of SOMA-RPT-SEC-CODE-DOCS-001 v1.0.0*
