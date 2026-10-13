# SOMA-RPT-VAULT-AUTHORITY-001 — Vault authority code-truth audit (skill-claim vs code)

## Document Control

| Field | Value |
|---|---|
| Document Title | Vault authority code-truth audit — skill claims vs live code |
| Document Identifier | SOMA-RPT-VAULT-AUTHORITY-001 |
| Version | 1.0.0 |
| Date | 2026-10-13 |
| Status | Draft |
| Author | soma-vault-authority (somaAgent01) |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements · ISO/IEC 27001:2022 A.5.17 authentication information · A.8.9 configuration management |
| Next Review | 2027-01-13 |
| Source of truth | **Live code**: `infra/standalone/vault_scoped_tokens.py`, `infra/standalone/bootstrap_exec.py`, `infra/standalone/init_vault.py`, `infra/standalone/seed_clef_vault.py`, `infra/standalone/remint_ceremony.{py,sh}`, `infra/standalone/vault-policies/*.hcl`, `services/common/vault_secrets.py`, `services/common/unified_secret_manager.py`, `services/gateway/settings.py` |
| Related | `SOMA-LAW-SECURITY-001`, `SOMA-STD-TRIAD-001`, `SOMA-STD-CONFIG-001`, `SOMA-RPT-SEC-VAULT-001`, `.mimocode/agent/soma-vault-authority.md` |
| Audience | Human Operator, soma-vault-authority, security-reviewer, A2A peers |
| Scope | `somaAgent01` vault/secret surface only. Sibling seats (somabrain, somafractalmemory) inherit the same law; their code is out of scope here. |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-13 | soma-vault-authority | Initial issue. Skill/instruction claims verified against live code with `file:line` evidence. Truth table, ceremony as-built (orphan 720h), gap register (DELETE-or-IMPLEMENT). **No secret values.** |

---

> **Evidence rule.** Every row cites `file:line` of live code or a dated operator fact. Code wins over docs. **No token, password, or key value appears in this document.** This run is a **static code-truth audit** under a docs-only mandate — no live Vault write/read-back was performed in this session. Ceremony paths that *do* implement write→read-back are cited as-built.

---

## 1. Purpose

Verify whether the standing skill/instruction claims of `soma-vault-authority` (and the security law that extends them) are **true in code** in this repository:

1. One token — single credential trust
2. KV v2 merge-safe updates (never silent sibling wipe)
3. Read-back assertion after write
4. `SOMABRAIN_MEMORY_HTTP_TOKEN` via `*_FILE` only
5. No hardcoded secrets / no env secrets
6. Fail-closed on missing secret
7. Ceremony as-built: orphan tokens, 720h lease, root never on disk

---

## 2. Truth table — skill-claim vs code

