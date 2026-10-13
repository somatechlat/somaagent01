# SOMA-STD-BOOTSTRAP-001 — TRIAD Credential & Secret Lifecycle

## Document Control

| Field | Value |
|---|---|
| Document Title | SOMA-STD-BOOTSTRAP-001 — TRIAD Credential & Secret Lifecycle |
| Document Identifier | SOMA-STD-BOOTSTRAP-001 |
| Version | 1.0.0 |
| Date | 2026-10-10 |
| Status | Draft |
| Author | SomaTech Engineering (architect agent) |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Applies to | `somaAgent01`, `somabrain`, `somafractalmemory` (Soma Cognitive TRIAD) |
| Supersedes | the `VAULT_TOKEN_FILE` / `SECRETS_DIR` delivery rule in `SOMA-RAPID-DEVELOPMENT-001.md` Rule 5, `SOMA-STD-CONFIG-001.md` R-SEC-03, `AGENT-BRIEFING-RAPID-TRIAD-001.md` Rule 5, `SOMA-SETTINGS-MODEL-001.md` R-ENV-02 (partial) |
| Governing law | VIBE Rule 164 (Vault-only, zero-hardcode), VIBE Rule 91 (fail-closed, no defaults) |
| Operator mandate | **NO SECRETS IN THE FILESYSTEM. EVER.** |
| Next Review | 2027-01-10 |

## Revision History

> **2026-10-13 update:** Operating rules for orphan service tokens, 720h TTL,
> no root on disk, and T0 volume vs tmpfs are specified in
> `docs/standards/SOMA-LAW-SECURITY-001.md` (code = truth).

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-10 | SomaTech Engineering | Initial issue. Resolves the three-generation secret-delivery split-brain. Establishes Vault-only custody, FD-channel delivery, and the sealed-bootstrap ceremony. |
| 1.1.0 | 2026-10-13 | security-reviewer (somaAgent01) | **Errata to match live code + validated ceremony** (SOMA-RPT-SEC-VAULT-001). Adds §2.1a T0 named-volume exception (this deploy = `standalone_t0_agent` ext4, **not** tmpfs). Mandates **orphan** service tokens (`no_parent: True`) so root `revoke-self` cannot kill children (outage root cause). Operator TTL 720h. Root never on disk; root revoke is mandatory. Corrects false claim that `vault_scoped_tokens.py` requires `VAULT_TOKEN_FILE`/`SECRETS_DIR`. |

---

## 0. Executive Summary

The TRIAD currently runs **three incompatible generations of secret delivery at once**. This standard collapses them to one:

> **Vault is the only system of record. No plaintext secret is ever written to any
> filesystem — host, container, image layer, bind mount, or Docker container
> config. Secrets are born in process memory, live in Vault, and are delivered to
> running processes over an inherited file descriptor. The only material permitted
> outside Vault is named, custodied key material (unseal key / root token) held by
> an OS keychain or a cloud KMS — never by a file in a repository.**

### The split-brain (finding, evidence-cited)

| Gen | Shape | Where it lives today | Verdict |
|---|---|---|---|
| **Gen 0** | plaintext secrets in compose `environment:` and host `.env` | `somafractalmemory/infra/standalone/docker-compose.yml:27,116,172,207` (`VAULT_DEV_ROOT_TOKEN_ID`, `POSTGRES_PASSWORD`, `MINIO_ROOT_PASSWORD` as bare env) | **BANNED.** Compose env is persisted by Docker in `/var/lib/docker/containers/<id>/config.v2.json`. This is a secret on disk. |
| **Gen 1** | host directory of secret files, `*_FILE` paths, bind-mounted into containers | **GONE** (F-05 / R-SEC-01, 2026-10-10). `secrets: file: ./secrets/*` and `SOMA_T0_SECRETS_DIR` binds removed from all three compose files. The `infra/standalone/secrets/` directory is deleted. | **BANNED.** The secret is a host file. Gitignored is not the same as not-on-disk. |
| **Gen 2** | OS keychain + in-memory generation | `somaAgent01/infra/standalone/vault_unseal.py`, `init_vault.py` — **now the live path**. Compose has no `secrets: file:` block; credentials are generated in process memory and written to Vault only; unseal custodian is OS keychain or T0_DIR RAM tmpfs. | **CORRECT SHAPE, LIVE.** This standard is the contract that closed the split-brain. |

**Gen 2 is live in somaAgent01 standalone.** `vault_scoped_tokens.py` (live) takes root from
one-shot `VAULT_TOKEN` env or the OS keychain — **not** from a repo file, **not** from T0, and it
does **not** require `SECRETS_DIR`. Issued service tokens are delivered to the T0 custodian
(§2.1a) under `agent_runtime_token` / `brain_runtime_token` only. Older text claiming
`vault_scoped_tokens.py` still requires `VAULT_TOKEN_FILE` + `SECRETS_DIR` is **superseded**
(errata 1.1.0). Token delivery to first-party apps remains `VAULT_TOKEN_FILE` → private T0
path (Channel T0), with Channel FD as the target state.

---

## 1. Threat Model

### 1.1 What the old `./secrets/` folder got wrong

| # | Defect | Why it is a real failure, not a style issue |
|---|---|---|
| T-1 | **Durable plaintext at rest.** `./secrets/postgres_password`, `./secrets/vault_root_token`, `./secrets/vault_unseal_key` are ordinary files. | They survive `docker compose down`, appear in Time Machine / rsync / `tar` backups, are recovered by `photorec` after `rm`, and are copied by any `cp -r` of the project. "Gitignored" only stops one of a hundred exfiltration paths. |
| T-2 | **Host bind mount widens the blast radius.** `- ./secrets:/work/secrets` (`somaAgent01/.../docker-compose.yml:216`) gives every mounted container read (sometimes RW) access to *all* secrets, not the ones it needs. | Compromise of one low-value sidecar (a seeder, a healthchecker) yields the root token and the unseal key. Least privilege is inverted: the mount is the whole keyring. |
| T-3 | **Docker secrets `file:` is a file with a nicer name.** `secrets: { vault_root_token: { file: ./secrets/vault_root_token } }` still reads host disk at `compose up`. | Swarm external secrets are memory-backed; Compose `file:` secrets are not. The YAML looks enterprise; the data path is `open(2)` on a host file. |
| T-4 | **Compose `environment:` is on disk.** `POSTGRES_PASSWORD: "${SOMA_DB_PASSWORD}"` in `somafractalmemory/.../docker-compose.yml:116`. | Docker writes the resolved container environment into the container's `config.v2.json` on the host filesystem, and it is returned by `docker inspect`. This is a durable plaintext secret that most threat models forget. |
| T-5 | **Bootstrap scripts *mint* secrets on disk first.** `somabrain/infra/standalone/vault_unseal.py:write_secret_file()` and the `vault_init` shell block (`docker-compose.yml:569-625`) `read_secret "$${POSTGRES_PASSWORD_FILE}"` and then `curl` that value into Vault. | The secret is *born* on disk and then copied to the good store. Vault becomes a backup of the filesystem, not the system of record. Reverses Rule 164. |
| T-6 | **Vault dev mode as a runtime default.** `somafractalmemory/.../docker-compose.yml:27` `VAULT_DEV_ROOT_TOKEN_ID: "${SOMA_VAULT_TOKEN}"`. | Dev mode stores the entire secret store in the Vault process's RAM, auto-unseals with a caller-chosen root token, and silently loses every credential on restart. It is a demo flag, not a deployment. |
| T-7 | **Standing root in every service.** Runtime containers historically held `vault_root_token`. | One RCE in any service rewrites the entire trust boundary: revoke, mint, rewrite policies. `vault_scoped_tokens.py:1-13` already names this correctly — the fix exists and must be the only path. |
| T-8 | **Unseal key next to the ciphertext.** `./secrets/vault_unseal_key` sits on the same host, usually the same disk, as `/vault/data`. | Sealing protects against a stolen *volume*. If the thief also gets the host file, sealing provides zero protection. The custodian must be a different trust domain. |
| T-9 | **`.env` as a quiet second store.** `somaAgent01/infra/standalone/.env`, `somabrain/infra/standalone/.env`, `somafractalmemory/.env` are live on disk right now. | Any `SOMA_*PASSWORD*`, `*_TOKEN`, `*_SECRET` value in these files is a Rule 164 violation and a durable copy. Topology only. |
| T-10 | **No rotation, no lease, no audit.** Static files have no TTL, no version history, and no access log. | A leaked file is leaked forever, undetectably. Vault KV v2 gives versions; leases give expiry; audit devices give an HMAC'd access trail. |

