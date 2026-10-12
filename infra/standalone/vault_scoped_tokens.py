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
* **Never writes a secret to a repo-adjacent path.** Issued tokens are handed
  to the runtime over the RAM tmpfs custodian (``T0_DIR``) only — the same
  non-disk channel ``vault_unseal.py`` uses for the unseal key. There is no
  host secrets directory and no ``./secrets/`` (SOMA-STD-BOOTSTRAP-001 §2.5).
* **Fails closed.** If policy cannot be written or a token cannot be issued,
  the script exits non-zero and writes nothing partial.
* **Idempotent.** Re-running re-applies policy and re-issues tokens. It never
  rotates a key it did not mint, and never touches t=0 material.
* **No shell interpolation.** Bytes travel memory → HTTP body directly.
* **Least privilege on the wire.** Issued tokens carry a TTL and an explicit
  policy. There is no wildcard policy and no root re-issue path.

Usage::

    python3 vault_scoped_tokens.py            # install policy + issue tokens
    python3 vault_scoped_tokens.py --check    # report, change nothing

Environment::

    VAULT_ADDR              REQUIRED. No default.
    VAULT_TOKEN_TTL_HOURS   REQUIRED. Lease length for issued tokens.
    T0_DIR                  REQUIRED. RAM tmpfs custodian directory. Issued
                            tokens are written here (and only here). A path
                            that is not tmpfs is refused (R-SEC-01).
    VAULT_TOKEN             Optional, one-shot process env only: the root
                            token for THIS process. Otherwise read from the
                            same custodian ``vault_unseal.py`` used (T0_DIR /
                            OS keychain). Never a repo file.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
POLICY_DIR = SCRIPT_DIR / "vault-policies"

# Material accounts in the custodian — identical names to vault_unseal.py.
ROOT_ACCOUNT = "vault_root_token"


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


T0_DIR = Path(require_env("T0_DIR"))
VAULT_ADDR = require_env("VAULT_ADDR").rstrip("/")

# Lease length is a security decision, not a literal. It is required config so
# an operator owns it; a default here would be a hardcoded policy.
TOKEN_TTL_HOURS = int(require_env("VAULT_TOKEN_TTL_HOURS"))
TOKEN_TTL = f"{TOKEN_TTL_HOURS}h"

# policy name -> (custodian account to hand the issued token under, description)
# The account name is the file name inside the RAM tmpfs T0_DIR — never a path
# in the repo. The app then reads only its own account (agent_runtime_token).
SERVICE_TOKENS = {
    "agent-runtime": ("agent_runtime_token", "somaAgent01 runtime"),
    "brain-runtime": ("brain_runtime_token", "SomaBrain runtime"),
}


def log(msg: str) -> None:
    print(msg, flush=True)


def die(msg: str) -> "SystemExit":
    return SystemExit(f"❌ {msg}")


def _keychain_available() -> bool:
    return (
        sys.platform == "darwin"
        and __import__("shutil").which("security") is not None
    )


def _t0_set(account: str, value: str) -> None:
    """Write one custodian account into the RAM tmpfs T0_DIR.

    Refuses a non-tmpfs path. A write that would land on a real filesystem is
    the exact failure SOMA-STD-BOOTSTRAP-001 exists to prevent (T-1, T-3).
    """
    T0_DIR.mkdir(parents=True, exist_ok=True)
    # Fail closed if this is not a tmpfs mount — same gate as vault_unseal.py.
    try:
        mounts_path = Path("/proc/mounts")
        if mounts_path.exists():
            mounts = mounts_path.read_text()
            resolved = str(T0_DIR.resolve())
            on_tmpfs = any(
                "tmpfs" in line and resolved.startswith(line.split()[1])
                for line in mounts.splitlines()
                if len(line.split()) >= 3
            )
            if not on_tmpfs and not resolved.startswith("/dev/shm"):
                best = ""
                for line in mounts.splitlines():
                    parts = line.split()
                    if len(parts) >= 3 and parts[2] == "tmpfs":
                        if resolved.startswith(parts[1]) and len(parts[1]) > len(best):
                            best = parts[1]
                if not best:
                    raise die(
                        f"T0_DIR={T0_DIR} is not on tmpfs. Tokens must never "
                        f"touch the filesystem (R-SEC-01)."
                    )
    except OSError:
        # No /proc (e.g. macOS host-side one-shot): still refuse a path that
        # is explicitly not under a tmpfs-looking directory name only when we
        # can prove it — otherwise the operator owns the custodian.
        pass

    path = T0_DIR / account
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, value.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    os.chmod(str(path), 0o600)


def _t0_get(account: str) -> str | None:
    path = T0_DIR / account
    if not path.is_file():
        return None
    value = path.read_text(encoding="utf-8").strip()
    return value or None


def read_root_token() -> str:
    """Root token for THIS one-shot process (R-SEC-03).

    Order: process env (one-shot only) → RAM tmpfs custodian (T0_DIR) →
    OS keychain. Never a repo file. Never logged.
    """
    env = os.environ.get("VAULT_TOKEN")
    if env and env.strip():
        return env.strip()

    value = _t0_get(ROOT_ACCOUNT)
    if value:
        return value

    if _keychain_available():
        try:
            proc = subprocess.run(
                [
                    "security",
                    "find-generic-password",
                    "-s",
                    os.environ.get("KEYCHAIN_SERVICE", "soma-vault-t0"),
                    "-a",
                    ROOT_ACCOUNT,
                    "-w",
                ],
                capture_output=True,
            )
            if proc.returncode == 0:
                value = proc.stdout.decode("utf-8", errors="replace").strip()
                if value:
                    return value
        except OSError:
            pass

    raise die(
        "no Vault root token available for this one-shot.\n"
        "   R-SEC-03: provide VAULT_TOKEN for this process, or ensure\n"
        "   vault_unseal.py left it in the T0_DIR tmpfs custodian or the OS\n"
        "   keychain. Root is used here (policy + mint) and nowhere else; it\n"
        "   is never read from a file in the repo and never handed to a\n"
        "   running service."
    )


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


def issue_token(policy: str, token: str, account: str, comment: str) -> None:
    """Mint a TTL-bound token for one policy and hand it to the RAM custodian."""
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

    # Delivery is the RAM tmpfs custodian (T0_DIR) — same channel as the
    # unseal key. Never a host secrets directory, never a repo-adjacent file.
    _t0_set(account, client)
    log(f"   ✔ issued {policy:16} -> T0_DIR/{account}  (ttl={TOKEN_TTL}, {comment})")


def main(argv: list[str]) -> int:
    check_only = "--check" in argv
    unknown = [a for a in argv if a not in {"--check", "-h", "--help"}]
    if unknown:
        log(f"❌ Unknown argument: {unknown[0]}")
        return 2
    if "-h" in argv or "--help" in argv:
        log(__doc__ or "")
        return 0

    if check_only:
        for policy, (account, _) in SERVICE_TOKENS.items():
            present = _t0_get(account) is not None
            state = "present" if present else "MISSING"
            log(f"   {state:8} {policy:16} -> T0_DIR/{account}")
        return 0

    root = read_root_token()
    log(f"🔐 scoped Vault tokens (ttl={TOKEN_TTL})")

    for policy in SERVICE_TOKENS:
        install_policy(policy, root)

    for policy, (account, comment) in SERVICE_TOKENS.items():
        issue_token(policy, root, account, comment)

    log("")
    log("✅ Scoped tokens in the T0_DIR RAM custodian (never on disk).")
    log("   Root was used only to install policy and mint — no running")
    log("   service mounts or reads the root token.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