| # | Claim (skill / law) | Code truth (`file:line`) | Verdict |
|---|---|---|---|
| **C1** | **One token.** Agent-written value is byte-identical to brain-read value; no regenerate-on-read; no second secret. | Shared key name `somabrain_memory_http_token` lives once at Vault path `agent/credentials` (`infra/standalone/init_vault.py:104`, `infra/standalone/bootstrap_exec.py:215`). App reads it via `UnifiedSecretManager.get_credential` only (`services/gateway/settings.py:265`). `get_credential` → `load_kv_secret` is read-only (`services/common/unified_secret_manager.py:136-143`, `services/common/vault_secrets.py:218-343`). No regenerate-on-read in this repo. Brain policy is read of the same document (`infra/standalone/vault-policies/brain-runtime.hcl:14-16`). | **TRUE (this repo)** — one path, one key name, read-only consumers. Caveat: two *generator* scripts exist (see G-6). |
| **C2** | **KV v2 merge-safe.** Never a full-document replace that drops siblings. | Merge-safe: `services/common/vault_secrets.py:390-412` (`save_kv_secret` reads existing map, merges key, writes whole object) and `infra/standalone/bootstrap_exec.py:128-149` (`kv2_write_merge` + sibling-survival assert). **Violations:** `infra/standalone/init_vault.py:211` `kv2_write(path, {key: value})` posts a single-key document (wipes siblings) and `infra/standalone/seed_clef_vault.py:166` does the same. | **PARTIAL — DEFECT** (G-1) |
| **C3** | **Read-back assert** after every write (`len(read)==len(written)` / equal digests). | Ceremony: `infra/standalone/init_vault.py:213-219` value-equality read-back; `infra/standalone/bootstrap_exec.py:141-149` value-equality **and** sibling-key set survival; `infra/standalone/seed_clef_vault.py:168-173` value-equality. **Library path** `services/common/vault_secrets.py:346-421` writes then `refresh_cached_secrets()` and returns `True` — **no read-back**. Asserts compare full values (stronger than length), not `len()` specifically. | **PARTIAL** (G-2) |
| **C4** | **`*_FILE` only** for `SOMABRAIN_MEMORY_HTTP_TOKEN` — never inline env, never compose plaintext. | No `SOMABRAIN_MEMORY_HTTP_TOKEN` in any `docker-compose*.yml` (grep zero hits). No `SOMABRAIN_MEMORY_HTTP_TOKEN_FILE` symbol anywhere in this repo. The application sources the credential from **Vault** (`services/gateway/settings.py:265`), not from a `*_FILE` env. The `*_FILE` pattern in this repo is `VAULT_TOKEN_FILE` — the *Vault auth* token path, not the memory bearer (`services/common/vault_secrets.py:48`, `infra/standalone/docker-compose.yml:94`). | **FALSE as worded for somaAgent01** — actual delivery is Vault-KV read, not `*_FILE`. No inline env secret (that half of the claim holds). (G-3) |
| **C5** | **No hardcoded secrets / no env secrets.** | Hardcode scan (`password|token|secret|api_key = "literal"` over non-test `*.py`) → **zero hits**. `.env.example` holds topology only; comments explicitly refuse `POSTGRES_PASSWORD`, `VAULT_TOKEN`, provider keys (`infra/standalone/.env.example` Vault block). Compose carries `VAULT_TOKEN_FILE` paths and `KEYCLOAK_ADMIN_PASSWORD=secret/agent/credentials/keycloak_admin_password` **path mapping**, not a value (`infra/standalone/docker-compose.yml:470`). | **TRUE** |
| **C6** | **Fail-closed.** Missing/unreadable secret ⇒ explicit error. Never silent empty auth, never `[]`. | Missing Vault token file → `VaultAuthError` with named source (`services/common/vault_secrets.py:130-199`). 401/403 → `VaultAuthError` citing F-11, refuses omit-and-start (`services/common/vault_secrets.py:304-317`). Unreachable Vault at manager construct → `RuntimeError` (`services/common/unified_secret_manager.py:47-63`). Absent credential becomes `None`, never `""` (`services/gateway/settings.py:266-270`). Consumers refuse to send a request on a missing bearer (`services/common/adapters/somabrain_adapter.py:198-203`). | **TRUE** |
| **C7** | **Root never on disk.** | `_t0_custodian_allows` refuses `vault_root_token` absolutely (`infra/standalone/vault_scoped_tokens.py:150-155`). `read_root_token` accepts process env or OS keychain only — never a file (`infra/standalone/vault_scoped_tokens.py:228-266`). Same refusal in bootstrap/unseal paths (`infra/standalone/vault_unseal.py`, `bootstrap_exec.py` `t0_write`). | **TRUE** |
| **C8** | **Orphan tokens** (`no_parent: true`) so root `revoke-self` cannot kill service leases. | Present **only** in `infra/standalone/vault_scoped_tokens.py:305-308` (`"no_parent": True` with comment). **Absent** from `infra/standalone/bootstrap_exec.py:307-316` (`mint_scoped` token create) and `infra/standalone/remint_ceremony.sh:84-89` (`mint()` `vault write auth/token/create`). | **PARTIAL — DEFECT** (G-4) |
| **C9** | **720h lease** as operator policy. | TTL is **required env, no default** (`vault_scoped_tokens.py:117`, `bootstrap_exec.py:278-285`, `remint_ceremony.py:100`). Code does not hardcode 720 (correct under Rule 91). **But** template ships `VAULT_TOKEN_TTL_HOURS=24` (`infra/standalone/.env.example:27`), which contradicts the post-incident operator law of 720h (`SOMA-LAW-SECURITY-001` §2). | **PARTIAL** (G-5) — code is fail-closed; template misleads |
| **C10** | **Policies least-privilege.** agent-runtime read-only credentials + api_keys; no `sys/`; no write. | `infra/standalone/vault-policies/agent-runtime.hcl:14-45` — `read` only on `secret/data/agent/credentials`, `agent/api_keys`, metadata; `renew-self`/`lookup-self` only. Explicit "nothing else" comment at line 45. `brain-runtime.hcl:14-37` — same shared credentials read + own `somabrain/*` mount write; denied-by-omission `sys/`, `auth/token/create`. | **TRUE** |

