#!/usr/bin/env python3
"""Standalone Vault seeder — VIBE Rule 164.

Reads deployer-supplied secret VALUES from ``./secrets/`` (gitignored) and
writes them into Vault at the paths the application actually reads:

    secret/agent/credentials/<snake_case>        UnifiedSecretManager.get_credential()
    secret/agent/api_keys/<provider>_api_key     UnifiedSecretManager.get_provider_key()

This is the local stand-in for the out-of-band secret creation production
performs. It is not a source of truth: it copies values into Vault and keeps
none.

Properties this script must have:

* **Never prints a secret value.** Not on success, not on failure, not in a
  request body that gets echoed, not in an exception. Every error message names
  a file or a path, never a value.
* **Fails closed.** A missing or empty required secret file is a hard error
  naming the file. It is never skipped, and an empty string is never written to
  Vault.
* **Idempotent.** Safe to re-run. Overwrites only with ``--force``, so a re-run
  cannot silently clobber a value someone rotated in Vault by hand.
* **No shell interpolation.** Values travel as Python ``bytes`` from file to
  HTTP body. They never appear in ``argv``, in a shell variable, or in a
  format string that a log could capture.

Usage::

    python3 init_vault.py            # seed keys not already present
    python3 init_vault.py --force    # overwrite every key from ./secrets/
    python3 init_vault.py --check    # report presence, write nothing

Environment::

    VAULT_TOKEN               bootstrap root credential (or VAULT_DEV_ROOT_TOKEN_ID)
    VAULT_ADDR                default http://localhost:20882
    VAULT_MOUNT               default "secret"
    SECRETS_DIR               default ./secrets next to this file
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SECRETS_DIR = Path(os.environ.get("SECRETS_DIR", SCRIPT_DIR / "secrets"))
VAULT_ADDR = os.environ.get("VAULT_ADDR", "http://localhost:20882").rstrip("/")
VAULT_MOUNT = os.environ.get("VAULT_MOUNT", "secret").rstrip("/")
VAULT_TOKEN = os.environ.get("VAULT_TOKEN") or os.environ.get("VAULT_DEV_ROOT_TOKEN_ID") or ""

CREDENTIALS_PATH = "agent/credentials"
API_KEYS_PATH = "agent/api_keys"

# Keys the settings modules read via get_credential(). Names are load-bearing:
# config/settings.py, services/gateway/settings.py and
# infra/aaas/unified_settings.py pass exactly these strings. Renaming one here
# silently breaks that read (get_credential returns None).
REQUIRED_CREDENTIALS = (
    "django_secret_key",
    "postgres_password",
    "test_db_password",
    "soma_api_token",
    "somabrain_memory_http_token",
    "keycloak_client_secret",
    "keycloak_admin_password",
)

# Legitimately absent in a standalone stack with no brain, no external LLM
# proxy and no Google OAuth. Missing is not fatal; the app fails closed on the
# specific feature that needs them.
OPTIONAL_CREDENTIALS = (
    "somabrain_api_key",
    "llm_api_key",
    "google_client_secret",
)


class SeedError(Exception):
    """A condition that must stop the deployment. Never carries a secret."""


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def die(msg: str) -> "None":
    raise SeedError(msg)


# ---------------------------------------------------------------------------
# HTTP — bodies are bytes that never round-trip through a log
# ---------------------------------------------------------------------------


def _request(method: str, path: str, body: bytes | None = None, timeout: float = 10.0):
    url = f"{VAULT_ADDR}/v1/{path.lstrip('/')}"
    headers = {"X-Vault-Token": VAULT_TOKEN}
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            status = resp.status
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        status = exc.code
    except urllib.error.URLError as exc:
        # exc.reason can embed the URL; the URL has no secret in it.
        raise SeedError(f"cannot reach Vault at {VAULT_ADDR}: {exc.reason}") from None

    if not raw:
        return status, None
    try:
        return status, json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        # Never include the body — it could contain a secret in a proxy error.
        return status, None


def vault_ready() -> bool:
    status, _ = _request("GET", "sys/health")
    # 200 = unsealed and active, 429 = unsealed standby, 472 = performance
    # standby, 473 = DR secondary, 501 = not initialized, 503 = sealed.
    return status in (200, 429, 472, 473)


def ensure_mount() -> None:
    body = json.dumps({"type": "kv", "options": {"version": "2"}}).encode("utf-8")
    # 204 = created, 400 = already mounted. Both are fine.
    _request("POST", f"sys/mounts/{VAULT_MOUNT}", body)


def read_secret_map(path: str) -> dict:
    """The whole KV document at `path`, or {} if it does not exist yet.

    KV v2 stores ONE map per path. Every key this script manages for a path
    lives side by side in that map, so a write has to be a read-modify-write.
    """
    status, data = _request("GET", f"{VAULT_MOUNT}/data/{path}")
    if status != 200 or not isinstance(data, dict):
        return {}
    inner = data.get("data") or {}
    values = inner.get("data") or {}
    return dict(values) if isinstance(values, dict) else {}


def key_present(path: str, key: str) -> bool:
    value = read_secret_map(path).get(key)
    # Present means a non-empty string. An empty value is treated as absent so
    # that --check reports it and --force can repair it.
    return isinstance(value, str) and value != ""


def write_secret(path: str, key: str, value: bytes) -> None:
    """Merge one key into the KV document at `path`.

    `value` is raw bytes from a file — never a shell string.

    KV v2 `POST /:mount/data/:path` REPLACES the document; it does not merge.
    Writing `{key: text}` alone would silently destroy every other key already
    stored at that path. So this reads the current document, sets one key in
    it, and writes the whole map back.
    """
    text = value.decode("utf-8")
    current = read_secret_map(path)
    current[key] = text
    body = json.dumps({"data": current}).encode("utf-8")
    status, _ = _request("POST", f"{VAULT_MOUNT}/data/{path}", body)
    if status not in (200, 204):
        # Deliberately no response body in the message.
        raise SeedError(
            f"Vault refused the write at {VAULT_MOUNT}/{path} [{key}] "
            f"(HTTP {status}). The value was not logged; see the Vault audit "
            f"log for the cause."
        )


# ---------------------------------------------------------------------------
# Seeding
# ---------------------------------------------------------------------------


def read_secret_file(name: str, *, required: bool) -> bytes | None:
    full = SECRETS_DIR / name
    if not full.is_file():
        if required:
            raise SeedError(
                f"required secret file missing: {full}\n"
                f"   Generate it (see {SECRETS_DIR / 'README.md'}) — the "
                f"deployment fails closed rather than boot without it."
            )
        log(f"   – skipped (no file): {name}")
        return None
    data = full.read_bytes()
    if not data.strip():
        raise SeedError(
            f"secret file is empty: {full}\n"
            f"   An empty secret is not a secret. Fill it or delete it — never "
            f"write a blank, and never a placeholder like 'change-me'."
        )
    # Every consumer of these values strips trailing newlines — `$(cat file)`,
    # `$(< file)`, the official Postgres image's file_env(). Storing the raw
    # bytes would put a newline in Vault that those consumers never see, so a
    # later get_credential() would disagree with the password actually in use.
    # Strip exactly that, and say so. Nothing else is altered — interior and
    # leading whitespace is part of the value.
    stripped = data.rstrip(b"\r\n")
    if stripped != data:
        log(f"   – stripped trailing newline(s) from {name}")
        data = stripped
    return data


def seed(path: str, key: str, filename: str, *, required: bool, force: bool, check: bool) -> str:
    """Returns 'seeded' | 'skipped' | 'present' | 'missing'."""
    if check:
        if key_present(path, key):
            log(f"   ✔ {VAULT_MOUNT}/{path}  [{key}]  present")
            return "present"
        log(f"   ✘ {VAULT_MOUNT}/{path}  [{key}]  MISSING")
        return "missing"

    value = read_secret_file(filename, required=required)
    if value is None:
        return "skipped"

    if not force and key_present(path, key):
        log(f"   ↷ already present, not overwriting: {VAULT_MOUNT}/{path}  [{key}]  (use --force)")
        return "skipped"

    write_secret(path, key, value)
    log(f"   ✔ seeded {VAULT_MOUNT}/{path}  [{key}]")
    return "seeded"


def main(argv: list[str]) -> int:
    force = "--force" in argv
    check = "--check" in argv
    unknown = [a for a in argv if a not in {"--force", "--check", "-h", "--help"}]
    if unknown:
        log(f"❌ Unknown argument: {unknown[0]}")
        return 2
    if "-h" in argv or "--help" in argv:
        log(__doc__ or "")
        return 0

    if not VAULT_TOKEN:
        log(
            "❌ VAULT_TOKEN (or VAULT_DEV_ROOT_TOKEN_ID) is required.\n"
            "   It is the bootstrap root credential — it authenticates TO "
            "Vault and therefore cannot itself live in Vault.\n"
            "   Export it for this process only. Never write it to .env and "
            "never to a file under version control."
        )
        return 1

    if not check and not SECRETS_DIR.is_dir():
        log(
            f"❌ secrets directory not found: {SECRETS_DIR}\n"
            f"   See {SECRETS_DIR / 'README.md'} — one file per secret, "
            f"generated locally, never committed."
        )
        return 1

    log(f"⏳ Waiting for Vault at {VAULT_ADDR} ...")
    for _ in range(60):
        if vault_ready():
            break
        time.sleep(2)
    else:
        log(f"❌ Vault is not reachable at {VAULT_ADDR}")
        return 1

    if not check:
        ensure_mount()
    log(f"✅ Vault is ready (mount: {VAULT_MOUNT})")

    counts = {"seeded": 0, "skipped": 0, "present": 0, "missing": 0}

    log(f"📝 Credentials → {VAULT_MOUNT}/{CREDENTIALS_PATH}")
    for key in REQUIRED_CREDENTIALS:
        counts[seed(CREDENTIALS_PATH, key, key, required=True, force=force, check=check)] += 1
    for key in OPTIONAL_CREDENTIALS:
        counts[seed(CREDENTIALS_PATH, key, key, required=False, force=force, check=check)] += 1

    # LLM provider keys: a <provider>_api_key file whose name is NOT one of the
    # credential names above is seeded to agent/api_keys/<provider>_api_key,
    # which is what get_provider_key() resolves for an LLMModelConfig provider
    # id (groq_api_key, openai_api_key, ...).
    #
    # The credential names that happen to end in `_api_key` (llm_api_key,
    # somabrain_api_key) are infrastructure credentials read by get_credential()
    # at agent/credentials/. Writing them here as well would put them in the
    # provider bucket under provider ids ("llm", "somabrain") that no
    # LLMModelConfig ever asks for. They belong in credentials only.
    log(f"📝 Provider API keys → {VAULT_MOUNT}/{API_KEYS_PATH}")
    credential_names = set(REQUIRED_CREDENTIALS) | set(OPTIONAL_CREDENTIALS)
    if SECRETS_DIR.is_dir():
        provider_files = [
            full for full in sorted(SECRETS_DIR.glob("*_api_key"))
            if full.name not in credential_names
        ]
        if not provider_files:
            log("   – no LLM provider key files (none named <provider>_api_key "
                "outside the credential set). The agent fails closed with "
                "LLMNotConfiguredError for a provider that has no key.")
        for full in provider_files:
            provider = full.name[: -len("_api_key")]
            if not provider:
                continue
            counts[
                seed(API_KEYS_PATH, f"{provider}_api_key", full.name,
                     required=False, force=force, check=check)
            ] += 1

    log("")
    if check:
        if counts["missing"]:
            log(f"❌ {counts['missing']} key(s) missing from Vault.")
            return 1
        log("✅ All required keys present in Vault.")
        return 0

    log(f"✅ Vault seeded — {counts['seeded']} written, {counts['skipped']} skipped.")
    log("   Values are in Vault only. They were never written to a log, to")
    log("   .env, or to any file under version control.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except SeedError as exc:
        log(f"❌ {exc}")
        sys.exit(1)
