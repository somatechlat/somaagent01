#!/usr/bin/env python3
"""Standalone Vault seeder — VIBE Rule 164 / Rule 91.

**NO SECRETS EVER TOUCH THE FILESYSTEM.**

Every credential is generated in process memory (``secrets.token_urlsafe``) and
written directly into Vault. There is no ``SECRETS_DIR``, no plaintext file,
and no local copy after this process exits. Vault is the only system of record.

    secret/agent/credentials/<snake_case>      UnifiedSecretManager.get_credential()
    secret/agent/api_keys/<provider>_api_key   UnifiedSecretManager.get_provider_key()

Properties:

* **Never prints a secret value.** Not on success, not on failure, not in a
  request body, not in an exception. Errors name keys and HTTP status only.
* **Never writes a secret to disk.** Not a file, not .env, not argv, not a
  shell history. Values live only in process memory and in Vault.
* **Fails closed.** Missing Vault / sealed Vault / HTTP error is a hard error.
  An empty string is never written.
* **Idempotent.** Without ``--force``, a key already in Vault is left alone
  (hand-rotation survives). With ``--force``, regenerate + overwrite.
* **Optional operator value** via process env ``SOMA_SECRET_<KEY>`` — used only
  for the current process, never persisted by this script.

Usage::

    python3 init_vault.py            # generate + seed missing keys
    python3 init_vault.py --force    # regenerate + overwrite every key
    python3 init_vault.py --check    # report presence, write nothing

Environment (bootstrap topology — REQUIRED, never defaulted; Rule 91)::

    VAULT_ADDR       Vault API address
    VAULT_TOKEN      root token IN MEMORY of this one-shot process (not on disk)
                     (vault_unseal.py obtains it from the OS keychain / prior
                     init and passes it in this process's environment only)

There is no VAULT_TOKEN_FILE. There is no SECRETS_DIR. Rule 164.
"""

from __future__ import annotations

import json
import os
import secrets as py_secrets
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

VAULT_ADDR = (os.environ.get("VAULT_ADDR") or "").rstrip("/")
VAULT_MOUNT = "secret"
T0_DIR = Path(os.environ["T0_DIR"]) if os.environ.get("T0_DIR") else None


def _load_vault_token() -> str:
    """Bootstrap token for THIS one-shot process (R-SEC-03).

    Order: process env (one-shot only) → RAM tmpfs custodian (T0_DIR) →
    OS keychain. Never a repo file. Never logged.
    """
    env = os.environ.get("VAULT_TOKEN")
    if env and env.strip():
        return env.strip()
    if T0_DIR is not None:
        path = T0_DIR / "vault_root_token"
        if path.is_file():
            value = path.read_text(encoding="utf-8").strip()
            if value:
                return value
    try:
        proc = subprocess.run(
            ["security", "find-generic-password",
             "-s", os.environ.get("KEYCHAIN_SERVICE", "soma-vault-t0"),
             "-a", "vault_root_token", "-w"],
            capture_output=True,
        )
        if proc.returncode == 0:
            value = proc.stdout.decode("utf-8", errors="replace").strip()
            if value:
                return value
    except FileNotFoundError:
        pass
    raise SystemExit(
        "ERROR: no Vault root token available for the seeder.\n"
        "   R-SEC-03: provide VAULT_TOKEN for this one-shot process, or\n"
        "   ensure vault_unseal.py left it in the T0_DIR tmpfs custodian or\n"
        "   the OS keychain. It is never read from a file in the repo."
    )


VAULT_TOKEN = _load_vault_token()

# Logical credentials the app reads via get_credential(). Generated, never stored
# to disk. (Name → minimum length of generated value.)
CREDENTIAL_KEYS = (
    "django_secret_key",
    "postgres_password",
    "test_db_password",
    "soma_api_token",
    "somabrain_memory_http_token",
    "somabrain_jwt_secret",
    "keycloak_client_secret",
    "keycloak_admin_password",
    "minio_access_key",
    "minio_secret_key",
    "supervisor_http_pass",
)

API_KEY_PROVIDERS = (
    "groq",
    "openai",
    "elevenlabs",
    "anthropic",
)

FORCE = "--force" in sys.argv
CHECK = "--check" in sys.argv


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(
            f"ERROR: required environment variable {name} is not set.\n"
            f"   Bootstrap topology is required and never defaulted "
            f"   (RAPID Rule 1 / VIBE Rule 91)."
        )
    return value


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def vault_req(method: str, path: str, body: dict | None = None):
    url = f"{VAULT_ADDR}/v1/{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("X-Vault-Token", VAULT_TOKEN)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            payload = json.loads(raw) if raw else {}
        except Exception:
            payload = {}
        return e.code, payload
    except Exception as e:
        raise SystemExit(f"ERROR: Vault request {method} {path} failed: {type(e).__name__}")