### 1.2 Enterprise baselines — what "good" looks like elsewhere

| System | Delivery of secrets to a running process | Where material at rest lives |
|---|---|---|
| **HashiCorp Vault (reference)** | Token / AppRole / cloud IAM auth → API read. Vault Agent renders to a **tmpfs** or injects env. | Ciphertext only (transit / seal). Unseal key in KMS (auto-unseal) or shamir shares held by operators. |
| **Cloud KMS (AWS KMS / GCP CloudKMS / Azure Key Vault)** | IAM-authenticated `Decrypt`/`Sign` calls; plaintext never persists in the caller's storage. | HSM-backed ciphertext. Key material never leaves the HSM. |
| **Docker Swarm secrets** | Mounted at `/run/secrets` which is **tmpfs** (RAM, never on the node's disk). | Swarm Raft log is encrypted; the host `./secrets` dir does not exist. |
| **Kubernetes Secrets (in use)** | Projected volume on tmpfs, or CSI driver (Vault Secrets Operator) that syncs to a **memory-only** volume; or the pod authenticates to Vault directly and holds secrets in process memory. | etcd with encryption-at-rest enabled (envelope encryption via KMS). |
| **systemd credentials** | `LoadCredential=` passes a secret over an **inherited file descriptor** / tmpfs `CREDENTIALS_DIRECTORY`; `ImportCredential=` reads from the host credential store. | Never in unit files, never in `/etc`. |

**The common pattern:** the secret's *resting place* is a cryptographic boundary
(Vault / KMS / HSM), and its *delivery path* into a process is RAM-resident —
process memory, an inherited FD, or a memory-backed filesystem. **A host-side
plaintext file is not part of any of these designs.** Compose `file:` secrets and
`./secrets/` are a local regression, not the industry norm.

### 1.3 Attack classes this standard defeats

| Class | Old shape | New shape |
|---|---|---|
| Repo / backup exfiltration | `./secrets/` copied by `tar`, backup, IDE, `git add -f` | No host plaintext exists to copy |
| `docker inspect` / `config.v2.json` | Compose env + mounts leak to anyone with Docker socket | No secret in container config; Docker socket yields topology only |
| Container breakout / `cp` | Bind-mounted secret dir readable | No secret mount; FD is per-process, closed after one read |
| Stolen data volume | Vault storage + `./secrets/` unseal key together = full compromise | Ciphertext without the KMS/keychain custodian is inert |
| Log / argv / `ps` leak | `export VAULT_TOKEN=…`, `curl -H "X-Vault-Token: $TOKEN"` in shell traces | Secrets never on argv, never in shell, never logged; FD number only in env |
| Standing root | Every service = root | Services hold TTL-scoped read-only tokens (or nothing) |
| Silent fallback | Dev mode, default passwords, `getattr(..., default=…)` | Rule 91: absence is a refusal, never a substitute |

---

## 2. Canonical Bootstrap Design

### 2.1 Custodian hierarchy — the only material allowed outside Vault

Rule 164 has one necessary exception, and the exception is **key material that
unlocks Vault itself**, not application credentials. It is never a repository file.

| Material | Why it cannot live in Vault | Local custodian | Staging custodian | Production custodian |
|---|---|---|---|---|
| **Unseal key / shamir share** | Chicken-and-egg: it seals the store that would hold it | **OS keychain** (macOS `security` / libsecret / Windows Credential Manager), service `soma-vault-t0` | 3-of-5 shamir shares; each share sealed to a separate operator's KMS key or held in a hardware token | **Cloud KMS auto-unseal** (`seal "awskms"` / `"gcpckms"` / `"azurekeyvault"`). Vault unseals itself. No share ever exists on a disk. |
| **Root token** | Authenticates *to* Vault | OS keychain, **or mint-and-revoke** (see §3.4) | Dual-control, KMS-sealed, time-boxed | **Never persisted.** Break-glass only: `vault operator generate-root` with unseal/KMS authority + dual control. |
| **AppRole `secret_id`** | Bootstraps service auth | Handed to `vault-inject` via OS keychain / parent FD | Same | Kubernetes auth (no secret) or AppRole `secret_id` from KMS, TTL-bound |
| **Cloud KMS / HSM key** | Is the root of trust | OS keychain (file-based keychain is OS-protected, not a repo file) | KMS | KMS/HSM, FIPS 140-2 L3 |

**Named non-exceptions (explicitly not "custodians"):** a file in the repository,
a `./secrets/` directory, a `.env` value, a compose `environment:` value, an image
layer, a bind mount, a Docker `secrets: file:` source, `/tmp`, an argv element, a
shell history entry, a CI log, a `docker inspect` field.

**Named designed exceptions (allowed, by construction):**

| Exception | Why it is not a violation |
|---|---|
| Vault **audit device** log file | Contains only **HMAC-SHA256** of secrets under a per-device salt. Required for compliance and forensics. Plaintext never enters it. |
| Database **catalog verifiers** (`pg_authid` SCRAM-SHA-256, Keycloak password hash, MinIO credential hash) | One-way salted hashes inside the datastore that owns that auth. Inherent to the datastore. Plaintext is not written. |
| **procfs** `/proc/<pid>/environ` and `/proc/<pid>/fd/*` | RAM-resident kernel objects, not durable storage. Mitigated in §2.5. |
| **tmpfs** mounts | RAM-only, never paged to durable storage **iff swap is disabled**. Permitted as a last resort for an upstream image that hard-requires a path. Prefer the FD channel. |

### 2.1a T0 custodian filesystem (normative — matches live code)

Live enforcement: `vault_scoped_tokens.py` `_t0_custodian_allows`, `vault_unseal.py` `t0_set`. The custodian directory (`T0_DIR`, typically `/run/t0`) must sit on **one of exactly two** shapes:

| Shape | Status | Notes |
|---|---|---|
| **tmpfs / ramfs** | **Preferred.** RAM-only. | Swap must be off (F-19). |
| **Dedicated named-volume mount** | **Allowed local-standalone exception.** Own `/proc/mounts` entry (not `/`, not overlay). | The 1-of-1 unseal key must survive container recreate or Vault is permanently un-unsealable. Linux containers have no OS keychain. Volume is container-native — not the repo, not a host bind. **Production replaces this with KMS auto-unseal; the exception disappears.** |

**Refused:** ordinary directory, repo path, host bind, container root fs / overlay, `/tmp` on the root filesystem.

#### As-built (this deploy, 2026-10-13) — do not call this tmpfs

| Property | Value |
|---|---|
| Compose volume | `t0_agent` |
| Docker volume name | **`standalone_t0_agent`** |
| Filesystem | **ext4** (named volume on Docker host disk) — **NOT tmpfs** |
| Mount | `/run/t0` (also `t0_postgres` → `/run/t0_pg`) |
| Mode | dir 0700 · files 0600 · consumer UID |
| Allowed accounts | `vault_unseal_key`, `agent_runtime_token`, `brain_runtime_token` |
| **Forbidden** | **`vault_root_token` (absolute — R-SEC-01)** |

Comments that say "RAM tmpfs custodian" while the service mounts `t0_agent` are **stale**. Code and this subsection are the source of truth.

#### Root is never a custodian account (absolute)

`vault_root_token` is **never** written to T0, key file, repo, `/tmp`, or compose env. Root exists only as process RAM of a one-shot (`generate-root` or `sys/init` response) and is **revoked** at the end of the ceremony (§3.4). Guards live in `vault_scoped_tokens.py:150-155`, `vault_unseal.py:117-121`, `bootstrap_exec.py` `t0_write`.

### 2.2 Canonical flow

```
                        ┌──────────────────────────────────────────────┐
                        │           SEALED BOOTSTRAP CEREMONY          │
                        │            (one-shot, operator-driven)       │
                        └──────────────────────────────────────────────╝

  OPERATOR                                              CUSTODIAN (never a repo file)
  ────────                                              ────────────────────────────
     │  unlock                                          ┌──────────────────────────┐
     │  (biometric /                                    │ LOCAL:  OS keychain      │
     │   password)                                      │         (soma-vault-t0)  │
     │─────────────────────────────────────────────────▶│ STAGING: 3-of-5 shares   │
     │                                                  │ PROD: Cloud KMS auto-    │
     │                                                  │        unseal / HSM      │
     │                                                  └───────────┬──────────────┘
     │                                                              │ unseal key
     │                                                              ▼
     │   ┌─────────────────────┐   sys/init (1-of-1 local / m-of-n) ┌─────────────┐
     └──▶│  vault_unseal.py    │───────────────────────────────────▶│    VAULT    │
         │  (Gen-2, keychain)  │◀──── unseal key + root token ──────│  (sealed →  │
         │  NEVER writes disk  │      into process memory ONLY      │   unsealed) │
         └──────────┬──────────┘                                    └──────┬──────┘
                    │ root token in RAM                                    │
                    ▼                                                      │
         ┌─────────────────────┐  install vault-policies/*.hcl              │
         │ vault_scoped_       │  mint per-service TTL tokens               │
         │ tokens.py           │──────────────────────────────────────────▶ │
         │ (root used HERE     │  then REVOKE root (§3.4)                   │
         │  and nowhere else)  │                                            │
         └──────────┬──────────┘                                            │
                    │ scoped admin token                                    │
                    ▼                                                       │
         ┌─────────────────────┐  generate IN MEMORY (secrets.token_urlsafe)│
         │ init_vault.py       │─────────── KV v2 write + read-back ───────▶│
         │ (seed credentials)  │  secret/agent/credentials/*                │
         └─────────────────────┘  secret/agent/api_keys/*                   │
                    │                                                       │
                    │ NOTHING written to disk at any step above             │
                    ▼                                                       │
  ═══════════════════════════════════════════════════════════════════════════
                        RUNTIME  (every container start)
  ═══════════════════════════════════════════════════════════════════════════

         ┌─────────────────────┐  AppRole / scoped token auth
         │  vault-inject       │◀────────────────────────────────────────── │
         │  (PID 1 wrapper)    │  reads ONLY what this service is allowed
         │                     │
         │  builds JSON envelope in RAM
         │  opens pipe / memfd
         └──────────┬──────────┘
                    │ fork + execve (FD inherited, env holds FD number only)
                    ▼
         ┌─────────────────────┐
         │  real service       │  read(fd, …) once → close(fd)
         │  (django, brain,    │  secrets now live ONLY in this process's RAM
         │   sfm, postgres,    │
         │   keycloak, minio)  │
         └─────────────────────┘
```

### 2.3 Unseal strategy — local vs prod

| | Local (laptop / T-8) | Staging | Production |
|---|---|---|---|
| **Mode** | `file` storage on a named Docker volume, real seal, `disable_mlock = true` | `file` or Raft, real seal, mlock on | Raft integrated storage (or Consul), TLS on listener, mlock on |
| **Unseal** | 1-of-1 shamir (`vault_unseal.py` `sys/init` with `secret_shares=1, secret_threshold=1`) | 3-of-5 shamir, human ceremony | **KMS auto-unseal** (`seal "awskms" { … }`). Vault unseals itself on start. |
| **Custodian** | OS keychain item `soma-vault-t0/vault_unseal_key` | Per-operator share, KMS-sealed or hardware token | KMS key policy = dual admin + CloudHSM optional. No share on any disk. |
| **Root token** | Keychain `soma-vault-t0/vault_root_token` **or mint-and-revoke** (preferred) | Dual-control, KMS-sealed, time-boxed, alert-on-use | Never persisted. Break-glass = `vault operator generate-root`. |
| **Dev mode** | **BANNED** — see T-6 | BANNED | BANNED |
| **Why not dev mode** | Dev mode keeps the store in Vault's RAM and auto-unseals with `VAULT_DEV_ROOT_TOKEN_ID`. Restart silently destroys every credential and the flag is a root token in compose env (on disk). It is the opposite of fail-closed. | | |

`vault.hcl` (already correct in shape) stays as-is for local, with one comment fix:
the sentence "the deployer holds in `./secrets/`" is now false and must be replaced
with "the operator holds in the OS keychain / KMS". Production `vault.hcl` adds:

```hcl
seal "awskms" {
  region     = "eu-west-1"
  kms_key_id = "<operator-supplied>"   # no default (Rule 91)
}
listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = 0
  tls_cert_file = "/vault/tls/tls.crt"
  tls_key_file  = "/vault/tls/tls.key"
}
```

### 2.4 How credentials are born

**Rule: a credential is generated in process memory and written to Vault in the
same breath. There is no intermediate representation. There is no template file.
There is no "export then import".**

| Credential | Birth | Storage | Death |
|---|---|---|---|
| `django_secret_key` | `secrets.token_urlsafe(32)` in `init_vault.py` | `secret/agent/credentials` KV v2 | rotate via `--rotate django_secret_key`; old versions destroyed deliberately |
| `postgres_password` | same | same | **prefer dynamic**: Vault DB secrets engine issues TTL users (§3.2); static value is first-boot only |
| `test_db_password` | same | same | test-only; never read by a deployed service |
| `soma_api_token`, `somabrain_memory_http_token`, `somabrain_jwt_secret` | same | same | rotate + read-back assert (already in `init_vault.py:172-178`) |
| `keycloak_admin_password`, `keycloak_client_secret` | same | same | rotate; Keycloak re-hashes into its own store |
| `minio_access_key`, `minio_secret_key` | same | same | rotate; MinIO re-hashes |
| `supervisor_http_pass` | same | same | rotate |
| Provider API keys (`groq`, `openai`, `elevenlabs`, `anthropic`) | **out-of-band**: the operator obtains the key from the provider and injects it for one process via `SOMA_SECRET_<KEY>` env, which `init_vault.py` reads and writes to Vault. The env is never persisted by the script. | `secret/agent/api_keys` KV v2 | revoke at the provider, then delete from Vault |

**Production matches local in shape:** production creates secrets *out-of-band*
(operator / Terraform / a break-glass ceremony writes them into Vault directly).
Local generates them *in-memory* because there is no external issuer. Both end at
the same place: **Vault is the only copy**. Neither writes a file.

`init_vault.py` already implements this correctly (`generate_value()` at
`init_vault.py:119-128`, read-back assert at `:172-178`, `del value, stored` at
`:181`). It becomes the **only** seeder. The somabrain `vault_init` shell block
(`somabrain/infra/standalone/docker-compose.yml:550-660`) and the somafractalmemory
`curl`-based seeder are **deleted**, not refactored.

### 2.5 How containers receive secrets at runtime — the delivery channels

Three channels. In strict order of preference. Channel F is banned.

```
CHANNEL FD  (canonical, first-party services)
────────────────────────────────────────────
vault-inject
  │  auth to Vault → fetch only the paths this service's policy allows
  │  build envelope: {"vault_token": "...", "secrets": {...}}   in RAM
  │  pipe()  or  memfd_create("soma-secrets")   ← RAM-backed, no directory entry
  │  write(envelope); lseek(0)  [memfd]  /  leave pipe open for read
  │  fork + execve(real_cmd, env={"SOMA_SECRET_FD": "<n>", ...topology only})
  ▼
real service
  │  fd = int(os.environ["SOMA_SECRET_FD"])
  │  raw = os.read(fd, MAX); os.close(fd)     ← one read, then the data is gone
  │  parse in memory; NEVER export to os.environ; NEVER write to disk
  ▼
  lifetime of the process: secrets are Python/C heap objects only

CHANNEL ENV  (permitted fallback — third-party images only)
──────────────────────────────────────────────────────────
vault-inject --env-map secret/data/agent/credentials[postgres_password]=POSTGRES_PASSWORD \
             -- /usr/local/bin/docker-entrypoint.sh postgres
  │  execve(real_cmd, env={..., "POSTGRES_PASSWORD": value})
  ▼
  the value exists only in the exec'd process's environment block
  (RAM / procfs). It is NOT in compose. It is NOT in config.v2.json.

CHANNEL API  (long-running apps that hold their own Vault client)
────────────────────────────────────────────────────────────────
service holds a TTL-scoped token from Channel FD, then reads KV v2 itself.
Used for secrets that must be re-read after rotation without a restart.

CHANNEL F  (BANNED)
────────────────────
  secrets: file: ./secrets/*          ❌ host file
  bind mount of a secrets directory   ❌ host file
  compose environment: <SECRET>       ❌ persists in config.v2.json
  *_FILE pointing at any of the above ❌ host file
  argv element containing a secret    ❌ visible in `ps`
  tmpfs file (last resort only)       ⚠️  requires swap disabled + written
                                        waiver in the service's README
```

**Why FD beats env for first-party code.** The old standard banned `VAULT_TOKEN`
env because of `ps`, `/proc/<pid>/environ`, and core dumps
(`vault_secrets.py:38-41` states this correctly). Channel FD keeps that property
and removes the file:

| Leak surface | Channel ENV | Channel FD |
|---|---|---|
| `docker inspect` / `config.v2.json` | clean (injected post-start) | clean |
| host filesystem | clean | clean |
| `ps e` / argv | env visible on some systems | only `SOMA_SECRET_FD=3` |
| `/proc/<pid>/environ` | full secret | only `SOMA_SECRET_FD=3` |
| `/proc/<pid>/fd/N` | n/a | readable by same UID **until the one read + close** |
| core dump | secret present | secret present in heap — mitigated by `PR_SET_DUMPABLE=0` / `ulimit -c 0` |

**Required mitigations around Channel FD:**
1. Target process sets `PR_SET_DUMPABLE 0` (or compose sets `ulimit: core: 0`).
2. Each service runs as its own UID (already true in containers).
3. The FD is `O_CLOEXEC`-cleared intentionally for exactly one child, then closed by the injector.
4. The envelope is size-capped and rejected if it exceeds the cap (no unbounded read).
5. `vault-inject` refuses to start if Vault is sealed or the policy denies a required path (Rule 91).

### 2.6 First-boot problem: Postgres / Keycloak / MinIO

These images require a password at PID 1. Solved **without a plaintext file**.

#### Postgres

```yaml
# BEFORE (BANNED — somafractalmemory/infra/standalone/docker-compose.yml:116)
environment:
  POSTGRES_PASSWORD: "${SOMA_DB_PASSWORD:?…}"     # ❌ lands in config.v2.json

# AFTER
services:
  postgres:
    image: postgres:16
    user: "999:999"
    entrypoint: ["/usr/local/bin/vault-inject"]
    command:
      - "--map"
      - "secret/data/agent/credentials[postgres_password]=POSTGRES_PASSWORD"
      - "--map"
      - "secret/data/agent/credentials[test_db_password]=POSTGRES_PASSWORD_TEST"
      - "--"
      - "/usr/local/bin/docker-entrypoint.sh"
      - "postgres"
    environment:
      VAULT_ADDR: "http://somaagent_vault:8200"        # topology only
      VAULT_AUTH_PATH: "auth/approle"                    # topology only
      VAULT_ROLE_ID: "postgres-bootstrap"                # identifier, not a secret
      # NO VAULT_TOKEN. NO POSTGRES_PASSWORD. NO *_FILE.
    # NO secrets: block. NO bind mount of any secret path.
    tmpfs: []          # not used
    volumes:
      - pgdata:/var/lib/postgresql/data     # data only
```

* `vault-inject` authenticates via AppRole (see §3.3), reads `postgres_password`
  from Vault, `execve`s the stock entrypoint with `POSTGRES_PASSWORD` set.
* On first init, postgres derives a **SCRAM-SHA-256 verifier** into `pg_authid`.
  Plaintext is never written. Subsequent boots the data volume already exists and
  the password is not consulted for local auth — but we still inject it so the
  stock entrypoint is satisfied and so a `pg_hba` trust fallback is never needed.
* **Production evolution:** enable the **Vault database secrets engine** against
  this cluster (using a one-time bootstrap connection), then drop the static
  password entirely. Services receive `v-app-role-…` users with TTL and automatic
  revocation (§3.2). The static `postgres_password` then exists only as a
  first-boot artifact and is rotated to an unguessable value immediately after
  the DB engine is configured.

#### Keycloak

`entrypoint-keycloak.sh` is kept in purpose (Keycloak ships no `*_FILE` for
`KC_DB_PASSWORD` / `KEYCLOAK_ADMIN_PASSWORD` — a correctly-named local
limitation) but its **source changes**:

```sh
# BEFORE: read_secret KC_DB_PASSWORD /run/secrets/postgres_password   ❌ file
# AFTER:  values arrive already in the process environment from vault-inject
: "${KC_DB_PASSWORD:?KC_DB_PASSWORD was not injected}"        # fail-closed
: "${KEYCLOAK_ADMIN_PASSWORD:?KEYCLOAK_ADMIN_PASSWORD was not injected}"
exec /opt/keycloak/bin/kc.sh start-dev
```

Wrapped exactly like Postgres:

```yaml
entrypoint: ["/usr/local/bin/vault-inject"]
command:
  - "--map"; - "secret/data/agent/credentials[postgres_password]=KC_DB_PASSWORD"
  - "--map"; - "secret/data/agent/credentials[keycloak_admin_password]=KEYCLOAK_ADMIN_PASSWORD"
  - "--map"; - "secret/data/agent/credentials[keycloak_client_secret]=KC_BOOTSTRAP_ADMIN_CLIENT_SECRET"
  - "--";    - "/opt/keycloak/bin/entrypoint-keycloak.sh"
```

`/run/secrets/` disappears. `secrets:` disappears from the compose service.

#### MinIO

```yaml
entrypoint: ["/usr/local/bin/vault-inject"]
command:
  - "--map"; - "secret/data/agent/credentials[minio_access_key]=MINIO_ROOT_USER"
  - "--map"; - "secret/data/agent/credentials[minio_secret_key]=MINIO_ROOT_PASSWORD"
  - "--";    - "minio"
  - "server"; - "/data"
```

Same treatment for Milvus's `MINIO_ACCESS_KEY_ID` / `MINIO_SECRET_ACCESS_KEY` /
`AWS_SECRET_ACCESS_KEY` (currently triple-written as bare env in
`somafractalmemory/.../docker-compose.yml:201-211` — collapse to one injection).

#### What these services do with the value afterwards

| Service | What it persists | Plaintext on disk? |
|---|---|---|
| Postgres | SCRAM-SHA-256 verifier in `pg_authid` (data volume) | **No** — salted hash |
| Keycloak | BCrypt/PBKDF2 admin hash + DB credential used to connect | **No** — hash; the DB password is used in-process only |
| MinIO | HMAC/derived credential config in its metadata store | **No** — derived |

This is the unavoidable residue of "the datastore owns its own auth". It is
hashing, not storage, and it is why §2.1 names database catalog verifiers as a
designed exception.

### 2.7 Component responsibilities

| Component | Owns | Never owns |
|---|---|---|
| `vault_unseal.py` | `sys/init` once, `sys/unseal` every boot, custodian I/O (keychain/KMS) | credential seeding, policy, running as a long-lived service |
| `vault_scoped_tokens.py` | policy install, per-service TTL token mint, root revocation | credential values, keychain writes |
| `init_vault.py` | generate-in-memory → KV v2 → read-back assert | unseal, policy, any file write |
| `vault-inject` (new) | AppRole auth, KV read, FD/env delivery, `execve` | logging values, caching to disk, serving other containers |
| `vault_secrets.py` / `vault_client.py` / `unified_secret_manager.py` | KV v2 read/write/delete with merge-safe semantics (already correct) | token acquisition from a file, any `SECRETS_DIR` |
| `vault-policies/*.hcl` | least-privilege grants | wildcards, `sys/`, write paths for runtime tokens |
| Docker Compose | topology, images, volumes, networks, healthchecks | any secret value, any secret path |

---

## 3. Enterprise Patterns

### 3.1 Lease / TTL (already present — make it the only path)

`vault_scoped_tokens.py` mints TTL-bound tokens from `vault-policies/*.hcl`.
Mandatory properties:

* Every runtime token has `TTL` and `max_ttl`. `VAULT_TOKEN_TTL_HOURS` is
  **required config, no default** (already correct at `vault_scoped_tokens.py:79`).
* Policies grant `auth/token/renew-self` + `lookup-self` only (already correct:
  `agent-runtime.hcl:37-43`). No `auth/token/create`, no `sys/`.
* A token that expires stops the service cleanly (fail-closed), it does not
  fall back to a broader identity.
* Production: prefer AppRole with `token_ttl` / `token_max_ttl` and periodic
  renewal over long-lived tokens.

### 3.2 Rotation

| Credential | Mechanism | Trigger |
|---|---|---|
| KV secrets (JWT, API tokens, django key) | `init_vault.py --rotate <key>` → regenerate in RAM → KV v2 write (new version) → read-back assert → consumers re-read via Channel API or restart | 90 days, or on suspicion |
| Postgres | **Preferred:** Vault database secrets engine (dynamic role, TTL, auto-revoke). **Interim:** one-shot runs `ALTER ROLE … PASSWORD` with a value read from Vault (never from argv) | 30 days / dynamic TTL |
| Keycloak admin | Keycloak Admin API (authenticated with the *current* secret from Vault) sets the new value, then Vault is updated | 90 days |
| MinIO | `mc admin user` add/rotate with values fetched from Vault | 90 days |
| Service tokens | TTL expiry is the rotation. `vault_scoped_tokens.py` re-issues on redeploy. | lease length |
| Unseal key | `vault operator rekey` (m-of-n reshared) via ceremony. Never a file. | annually / on operator departure |
| Root token | `vault operator generate-root` (recovery) or revoke-after-serve (§3.4) | never long-lived |
| Provider API keys | revoke at provider, delete key from Vault, insert new via `SOMA_SECRET_<KEY>` one-shot | provider terms |

**Invariant:** rotation must never require writing the new value to a file to
"get it into" the consumer. If a rotation path needs a file, the path is wrong.

### 3.3 Service authentication (zero-trust boot)

Two supported methods, both file-free:

**(a) Scoped token via Channel FD (local / standalone — the default now).**
`vault_scoped_tokens.py` mints the token in RAM; `vault-inject` receives it from
its parent over the same FD envelope and either (i) uses it to fetch secrets and
does not pass it on, or (ii) passes it to a first-party app that keeps calling
Vault (Channel API).

**(b) AppRole (the target state for all services).**
* `role_id` is a non-secret identifier, safe in compose env (like a username).
* `secret_id` is a real secret: delivered by Channel FD from the injector's
  parent, or from KMS, **never** from a file. TTL-bound, renewable.
* Policies are per-service (`agent-runtime.hcl`, `brain-runtime.hcl` already exist;
  add `sfm-runtime.hcl`).

**(c) Kubernetes auth (production on K8s).** The pod's service-account JWT is the
credential; Vault verifies it with the TokenReview API. **No secret is delivered
at all.** This is the gold standard and should be the production target.

Services **never** hold root. `vault_scoped_tokens.py`'s docstring
(`vault_scoped_tokens.py:1-13`) is the standing order.

### 3.4 Sealed-bootstrap ceremony + dual-control root + break-glass

**AMENDED 2026-10-13 (SOMA-RPT-SEC-VAULT-001).** Root revoke is **mandatory** in every
environment. Service tokens **must** be minted as **orphans**. The prior "local may skip
step 6" text is **withdrawn** — skipping revoke left standing root; revoking without orphan
killed every child service token (outage root cause I-3).

```
CEREMONY (validated 2026-10-13 — this is the as-built process)
  1. Operator authenticates to the custodian (unseal key from T0 / keychain).
  2. Unseal if sealed (vault_unseal.py --unseal-only). Never init here if a
     ceremonial seeder owns sys/init.
  3. Root in THIS process's memory only:
       vault operator generate-root   (unseal key + OTP)   — or sys/init response
     ABSOLUTE: root is never written to T0, /tmp, repo, or compose env.
  4. vault_scoped_tokens.py (root in one-shot process env):
       - writes vault-policies/*.hcl
       - mints per-service tokens with ALL of:
           no_parent: True            ← ORPHAN (mandatory)
           no_default_policy: True
           ttl: VAULT_TOKEN_TTL_HOURS (required; this deploy = 720h)
       - accounts: agent_runtime_token, brain_runtime_token only
  5. (If needed) init_vault.py: seed credentials in RAM → KV v2 → read-back.
  6. ROOT REVOKE — ALWAYS. auth/token/revoke-self on the root token.
     Safe ONLY because step 4 used no_parent. Root revoke without orphan
     revokes the entire child tree (Vault behaviour) = outage.
  7. No container ever sees root. No root file remains anywhere.

BREAK-GLASS (prod and local)
  - Recovery: vault operator generate-root (unseal/KMS authority)
  - Use in RAM only; revoke-self in the SAME session; never park root.
  - Dual control in prod: two humans, two IAM principals, alert on use.
  - Drill quarterly; execution is itself audited.
```

**Orphan rule (normative).** Every runtime service token is created with `no_parent: True`.
A non-orphan service token is a defect: the next root `revoke-self` will kill it.

**TTL rule (normative).** `VAULT_TOKEN_TTL_HOURS` is required operator config. This deploy
uses **720h (30d)** (`infra/standalone/.env`). There is no coded default (Rule 91).

**Dual control for root in prod is mandatory.** No single human, no single
laptop, no single CI job can both mint and use root.

### 3.5 Audit

* Enable Vault's `audit "file"` device to a **dedicated volume**. Contents are
  HMAC-SHA256'd with a per-device salt — this is the designed exception in §2.1.
* Ship audit logs off-host (append-only object store / SIEM).
* `vault-inject` emits **structured logs with paths and HTTP status only** —
  the same contract `init_vault.py:94-96` and `vault_unseal.py:69-70` already hold.
* Every mint, renew, revoke, and KV write is attributable to a token accessor.

### 3.6 Zero-trust boot checklist

- [ ] Vault starts sealed in every non-dev environment (and dev mode is absent).
- [ ] Unseal key is in a custodian outside the repo (tmpfs OR §2.1a named-volume exception).
- [ ] Root exists only during the ceremony and is **always** revoked (`revoke-self`). **Never root on disk.**
- [ ] Every runtime service token is **orphan** (`no_parent: True`) before root is revoked.
- [ ] Every running service holds a TTL-scoped, policy-bound token — or none.
- [ ] No compose service has a `secrets:` block sourced from a host file.
- [ ] No compose service has a secret in `environment:`.
- [ ] No `*_FILE` path points outside a memfd/pipe (i.e. no `*_FILE` at all).
- [ ] `grep -RInE '(PASSWORD|SECRET|TOKEN|API_KEY)=' infra/**/docker-compose*.yml` returns nothing.
- [ ] `find . -name '.env' -o -path '*/secrets/*'` finds no credential values.

---

## 4. Concrete File-by-File Change List

### 4.1 somaAgent01

| Path | Action | Detail |
|---|---|---|
| `infra/standalone/secrets/` | **DELETE the directory** | Currently holds only `README.md` (the values were already removed). Delete the dir and the README; the concept is gone. |
| `infra/standalone/secrets/README.md` | **DELETE** | Documents the banned shape. |
| `infra/standalone/docker-compose.yml` | **REWRITE the secret surfaces** | (1) Delete the top-level `secrets:` block (lines ~52-63) entirely. (2) Delete every `secrets:` list on every service (lines ~122-123, ~250, ~277, ~334, ~400). (3) Delete `VAULT_TOKEN_FILE` / `SECRETS_DIR` from every `environment:` block. (4) Replace the `vault_unseal` / `vault_init` services (lines ~203-255) with a **one-shot, host-run** ceremony (not a compose service) documented in `README.md`, or with an `init: true` one-shot that does **not** mount `./secrets`. (5) Postgres / Keycloak / app services get the `vault-inject` entrypoint shape from §2.6. Keep `env_file` for topology-only `.env`. |
| `infra/standalone/docker-compose.yml` header comment (lines 8-27) | **REWRITE** | The "SECRET CONTRACT" still says "Keys are seeded by init_vault.py from `./secrets/`" and "`./secrets/vault_unseal_key`". Replace with this standard's contract. |
| `infra/standalone/vault.hcl` | **EDIT comments only** | Line 9 "the deployer holds in `./secrets/`" → "the operator holds in the OS keychain / KMS (SOMA-STD-BOOTSTRAP-001 §2.3)". Storage/shape stays. |
| `infra/standalone/init_vault.py` | **KEEP** (Gen-2, correct) | Minor: drop the `SOMA_SECRET_<KEY>` env override *from the public contract* for provider keys only if the operator wants stricter rules; current behaviour (process env, never persisted) is acceptable and documented. |
| `infra/standalone/vault_unseal.py` | **KEEP** (Gen-2, correct) | Change `VAULT_ADDR` default `http://localhost:20882` → **required, no default** (Rule 91). Keep keychain + `VAULT_UNSEAL_KEY` env. |
| `infra/standalone/vault_scoped_tokens.py` | **REWRITE token acquisition** | Remove `SECRETS_DIR` and `VAULT_TOKEN_FILE` requirements (`vault_scoped_tokens.py:36-37,73-74`). Take root from the same source as `vault_unseal.py` (keychain / process env of the one-shot). Stop writing token files: mint into the process and hand to `vault-inject` over FD. |
| `infra/standalone/vault-policies/*.hcl` | **KEEP** | Add `sfm-runtime.hcl` for somafractalmemory. Re-verify no `sys/` and no write paths in runtime policies. |
| `infra/standalone/entrypoint-keycloak.sh` | **REWRITE** | Source values from the injected environment (§2.6), delete `read_secret` and the `/run/secrets/*` paths. Add the two `: "${VAR:?…}"` fail-closed guards. |
| `infra/standalone/` **new** `vault-inject` | **ADD** | Small Python (or Go) binary implementing Channel FD / Channel ENV per §2.5. Ships in `infra/standalone/Dockerfile` as `/usr/local/bin/vault-inject`. This is the single delivery mechanism. |
| `infra/standalone/.env` | **AUDIT then keep as topology-only** | Strip any `*PASSWORD*`, `*SECRET*`, `*TOKEN*` **value**. Keep `SA01_DEPLOYMENT_MODE`, `VAULT_ADDR`, `POSTGRES_HOST`, `POSTGRES_PORT`, ports, image tags. |
| `infra/standalone/.env.example` | **AUDIT** | Same. It is the committed shape; it must never contain a real value. |
| `services/common/vault_secrets.py` | **REWRITE `_resolve_vault_token`** | Delete `DEFAULT_TOKEN_FILE_ENV = "VAULT_TOKEN_FILE"` and the whole file-reading path (`vault_secrets.py:42-92`). New resolution: (1) explicit `token=` argument from the caller's in-memory store, (2) the token delivered over `SOMA_SECRET_FD` at import/start and cached in a module-level `str` that is never written anywhere. Missing token → `VaultAuthError` (unchanged, fail-closed). Update the error text: it currently tells operators to create `infra/standalone/secrets/vault_root_token` (`vault_secrets.py:88`) — that instruction is now a Rule 164 violation. |
| `services/common/unified_secret_manager.py` | **KEEP** | Already Vault-only and fail-closed. No change beyond import surface if `vault_secrets` renames a helper. |
| `docs/standards/SOMA-STD-CONFIG-001.md` R-SEC-03 | **AMEND** | Replace "`VAULT_ADDR`, `VAULT_TOKEN`, `VAULT_TOKEN_FILE`" with "`VAULT_ADDR` (topology) and a service token delivered over an inherited FD or by AppRole". Mark `VAULT_TOKEN_FILE` deprecated-banned. |
| `docs/standards/SOMA-RAPID-DEVELOPMENT-001.md` Rule 5 | **AMEND** | "`VAULT_TOKEN` env is banned; `VAULT_TOKEN_FILE` only." → "No token on disk and no token in compose env. Delivery is Channel FD (§SOMA-STD-BOOTSTRAP-001 §2.5) or AppRole." |
| `docs/plans/AGENT-BRIEFING-RAPID-TRIAD-001.md` Rule 5 | **AMEND** | Same substitution. |
| `docs/plans/2026-10-04-RAPID-TRIAD-001.md` X-3 | **AMEND** | The recorded decision "Banned. `VAULT_TOKEN_FILE` only." is superseded by this standard; record the new decision rather than leaving a contradiction. |
| `docs/iso/SOMA-SETTINGS-MODEL-001.md` R-ENV-02 + the `VAULT_TOKEN_FILE` row | **AMEND** | Drop `VAULT_TOKEN_FILE` from the allowed-bootstrap list and from the settings table (`SOMA-SETTINGS-MODEL-001.md:263,364`). |
| `docs/iso/SOMA-01-UIUX-005.md` UI-S-29 | **AMEND** | The UI field labelled `VAULT_TOKEN_FILE` becomes "service token source (FD / AppRole)" or is removed. |
| `docs/plans/a2a/CLAIMS.md` | **DONE** | Path claimed for this work. |
| `docs/plans/a2a/LEDGER.md` | **APPEND** | Log the commit when this lands. |

### 4.2 somabrain

| Path | Action | Detail |
|---|---|---|
| `infra/standalone/docker-compose.yml` | **REWRITE** | (1) Delete every `${SOMA_T0_SECRETS_DIR}` bind mount (lines ~366, ~461, ~487, ~537, ~689, ~721, ~784, ~917, ~1096, ~1211). (2) Delete every `*_FILE` secret env (`POSTGRES_PASSWORD_FILE`, `SOMABRAIN_JWT_SECRET_FILE`, `SUPERVISOR_HTTP_PASS_FILE`, `SOMABRAIN_API_TOKEN_FILE`, `SOMABRAIN_MEMORY_HTTP_TOKEN_FILE`, `MINIO_ROOT_USER_FILE`, `MINIO_ROOT_PASSWORD_FILE`). (3) **Delete the entire `vault_init` shell service** (the `read_secret` / `curl`-into-Vault block at ~550-660). Seeding is `init_vault.py`'s job and it seeds from memory. (4) Every consumer service gets `vault-inject` (§2.6). (5) `VAULT_TOKEN_FILE` / `SOMABRAIN_VAULT_TOKEN_FILE` deleted from all environments. |
| `infra/standalone/vault_unseal.py` | **REWRITE → align to Gen-2** | Replace `write_secret_file` / `read_secret_file` / `SECRETS_DIR` (lines ~125-150, `init_vault`, `unseal_vault`) with the OS-keychain / KMS custodian model of `somaAgent01/infra/standalone/vault_unseal.py`. Keep the careful "brain_vault_unseal_key is NOT the agent's key" comment as a policy note (the two stacks must stay separate custodian items: `soma-vault-t0` vs `soma-vault-brain`). |
| `infra/standalone/vault.hcl` | **EDIT comments** | Same as somaAgent01. |
| `somabrain/core/security/vault_client.py` | **REWRITE `_read_vault_token`** | Same as `vault_secrets.py`: remove the `VAULT_TOKEN_FILE` file read (`vault_client.py:48-90` and onward). Accept the token from Channel FD / AppRole. Keep `VaultAuthError` fail-closed semantics. |
| `somabrain/settings/infra.py`, `somabrain/settings/django_core.py` | **VERIFY** | The known anti-patterns AP-05 (writing Vault-sourced secrets back into `os.environ`, `SOMA-STD-CONFIG-001.md:317`) and AP-07 (`env.str(..., default="")` for a credential) must be gone. A secret is read from Vault and used; never exported. |
| `infra/standalone/docker-compose.override.yml`, `docker-entrypoint.sh`, `Dockerfile` | **AUDIT** | `docker-entrypoint.sh` must not `cat` any secret file. `Dockerfile` must not `COPY` any secret. Add `/usr/local/bin/vault-inject`. |
| `infra/standalone/.env`, `.env.example` | **AUDIT** | Topology only. |
| `DEPLOYMENT_GUIDE.md` | **REWRITE the secret chapter** | Point at SOMA-STD-BOOTSTRAP-001. Remove instructions that create `SOMA_T0_SECRETS_DIR` or secret files. |

### 4.3 somafractalmemory

| Path | Action | Detail |
|---|---|---|
| `infra/standalone/docker-compose.yml` | **REWRITE (highest priority — worst state)** | (1) **Delete `VAULT_DEV_ROOT_TOKEN_ID: "${SOMA_VAULT_TOKEN}"`** (line 27). Dev mode is banned. (2) **Delete bare `POSTGRES_PASSWORD: "${SOMA_DB_PASSWORD}"`** (line 116) → `vault-inject` (§2.6). (3) **Delete `MINIO_ROOT_PASSWORD`** (line 172) and the triple-written Milvus MinIO credential envs (lines 201-211: `MINIO_SECRET_ACCESS_KEY`, `MINIO_SECRET_KEY`, `AWS_SECRET_ACCESS_KEY`) → one `vault-inject`. (4) Delete the `curl`-based `vault_init` seeder block (lines ~78-104). (5) Delete `${SOMA_T0_SECRETS_DIR}` bind (line 254) and every `*_FILE` secret env (lines 59-61). (6) Delete `SOMA_DB_PASSWORD` pass-through (line 275). |
| `infra/standalone/docker-compose.override.yml` | **AUDIT** | Same rules. |
| `somafractalmemory/admin/core/security/vault_client.py` | **REWRITE `_read_vault_token`** | Remove `VAULT_TOKEN_FILE` file I/O (`vault_client.py:22-102`). Channel FD / AppRole. Keep the correct "token is never from ENV values" *intent* — just change the carrier from a file to an FD. |
| `.env`, `.env.example` | **AUDIT** | `SOMA_DB_PASSWORD`, `SOMA_MINIO_ROOT_PASSWORD`, `SOMA_API_TOKEN`, `SOMA_REDIS_PASSWORD`, `SOMA_VAULT_TOKEN` must not carry values. Topology only. |
| `infra/standalone/DEPLOYMENT_GUIDE.md`, `README.md` | **REWRITE secret sections** | Cite SOMA-STD-BOOTSTRAP-001. |
| `infra/standalone/` **new** | **ADD `vault-inject`** | Same binary as somaAgent01 (shared via the TRIAD standard, copied or built into each image). Consider one canonical source: `somaAgent01/infra/standalone/vault_inject.py` published as the TRIAD reference implementation. |

### 4.4 Cross-repo (TRIAD)

| Item | Action |
|---|---|
| One credential authority | `init_vault.py` (somaAgent01) is **the** generator. somabrain and somafractalmemory do not generate; they read the same KV paths, or write only their own mount (`somabrain/`, `somafractalmemory/`) under their own scoped token. Shared keys (`somabrain_memory_http_token`) live once at `secret/agent/credentials` and are merge-written with read-back (already implemented correctly in the current shell block — keep that *assert*, drop the file source). |
| One naming table | `VAULT_ADDR` is the only Vault topology name. `SOMABRAIN_VAULT_ADDR` / `SOMA_VAULT_ADDR` are deleted (name-fork rule). |
| One token policy | No `VAULT_TOKEN`, no `VAULT_TOKEN_FILE`, no `*_TOKEN_FILE` anywhere in the TRIAD. |
| One seeder | `init_vault.py`. Delete brain and SFM seeders. |
| One injector | `vault-inject`. No bespoke `read_secret()` shell functions. |

### 4.5 Verification (the change list is not done until these pass)

```bash
# 1. No host secret directories remain
find /Users/macbookpro201916i964gb1tb/Documents/GitHub/{somaAgent01,somabrain,somafractalmemory} \
     -type d -name 'secrets' -o -type d -name 'secrets_t0' -o -type d -name 't0'
# expected: no output

# 2. No secret-valued env in any compose file
grep -RInE '^\s*[A-Z_]*(PASSWORD|SECRET|TOKEN|API_KEY|ROOT_USER|ROOT_PASSWORD)\s*[:=]' \
     /Users/macbookpro201916i964gb1tb/Documents/GitHub/{somaAgent01,somabrain,somafractalmemory}/infra
# expected: no output (matches only *_FILE if left behind — also forbidden)

# 3. No *_FILE secret paths
grep -RInE '[A-Z_]+_FILE:' /Users/macbookpro201916i964gb1tb/Documents/GitHub/{somaAgent01,somabrain,somafractalmemory}/infra
# expected: no output

# 4. No compose secrets: file: blocks
grep -RInE '^\s*file:\s*\./secrets' /Users/macbookpro201916i964gb1tb/Documents/GitHub/{somaAgent01,somabrain,somafractalmemory}/infra
# expected: no output

# 5. No token-file readers left in Python
grep -RInE 'VAULT_TOKEN_FILE|SECRETS_DIR|read_secret_file|write_secret_file|vault_root_token' \
     /Users/macbookpro201916i964gb1tb/Documents/GitHub/{somaAgent01,somabrain,somafractalmemory} \
     --include='*.py' --include='*.sh'
# expected: only docstrings that name the ban

# 6. No dev-mode Vault
grep -RInE 'VAULT_DEV|server -dev|-dev-root-token' \
     /Users/macbookpro201916i964gb1tb/Documents/GitHub/{somaAgent01,somabrain,somafractalmemory}/infra
# expected: no output

# 7. .env files carry topology only
grep -RInE '(PASSWORD|SECRET|TOKEN|API_KEY)\s*=' \
     /Users/macbookpro201916i964gb1tb/Documents/GitHub/{somaAgent01,somabrain,somafractalmemory}/**/.env
# expected: no output
```

---

## 5. Failure Modes — every one fails closed

| # | Failure | Detection | Behaviour (must be) | Never |
|---|---|---|---|---|
| F-1 | Vault unreachable | `sys/health` timeout | `vault-inject` exits non-zero; container does not start; `VaultAuthError` raised | fall back to a default, an empty string, or a cached file |
| F-2 | Vault sealed | `sys/health` 503 | same as F-1. A sealed Vault is not a "missing secret" | treat as "secret absent" (that is the `vault_secrets.py` `InvalidPath` vs `VaultAuthError` distinction — keep it) |
| F-3 | No unseal key in custodian | keychain miss / KMS deny | `vault_unseal.py` exits non-zero with an actionable message naming the custodian item | write a new key (that would create a second root of trust), or fall back to dev mode |
| F-4 | Keychain / KMS unavailable | `security` non-zero / KMS error | hard error | write the key to disk "temporarily" |
| F-5 | `sys/init` returns empty keys/root | payload assert | hard error, nothing stored | proceed with an empty token |
| F-6 | KV write rejected | HTTP non-2xx | `RuntimeError`, value not logged (`init_vault.py:133-138`) | continue as if saved |
| F-7 | Read-back mismatch | `init_vault.py:172-178` | hard error | treat the seed as successful |
| F-8 | Empty generated value | `init_vault.py:167-169` | hard error | write an empty string |
| F-9 | Policy write fails | `vault_scoped_tokens.py` | exit non-zero, no partial token issuance | issue a token against a half-written policy |
| F-10 | Service token expired | 403 on renew/read | service stops cleanly (or retries renew, then stops) | widen its policy, re-mint as root, or read a backup file |
| F-11 | Policy denies a required path | 403 at inject time | `vault-inject` exits non-zero naming the path | omit the secret and start anyway |
| F-12 | `SOMA_SECRET_FD` missing / not readable | `os.read` fails | service refuses to start | read a default from env or a file |
| F-13 | Envelope oversized / malformed | size cap + JSON parse | hard error | truncate and hope |
| F-14 | Postgres data volume exists but password rotated | auth failure at connect | surfaces as a real auth error; operator runs the rotation path | silently reset the password |
| F-15 | Root used after ceremony | audit device + token accessor | page; revoke; incident | leave root standing "for convenience" |
| F-16 | A secret file is created by accident | CI grep (§4.5) + pre-commit hook | build fails | ship it |
| F-17 | `.env` grows a credential | same CI grep | build fails | ship it |
| F-18 | Container configured with a secret in `environment:` | CI grep on compose + `docker inspect` in e2e | build fails | ship it |
| F-19 | Swap enabled while tmpfs used | runtime check in `vault-inject` | refuse to use tmpfs; require FD channel | write the secret to a paged tmpfs |
| F-20 | Two seeders race (agent + brain) | KV v2 version conflict / read-back | fail closed, re-run one seeder | last-write-wins with a lost credential |

**The general rule, restated as a test:** *any* path that would let the system
"keep going" by inventing, defaulting, or recalling a secret value is a defect.
Absence of a secret is a refusal naming the setting (Rule 91). Absence of Vault
is a refusal naming Vault (Rule 164). There is no third option.

---

## 6. Supersession Record

This standard **supersedes** the file-based token delivery contract. The
following are recorded so the next reader does not re-litigate them:

| ID | Old statement | Source | New statement | Source |
|---|---|---|---|---|
| X-A | "`VAULT_TOKEN` env is banned; `VAULT_TOKEN_FILE` only." | `SOMA-RAPID-DEVELOPMENT-001.md` Rule 5; `AGENT-BRIEFING-RAPID-TRIAD-001.md` Rule 5; `SOMA-AGENT-HANDOFF-001.md:86` | **Both are banned as a durable contract.** Delivery is Channel FD (preferred) or Channel ENV for third-party images. `VAULT_TOKEN_FILE` is deleted. | this standard §2.5 |
| X-B | "Env MAY carry a Vault bootstrap only (`VAULT_ADDR`, `VAULT_TOKEN`, `VAULT_TOKEN_FILE`)" | `SOMA-STD-CONFIG-001.md` R-SEC-03 | Env may carry `VAULT_ADDR` and non-secret auth *identifiers* (`VAULT_ROLE_ID`). No token in env as a standing contract. | §2.5, §3.3 |
| X-C | "`VAULT_TOKEN_FILE` / `VAULT_TOKEN` / `SOMABRAIN_VAULT_TOKEN` / `SOMA_VAULT_TOKEN` — rename everywhere" | `2026-10-04-RAPID-TRIAD-001.md` D-04, X-3 | The rename target is **none of the above**. One name: a service token delivered over an FD. | §4.4 |
| X-D | "Never write a secret to any file including `/tmp`" | `AGENT-BRIEFING-RAPID-TRIAD-001.md` Rule 5 | **Retained and strengthened.** This standard agrees completely and adds: never in compose env, never in Docker container config, never in an image layer. | §1.1, §2.5 |
| X-E | "The token is a credential and is delivered as a file" | `vault_secrets.py:67-72` (current error text) | Rejected. A file is a durable plaintext copy. Delivery is FD or AppRole. | §2.5 |
| X-F | Unseal key "held in `./secrets/`" | `vault.hcl:9`, `docker-compose.yml:27` | Unseal key is held by an OS keychain (local) or a cloud KMS (prod). | §2.1, §2.3 |

| X-G | "Local may skip root revoke" | §3.4 v1.0.0 | **Withdrawn.** Root revoke is mandatory everywhere. Service tokens are orphans so revoke is safe. Standing root is banned. | §3.4 errata 2026-10-13 |
| X-H | T0 custodian is "RAM tmpfs" only | multiple comments / v1.0.0 prose | tmpfs **or** §2.1a dedicated named-volume. This deploy: `standalone_t0_agent` ext4. | §2.1a |
| X-I | Service tokens may be children of root | implied by any mint without `no_parent` | **Banned.** Orphan only (`no_parent: True`). Non-orphan + revoke-self = outage. | §3.4, SOMA-RPT-SEC-VAULT-001 |

**One rule that did not change and is not up for negotiation:**
Rule 164 (Vault is the only system of record) and Rule 91 (fail-closed, no
defaults) remain exactly as written. This standard *implements* them; it does
not soften them.

---

## Appendix A — `vault-inject` contract (normative)

```
vault-inject --map <vault-path>[<key>]=<ENV_NAME> ... [--] <command> [args...]

Environment (topology only, all required, no defaults):
  VAULT_ADDR          Vault API address
  VAULT_AUTH_PATH     auth method mount (e.g. auth/approle)
  VAULT_ROLE_ID       AppRole role_id (an identifier, not a secret)

Credentials (from the parent, never from a file):
  received over inherited FD named by SOMA_SECRET_FD (preferred)
  OR provided as the process environment of this one-shot by the ceremony

Behaviour:
  1. read envelope from SOMA_SECRET_FD (once, size-capped), or use the
     one-shot's in-memory token
  2. authenticate to VAULT_ADDR (AppRole or token)
  3. for each --map: KV v2 read; 404 on a required map is FATAL (Rule 91)
  4. build child env = parent topology env + mapped values
     (values are added ONLY to the child env block, never logged)
  5. execve(command, argv, child_env)   # replaces this process

Properties:
  - never writes a file
  - never prints a value (paths, keys, HTTP status only)
  - never puts a value on argv
  - exits non-zero on every failure in the table in §5
  - sets PR_SET_DUMPABLE 0 on itself before exec where the platform allows
```

## Appendix B — Quick reference card

```
BANNED, forever
  ./secrets/                    any secrets directory
  secrets: file: …              compose file-secret sources
  *_FILE= path to a secret      any secret-file indirection
  PASSWORD/SECRET/TOKEN in
    compose environment:        persists in config.v2.json
  .env values that are secrets  durable host plaintext
  VAULT_DEV_* / server -dev     RAM store, auto-unseal, loses everything
  root token in a running
    service                     standing root
  export VAULT_TOKEN=…          ps / procfs / crash dumps
  SECRETS_DIR                   the whole concept

REQUIRED, always
  Vault KV v2                   only system of record
  generate in RAM → Vault       credential birth
  OS keychain / KMS / T0 §2.1a  custodian for unseal key ONLY
  orphan service tokens         no_parent: True — survives root revoke
  root revoke-self              ALWAYS after mint — never root on disk
  Channel FD                    delivery to first-party processes (target)
  Channel ENV                   delivery to third-party images only
  Channel T0 token file         blessed interim: VAULT_TOKEN_FILE → private T0
  TTL-scoped policy-bound
    tokens                      what a running service holds (720h this deploy)
  read-back assert              after every write
  fail-closed (Rule 91)         absence is a refusal, never a default
  audit device (HMAC'd)         forensics
```

---

## Errata — 2026-10-13 (binding)

Authoritative narrative: `docs/reports/SOMA-RPT-SEC-VAULT-001.md`. Summary of what changed
relative to v1.0.0 prose:

1. **T0 filesystem:** this deploy is Docker volume `standalone_t0_agent` (**ext4**), **not**
   tmpfs. §2.1a is the normative exception. Do not describe it as RAM tmpfs.
2. **Orphan tokens:** `no_parent: True` is mandatory. Root `revoke-self` without orphan killed
   all service tokens (children) — that was the outage root cause.
3. **TTL:** operator value **720h** (30d) for `agent_runtime_token` / `brain_runtime_token`.
4. **Root:** never on disk; revoke-self always; break-glass = `generate-root` in RAM only.
5. **`vault_scoped_tokens.py`** does not use `SECRETS_DIR` / T0 root. Mint path of record.

---

*End of SOMA-STD-BOOTSTRAP-001 v1.0.0*
