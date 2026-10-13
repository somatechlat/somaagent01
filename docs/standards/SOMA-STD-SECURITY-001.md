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

**Operator LAW (verbatim constraints this pattern satisfies):** no secret files · no secrets in ENV steady-state · all secrets only in Vault · Channel ENV for third-party passwords · `VAULT_TOKEN_FILE` + T0 0700/0600 for scoped TTL tokens only · root in process RAM only, **never any volume, never disk** · **orphan service tokens only** (`no_parent: True`) · never log secrets · never weaken fail-closed checks · no 0777 T0. **Code is the only source of truth.**

---

## Revision History

> **2026-10-13 update:** Operating rules for orphan service tokens, 720h TTL,
> no root on disk, and T0 volume vs tmpfs are specified in
> `docs/standards/SOMA-LAW-SECURITY-001.md` (code = truth).

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-11 | security-reviewer (somaAgent01) | Initial issue. Vault-only secret custody, KV v2 merge-write lifecycle, channel delivery. Document Control brought to house style (SOMA-01-DOCS-001). |
| 1.1.0 | 2026-10-13 | security-reviewer (somaAgent01) | **Errata — match live code + validated ceremony** (SOMA-RPT-SEC-VAULT-001). T0 as-built = named volume `standalone_t0_agent` **ext4**, not tmpfs (§2.1a exception). **Orphan service tokens mandatory** (`no_parent: True`) — root `revoke-self` without orphan killed all children (outage root cause). Operator TTL **720h**. Root never on disk; revoke always. Policy table corrected to live `agent-runtime.hcl` / `brain-runtime.hcl`. |

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
| Unseal key | OS keychain (`soma-vault-t0/vault_unseal_key`), operator `VAULT_UNSEAL_KEY` **in ceremony process ENV only**, or T0 account `vault_unseal_key` on tmpfs **or** §2.1a named volume | 3-of-5 shamir, dual control | Cloud KMS auto-unseal | Repo · `.env` · compose env · next to ciphertext without a distinct custodian story |
| Root token | **Process RAM of the Ceremonial Seeder only**; mint-orphan-**then-revoke** (mandatory) | Dual-control, time-boxed | Never persisted; break-glass `generate-root` in RAM → `revoke-self` | **Any T0 · any running app · any file · any disk** |
| Scoped service token | Per-consumer private T0 file (see 1.4), **orphan** (`no_parent: True`) | same | Vault Agent / K8s auth | Shared T0 · ENV value · repo · non-orphan mint |
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

**AS-BUILT 2026-10-13 (do not call this tmpfs):** this deploy mounts Docker named volume
**`standalone_t0_agent`** (`t0_agent` in compose) at `/run/t0` — filesystem **ext4**, not
tmpfs. That is the BOOTSTRAP-001 **§2.1a** dedicated-volume exception (unseal key must survive
container recreate; no OS keychain in Linux containers). Directory 0700, files 0600, consumer
UID. Accounts: `vault_unseal_key`, `agent_runtime_token`, `brain_runtime_token`. **`vault_root_token` is forbidden (absolute).**

The earlier defect (one shared `t0_ram` mounted rw everywhere → root 0600 → appuser
`PermissionError`) is fixed by per-consumer accounts and by never writing root to T0.
**0777/0644 is banned** (world-readable root/unseal = full compromise).

**Normative T0 model:**

```
Each consumer gets its OWN T0 directory (tmpfs preferred, OR §2.1a named volume),
mode 0700, owned by that container's UID, mounted at /run/t0 in that consumer.

  /run/t0/agent_runtime_token   → somaagent_standalone  (0600, that UID)
  /run/t0/brain_runtime_token   → somabrain app         (0600, that UID)
  /run/t0/sfm_runtime_token     → SFM worker (if any)   (0600, that UID)

Preferred compose shape (tmpfs):
  tmpfs:
    - /run/t0:mode=0700,uid=<svc-uid>,size=1m

Local-standalone exception (this deploy):
  volumes:
    - t0_agent:/run/t0:rw     # named volume standalone_t0_agent (ext4)
```

Rules:
1. **Root token NEVER enters any T0 or any disk.** Root lives only in the Ceremonial Seeder's
   process RAM and is **revoked** (`revoke-self`) at the end of mint. Guards refuse
   `vault_root_token` writes (`vault_scoped_tokens.py`, `vault_unseal.py`, `bootstrap_exec.py`).
2. Scoped token files only (plus `vault_unseal_key` where the unseal custodian is T0). Mode
   0600. Owner = consumer UID.
3. Seeder writes the token **as the consumer UID** (seteuid / chown). Never chmod 0777.
4. T0 is tmpfs (swap off) **or** the §2.1a dedicated named volume. Ordinary directories refused.
5. App runtime reads **only** `VAULT_TOKEN_FILE` of its own T0. Fail-closed if unreadable.

### 1.5 Policies (`infra/standalone/vault-policies/*.hcl`) — LIVE as-built

