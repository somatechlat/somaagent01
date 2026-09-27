# Infra — Secrets & Model Wiring (Operator Runbook)

One page: how the deployed agent reaches Vault, picks a model from the model
administration, and never carries a secret in a manifest or an environment
variable.

**Rules:** VIBE 164 — all secrets from Vault, never in files. VIBE 91 — no
localhost fallbacks. VIBE §4 — no hardcoded values.

## Where model credentials live

Model credentials are **never** environment variables. The agent has full model
administration:

| Concern | Source of truth |
|---|---|
| Which model / provider to use | `LLMModelConfig` (Django admin, `admin.llm`) |
| Provider API keys | Vault `secret/agent/api_keys` field `{provider}_api_key` |
| Resolution | `UnifiedSecretManager.get_provider_key()` → `get_api_key()` |
| Missing key | fail-closed `LLMNotConfiguredError` — no env fallback |

Code: `services/common/unified_secret_manager.py:26,80-88`,
`admin/llm/services/litellm_helpers.py:144-148`,
model seeding `admin/llm/migrations/0004_seed_groq_models.py`.

## 1. Seed the Vault key

```bash
vault kv put secret/agent/api_keys groq_api_key='<real key>'
```

(Any Vault KV v2 mount works; the agent reads path `agent/api_keys`, key
`{provider}_api_key` via `UnifiedSecretManager`.)

Rotation: `vault kv put` the new value, then flush the Django cache entry
`llm_api_key:<provider>` (`admin/core/api/llm.py:133` caches 300s).

## 2. Kubernetes

The manifests carry **no** model credentials — not as values, not as
`secretKeyRef`, not as env. The in-cluster agent reads keys from Vault directly.

```bash
kubectl apply -f k8s/somaagent/
```

Non-secret infrastructure credentials (`somaagent-secrets` with `db-dsn`,
`redis-url`, `spicedb-token`, `django-secret-key`) are still created
out-of-band. Those are service credentials, not model credentials.

`VAULT_ADDR` is set in `k8s/somaagent/deployment.yaml` to the in-cluster
Vault service (`http://vault.shared.svc.cluster.local:8200`). Adjust there if
your Vault runs elsewhere. NetworkPolicy egress already allows port 8200.

| Env var | Source |
|---|---|
| `VAULT_ADDR` | deployment.yaml literal (in-cluster Vault) |
| `AAAS_DEFAULT_CHAT_MODEL` | deployment.yaml literal — model *pointer*, not a credential |
| `AAAS_DEFAULT_TENANT_ID` | deployment.yaml literal |

There is deliberately **no** `GROQ_API_KEY` row. See
`k8s/somaagent/secret.example.yaml` for the runbook.

## 3. Standalone (docker compose)

```bash
cd standalone
cp .env.example .env
# edit .env: VAULT_DEV_ROOT_TOKEN_ID, POSTGRES_PASSWORD, AAAS_DEFAULT_TENANT_ID
#            — never a model API key
vault kv put secret/agent/api_keys groq_api_key='<real key>'
docker compose up --build -d
```

`docker-compose.yml` passes `AAAS_DEFAULT_CHAT_MODEL` and
`AAAS_DEFAULT_TENANT_ID`. Model keys are **not** read from `.env` — seed them
into Vault (`http://somaagent_vault:8200`, `VAULT_TOKEN` derived from
`VAULT_DEV_ROOT_TOKEN_ID`).

## Grep-check (CI)

No file under `infra/` may contain a real key. CI greps:

```
gsk_[A-Za-z0-9]{16,}
ghp_[A-Za-z0-9]{20,}
```