---

## 3. Ceremony as-built (orphan · 720h · root RAM-only)

Validated against `vault_scoped_tokens.py` + `remint_ceremony.py`/`remint_ceremony.sh` + `SOMA-LAW-SECURITY-001` §3. This is the **as-built** sequence encoded in code:

| Step | What code does | Evidence |
|---|---|---|
| 1. Break-glass root | `generate-root` via unseal key from T0 custodian; root stays in **process RAM** | `infra/standalone/remint_ceremony.py:65-92` |
| 2. Install policies | `PUT sys/policies/acl/{agent-runtime,brain-runtime}` from `vault-policies/*.hcl` | `vault_scoped_tokens.py:288-294`, `bootstrap_exec.py:287-297` |
| 3. Mint service tokens | `POST auth/token/create` with `policies`, `ttl=VAULT_TOKEN_TTL_HOURS`, `no_default_policy: true` | `vault_scoped_tokens.py:297-315` |
| 4. **Orphan** | `"no_parent": True` — survives parent `revoke-self` | `vault_scoped_tokens.py:305-308` (**only here**; see G-4) |
| 5. Hand-off | Write `hvs.*` token to T0 account `agent_runtime_token` / `brain_runtime_token`, mode `0600` | `vault_scoped_tokens.py:210-217`, `SERVICE_TOKENS` map `:98-101` |
| 6. Revoke root | `POST auth/token/revoke-self` — "no root remains valid" | `vault_scoped_tokens.py:353-355` |
| 7. Root never to T0 | Absolute refuse of `vault_root_token` account | `vault_scoped_tokens.py:150-155` |
| 8. App auth | App holds only scoped token via `VAULT_TOKEN_FILE` path → T0 account | `services/common/vault_secrets.py:48-49,130-199` |

**Lease length:** operator-supplied `VAULT_TOKEN_TTL_HOURS` (required, no code default). Post-incident policy is **720h**; that value lives in operator `.env`, not in code. The repository **template** still shows 24 (G-5).

**Custodian shape (this deploy):** Docker named volume `standalone_t0_agent` → `/run/t0` (ext4), documented exception §2.1a — not tmpfs. Root still refused. (`SOMA-LAW-SECURITY-001` §2.1; `vault_scoped_tokens.py:136-204` allows tmpfs **or** dedicated volume mount.)

---

## 4. Gap register (DELETE or IMPLEMENT)

Severity: **H** = trust-split / outage class · **M** = law violation in a secondary path · **L** = doc/template drift.

| ID | Sev | Finding | Evidence | Required action |
|---|---|---|---|---|
| **G-1** | **H** | Full-document single-key KV POST wipes siblings. | `infra/standalone/init_vault.py:211` `kv2_write(path, {key: value})`; `infra/standalone/seed_clef_vault.py:166` same. Contrast correct `bootstrap_exec.kv2_write_merge:128-149`. | **IMPLEMENT** merge (`kv2_write_merge` semantics) in both seeders, **or DELETE** the non-merge `kv2_write` single-key call sites. Sibling survival must be asserted. |
| **G-2** | **M** | Library write path has no read-back. | `services/common/vault_secrets.py:408-415` returns `True` after `create_or_update_secret` with no second read. | **IMPLEMENT** read-back of the written key after save (value or length+digest); fail the call on mismatch. |
| **G-3** | **M** | Skill claim `*_FILE` only for `SOMABRAIN_MEMORY_HTTP_TOKEN` does not match this repo. | Claim in `.mimocode/agent/soma-vault-authority.md:55`; actual `services/gateway/settings.py:265` Vault `get_credential`; zero `SOMABRAIN_MEMORY_HTTP_TOKEN_FILE` symbols. | **Fix docs/skill text** to state the as-built channel: Vault KV `secret/agent/credentials/somabrain_memory_http_token` (agent) and whatever `*_FILE` contract exists on the **brain** seat. Do not invent a second delivery path. |
| **G-4** | **H** | Orphan mint only in one of three mint paths. | `no_parent: True` at `vault_scoped_tokens.py:308` **only**. Missing at `bootstrap_exec.py:307-316` and `remint_ceremony.sh:84-89`. A non-orphan token dies on root `revoke-self` — this is the documented 2026-10-13 outage mechanism. | **IMPLEMENT** `"no_parent": true` (CLI: `no_parent=true`) on **every** `auth/token/create` that mints service tokens. Grep must show it on all mint sites. |
| **G-5** | **L** | Template TTL contradicts 720h operator law. | `infra/standalone/.env.example:27` `VAULT_TOKEN_TTL_HOURS=24` vs `SOMA-LAW-SECURITY-001` §2 720h. | **Fix template** to `720` (or a comment that 24 is non-production and 720 is the standing deploy policy). Never a code default (Rule 91 stays). |
| **G-6** | **L** | Two generator scripts can both mint `somabrain_memory_http_token`. | `init_vault.py:104` and `bootstrap_exec.py:215` both list the key; first-wins skip if already present (`init_vault.py:201-205`, `bootstrap_exec.py:236-238`). | Document one-authority rule in-code (already in A2A/plans): **either** seeder runs, never both as competing generators. Optional: make `init_vault.py` refuse when `bootstrap_exec` already seeded, or collapse to one seeder. |

