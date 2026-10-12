# SOMA-STD-SECURITY-001 — TRIAD Enterprise Secret & Bootstrap Pattern

## Document Control

| Field | Value |
|---|---|
| Document Title | TRIAD Enterprise Secret & Bootstrap Pattern |
| Document Identifier | SOMA-STD-SECURITY-001 |
| Version | 1.0.0 |
| Date | 2026-10-11 |
| Status | Draft |
| Author | security-reviewer (somaAgent01) |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2027-01-11 |
| Applies to | `somaAgent01`, `somabrain`, `somafractalmemory` |
| Relationship | **Subordinate to `SOMA-ARCH-SEC-TOKEN-001` (sole trust-boundary authority: generation binding, Channel unification, degradation security, C-1/C-2/C-3).** This document **operationalizes** that ADR and SOMA-STD-BOOTSTRAP-001 (lifecycle/threat model) and SOMA-STD-CONFIG-001 R-SEC-*. Where this pattern conflicts with the ADR on trust boundary / token custody / degradation security, **the ADR wins**. |
| Supersedes | any T0 0777/0644 workaround, shared-root-token T0 handoff, `/run/secrets/*` password files, `SOMABRAIN_VAULT_TOKEN_FILE` / `SOMA_VAULT_TOKEN_FILE` aliases, `VAULT_TOKEN` as steady-state ENV |
| Governing law | VIBE 164 (Vault-only), VIBE 91 (fail-closed), Operator LAW 2026-10-11 |

**Operator LAW (verbatim constraints this pattern satisfies):** no secret files · no secrets in ENV steady-state · all secrets only in Vault · Channel ENV for third-party passwords · `VAULT_TOKEN_FILE` + T0 tmpfs 0700/0600 for scoped TTL tokens only · root in process RAM only, never a shared volume · never log secrets · never weaken fail-closed checks · no 0777 T0.

---

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-11 | security-reviewer (somaAgent01) | Initial issue. Vault-only secret custody, KV v2 merge-write lifecycle, channel delivery. Document Control brought to house style (SOMA-01-DOCS-001). |

---

## 1. THE ONE PATTERN (normative)

### 1.1 Lifecycle (every credential, every seat)

```
generate (CSPRNG, process RAM)
  → KV v2 MERGE-write (read-modify-write whole map; POST replaces document)
  → read-back assert (new key present AND all sibling keys survive)
  → deliver (Channel ENV for third-party PID1 | scoped TTL token to private T0)
  → drop root / del local value
  → execve target (VAULT_TOKEN / VAULT_UNSEAL_KEY stripped from child env)
```

Implemented by `infra/standalone/bootstrap_exec.py` (`kv2_write_merge` :102-123 is the reference; `seed_credentials` :177-219 must use it for **every** key). Reference merge assert also in peer `init_vault.py:seed_shared`.

**Banned at every step:** intermediate file · argv value · compose `environment:` secret · `.env` value · image layer · bind-mounted secret dir · log line · default/fallback (Rule 91).

### 1.2 Custodians (the only material outside Vault)

| Material | Local / T-8 | Staging | Production | NEVER |
|---|---|---|---|---|
| Unseal key | OS keychain (`soma-vault-t0/vault_unseal_key`) or operator `VAULT_UNSEAL_KEY` **in ceremony process ENV only** | 3-of-5 shamir, dual control | Cloud KMS auto-unseal | T0 shared volume · repo · `.env` |
| Root token | **Process RAM of the Ceremonial Seeder only**; mint-and-revoke preferred | Dual-control, time-boxed | Never persisted; break-glass `generate-root` | Any T0 · any running app · any file |
| Scoped service token | Per-consumer private T0 file (see 1.4) | same | Vault Agent / K8s auth | Shared T0 · ENV value · repo |
| AppRole `secret_id` | **Not used in this generation** (see §2) | — | KMS / orchestrator delivery | File |

### 1.3 Token environment names (ONE name, whole TRIAD)

| Name | Type | Who sets | Who reads | Notes |
|---|---|---|---|---|
| `VAULT_ADDR` | topology | compose | all | only Vault URL |
| `VAULT_TOKEN_FILE` | **path** to scoped TTL token | compose → `/run/t0/<consumer>_runtime_token` | app Vault clients | path only; never the credential |
| `VAULT_TOKEN` | **one-shot only** | ceremony operator / seeder parent | seeder / vault_inject | stripped before execve (`bootstrap_exec.py:303`) |
| `VAULT_UNSEAL_KEY` | one-shot only | operator to ceremony | `vault_unseal.py` | stripped before execve |
| `VAULT_INJECT` | Channel ENV map | compose | `vault_inject.py` | mapping spec, not secrets |
| `VAULT_TOKEN_TTL_HOURS` | required config | compose | seeder | **no default** (Rule 91) |

