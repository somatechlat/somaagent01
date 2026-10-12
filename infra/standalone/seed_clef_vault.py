#!/usr/bin/env python3
"""seed_clef_vault.py — Cloudflare Clef / R2 credentials into Vault only.

**NO SECRETS EVER TOUCH THE FILESYSTEM. NO VALUE IS EVER PRINTED.**

Writes to ``secret/agent/credentials`` (UnifiedSecretManager.get_credential)::

    clef_api_token
    cloudflare_account_id
    r2_access_key_id
    r2_secret_access_key
    r2_endpoint

Also mirrors the API token to ``secret/agent/api_keys/cloudflare_api_key``
(UnifiedSecretManager.get_provider_key("cloudflare")) so the provider seam and
ClefClient resolve one material.

These are operator-supplied Cloudflare credentials — they cannot be generated.
Each value MUST arrive via the one-shot process env ``SOMA_SECRET_<KEY>`` and is
held in memory only for this process (R-SEC-03). Never argv, never a file,
never a log line.

Usage::

    SOMA_SECRET_CLEF_API_TOKEN=... \\
    SOMA_SECRET_CLOUDFLARE_ACCOUNT_ID=... \\
    SOMA_SECRET_R2_ACCESS_KEY_ID=... \\
    SOMA_SECRET_R2_SECRET_ACCESS_KEY=... \\
    SOMA_SECRET_R2_ENDPOINT=... \\
    VAULT_ADDR=... VAULT_TOKEN=... \\
    python3 seed_clef_vault.py

    python3 seed_clef_vault.py --check    # report presence, write nothing
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

VAULT_ADDR = (os.environ.get("VAULT_ADDR") or "").rstrip("/")
VAULT_MOUNT = "secret"
T0_DIR = Path(os.environ["T0_DIR"]) if os.environ.get("T0_DIR") else None

# (vault path, key, env var) — values are operator material, never generated.
CLEF_SECRETS = (
    ("agent/credentials", "clef_api_token", "SOMA_SECRET_CLEF_API_TOKEN"),
    ("agent/credentials", "cloudflare_account_id", "SOMA_SECRET_CLOUDFLARE_ACCOUNT_ID"),
    ("agent/credentials", "r2_access_key_id", "SOMA_SECRET_R2_ACCESS_KEY_ID"),
    ("agent/credentials", "r2_secret_access_key", "SOMA_SECRET_R2_SECRET_ACCESS_KEY"),
    ("agent/credentials", "r2_endpoint", "SOMA_SECRET_R2_ENDPOINT"),
)

# ClefClient / UnifiedSecretManager.get_provider_key("cloudflare") reads this.
PROVIDER_MIRROR = ("agent/api_keys", "cloudflare_api_key", "SOMA_SECRET_CLEF_API_TOKEN")

FORCE = "--force" in sys.argv
CHECK = "--check" in sys.argv


def _load_vault_token() -> str:
    """Bootstrap token for THIS one-shot process (R-SEC-03)."""
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
            [
                "security",
                "find-generic-password",
                "-s",
                os.environ.get("KEYCHAIN_SERVICE", "soma-vault-t0"),
                "-a",
                "vault_root_token",
                "-w",
            ],
            capture_output=True,
        )
        if proc.returncode == 0:
            return proc.stdout.decode().strip()
    except Exception:
        pass
    return ""


VAULT_TOKEN = _load_vault_token()


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
        raise SystemExit(
            f"ERROR: Vault request {method} {path} failed: {type(e).__name__}"
        )


def kv2_read(path: str, key: str) -> str | None:
    status, payload = vault_req("GET", f"{VAULT_MOUNT}/data/{path}")
    if status == 404:
        return None
    if status != 200:
        raise SystemExit(f"ERROR: read {VAULT_MOUNT}/data/{path} -> HTTP {status}")
    data = (payload.get("data") or {}).get("data") or {}
    value = data.get(key)
    return str(value) if value else None


def kv2_write(path: str, data: dict) -> None:
    status, payload = vault_req("POST", f"{VAULT_MOUNT}/data/{path}", {"data": data})
    if status not in (200, 204):
        raise SystemExit(f"ERROR: write {VAULT_MOUNT}/data/{path} -> HTTP {status}")


def seed_secret(path: str, key: str, env_var: str) -> str:
    """Write one operator credential. Never logs the value. Paths only."""
    if CHECK:
        present = kv2_read(path, key)
        log(f"   {'present' if present else 'MISSING'}  secret/{path}[{key}]")
        return "check"

    existing = kv2_read(path, key)
    if existing and not FORCE:
        log(f"   - skipped (already in Vault): secret/{path}[{key}]")
        return "skip"

    value = os.environ.get(env_var)
    if not value or not value.strip():
        raise SystemExit(
            f"ERROR: {env_var} is required to seed secret/{path}[{key}]. "
            f"Cloudflare Clef/R2 material is operator-supplied and cannot be "
            f"generated. Pass it one-shot in this process env (R-SEC-03)."
        )
    value = value.strip()

    kv2_write(path, {key: value})

    stored = kv2_read(path, key)
    if stored != value:
        raise SystemExit(
            f"ERROR: read-back mismatch at secret/{path}[{key}]. "
            f"Value was not logged. Refusing to treat the seed as successful."
        )
    log(f"   ok seeded secret/{path}[{key}]  (in-memory only, never on disk)")
    del value, stored
    return "seeded"


def main() -> int:
    if not VAULT_ADDR:
        raise SystemExit("ERROR: VAULT_ADDR is required (Rule 91 - never defaulted).")
    if not VAULT_TOKEN:
        raise SystemExit(
            "ERROR: no Vault token for the seeder. R-SEC-03: one-shot env, "
            "T0_DIR custodian, or OS keychain. Never a repo file."
        )

    for _ in range(30):
        try:
            status, _ = vault_req("GET", "sys/health")
            break
        except SystemExit:
            time.sleep(1)
    else:
        raise SystemExit(f"ERROR: Vault at {VAULT_ADDR} is unreachable.")

    for mount in (VAULT_MOUNT, "secret"):
        st, _ = vault_req("POST", f"sys/mounts/{mount}", {"type": "kv-v2"})
        if st not in (200, 204, 400):
            raise SystemExit(f"ERROR: mount {mount} -> HTTP {st}")

    log("Cloudflare Clef credentials -> secret/agent/credentials  (paths only)")
    for path, key, env_var in CLEF_SECRETS:
        seed_secret(path, key, env_var)

    log("Cloudflare provider API key -> secret/agent/api_keys")
    seed_secret(*PROVIDER_MIRROR)

    if CHECK:
        log("check complete - nothing written.")
    else:
        log("Clef vault seeded - values exist ONLY in Vault. Paths:")
        for path, key, _env in CLEF_SECRETS:
            log(f"   secret/{path}/{key}")
        log(f"   secret/{PROVIDER_MIRROR[0]}/{PROVIDER_MIRROR[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
