# SOMA-RPT-SEC-VAULT-001 — Vault token custody, orphan-lease incident & ceremony as-built

## Document Control

| Field | Value |
|---|---|
| Document Title | Vault token custody, orphan-lease incident & ceremony as-built |
| Document Identifier | SOMA-RPT-SEC-VAULT-001 |
| Version | 1.0.0 |
| Date | 2026-10-13 |
| Status | Draft |
| Author | security-reviewer (somaAgent01) |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2027-01-13 |
| Related | `SOMA-STD-BOOTSTRAP-001`, `SOMA-STD-SECURITY-001`, `SOMA-LAW-SECURITY-001`, `SOMA-ARCH-SEC-TOKEN-001`, `SOMA-RPT-SEC-REVIEW-2026-10-13`, `infra/standalone/vault_scoped_tokens.py` |
| Source of truth | **Live code** under `infra/standalone/` + validated operator ceremony (2026-10-13). Docs yield to code. |
| Audience | Human Operator, security-reviewer, soma-vault-authority, A2A peers |
| Scope | `somaAgent01` standalone Vault bootstrap (sibling seats inherit the same ceremony law) |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-13 | security-reviewer (somaAgent01) | Initial issue. Incident audit (token expiry + revoke-self child kill + root-on-disk), ceremony as-built, T0 custodian truth (named volume, not tmpfs), orphan-token rule, 720h operator TTL, doc-vs-code delta register. |

---

> **Evidence rule:** every operational claim cites live code (`file:line`) or a dated operator observation. No secret values appear in this document. Code wins over docs.

---

## 1. Executive summary

Three linked Vault failures occurred on 2026-10-13. All three are now explained by live code and the validated ceremony. None is a mystery.

| # | Event | Root cause | Status |
|---|---|---|---|
| **I-1** | Login `503 Identity service is not configured` after ~24h of uptime | Scoped `agent_runtime_token` expired (TTL was 24h). App fail-closed on `VaultAuthError` while reading `identity_password_pepper` / `django_secret_key` / `*_api_key`. **Fail-closed was correct.** | Recovered by re-ceremony; TTL now operator-set **720h** |
| **I-2** | During recovery, root token was written to `/run/t0/vault_root_token` | R-SEC-01 violation by operator session. Mount is a Docker named volume on **ext4**, not tmpfs. | Root file deleted; that root `revoke-self`'d. Mint script correctly refused the write. |
| **I-3** | Service tokens died immediately after root was revoked | **Outage root cause.** Tokens minted as **children** of the one-shot root. Vault revokes the child tree on parent `auth/token/revoke-self`. Without `no_parent`, every service token dies with root. | Fixed in `vault_scoped_tokens.py` (`no_parent: True`); validated. |

**Law now encoded in code and in this report:**

1. Service tokens are **orphans** (`no_parent: True`) so root `revoke-self` cannot kill them.
2. Service token TTL in this deploy is **720h (30d)** operator policy — required env, no default.
3. T0 custodian in this deploy is Docker named volume **`standalone_t0_agent` (ext4)** — **not** tmpfs — documented as the §2.1a local-standalone exception.
4. Ceremony: `generate-root` (unseal key) → mint **orphan** `agent-runtime` + `brain-runtime` → **revoke root immediately** → **never leave root on disk**.
5. Policy grants are read-only on `secret/data/agent/credentials` + `secret/data/agent/api_keys` (agent). No write on those paths. No `sys/`. Brain additionally owns `somabrain/*` only.

---

## 2. Incident audit

### 2.1 I-1 — Scoped token expiry (availability, fail-closed correct)

