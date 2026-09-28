# SomaAgent01 Standalone Deployment

> **Mode**: `SA01_DEPLOYMENT_MODE=STANDALONE`
> **Port Namespace**: 20xxx (strict isolation from AAAS 63xxx)
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

### The one carve-out: `VAULT_TOKEN`

`VAULT_TOKEN` is the **bootstrap root credential**. It authenticates *to* Vault,
so it cannot itself be stored in Vault — that would be circular. It is exported
by the deployer for the `docker compose up` process only:

```bash
export VAULT_TOKEN="$(cat /path/kept/outside/the/repo)"
```

Never write it to `.env`. Never commit it. This is the single exception to
"secrets come from Vault", and it is the root of trust that makes the rest
possible.

**The value must not start with `s.`** (measured on `hashicorp/vault:1.15`).
Vault reserves that prefix for tokens it issues itself and refuses it as a
custom root token ID:

```
Error initializing Dev mode: failed to create root token with ID "s.…":
  * invalid request
```

The container then exits 1 — but only *after* logging `core: vault is unsealed`,
so a log tail looks healthy while the process is already dead. A plain random
string (`openssl rand -hex 16`) is fine.

### Operator-supplied values

Plaintext values are seeded into Vault from `./secrets/`, which is **gitignored**.
See [`secrets/README.md`](secrets/README.md) for the file names and how to
generate them. `init_vault.py` copies them into Vault and keeps none; it never
prints a value and fails closed if a required file is missing or empty.

## Directory structure

| File | Purpose |
|---|---|
| `docker-compose.yml` | Services, secrets, dependency order |
| `Dockerfile` | Agent container |
| `entrypoint-app.sh` | Composes `SA01_DB_DSN` from the mounted secret + topology |
| `entrypoint-keycloak.sh` | Supplies Keycloak's two passwords from mounted secrets |
| `init_vault.py` | One-shot seeder: `./secrets/` → Vault at the real paths |
| `secrets/` | Operator-supplied values. Gitignored except its README |
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
- `openssl` (to generate secret values)

### 1. Configure topology

```bash
cp .env.example .env
# edit .env — deployment topology only, no secrets
```

### 2. Create the operator secrets

```bash
mkdir -p secrets && chmod 700 secrets
cd secrets
for f in django_secret_key postgres_password test_db_password soma_api_token \
         somabrain_memory_http_token somabrain_api_key llm_api_key \
         keycloak_client_secret keycloak_admin_password google_client_secret
do
  openssl rand -hex 32 | tr -d '\n' > "$f"
  chmod 600 "$f"
done
cd ..
```