**Deleted forever:** `SOMABRAIN_VAULT_TOKEN*`, `SOMA_VAULT_TOKEN*`, `SECRETS_DIR`, `*_PASSWORD_FILE`, `SOMA_T0_SECRETS_DIR`.

### 1.4 T0 layout — PER CONSUMER (fixes multi-uid PermissionError)

The live defect: one shared `t0_ram` volume (`docker-compose.yml:59-64`) is mounted rw into every service (:150, :242, :270, :304, :331, :366, :439, :503). Root writes `vault_root_token` 0600 → appuser hits `PermissionError`. **0777/0644 is banned** (world-readable root/unseal = full compromise).

**Normative T0 model:**

```
Each consumer gets its OWN tmpfs, mode 0700, owned by that container's UID,
mounted at /run/t0 in that container ONLY.

  /run/t0/agent_runtime_token   → somaagent_standalone  (0600, that UID)
  /run/t0/brain_runtime_token   → somabrain app         (0600, that UID)
  /run/t0/sfm_runtime_token     → SFM worker (if any)   (0600, that UID)

Compose shape (per service, NOT one named volume):
  tmpfs:
    - /run/t0:mode=0700,uid=<svc-uid>,size=1m
```

Rules:
1. **Root token and unseal key NEVER enter any consumer T0.** Root lives only in the Ceremonial Seeder's process RAM (`bootstrap_exec.py:137` must drop `t0_read(ROOT_ACCOUNT)`; :155 must not write unseal to a volume shared with appusers — keychain or ceremony-only).
2. Exactly one file per T0: that consumer's scoped token. Mode 0600. Owner = consumer UID.
3. Seeder writes the token **as the consumer UID** (seteuid) or via a 0-byte pipe the consumer reads once. Never chmod 0777.
4. T0 is tmpfs with swap disabled. If swap is present, refuse (F-19).
5. App runtime reads **only** `VAULT_TOKEN_FILE` of its own T0. Fail-closed if unreadable.

### 1.5 Policies (`infra/standalone/vault-policies/*.hcl`)

| Policy | Grants | Denies |
|---|---|---|
| `agent-runtime` | read `secret/data/agent/*`, renew/lookup-self | `sys/*`, write, `auth/token/create` |
| `brain-runtime` | read `secret/data/somabrain/*` + **named shared keys** only (see 1.7), renew/lookup-self | same |
| `sfm-runtime` | read `secret/data/somafractalmemory/*`, renew/lookup-self | same |
| `ceremony` (seeder-only, root or short-lived) | all of the above + write KV + `auth/token/create` + policy install | never issued to a long-running app |

KV v2 is document-granular: `brain-runtime.hcl:14-16` reading the whole `agent/credentials` doc is **accepted and documented** OR shared keys are split to `secret/data/shared/*`. Pick one in the ACK; do not leave the comment lying.

### 1.6 First-boot identity material (`identity_password_pepper`)

Enterprise story — **ceremony-born, runtime-read-only**:

1. Birth: Ceremonial Seeder (`seed_credentials`) generates 32B CSPRNG and merge-writes `secret/agent/credentials/identity_password_pepper` **before** minting scoped tokens. This is the only writer.
2. Runtime: `services/common/identity/pepper.py` is read-only. `admin/auth/identity.py:114-117` fail-closes if absent.
3. `manage.py bootstrap_identity` (`admin/core/management/commands/bootstrap_identity.py`) is **verify/create-byceremony only**:
   - `--check` → read-only assert.
   - default create path **must not** run under `agent-runtime` (read-only policy correctly denies it). If pepper is missing after ceremony, that is an **incident**: re-run ceremony with root-in-RAM, not a policy widening.
4. Rotation invalidates every password hash — explicit, dual-control, never automatic.

The "agent-runtime cannot write the pepper" failure is **correct fail-closed behaviour**. Do not fix by granting write to runtime.

### 1.7 Shared credentials (agent ↔ brain)

Single authority: `secret/agent/credentials/somabrain_memory_http_token` (and `soma_api_token`). Seeded once by ceremony with merge-write + read-back. Brain reads; brain never regenerates. `SOMA-STD-BOOTSTRAP-001` §4.4 one-seeder rule stands.

### 1.8 Delivery channels

| Channel | Use | Mechanism |
|---|---|---|
| **Channel ENV** | third-party PID1 (postgres, keycloak, minio) | `vault_inject.py` reads KV into RAM → `execve` with mapped env only; bootstrap token stripped (:62-65) |
| **T0 token file** | first-party long-running apps | `VAULT_TOKEN_FILE` → private T0 scoped token |
| **Channel FD** | preferred long-term for first-party | inherited FD, one read + close (BOOTSTRAP-001 §2.5); implement when injector is unified |
| **BANNED** | — | `/run/secrets/*`, `secrets/vault-token`, compose secret env, `*_FILE` passwords |