| Field | Detail |
|---|---|
| Symptom | `POST /auth/login` → HTTP 503 `Identity service is not configured`. E2E 8/8 honest FAIL at login. |
| Detection | Playwright live run + operator session |
| Mechanism | `agent_runtime_token` (95B, mtime 2026-10-12) TTL 24h expired → Vault 403 on `secret/data/agent/credentials` (`identity_password_pepper`, `django_secret_key`) and `secret/data/agent/api_keys` |
| Code path | `services/common/vault_secrets.py` / UnifiedSecretManager → `VaultAuthError`; identity fail-closes (`admin/auth/identity.py`) |
| Verdict | **Correct fail-closed behaviour** (F-10 / F-11). An expired lease must stop the service cleanly, never widen policy, never invent a secret. |
| Residual | Operator TTL was too short for this environment. `.env` now carries `VAULT_TOKEN_TTL_HOURS=720`. Lease length remains **required config, no default** (Rule 91). |

### 2.2 I-2 — Root token written to T0 (R-SEC-01 absolute violation)

| Field | Detail |
|---|---|
| Symptom | `vault_root_token` created at `/run/t0/vault_root_token` |
| Custodian reality | Docker volume `standalone_t0_agent` mounted at `/run/t0` → **ext4** (`/dev/vda1` class). **Not tmpfs.** |
| Law | R-SEC-01 absolute: root is **never** written to T0 or any filesystem. Root is process RAM of a one-shot only. |
| Detection | `vault_scoped_tokens.py` `_t0_custodian_allows(ROOT_ACCOUNT, …)` refused the mint write (correct). Operator inspection confirmed file presence. |
| Remediation | File removed. That root revoked via `auth/token/revoke-self`. No root remains on disk (confirmed: T0 holds `vault_unseal_key`, `agent_runtime_token`, `brain_runtime_token` only). |
| Code hardening | `vault_scoped_tokens.py:150-155`, `vault_unseal.py:117-121`, `bootstrap_exec.py` `t0_write` all refuse `vault_root_token`. |
| Operator directive | **"NO TOENS IN ROOT" / never root on disk.** Standing law. |

### 2.3 I-3 — Root `revoke-self` killed child service tokens (**outage root cause**)

| Field | Detail |
|---|---|
| Symptom | Newly minted `hvs.*` service tokens became invalid the moment root was revoked. Services 403. |
| Mechanism | Vault token hierarchy: `auth/token/create` without `no_parent` produces a **child** of the creating token. `auth/token/revoke-self` on root **revokes the entire descendant tree**. |
| Timeline | Mint service tokens (children of root) → `revoke-self` root → children die → "tokens are broken" → operator re-mints → same cycle. |
| Fix (live code) | `infra/standalone/vault_scoped_tokens.py:305-308` — `"no_parent": True` (orphan). Commit `5cd70896` *"fix: orphan Vault service tokens + 720h lease"*. |
| Fix (process) | Ceremony always: mint **orphans first**, then revoke root. Root revoke is mandatory and must remain safe **because** children are orphans. |
| Law | **Every service token MUST be orphan (`no_parent: True`).** Root revoke without orphan is a self-inflicted outage. |
| Token shape | Client tokens are `hvs.*`, TTL `720h`, `no_default_policy: True`, renewable via `auth/token/renew-self` only. |

### 2.4 What was verified after remediation (2026-10-13)

- T0 volume `standalone_t0_agent` at `/run/t0`: **no** `vault_root_token` present.
- `agent_runtime_token` / `brain_runtime_token` present (scoped, orphan).
- `vault_unseal_key` present (unseal custodian account — not root).
- `vault operator generate-root` works from the T0 unseal key + OTP; decoded root is **process RAM only**.
- Mint path requires `T0_DIR`, `VAULT_ADDR`, `VAULT_TOKEN_TTL_HOURS`, optional one-shot `VAULT_TOKEN`.
- Root after mint is revoked (`revoke-self`); service tokens survive **because** they are orphans.

---

## 3. Ceremony as-built (normative for this deploy)

This is the process that was validated. Docs that disagree with this section are stale.