| Policy | Grants (live `.hcl`) | Denies |
|---|---|---|
| `agent-runtime` | **read only:** `secret/data/agent/credentials`, `secret/data/agent/api_keys` (+ `api_keys/*`), matching `secret/metadata/…` read; `auth/token/renew-self` + `lookup-self` | **no write**, no `sys/*`, no `auth/token/create`, no other mounts |
| `brain-runtime` | read `secret/data/agent/credentials` (shared doc); **own mount only:** `somabrain/data/*` CRUD, `somabrain/metadata/*` read/list/delete; `renew-self` + `lookup-self` | `sys/*`, `auth/token/create`, `secret/data/agent/api_keys`, every other mount |
| `sfm-runtime` (planned) | read `secret/data/somafractalmemory/*`, renew/lookup-self | same |
| `ceremony` (seeder-only, root or short-lived) | policy install + `auth/token/create` + KV seed | never issued to a long-running app |

Operator law (agent seat): **read `secret/data/agent/credentials` + `api_keys` only. No write.
No `sys/`.** Matches `agent-runtime.hcl` exactly.

KV v2 is document-granular: `brain-runtime.hcl` reading the whole `agent/credentials` doc is
**accepted and documented** (shared keys live in that map). Split to `secret/data/shared/*`
only with a deliberate ADR; do not leave comments lying.

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

Sequencing (normative — **AMENDED 2026-10-13**):

```
1. Operator starts VAULT (sealed).
2. Unseal if needed (vault_unseal.py --unseal-only). No root yet.
3. Root in process RAM ONLY:
     vault operator generate-root   (unseal key + OTP)  — or sys/init response
   NEVER written to T0 / disk / compose env.
4. Mint (vault_scoped_tokens.py is mint path of record):
     install vault-policies/*.hcl
     auth/token/create with:
       no_parent: True            ← ORPHAN (MANDATORY)
       no_default_policy: True
       ttl: VAULT_TOKEN_TTL_HOURS (required; this deploy 720h)
     → T0 accounts agent_runtime_token, brain_runtime_token only
5. Seed credentials if needed (init_vault / bootstrap_exec seed) — RAM → KV v2 → read-back.
6. ROOT REVOKE — ALWAYS. auth/token/revoke-self.
   Safe ONLY because step 4 minted orphans. Non-orphan mint + revoke-self
   revokes every child service token (2026-10-13 outage root cause).
7. Consumers start AFTER step 4/6; each reads only its own T0 token.
```

**Mint path of record:** `infra/standalone/vault_scoped_tokens.py` (orphan + revoke-self).
`bootstrap_exec.py` `mint_scoped` does **not** yet set `no_parent` and does **not** revoke-self —
do not pair that mint with root revoke until it matches (SOMA-RPT-SEC-VAULT-001 Δ-06).

For the agent container, seeder + target may share PID1 (`bootstrap_exec.py --target /app/start.sh`).
Brain/SFM receive tokens from the ceremony — **never** from another consumer's T0.

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
| R-10 | Named-volume T0 (`standalone_t0_agent`, ext4) is durable storage | MED | §2.1a exception, local-only; 0600/0700; never root; prod KMS + tmpfs/FD |
| R-11 | Non-orphan mint in `bootstrap_exec.py` (Δ-06) | HIGH | Mint path of record = `vault_scoped_tokens.py` (orphan). Align bootstrap mint before any revoke-self pairing. |
| R-12 | 720h service lease long if token leaks | MED | Read-mostly policy; renew-self only; re-mint on suspicion; F-10 stop-not-widen |

---

## 5. Verification gates (CI / e2e)

```bash
# no secret files
find . -name 'vault-token' -o -path '*/secrets/*' -o -name '*_PASSWORD_FILE*'
# no shared-mode T0
grep -RInE '0o777|0o644|chmod 777|mode=0?777' infra/
# no root on T0 — guards must refuse, never write
grep -RInE 'ROOT_ACCOUNT|vault_root_token' infra/standalone/*.py
# orphan mandatory on mint
grep -n 'no_parent' infra/standalone/vault_scoped_tokens.py   # must be True
# no token ENV aliases
grep -RInE 'SOMABRAIN_VAULT_TOKEN|SOMA_VAULT_TOKEN' .
# scram proof (live): TCP login with Vault password = success; wrong password = fail
# T0 as-built: docker volume inspect standalone_t0_agent — named volume, not tmpfs
```

---

## Errata — 2026-10-13 (binding)

Full narrative: `docs/reports/SOMA-RPT-SEC-VAULT-001.md`.

1. **T0 = `standalone_t0_agent` (ext4 named volume)** in this deploy, not tmpfs. §2.1a exception.
2. **Orphan tokens only** (`no_parent: True`). Root `revoke-self` without orphan killed all
   service tokens — outage root cause.
3. **TTL 720h** operator policy for runtime tokens (required env, no default).
4. **Root never on disk; revoke-self always.** Break-glass = `generate-root` in RAM → revoke.
5. **Policy table** above now matches live `agent-runtime.hcl` / `brain-runtime.hcl`.
6. **Code is the only source of truth.** Where docs disagree with `infra/standalone/*.py`,
   code wins.

---

*security-reviewer owns this document. Peer seats implement the same pattern; no seat invents a local variant. ACK required in `docs/plans/a2a/` before merge.*

*End of SOMA-STD-SECURITY-001 v1.0.0*
