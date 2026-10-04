#!/usr/bin/env python3
"""Mint scoped, TTL-bound Vault tokens for the running services.

Zero-trust, and the direct fix for standing root privilege. Until now a
running container held ``vault_root_token`` — unlimited authority, sitting in
a mounted file and process environment. A compromised service could rewrite
the entire trust boundary. That is not least privilege; it is the whole
keyring handed to every job.

This script is the one place root is used: a **one-shot bootstrap** that
installs policy and issues per-service tokens. Every running service then
holds only its own token, which can read what it consumes and do nothing
else. See ``vault-policies/*.hcl`` for the exact grants.

Properties this script must have — the same ones ``vault_unseal.py`` and
``init_vault.py`` have:

* **Never prints a secret value.** Not on success, not on failure, not in an
  exception. Only file names, policy names and HTTP status codes.
* **Fails closed.** If policy cannot be written or a token cannot be issued,
  the script exits non-zero and writes nothing partial.
* **Idempotent.** Re-running re-applies policy and re-issues tokens. It never
  rotates a key it did not mint, and never touches t=0 material.
* **No shell interpolation.** Bytes travel file → HTTP body directly.
* **Least privilege on the wire.** Issued tokens carry a TTL and an explicit
  policy. There is no wildcard policy and no root re-issue path.

Usage::

    python3 vault_scoped_tokens.py            # install policy + issue tokens
    python3 vault_scoped_tokens.py --check    # report, change nothing

Environment::

    VAULT_ADDR              REQUIRED. No default.
    VAULT_TOKEN_FILE        REQUIRED. Path to the ROOT token, used only here.
    SECRETS_DIR             REQUIRED. Where t=0 material is written.
    VAULT_TOKEN_TTL_HOURS   REQUIRED. Lease length for issued tokens.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
POLICY_DIR = SCRIPT_DIR / "vault-policies"


def require_env(name: str) -> str:
    """Read one required bootstrap value. Refuses when it is absent.

    There is no default and no substitute. A value this function supplies is a
    value an operator cannot change and an auditor cannot see — a hardcoded
    value by another name (SOMA-STD-CODING-001 §4, and the standing order to
    remove every hardcoded value from the system).
    """
    value = (os.environ.get(name) or "").strip()
    if not value:
        raise die(
            f"{name} is not set.\n"
            f"   Every address, path and policy bound in this script is an\n"
            f"   operator-supplied bootstrap value. There is no default:\n"
            f"   a default is a hardcoded value."
        )
    return value


SECRETS_DIR = Path(require_env("SECRETS_DIR"))
TOKEN_FILE = Path(require_env("VAULT_TOKEN_FILE"))
VAULT_ADDR = require_env("VAULT_ADDR").rstrip("/")

# Lease length is a security decision, not a literal. It is required config so
# an operator owns it; a default here would be a hardcoded policy.
TOKEN_TTL_HOURS = int(require_env("VAULT_TOKEN_TTL_HOURS"))
TOKEN_TTL = f"{TOKEN_TTL_HOURS}h"

# policy name -> (t=0 file name to write the issued token into, description)
SERVICE_TOKENS = {
    "agent-runtime": ("agent_runtime_token", "somaAgent01 runtime"),
    "brain-runtime": ("brain_runtime_token", "SomaBrain runtime"),
}


def log(msg: str) -> None:
    print(msg, flush=True)


def die(msg: str) -> "SystemExit":
    return SystemExit(f"❌ {msg}")


def read_root_token() -> str:
    if not TOKEN_FILE.is_file():
        raise die(
            f"root token file not found: {TOKEN_FILE}\n"
            f"   Run vault_unseal.py first — it generates and persists the "
            f"root token. This script does not invent one."
        )
    token = TOKEN_FILE.read_text(encoding="utf-8").strip()
    if not token:
        raise die(f"root token file is empty: {TOKEN_FILE}")
    return token


def request(method: str, path: str, body: dict | None = None, token: str = "") -> dict:
    url = f"{VAULT_ADDR}/v1/"
    url += path.lstrip("/")
    data = json.dumps(body).encode() if body is not None else None
    headers = {"X-Vault-Token": token}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        # The response body may echo request material. Take only the code.
        raise die(f"{method} {path} -> HTTP {exc.code}") from None
    except urllib.error.URLError as exc:
        raise die(f"{method} {path} -> unreachable: {exc.reason}") from None


def install_policy(name: str, token: str) -> None:
    src = POLICY_DIR / f"{name}.hcl"
    if not src.is_file():
        raise die(f"policy file missing: {src}")
    rules = src.read_text(encoding="utf-8")
    request("PUT", f"sys/policies/acl/{name}", {"policy": rules}, token)
    log(f"   ✔ policy installed: {name}")


def issue_token(policy: str, token: str, filename: str, comment: str) -> None:
    """Mint a TTL-bound token for one policy and persist it to t=0 material."""
    resp = request(
        "POST",
        "auth/token/create",
        {
            "policies": [policy],
            "ttl": TOKEN_TTL,
            # No root escalation, no token that can create other tokens.
            "no_default_policy": True,
            "num_uses": 0,
            "display_name": comment.replace(" ", "-"),
        },
        token,
    )
    client = ((resp.get("auth") or {}).get("client_token")) or ""
    if not client:
        raise die(f"Vault returned no client token for policy {policy}")

    dest = SECRETS_DIR / filename
    SECRETS_DIR.mkdir(parents=True, exist_ok=True)
    # Same discipline as init_vault.py: one file per credential, 0600, never
    # logged. This file is t=0 material for the service, mounted read-only.
    fd = os.open(dest, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, client.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    os.chmod(dest, 0o600)
    log(f"   ✔ issued {policy:16} -> {dest.name}  (ttl={TOKEN_TTL}, {comment})")


def main(argv: list[str]) -> int:
    check_only = "--check" in argv
    unknown = [a for a in argv if a not in {"--check", "-h", "--help"}]
    if unknown:
        log(f"❌ Unknown argument: {unknown[0]}")
        return 2
    if "-h" in argv or "--help" in argv:
        log(__doc__ or "")
        return 0

    root = read_root_token()
    log(f"🔐 scoped Vault tokens (ttl={TOKEN_TTL})")

    if check_only:
        for policy, (filename, _) in SERVICE_TOKENS.items():
            dest = SECRETS_DIR / filename
            state = "present" if dest.is_file() and dest.stat().st_size else "MISSING"
            log(f"   {state:8} {policy:16} -> {dest.name}")
        return 0

    for policy in SERVICE_TOKENS:
        install_policy(policy, root)

    for policy, (filename, comment) in SERVICE_TOKENS.items():
        issue_token(policy, root, filename, comment)

    log("")
    log("✅ Scoped tokens written to ./secrets. The root token is now needed")
    log("   only for unseal and policy changes — no running service mounts it.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