```
PRECONDITION
  Vault running (sealed or unsealed). Unseal key in T0 account
  `vault_unseal_key` (or operator-held VAULT_UNSEAL_KEY). No root on disk.

1. UNSEAL (if sealed)
   python3 vault_unseal.py --unseal-only
   # reads unseal key from T0 / keychain / one-shot env — never a repo file

2. ROOT (one-shot, RAM only)
   vault operator generate-root   # unseal key + OTP
   decode encoded token in process memory
   export VAULT_TOKEN=<root>      # THIS process env only — never a file
   # ABSOLUTE: do not write vault_root_token to T0, /tmp, or any path

3. MINT ORPHANS + INSTALL POLICY
   T0_DIR=/run/t0 VAULT_ADDR=… VAULT_TOKEN_TTL_HOURS=720 \
     python3 vault_scoped_tokens.py
   # installs vault-policies/*.hcl
   # mints agent-runtime + brain-runtime with:
   #   no_parent: True          ← ORPHAN (survives root revoke)
   #   no_default_policy: True
   #   ttl: 720h (operator env)
   # writes ONLY: agent_runtime_token, brain_runtime_token
   # refuses vault_root_token (R-SEC-01 absolute)

4. REVOKE ROOT (mandatory, safe because step 3 was orphan)
   auth/token/revoke-self
   # performed automatically at end of vault_scoped_tokens.py:353-355
   # no root remains valid; no root remains on disk

5. RUNTIME
   Services read their own T0 token via VAULT_TOKEN_FILE=/run/t0/<account>
   Never root. Never another consumer's token. Never a secret in ENV steady-state.
```

**Break-glass root later:** same as step 2 — `generate-root` + unseal authority, use in RAM, `revoke-self` in the same session. Never park root.

### 3.1 Why orphan is not optional

| Mint shape | Root `revoke-self` effect | Result |
|---|---|---|
| Child token (no `no_parent`) | **Entire subtree revoked** | Service tokens die → outage (I-3) |
| Orphan token (`no_parent: True`) | Only root dies | Service leases continue to TTL |

---

## 4. T0 custodian truth (as-built)

### 4.1 This deploy — exact

| Property | Value |
|---|---|
| Compose volume | `t0_agent` (`docker-compose.yml` volumes block) |
| Docker volume name | **`standalone_t0_agent`** (project `standalone` + volume `t0_agent`) |
| Filesystem | **ext4** (named volume on the Docker host disk) — **NOT tmpfs** |
| Mountpoint in containers | `/run/t0` |
| Mode / ownership | directory 0700; token files 0600; chowned to consumer UID (`BOOTSTRAP_T0_UID=1000`) |
| Accounts allowed | `vault_unseal_key`, `agent_runtime_token`, `brain_runtime_token` |
| Accounts forbidden | **`vault_root_token` (absolute)** |

There is also `standalone_t0_postgres` (`t0_postgres` → `/run/t0_pg`) for the postgres consumer mirror of the **scoped** agent token. Same rules.

### 4.2 Doc-vs-history contradiction (resolved here)

Many comments still say "RAM tmpfs custodian" (`vault_unseal.py` module docstring, `docker-compose.yml` header, older standards). **That is not this deploy.** The live code accepts two custodian shapes (§2.1a):

1. **tmpfs / ramfs** — preferred. RAM-only.
2. **Dedicated named-volume mount** (own `/proc/mounts` entry, not `/`, not overlay) — **documented local-standalone exception**. Justification: the 1-of-1 unseal key must survive container recreate or the store becomes permanently un-unsealable; Linux containers have no OS keychain; the volume is container-native (not the repo, not a host bind). Production replaces this with KMS auto-unseal and the exception disappears.

Refused: repo path, host bind, overlay/root-fs, ordinary directory, `/tmp` on root fs.

**This deploy uses exception (2).** Documented, allowed, residual risk accepted for local standalone only. Do not describe it as tmpfs.

---

## 5. Policy grants (as-built, live `.hcl`)

### 5.1 `agent-runtime` — somaAgent01 runtime