**Hex, not base64, and no trailing newline** — both matter. Base64 can emit
`/`, which is illegal unencoded in the DSN userinfo that `postgres_password`
is embedded in; `openssl rand` also appends a newline that shell substitution
and the Postgres image strip, so the on-disk bytes would not match the value
consumers authenticate with. See
[`secrets/README.md`](secrets/README.md#why-hex-not-base64--and-why-tr--d-n).

Put the real LLM provider key in `secrets/groq_api_key` (or your provider's
`<provider>_api_key`) by hand.

### 3. Start

```bash
export VAULT_TOKEN="$(openssl rand -hex 16)"   # dev only — see the carve-out
docker compose up --build -d
docker compose logs -f somaagent_vault_init somaagent_standalone
```

Startup order is enforced, not hoped for: Vault is healthy →
`init_vault.py` completes successfully → Postgres and Redis are healthy →
the app starts. If any required secret file is absent, `init_vault.py` exits
non-zero and the app never starts.

### 4. Verify

```bash
# Every required key is present in Vault
SECRETS_DIR=./secrets VAULT_ADDR=http://localhost:20882 VAULT_TOKEN=$VAULT_TOKEN \
  python3 init_vault.py --check

# Agent is up
curl -fsS http://localhost:20020/api/health/
```

- **Agent API**: http://localhost:20020
- **Vault UI**: http://localhost:20882

## Rotation

1. Overwrite the file under `secrets/`.
2. `python3 init_vault.py --force`
3. Restart the container that consumes it:
   `docker compose up -d --force-recreate <service>`

**`postgres_password` is the exception.** The Postgres image reads
`POSTGRES_PASSWORD_FILE` only when it initialises the data volume, and
`docker compose down` does **not** delete that volume. After first boot the
file is ignored and the role keeps its original password, so step 3 alone
looks successful and then fails with
`password authentication failed for user "somaagent"`. Rotate the role
explicitly over the local socket (it is `trust` inside the container, so this
never needs the old password, and the value is read from the mounted secret —
never typed, never logged):

```bash
docker exec -i somaagent_postgres sh -s <<'EOS'
set -eu
psql -U somaagent -d postgres -v ON_ERROR_STOP=1 <<'SQL'
\set pw `cat /run/secrets/postgres_password`
ALTER USER somaagent WITH PASSWORD :'pw';
SQL
EOS
docker compose restart somaagent_standalone
```

Then confirm the app is healthy. The alternative is to delete
`standalone_somaagent_postgres_data` and let Postgres re-initialise — that
**destroys the database**, so only do it when you do not care about the data.

## Local limitations

Everything in this table is a deliberate difference from production, not an
oversight. Each row names the production behaviour it stands in for.

| # | Local | Production | Why locally |
|---|---|---|---|
| 1 | **Vault runs in dev mode** (`hashicorp/vault` + `VAULT_DEV_ROOT_TOKEN_ID`) | Unsealed Vault with AppRole / Kubernetes auth, real seal, audit devices | Dev mode needs no unseal ceremony and no PKI, which is disproportionate for one laptop. **Consequence: secrets are in memory and a container restart loses them — re-run `init_vault.py`.** |
| 2 | **Keycloak runs `start-dev`** | `start --optimized` behind TLS with a real hostname | Dev mode disables hostname strictness and TLS requirements that a local stack cannot satisfy. |
| 3 | **Keycloak has no `_FILE` secret support** | Platform secret store injects `KC_DB_PASSWORD` / `KEYCLOAK_ADMIN_PASSWORD` | Verified against keycloak.org/server/configuration: the image documents `KC_DB_PASSWORD` but ships no `_FILE` variant. `entrypoint-keycloak.sh` exports them from mounted Docker secrets into that container's process env only. |
| 4 | **`SA01_DB_DSN` is composed in `entrypoint-app.sh`** | The app builds its connection from topology + `secret/agent/credentials/postgres_password` | `services/gateway/settings.py` still parses `SA01_DB_DSN`. Until that read is converted (tracked; needs the settings lane), the DSN is formed in-container from the mounted Docker secret. It never touches the host, `.env` or git. **This is the one place a password-bearing DSN exists, and it should reach zero.** |
| 5 | **Redis has no auth** | Redis ACL / `requirepass`, password in Vault | Standalone Redis is on the isolated bridge network only. |
| 6 | **No TLS anywhere** | TLS at every hop | Local CA + certs is out of scope for a single-machine stack. Do not expose these ports beyond localhost. |
| 7 | **Root token is a shared static value** | Short-lived, per-workload identity (AppRole role_id/secret_id, or K8s service account) | See carve-out above. |
| 8 | **No external secret store, no audit device** | Vault audit logging, HSM-backed seal, off-box backup | Dev mode has no seal and no audit backend to configure. |
| 9 | **The Postgres volume pins the first-boot password** | The platform re-provisions the database with the secret store's value, so rotation is automatic | The `postgres:15-alpine` image reads `POSTGRES_PASSWORD_FILE` only on first init of the data volume, and `docker compose down` keeps the volume. Rotating `postgres_password` therefore needs an explicit `ALTER USER` — see [Rotation](#rotation). Measured on this stack: the app starts, migrations fail with `password authentication failed for user "somaagent"`. |

### What is *not* a limitation

These match production and must not be "simplified" locally:

- Secret values are absent from every file under version control.
- The application reads secrets from Vault only, via `UnifiedSecretManager`.
- Missing credentials fail closed with an error naming the exact Vault path or
  secret file — never an empty string, never a default, never a `change-me`.
- LLM provider keys are resolved by provider id through `LLMModelConfig`, not
  from environment variables.
- Startup order is enforced by healthchecks and `service_completed_successfully`.
