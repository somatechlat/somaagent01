"""Provision ONE shared SomaBrain memory HTTP token into both Vaults.

The trust boundary between the agent and SomaBrain is a single pre-shared
bearer token. Two independently seeded values is exactly the 401 this caused
(somabrain ``vault_client.get_runtime_secret`` docstring).

Authority for the VALUE is the agent stack's t=0 material:
``infra/standalone/secrets/somabrain_memory_http_token`` — seeded by
``init_vault.py``. Everything else converges on it.

Authority for the PATH is somabrain ``vault_client.py``:
``secret/agent/credentials`` (KV v2) key ``somabrain_memory_http_token``.

This script:
  1. reads the authoritative value from the agent's t=0 file (or the agent's
     own Vault if the file is absent),
  2. writes that same value to the agent's Vault   (keeps it the authority),
  3. writes that same value to the brain's Vault   (fixes the 401).

It never prints the secret. Only lengths and digests are logged.

Usage:
    python3 infra/standalone/provision_shared_brain_token.py
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
AGENT_SECRETS = HERE / "secret"

AGENT_VAULT = os.environ.get("SA01_VAULT_ADDR", "http://localhost:20882").rstrip("/")
BRAIN_VAULT = os.environ.get("SOMABRAIN_VAULT_ADDR", "http://localhost:30200").rstrip("/")

# KV v2 write path + the document key. Both are load-bearing: somabrain
# vault_client.MEMORY_HTTP_TOKEN_KEY and UnifiedSecretManager.get_credential
# name exactly this string.
KV_PATH = "secret/data/agent/credentials"
DOC_KEY = "somabrain_memory_http_token"
TOKEN_FILE = AGENT_SECRETS / DOC_KEY


def _fingerprint(value: str) -> str:
    return f"len={len(value)} sha256={hashlib.sha256(value.encode()).hexdigest()[:12]}"


def _read_token_file() -> str:
    if not TOKEN_FILE.is_file():
        raise SystemExit(
            f"missing authoritative token file: {TOKEN_FILE}\n"
            f"Run infra/standalone/init_vault.py first — it generates the value."
        )
    value = TOKEN_FILE.read_text(encoding="utf-8").strip()
    if not value:
        raise SystemExit(f"token file is empty: {TOKEN_FILE}")
    return value


def _vault_token(stack: str) -> str:
    """Read one stack's Vault root token from its t=0 bootstrap material.

    The root token is how Vault itself is unlocked, so it cannot live inside
    Vault. It is read from a file where one exists (agent stack), otherwise
    from the brain stack's compose ``.env`` — the same source that stack's own
    ``vault_init`` authenticates with. It is never taken from this process's
    environment.
    """
    candidates = [
        AGENT_SECRETS / "vault_root_token",
        HERE.parent.parent / "secret" / "vault_root_token",
        Path(f"/run/secrets/{stack}_vault_root_token"),
    ]
    for path in candidates:
        if path.is_file():
            value = path.read_text(encoding="utf-8").strip()
            if value:
                return value

    # Brain stack: the root token is the one Vault-auth bootstrap entry its own
    # vault_init uses (SOMABRAIN_VAULT_TOKEN in infra/standalone/.env).
    brain_env = HERE.parent.parent.parent / "somabrain" / "infra" / "standalone" / ".env"
    if brain_env.is_file():
        for line in brain_env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("SOMABRAIN_VAULT_TOKEN="):
                value = line.split("=", 1)[1].strip().strip('"').strip("'")
                if value:
                    return value

    raise SystemExit(
        f"no vault root token for {stack} (tried: "
        + ", ".join(str(c) for c in candidates)
        + f", {brain_env})"
    )


def _request(vault_addr: str, token: str, method: str, path: str, body: dict | None) -> dict:
    url = f"{vault_addr}/v1/{path.lstrip('/')}"
    data = json.dumps(body).encode() if body is not None else None
    headers = {"X-Vault-Token": token}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:200]
        raise SystemExit(f"{method} {url} -> HTTP {exc.code}: {detail}") from None
    except urllib.error.URLError as exc:
        raise SystemExit(f"{method} {url} -> unreachable: {exc.reason}") from None


def write_token(vault_addr: str, token: str, value: str, label: str) -> None:
    """Write the shared credential into one Vault. KV v2 merge."""
    _request(
        vault_addr,
        token,
        "POST",
        KV_PATH,
        {"data": {DOC_KEY: value}},
    )
    check = _request(vault_addr, token, "GET", KV_PATH, None)
    stored = ((check.get("data") or {}).get("data") or {}).get(DOC_KEY)
    if not isinstance(stored, str) or stored != value:
        raise SystemExit(f"{label}: read-back mismatch — write did not land")
    print(f"  ✓ {label}: {_fingerprint(stored)}")


def main() -> int:
    value = _read_token_file()
    print(f"authoritative value: {_fingerprint(value)}")

    for vault_addr, stack, label in (
        (AGENT_VAULT, "somaagent", "agent vault"),
        (BRAIN_VAULT, "somabrain", "brain vault"),
    ):
        token = _vault_token(stack)
        print(f"{label} at {vault_addr}")
        write_token(vault_addr, token, value, label)

    print("\nBoth Vaults now hold the same shared credential.")
    print("Restart SomaBrain so it re-reads settings.SOMABRAIN_MEMORY_HTTP_TOKEN.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