| Path | Capabilities |
|---|---|
| `secret/data/agent/credentials` | `read` |
| `secret/data/agent/api_keys` | `read` |
| `secret/data/agent/api_keys/*` | `read` |
| `secret/metadata/agent/credentials` | `read` |
| `secret/metadata/agent/api_keys/*` | `read` |
| `auth/token/renew-self` | `update` |
| `auth/token/lookup-self` | `read` |

**Denied by omission:** any write on secret paths, `sys/*`, `auth/token/create`, other mounts.

### 5.2 `brain-runtime` — SomaBrain runtime

| Path | Capabilities |
|---|---|
| `secret/data/agent/credentials` | `read` (shared keys only — document-granular KV) |
| `somabrain/data/*` | `read`, `update`, `create`, `delete` |
| `somabrain/metadata/*` | `read`, `list`, `delete` |
| `auth/token/renew-self` | `update` |
| `auth/token/lookup-self` | `read` |

**Denied by omission:** `sys/*`, `auth/token/create`, `secret/data/agent/api_keys`, every other mount.

Operator fact for the agent seat: **read `secret/data/agent/credentials` + `api_keys` only. No write. No `sys/`.** Matches `agent-runtime.hcl`.

---

## 6. Doc-vs-code delta register

| ID | Document claim | Live code / validated process | Severity | Disposition |
|---|---|---|---|---|
| Δ-01 | T0 is "RAM tmpfs" everywhere | `standalone_t0_agent` is a **named volume on ext4**. Code allows tmpfs **or** dedicated volume (§2.1a). | HIGH | Errata in BOOTSTRAP-001 / SECURITY-001; this report is as-built truth |
| Δ-02 | BOOTSTRAP-001 §0 "vault_scoped_tokens still requires VAULT_TOKEN_FILE and SECRETS_DIR" | **False.** Live script: `T0_DIR` + one-shot `VAULT_TOKEN` / keychain. No `SECRETS_DIR`. No root in T0. | HIGH | Corrected in BOOTSTRAP-001 errata |
| Δ-03 | Ceremony "Local may skip root revoke (step 6)" | **Always revoke** after mint (`vault_scoped_tokens.py:353-355`). Leaving root alive is banned. | CRITICAL | BOOTSTRAP-001 §3.4 amended |
| Δ-04 | No orphan-token rule in standards | `no_parent: True` is **mandatory**. Without it, `revoke-self` kills children (I-3). | CRITICAL | New normative rule (this report §3.1; SECURITY-001; CLAUDE.md) |
| Δ-05 | `.env.example` `VAULT_TOKEN_TTL_HOURS=24` | Operator deploy uses **720h**. Value is required, never defaulted. | MED | Documented; example stays short-TTL as a *safer* sample; live `.env` is 720h by operator choice |
| Δ-06 | `bootstrap_exec.py` `mint_scoped` creates tokens **without** `no_parent` and does **not** `revoke-self` | Delta vs `vault_scoped_tokens.py`. If this mint is paired with root revoke, children die (I-3). | **CRITICAL residual** | **Mint path of record = `vault_scoped_tokens.py`.** `bootstrap_exec.py` mint must not be used with `revoke-self` until it sets `no_parent`. (Code fix deferred — docs-only turn.) |
| Δ-07 | `vault_unseal.py` module docstring "never a named disk volume" | Contradicts §2.1a and live T0 volume. Function bodies already updated (dirty tree). | MED | Docstring truth = §2.1a (see errata) |
| Δ-08 | compose comments "T0_DIR RAM tmpfs custodian" on services that mount `t0_agent` | Those mounts are named volumes. Comments are aspirational. | LOW | Errata; comment cleanup is code-adjacent, deferred |
| Δ-09 | Root written to T0 (historical) | Now hard-refused in three scripts. | FIXED | Verified in code |
| Δ-10 | Policy "read secret/data/agent/*" (SECURITY-001 §1.5 table) | Live agent policy is **credentials + api_keys only** (not a wildcard `agent/*`). | MED | SECURITY-001 table corrected in errata |