### 1.9 Postgres auth truth

- `pg_hba.conf`: **`scram-sha-256` only** for host connections. No `127.0.0.1 trust`. `trust` only on the unix socket inside the postgres container for the entrypoint's own init, and only if the image requires it — documented exception.
- Password sync is **proven over SCRAM**: after Channel ENV inject, a TCP login as the app role must succeed with the Vault-sourced password and fail with a wrong one. A trust leg that "works with any password" is a failed test, not a pass.
- First init stores a SCRAM verifier in `pg_authid` (designed exception: hash, not plaintext).

### 1.10 Restart / unseal

| Event | Action |
|---|---|
| Vault sealed | ceremony unseals (keychain / KMS / operator ENV). Apps refuse to start (F-2). |
| App restart, T0 token valid | app reads T0, renews self. No root. |
| Scoped token expired (F-10) | app stops cleanly. Re-ceremony mints a new token into that consumer's T0. **Never** widen policy, re-mint as root, or read a backup. |
| Vault data volume lost | full re-ceremony (`sys/init`); old ciphertext gone; rotate all credentials. |
| Unseal key lost | Vault is sealed forever; restore from backup ciphertext + rekey ceremony. |

### 1.11 Audit

- Vault `audit "file"` on dedicated volume (`somaagent_vault_audit`) — HMAC-SHA256 under per-device salt only.
- Logs: paths, keys, HTTP status, token accessor. **Never values** (8-char fingerprint max, and only if unavoidable).
- Every mint/renew/revoke/KV write attributable.

---

## 2. Multi-container bootstrap decision

| Option | Verdict | Why |
|---|---|---|
| AppRole per service | **REJECTED for this generation** | `secret_id` delivery has no compliant non-file channel under compose without K8s/KMS. Adds a second credential class with the same bootstrap problem. **Named production target** when K8s auth / KMS-delivered secret_id exists. |
| One-shot root-in-RAM **per container** | **REJECTED** | Root in every start path = blast radius on any container RCE. Causes the shared-T0 PermissionError when root is parked on a volume. |
| **Cluster Ceremonial Seeder (chosen)** | **ADOPTED** | See below. |

**THE PICK: one Cluster Ceremonial Seeder per stack + per-service scoped TTL tokens in per-consumer T0.**

Rationale against the operator's axes:
- **Security:** root exists in exactly one process, for the length of one ceremony, then is dropped/revoked. Never on a shared volume, never in an app container. App compromise = one policy, one TTL.
- **Speed / millions of txns:** Vault is not on the txn hot path (SCRAM sessions + cached KV). Ceremony is O(services) per deploy/restart-window, not per txn. Tokens are renewable (`auth/token/renew-self`).
- **Thin:** one seeder binary (`bootstrap_exec.py`), one policy set, one T0 contract. No AppRole role/secret_id/rotation machinery until an orchestrator can deliver secrets without files.

Sequencing (normative):

```
1. Operator starts VAULT (sealed).
2. ONE Ceremonial Seeder (bootstrap_exec.py) runs with root-in-RAM
   (sys/init if first boot → else VAULT_TOKEN one-shot ENV from operator).
3. Seeder: unseal → install policies → seed credentials (incl. pepper)
   → mint agent/brain/sfm scoped tokens into EACH consumer's private T0
   → revoke root (prod) / drop from RAM (local) → exit OR execve agent target.
4. Other consumers start AFTER step 3; they only read their own T0.
```

For the agent container, seeder + target are the same PID1 (`bootstrap_exec.py --target /app/start.sh`). Brain/SFM run the same seeder shape **or** receive tokens from a brain-side ceremony — but **never** from the agent's T0.

---

## 3. Per-seat change list (file-level, no secret values)

### 3.1 somaAgent01 (this seat)

| File | Change |
|---|---|
| `infra/standalone/bootstrap_exec.py:137` | **Delete** `t0_read(ROOT_ACCOUNT)` fallback. Root = ceremony ENV or sys/init RAM only. |
| `infra/standalone/bootstrap_exec.py:155` | Stop writing `vault_unseal_key` to shared T0. Keychain / ceremony ENV only. |
| `infra/standalone/bootstrap_exec.py:102-123,177-219` | All seed paths already merge-safe; ensure `identity_password_pepper` stays ceremony-only. |
| `infra/standalone/bootstrap_exec.py:305` | Point `VAULT_TOKEN_FILE` at **private** T0 path; confirm child env has no root. |
| `infra/standalone/docker-compose.yml:59-64,150,242,…` | **Replace shared `t0_ram`** with per-service `tmpfs: /run/t0:mode=0700,uid=…`. |
| `infra/standalone/vault_unseal.py`, `init_vault.py`, `vault_scoped_tokens.py` | Remove any root/unseal T0 write that a non-ceremony UID can read. |
| `infra/standalone/vault_inject.py:37-46` | Keep Channel ENV; fail-closed; never log values. |
| `infra/standalone/entrypoint_pg_vault.py` + postgres image | pg_hba scram-sha-256; prove password over TCP scram. |
| `services/common/identity/pepper.py`, `bootstrap_identity.py` | No write from runtime. Document ceremony-only create. |
| `services/common/vault_secrets.py` | Token from `VAULT_TOKEN_FILE` private T0 only; fail-closed. |
| `docs/plans/a2a/*` | This pattern + LEDGER/CLAIMS. |