def generate_value(key: str) -> str:
    """Operator override via process env only; otherwise generate in memory."""
    env_key = f"SOMA_SECRET_{key.upper()}"
    override = os.environ.get(env_key)
    if override:
        if not override.strip():
            raise SystemExit(f"ERROR: {env_key} is set but empty. Refusing.")
        return override.strip()
    # 43 url-safe chars ~= 256 bits. Enough for any bearer/password material.
    return py_secrets.token_urlsafe(32)


def kv2_write(path: str, data: dict) -> None:
    status, payload = vault_req("POST", f"{VAULT_MOUNT}/data/{path}", {"data": data})
    if status not in (200, 204):
        raise SystemExit(
            f"ERROR: write {VAULT_MOUNT}/data/{path} -> HTTP {status}. "
            f"Value was not logged."
        )


def kv2_read(path: str, key: str) -> str | None:
    status, payload = vault_req("GET", f"{VAULT_MOUNT}/data/{path}")
    if status == 404:
        return None
    if status != 200:
        raise SystemExit(
            f"ERROR: read {VAULT_MOUNT}/data/{path} -> HTTP {status}."
        )
    data = (payload.get("data") or {}).get("data") or {}
    value = data.get(key)
    return str(value) if value else None


def seed_key(path: str, key: str) -> str:
    """Generate (or take operator env) and write to Vault. Never touches disk."""
    if CHECK:
        present = kv2_read(path, key)
        log(f"   {'present' if present else 'MISSING'}  {path}[{key}]")
        return "check"

    if not FORCE:
        existing = kv2_read(path, key)
        if existing:
            log(f"   – skipped (already in Vault): {path}[{key}]")
            return "skip"

    value = generate_value(key)
    if not value:
        raise SystemExit(f"ERROR: generated empty value for {key}. Refusing.")

    kv2_write(path, {key: value})

    # Read-back assert — compare in memory only.
    stored = kv2_read(path, key)
    if stored != value:
        raise SystemExit(
            f"ERROR: read-back mismatch at {path}[{key}]. "
            f"Value was not logged. Refusing to treat the seed as successful."
        )
    log(f"   ✔ generated + seeded {path}[{key}]  (in-memory only, never on disk)")

    # NO password file handoff. Third-party images get the secret via Channel
    # ENV only (vault_inject.py / entrypoint_pg_vault.py execve) — never a
    # T0 file, never /run/t0, never disk. Operator LAW 2026-10-11.
    del value, stored
    return "seeded"


def main() -> int:
    require_env("VAULT_ADDR")
    # VAULT_TOKEN is loaded by _load_vault_token() (env or T0 custodian or
    # keychain). It is intentionally NOT require_env — that would demand a
    # long-lived env secret (R-SEC-03 one-shot / custodian only).
    if not VAULT_TOKEN:
        raise SystemExit(
            "ERROR: no Vault token for the seeder. R-SEC-03: one-shot env, "
            "T0_DIR custodian, or OS keychain. Never a repo file."
        )

    # Wait for Vault API.
    for _ in range(30):
        try:
            status, _ = vault_req("GET", "sys/health")
            break
        except SystemExit:
            time.sleep(1)
    else:
        raise SystemExit(f"ERROR: Vault at {VAULT_ADDR} is unreachable.")

    # Ensure the KV v2 mounts the app reads exist (idempotent).
    for mount in (VAULT_MOUNT, "secret"):
        st, _ = vault_req("POST", f"sys/mounts/{mount}", {"type": "kv-v2"})
        # 204/200 = created; 400 "path is already in use" is fine.
        if st not in (200, 204, 400):
            raise SystemExit(f"ERROR: mount {mount} -> HTTP {st}")

    log("📝 Credentials → secret/agent/credentials  (generated in memory)")
    for key in CREDENTIAL_KEYS:
        seed_key("agent/credentials", key)

    log("📝 Provider API keys → secret/agent/api_keys")
    for provider in API_KEY_PROVIDERS:
        seed_key("agent/api_keys", f"{provider}_api_key")

    if CHECK:
        log("✅ check complete — nothing written.")
    else:
        log("✅ Vault seeded — values exist ONLY in Vault. Nothing was written to disk.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