---

## 7. Standing security law (after this incident)

1. **Code is the only source of truth.** Docs must match `infra/standalone/*.py` and `vault-policies/*.hcl`. When they disagree, code wins and the doc is a defect.
2. **Never root on disk.** No `vault_root_token` in T0, `/tmp`, repo, key file, or compose env. Root = one-shot process RAM → `revoke-self`.
3. **Never secrets in ENV steady-state.** `VAULT_TOKEN` / `VAULT_UNSEAL_KEY` are one-shot only and stripped before `execve`. Long-running services hold a scoped T0 token path (`VAULT_TOKEN_FILE`).
4. **Orphan service tokens only.** `no_parent: True` on every `auth/token/create` for runtime. Root revoke must be safe.
5. **Fail closed.** Expired/missing token ⇒ refuse (503 / raise). Never invent, default, or fall back to a broader identity.
6. **T0 is a custodian, not a junk drawer.** tmpfs or documented named-volume exception only. Scoped tokens + unseal key. Never root. 0700/0600. Per-consumer accounts.
7. **No shims, fakes, mocks, stubs, placeholders.** Acceptance = live real services.

---

## 8. Verification checklist (re-run after any Vault change)

```bash
# 1. No root account file in any T0 volume
docker run --rm -v standalone_t0_agent:/t0 alpine ls -la /t0
# expect: vault_unseal_key, agent_runtime_token, brain_runtime_token
# expect ABSENT: vault_root_token

# 2. Mint script refuses root writes (unit of the guard)
grep -n 'ROOT_ACCOUNT\|vault_root_token' infra/standalone/vault_scoped_tokens.py infra/standalone/vault_unseal.py infra/standalone/bootstrap_exec.py
# expect: refusal paths only — never a store/write of root

# 3. Orphan is mandatory on mint
grep -n 'no_parent' infra/standalone/vault_scoped_tokens.py
# expect: True

# 4. TTL is required, not defaulted
grep -n 'VAULT_TOKEN_TTL_HOURS' infra/standalone/vault_scoped_tokens.py infra/standalone/.env
# expect: require_env / operator value; no silent default in mint

# 5. Policies have no sys/ and no runtime write on secret/agent/*
grep -n 'sys/\|capabilities' infra/standalone/vault-policies/*.hcl
```

---

## 9. Residual risks

| # | Risk | Sev | Mitigation |
|---|---|---|---|
| RV-1 | `bootstrap_exec.py` mints non-orphan tokens (Δ-06) | HIGH | Use `vault_scoped_tokens.py` as mint path of record; add `no_parent` in a later code turn |
| RV-2 | Named-volume T0 is durable storage (ext4) — leftover files survive container recreate | MED | 0600 + per-consumer; never root; production KMS auto-unseal + tmpfs/FD |
| RV-3 | 720h lease is long if a token leaks | MED | Renewable; re-mint on suspicion; policy is read-mostly; monitor lookup-self anomalies |
| RV-4 | 1-of-1 unseal key in the same volume family as services | MED | Local-only; prod = KMS auto-unseal / 3-of-5 |
| RV-5 | Comments still say "tmpfs" in several files (Δ-07/Δ-08) | LOW | Errata until comment pass; this report is authoritative for as-built |

---

## 10. Disposition

| Deliverable | Status |
|---|---|
| This report | ISSUED |
| BOOTSTRAP-001 errata (T0 volume, orphan, 720h, root) | Issued in same commit |
| SECURITY-001 errata (same + policy table) | Issued in same commit |
| CLAUDE.md SOMA LAW security block | Issued in same commit |
| DOCUMENT-REGISTER | Regenerated (`scripts/gen_register.py`) |
| Product code changes | **None this turn** (docs-only operator order) |

---

*End of SOMA-RPT-SEC-VAULT-001 v1.0.0*
