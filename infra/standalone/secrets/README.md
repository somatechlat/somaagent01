# Deployer-supplied secrets — NOT for git

This directory holds the plaintext secrets the local deployment seeds into
Vault. **It is gitignored. Nothing in here is ever committed.**

It is the local stand-in for the out-of-band secret creation that production
does with its secret store. Production does not read these files; production
creates the same values directly in Vault (or in the platform secret store)
and this directory does not exist.

## Layout

One file per secret, named exactly as the Vault key it becomes. No extension,
no quotes, no trailing whitespace, no newline if your editor can avoid it.
Mode `0600`.

There are **two buckets**, and a file name decides which one it is in. The
name is the whole contract — see [Which bucket](#which-bucket) below.

```
secrets/
  # → secret/agent/credentials/<name>          read by get_credential()
  django_secret_key
  postgres_password
  test_db_password
  soma_api_token
  somabrain_memory_http_token
  somabrain_api_key
  llm_api_key
  keycloak_client_secret
  keycloak_admin_password
  google_client_secret

  # service credentials — optional; each fail-closes its own feature
  jwt_secret                       # JWT session signing
  auth_internal_token              # internal service auth
  gateway_internal_token           # gateway internal auth
  spicedb_token                    # SpiceDB pre-shared key
  kafka_sasl_password              # Kafka SASL (PLAINTEXT/mTLS need none)
  wa_cloud_api_token               # WhatsApp Cloud API
  wa_cloud_webhook_verify_token    # WhatsApp webhook handshake
  wa_cloud_app_secret              # WhatsApp webhook signature

  # → secret/agent/api_keys/<provider>_api_key  read by get_provider_key()
  groq_api_key            # optional — LLM provider key, one per provider
```

## Which bucket

`init_vault.py` decides by **name**, and the rule is closed:

| File name | Bucket | Read by |
|---|---|---|
| One of the credential names listed above | `secret/agent/credentials/` | `UnifiedSecretManager.get_credential(name)` |
| Any other `*_api_key` file | `secret/agent/api_keys/` | `UnifiedSecretManager.get_provider_key(provider)` |

So `llm_api_key` and `somabrain_api_key` are **credentials**, not provider
keys, despite the `_api_key` suffix. They are read with `get_credential()`.
Writing them to `agent/api_keys/` would file them under provider ids (`llm`,
`somabrain`) that no model config ever asks for — dead data in the wrong
bucket.

A provider key's provider id must be a real LLM provider. The ids
`UnifiedSecretManager.list_providers()` knows are `openai`, `groq`,
`anthropic`, `openrouter`, `ollama`, `fireworks`. Name the file
`<provider>_api_key`, e.g. `groq_api_key`, `openai_api_key`.

Provider keys are optional — the agent fails closed with
`LLMNotConfiguredError` if the selected provider has no key.

## Where each value lands in Vault

| File | Vault path | Also |
|---|---|---|
| `django_secret_key` | `secret/agent/credentials/django_secret_key` | |
| `postgres_password` | `secret/agent/credentials/postgres_password` | Docker secret for the Postgres and Keycloak containers |
| `test_db_password` | `secret/agent/credentials/test_db_password` | |
| `soma_api_token` | `secret/agent/credentials/soma_api_token` | |
| `somabrain_memory_http_token` | `secret/agent/credentials/somabrain_memory_http_token` | |
| `somabrain_api_key` | `secret/agent/credentials/somabrain_api_key` | |
| `llm_api_key` | `secret/agent/credentials/llm_api_key` | |
| `keycloak_client_secret` | `secret/agent/credentials/keycloak_client_secret` | |
| `keycloak_admin_password` | `secret/agent/credentials/keycloak_admin_password` | Docker secret for the Keycloak container |
| `google_client_secret` | `secret/agent/credentials/google_client_secret` | |
| `groq_api_key` | `secret/agent/api_keys/groq_api_key` | |

## Generate

```bash
mkdir -p infra/standalone/secrets
cd infra/standalone/secrets
chmod 700 .
for f in django_secret_key postgres_password test_db_password soma_api_token \
         somabrain_memory_http_token somabrain_api_key llm_api_key \
         keycloak_client_secret keycloak_admin_password google_client_secret
do
  openssl rand -hex 32 | tr -d '\n' > "$f"
  chmod 600 "$f"
done
```

### Why hex, not base64 — and why `tr -d '\n'`

Two traps, both hit and measured on this stack:

1. **`openssl rand -base64` can emit `/`.** That character is illegal
   unencoded in a URL userinfo, so `postgresql://user:<password>@host/db` is
   not a valid URI when the password contains it. `postgres_password` is
   exactly such a password — it is embedded in a DSN by
   `entrypoint-app.sh` and parsed by `services/gateway/settings.py`. That
   parse happens to use a regex that tolerates `/`, which is why it worked;
   any URL parser would not. Hex is unambiguously safe in a DSN, a JDBC URL
   and a query string. It is what every consumer here expects.
2. **`openssl rand` terminates its output with a newline.** Shell command
   substitution (`$(cat f)`, `$(< f)`) and the official Postgres image's
   `file_env()` all strip it, so the value those consumers *use* differs from
   the bytes on disk. Writing the raw bytes into Vault would leave
   `get_credential()` returning a password that no consumer ever authenticates
   with. `tr -d '\n'` removes it at the source; `init_vault.py` also strips a
   trailing newline and says so, so a file your editor "fixed" still lands
   correctly.

Then put the real LLM provider key in `groq_api_key` (or your provider's file)
by hand.

## Rules

- **Never** echo a value. `init_vault.py` reads these files and writes them to
  Vault without printing them.
- **Never** copy one into `.env`. `.env` is non-secret deployment topology only.
- **Rotate** by overwriting the file and re-running
  `python3 init_vault.py --force`, then restarting the affected container.
- Deleting this directory does not revoke anything already seeded into Vault.
  Rotate in Vault as well if the files may have leaked.