### 3.2 somabrain (peer seat)

| File | Change |
|---|---|
| compose / vault-agent templates | **Delete** `/run/secrets/postgres_password`, `/run/secrets/minio_*`, `/run/secrets/.vault_token` renders. Replace with Channel ENV (`vault_inject` pattern) at exec. |
| `infra/standalone/init_vault.py` | Keep `seed_shared` merge logic (reference). No password files. |
| token env | Unify to `VAULT_TOKEN_FILE` only; delete `SOMABRAIN_VAULT_TOKEN_FILE`. |
| T0 | Private per-consumer tmpfs 0700/0600; **no** shared T0 with root. |
| `somabrain/core/security/vault_client.py` | Read scoped token from private T0 via `VAULT_TOKEN_FILE`; fail-closed. |
| `brain-runtime.hcl` | Document whole-doc read or split `secret/data/shared/*`. |

### 3.3 somafractalmemory (peer lane)

| File | Change |
|---|---|
| `secrets/vault-token` | **DELETE** the file. Use `VAULT_TOKEN_FILE` → private T0. |
| compose `POSTGRES_PASSWORD_FILE` / `*_FILE` | **DELETE**. Channel ENV only. |
| compose `VAULT_DEV_*` | **DELETE** if present (dev mode banned). |
| token env | Unify to `VAULT_TOKEN_FILE`; delete `SOMA_VAULT_TOKEN_FILE`. |
| `admin/core/security/vault_client.py` | Same private-T0 resolution; keep fail-closed. |

---

## 4. Residual risks (ranked)

| # | Risk | Sev | Mitigation |
|---|---|---|---|
| R-1 | Root in ceremony RAM during first boot (memory scrape, core dump) | HIGH | `PR_SET_DUMPABLE=0`, short ceremony, revoke root after mint, no shared T0 |
| R-2 | Scoped token in T0 tmpfs readable by same-UID compromise | HIGH | 0700/0600, per-consumer T0, short TTL, renewable, F-10 stop-not-widen |
| R-3 | Peer seat still shipping `/run/secrets/*` + SFM `vault-token` until ACK/impl | HIGH | A2A HOLD + this standard; CI grep gates (BOOTSTRAP-001 §4.5) |
| R-4 | Channel ENV secrets visible in `/proc/<pid>/environ` of third-party PID1 | MED | container UID isolation, no sidecars sharing PID ns, core dumps off |
| R-5 | 1-of-1 local unseal key = single operator compromise | MED | local-only; prod = KMS auto-unseal / 3-of-5 |
| R-6 | Pepper ceremony loss → cannot verify passwords (availability) | MED | documented re-provision via `bootstrap_identity --email` (stdin password); never mint on read path |
| R-7 | KV merge race two seeders | MED | single ceremonial seeder invariant (F-20) |
| R-8 | AppRole deferred — restart without ceremony depends on TTL window | LOW | tokens renewable; F-10 fail-closed; AppRole/K8s auth is the named upgrade |
| R-9 | pg_hba unix-socket trust inside postgres container | LOW | documented image limitation; host/TCP always scram |

---

## 5. Verification gates (CI / e2e)

```bash
# no secret files
find . -name 'vault-token' -o -path '*/secrets/*' -o -name '*_PASSWORD_FILE*'
# no shared-mode T0
grep -RInE '0o777|0o644|chmod 777|mode=0?777' infra/
# no root on T0
grep -RInE 'ROOT_ACCOUNT|vault_root_token' infra/standalone/*.py   # must be RAM-only comments
# no token ENV aliases
grep -RInE 'SOMABRAIN_VAULT_TOKEN|SOMA_VAULT_TOKEN' .
# scram proof (live): TCP login with Vault password = success; wrong password = fail
```

---

*security-reviewer owns this document. Peer seats implement the same pattern; no seat invents a local variant. ACK required in `docs/plans/a2a/` before merge.*

*End of SOMA-STD-SECURITY-001 v1.0.0*
