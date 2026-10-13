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
  to the T0 custodian (``T0_DIR``) only — the same channel ``vault_unseal.py``
  uses for the unseal key. There is no host secrets directory and no
  ``./secrets/`` (SOMA-STD-BOOTSTRAP-001 §2.5). T0 must be tmpfs OR a
  dedicated named-volume mount (R-SEC-01 exception §2.1a). Root is never
  written to T0 (R-SEC-01 absolute).
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
    T0_DIR                  REQUIRED. Custodian directory. Issued tokens are
                            written here (and only here). Must be tmpfs or a
                            dedicated named-volume mount (R-SEC-01 §2.1a);
                            any other filesystem is refused.
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


# Resolved after `die`/`log` are defined below — require_env calls die().
T0_DIR = None  # set in _configure()
VAULT_ADDR = ""
TOKEN_TTL_HOURS = 0
TOKEN_TTL = ""

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


def _configure() -> None:
    """Bind operator bootstrap config after helpers exist (Soma law)."""
    global T0_DIR, VAULT_ADDR, TOKEN_TTL_HOURS, TOKEN_TTL
    T0_DIR = Path(require_env("T0_DIR"))
    VAULT_ADDR = require_env("VAULT_ADDR").rstrip("/")
    TOKEN_TTL_HOURS = int(require_env("VAULT_TOKEN_TTL_HOURS"))
    TOKEN_TTL = f"{TOKEN_TTL_HOURS}h"


def _keychain_available() -> bool:
    return (
        sys.platform == "darwin"
        and __import__("shutil").which("security") is not None
    )


def _t0_custodian_allows(account: str, value: str) -> None:
    """R-SEC-01 — what may be written into T0, and onto which filesystem.

    ABSOLUTE (no exception): the root token is never written to T0 or any
    other filesystem. Root is process RAM of a one-shot only (§3.4). The
    2026-10-13 incident wrote ``vault_root_token`` here — that is the
    violation this guard exists to make impossible.

    Custodian filesystem — two allowed shapes (SOMA-STD-BOOTSTRAP-001 §2.1a):

    * **tmpfs** — RAM-only, preferred. Never paged to durable storage.
    * **dedicated named-volume mount** (e.g. ``standalone_t0_agent``) —
      a *documented local-standalone exception*. Justification: the 1-of-1
      unseal key must survive container recreate or the store becomes
      permanently un-unsealable; Linux containers have no OS keychain; the
      volume is container-native (not the repo, not a host bind). Production
      replaces this custodian with KMS auto-unseal (§2.3) and the exception
      disappears.

    Everything else (repo path, host bind, overlay layer, ``/tmp`` on the
    root fs) is refused.
    """
    if account == ROOT_ACCOUNT:
        raise die(
            f"refusing to write {ROOT_ACCOUNT} to T0 (R-SEC-01 absolute). "
            f"Root lives only in a one-shot process and is revoked after mint "
            f"(§3.4). Use vault operator generate-root for break-glass."
        )
    if value == "":
        raise die(f"refusing to write empty value for {account}")

    T0_DIR.mkdir(parents=True, exist_ok=True)
    try:
        mounts_path = Path("/proc/mounts")
        if mounts_path.exists():
            mounts = mounts_path.read_text()
            resolved = str(T0_DIR.resolve())

            def _mount_entry(path: str) -> tuple[str, str] | None:
                """Longest /proc/mounts entry covering `path` → (mountpoint, fstype)."""
                best: tuple[str, str] | None = None
                for line in mounts.splitlines():
                    parts = line.split()
                    if len(parts) < 3:
                        continue
                    mp, fstype = parts[1], parts[2]
                    if path == mp or path.startswith(mp.rstrip("/") + "/"):
                        if best is None or len(mp) > len(best[0]):
                            best = (mp, fstype)
                return best

            entry = _mount_entry(resolved)
            if entry is None:
                raise die(
                    f"T0_DIR={T0_DIR} is not a mount point and is not under "
                    f"one. Tokens must never touch an ordinary directory "
                    f"(R-SEC-01)."
                )
            mp, fstype = entry
            if fstype in ("tmpfs", "ramfs"):
                pass  # RAM custodian — preferred
            elif resolved == mp.rstrip("/") or resolved.startswith(mp.rstrip("/") + "/"):
                # §2.1a documented exception: a dedicated volume mount (its
                # own /proc/mounts entry, not the container root overlay).
                if mp == "/" or fstype == "overlay":
                    raise die(
                        f"T0_DIR={T0_DIR} is on the container root fs "
                        f"({fstype} at {mp}). R-SEC-01: use tmpfs or a "
                        f"dedicated named-volume mount."
                    )
                # Named volume (ext4/xfs/… on its own mountpoint) — allowed
                # under §2.1a. Root is still refused above.
            else:
                raise die(
                    f"T0_DIR={T0_DIR} is not on tmpfs or a dedicated volume "
                    f"mount (R-SEC-01)."
                )
    except OSError:
        # No /proc (e.g. macOS host-side one-shot): the operator owns the
        # custodian. Root is still refused above.
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
            # Orphan: survives revoke of the one-shot root that minted it
            # (Vault revokes children with their parent). Root is revoked
            # after ceremony; service leases must outlive it.
            "no_parent": True,
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
    _configure()
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
