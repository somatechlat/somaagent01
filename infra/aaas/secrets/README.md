# AAAS bootstrap secrets — NOT for git

Vault is the store for every application secret (VIBE Rule 164). This
directory holds **only** the material a service cannot read from Vault at
first init. Nothing else belongs here.

## What may live in this directory

```
postgres_password           # postgres superuser — read by the image at first init
test_db_password            # least-privileged app/test role
keycloak_admin_password     # Keycloak admin — read at first boot
vault_root_token            # Vault lifecycle — cannot live inside Vault
vault_unseal_key            # Vault lifecycle — cannot live inside Vault
```

That is the complete list. Each one is either consumed by a container that
has no Vault client at `t=0`, or is a Vault lifecycle credential that cannot
be stored in the thing it unlocks.

## What must NOT live here

Every application secret — `django_secret_key`, `soma_api_token`,
`llm_api_key`, `google_client_secret`, `keycloak_client_secret`,
`somabrain_api_key`, `somabrain_memory_http_token`, and the service
credentials (`jwt_secret`, `auth_internal_token`, `spicedb_token`, …) — is
read from Vault at runtime via `UnifiedSecretManager.get_credential()`.
If you find one of those as a file here, it is a defect: seed it into Vault
and delete the file.

## Contract

* One file per secret, named exactly as the Docker secret key. No extension,
  no quotes, no trailing whitespace. Mode `0600`.
* Gitignored. Nothing in here is ever committed. Only this README is tracked.
* Values are never in `.env`, never in `docker-compose.yml`, never in an
  environment variable. The compose file lists **paths** only.
* This directory is a local stand-in for the out-of-band secret creation
  production performs directly in Vault. Production does not read these files.

## Seeding

Vault is seeded once by `infra/standalone/init_vault.py`, which copies values
in and keeps none. After a successful seed, any file whose value is now in
Vault is deleted — Vault is the only store, not a second one.
