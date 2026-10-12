# SomaAgent01 Standalone Deployment

> **Mode**: `SA01_DEPLOYMENT_MODE=STANDALONE`
> **Port Namespace**: 20xxx (strict isolation from Soma Platform 63xxx)
> **Triad**: Agent + SomaBrain + SomaFractalMemory (full memory lane)

Local Docker deployment shaped like production. The secret contract, the
service topology and the fail-closed behaviour match production; the places
where they deliberately do not are listed under
[Local limitations](#local-limitations) at the bottom of this page. Read that
section before assuming anything here is production-ready.

## Secret contract

**No secret value lives in this repository, in `docker-compose.yml`, or in
`.env`.** `.env` is non-secret deployment topology only.

| Secret | Where it lives | How the app reads it |
|---|---|---|
| LLM provider API keys | Vault `secret/agent/api_keys/{provider}_api_key` | `UnifiedSecretManager.get_provider_key()` |
| Everything else (below) | Vault `secret/agent/credentials/<snake_case>` | `UnifiedSecretManager.get_credential()` |
| Vault bootstrap token | Process env of the deployer, injected | `vault_secrets.py` — see the carve-out below |

Credential keys the settings modules read from Vault:

`django_secret_key`, `postgres_password`, `test_db_password`, `soma_api_token`,
`somabrain_memory_http_token`, `somabrain_api_key`, `llm_api_key`,
`keycloak_client_secret`, `google_client_secret`, `keycloak_admin_password`.

### The Vault lifecycle credentials

Vault's root token and unseal key authenticate *to* Vault, so they cannot live
inside it — that would be circular. Per **SOMA-STD-BOOTSTRAP-001 §2.3** they
are held by a custodian in a different trust domain from the Vault data volume:

| Material | Custodian | Never |
|---|---|---|
| `vault_unseal_key` | OS keychain, or `VAULT_UNSEAL_KEY` in the operator's shell | a file in this repo, stdout, `os.environ` as steady state |
| `vault_root_token` | OS keychain, or the T0_DIR RAM tmpfs (`/run/t0/vault_root_token`) for the one-shot seeder | a file in this repo, a long-running app process |

There is no `./secrets/` directory and no `SECRETS_DIR`. `vault_unseal.py`
generates both values in process memory and stores them in the OS keychain
(macOS `security`) or the T0_DIR tmpfs custodian — never on disk. `init_vault.py`
reads the root token from that same custodian and writes application
credentials **only** into Vault.

If the Vault volume is wiped but the keychain/tmpfs material remains, the
scripts refuse to overwrite it and tell you so, rather than silently minting a
second root of trust for the same store.

### Application credential values

`init_vault.py` **generates** every application credential in process memory
(`secrets.token_urlsafe`) and writes it directly to Vault. Nothing is written
to disk. Re-run with `--force` to rotate. First-boot handoffs to Postgres and
Keycloak use the T0_DIR RAM tmpfs only — not a repo file.

## Directory structure

| File | Purpose |
|---|---|
| `docker-compose.yml` | Services, secret contract, dependency order |
| `Dockerfile` | Agent container |
| `entrypoint-keycloak.sh` | Supplies Keycloak's two passwords from the T0_DIR RAM tmpfs |
| `vault.hcl` | Vault server config: `file` storage on a named volume, real seal |
| `vault_unseal.py` | Init-once, unseal-on-every-boot. Generates lifecycle credentials into the keychain / T0_DIR tmpfs |
| `init_vault.py` | One-shot seeder: in-memory generation → Vault. No `SECRETS_DIR`, no repo files |
| `start.sh` | Container init: wait for infra, migrate, warm up, start uvicorn |
| `.env.example` | Non-secret topology template |
| `up-cluster.sh` | Brings up the full triad across the three repos |

## Port mapping (20xxx namespace)

| Service | Internal | External |
|---------|----------|----------|
| Agent API | 9000 | 20020 |
| PostgreSQL | 5432 | 20432 |
| Redis | 6379 | 20379 |
| Keycloak | 8080 | 20880 |
| Vault | 8200 | 20882 |

## Usage

### Prerequisites
- Docker & Docker Compose
- Ports 20xxx free
- macOS keychain access (or a tmpfs `T0_DIR` such as `/run/t0`)

### 1. Configure topology

```bash
cp .env.example .env
# edit .env — deployment topology only, no secrets
```

### 2. Start

```bash
# Custodian for the Vault lifecycle credentials (RAM tmpfs — never a repo file)
export T0_DIR=/run/t0
mkdir -p "$T0_DIR"

docker compose up --build -d
docker compose logs -f somaagent_vault_unseal somaagent_vault_init somaagent_standalone
```

No token to export. `vault_unseal.py` initialises Vault on this first boot and
stores `vault_root_token` / `vault_unseal_key` in the OS keychain (or the
T0_DIR tmpfs). `init_vault.py` then generates every application credential in
process memory and writes it to Vault only.

Startup order is enforced, not hoped for: Vault is reachable → `vault_unseal.py`
initialises/unseals it → `init_vault.py` completes successfully → Postgres and
Redis are healthy → the app starts. If any required secret cannot be generated
or written to Vault, `init_vault.py` exits non-zero and the app never starts.

### 3. Verify

```bash
# Every required key is present in Vault (reads the root token from the custodian)
T0_DIR=/run/t0 VAULT_ADDR=http://localhost:20882 \
  python3 init_vault.py --check

# Vault is unsealed
T0_DIR=/run/t0 VAULT_ADDR=http://localhost:20882 \
  python3 vault_unseal.py --status

# Agent is up
curl -fsS http://localhost:20020/api/health/
```

- **Agent API**: http://localhost:20020
- **Vault UI**: http://localhost:20882

## Rotation

1. `python3 init_vault.py --force` — regenerates every application credential
   in process memory and overwrites it in Vault. Nothing is written to disk.
2. Sync the Postgres role to the new Vault value over the trust socket inside
   the container (Channel ENV — password never in argv or a file):
   `ALTER USER somaagent WITH PASSWORD ...` using the value read from Vault in
   process RAM. Then `docker compose restart somaagent_standalone`.
3. Confirm the app is healthy: `curl -fsS http://localhost:20020/api/health/`.

Channel ENV only — no password file (R-SEC-01).
Passwords reach postgres only via Channel ENV (`entrypoint_pg_vault.py` execve).

## Local limitations

Everything in this table is a deliberate difference from production, not an
oversight. Each row names the production behaviour it stands in for.

| # | Local | Production | Why locally |
|---|---|---|---|
| 1 | **Vault unseal key is held by the operator** (OS keychain / `VAULT_UNSEAL_KEY`, 1-of-1) | Auto-unseal against a cloud KMS, m-of-n key shares, audit devices | A laptop has no KMS to auto-unseal against and no second operator to hold a second share. **No consequence for durability:** Vault runs in server mode with `file` storage on a named volume, so credentials survive restarts — the previous dev-mode design lost every secret on `docker compose restart`. What is local is only *who holds the unseal key*, not whether secrets persist. |
| 2 | **Keycloak runs `start-dev`** | `start --optimized` behind TLS with a real hostname | Dev mode disables hostname strictness and TLS requirements that a local stack cannot satisfy. |
| 3 | **Keycloak has no `_FILE` secret support** | Platform secret store injects `KC_DB_PASSWORD` / `KEYCLOAK_ADMIN_PASSWORD` | Verified against keycloak.org/server/configuration: the image documents `KC_DB_PASSWORD` but ships no `_FILE` variant. `entrypoint-keycloak.sh` exports them from mounted Docker secrets into that container's process env only. |
| 4 | **Database password comes from Vault, same as production** | Identical | No local deviation. Topology (`SA01_DB_HOST/PORT/NAME/USER`) is ENV; the password is `secret/agent/credentials/postgres_password`. `config/settings_registry.py` assembles `DATABASES` from those two sources and nothing else. No `SA01_DB_DSN` exists in any environment. |
| 5 | **Redis has no auth** | Redis ACL / `requirepass`, password in Vault | Standalone Redis is on the isolated bridge network only. |
| 6 | **No TLS anywhere** | TLS at every hop | Local CA + certs is out of scope for a single-machine stack. Do not expose these ports beyond localhost. |
| 7 | **Root token is a shared static value** | Short-lived, per-workload identity (AppRole role_id/secret_id, or K8s service account) | See carve-out above. |
| 8 | **No external secret store, no audit device** | Vault audit logging, HSM-backed seal, off-box backup | Dev mode has no seal and no audit backend to configure. |
| 9 | **The Postgres volume pins the first-boot password** | The platform re-provisions the database with the secret store's value, so rotation is automatic | Channel ENV delivers the Vault `postgres_password` at exec only (no password file). Role rotation is `ALTER USER` from Vault in process RAM — see Rotation. |

### What is *not* a limitation

These match production and must not be "simplified" locally:

- Secret values are absent from every file under version control.
- The application reads secrets from Vault only, via `UnifiedSecretManager`.
- Missing credentials fail closed with an error naming the exact Vault path or
  secret file — never an empty string, never a default, never a `change-me`.
- LLM provider keys are resolved by provider id through `LLMModelConfig`, not
  from environment variables.
- Startup order is enforced by healthchecks and `service_completed_successfully`.