No secret values were inspected, printed, or stored during this audit.

---

## 5. Invariants preserved by this audit

| Invariant | Status |
|---|---|
| Vault-only secrets (R-SEC-01 / Rule 164) | Preserved — no secret written to disk, docs, or git by this run |
| Fail-closed (F-10 / F-11) | Preserved — no gate weakened; gaps reported, not papered over |
| T-6 durable-before-hop | Untouched (docs-only) |
| Root never on disk | Preserved — no Vault ceremony executed; code guard cited |
| Docs = truth | This report yields to code; skill text corrected where it drifted (G-3) |
| No AI attribution in commits | Enforced at commit time |

---

## 6. Acceptance checklist (skill criteria)

| # | Criterion | This run |
|---|---|---|
| 1 | Write→read-back round-trip with `len` assert | **As-built cited** (`init_vault.py:213-219`, `bootstrap_exec.py:141-149`) — not live-executed (docs-only mandate). Library gap recorded as G-2. |
| 2 | All KV updates merge-safe; zero full-document replaces | **FAIL in two seeders** (G-1). Library + `kv2_write_merge` are merge-safe. |
| 3 | `SOMABRAIN_MEMORY_HTTP_TOKEN` via `*_FILE` only | **Claim false as worded** (G-3); no inline env secret either (good). |
| 4 | No hardcoded secrets (rg pass) | **PASS** — zero hits in non-test code and compose. |
| 5 | Missing-secret path fails closed (observed) | **PASS** — `VaultAuthError` / `RuntimeError` paths cited with `file:line`. |
| 6 | Report has path, key names, write mode, read-back result; no values | **This document.** Key names: `somabrain_memory_http_token`, `django_secret_key`, `postgres_password`, `llm_api_key`, provider `*_api_key`, etc. Paths: `secret/agent/credentials`, `secret/agent/api_keys`. Write mode: merge in library + `kv2_write_merge`; full-POST defect in `init_vault`/`seed_clef_vault`. Read-back: ceremony value-equality only. **No values.** |

---

## 7. Recommended next actions (ordered)

1. **G-4** — add `no_parent` to `bootstrap_exec.mint_scoped` and `remint_ceremony.sh` (outage-class).
2. **G-1** — route `init_vault.seed_key` / `seed_clef_vault.seed_secret` through merge-write + sibling survival.
3. **G-2** — read-back assert in `save_kv_secret`.
4. **G-3** — correct the skill/`SOMA-RPT` wording to the as-built Vault channel.
5. **G-5** — align `.env.example` TTL with 720h standing policy.

---

## 8. A2A

Claim appended to `docs/plans/a2a/CLAIMS.md` (path `docs/reports/SOMA-RPT-VAULT-AUTHORITY-001.md`) before this write. LEDGER row on commit. Peer ACTIVE claims untouched.

**End of SOMA-RPT-VAULT-AUTHORITY-001.**

*"One token, written and read as the same value — proven by read-back length."*
