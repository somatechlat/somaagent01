#!/usr/bin/env python3
"""bootstrap_exec.py — one process: init/unseal → seed → mint → execve.

SOMA-STD-BOOTSTRAP-001. Operator LAW 2026-10-11: no secret files, no secrets
in ENV as steady state. Vault is the system of record.

Root token lives ONLY in this process's memory. It is never written to T0,
never logged, never passed to the target. The scoped TTL service token is
written to T0 tmpfs for VAULT_TOKEN_FILE (documented Channel for the app).

Usage:
    bootstrap_exec.py --target /app/start.sh -- [args...]
"""
from __future__ import annotations

import json
import os
import secrets as py_secrets
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

VAULT = (os.environ.get("VAULT_ADDR") or "").rstrip("/")
T0 = Path(os.environ.get("T0_DIR") or "/run/t0")
POLICY_DIR = Path("/work/vault-policies")
TOKEN_TTL_HOURS = os.environ.get("VAULT_TOKEN_TTL_HOURS") or ""

UNSEAL_ACCOUNT = "vault_unseal_key"
AGENT_TOKEN_ACCOUNT = "agent_runtime_token"
BRAIN_TOKEN_ACCOUNT = "brain_runtime_token"


def log(m: str) -> None:
    print(m, file=sys.stderr, flush=True)


def die(m: str) -> None:
    log(f"ERROR: {m}")
    raise SystemExit(1)


def vault(method: str, path: str, body=None, token: str | None = None):
    req = urllib.request.Request(
        f"{VAULT}/v1/{path}",
        data=json.dumps(body).encode() if body is not None else None,
        method=method,
    )
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("X-Vault-Token", token)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read()
            return r.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw) if raw else {}
        except Exception:
            return e.code, {}
    except Exception as e:
        raise SystemExit(f"vault {method} {path}: {type(e).__name__}")


def t0_write(account: str, value: str) -> None:
    T0.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(str(T0), 0o700)
        _uid = int(os.environ.get("BOOTSTRAP_T0_UID", "0"))
        _gid = int(os.environ.get("BOOTSTRAP_T0_GID", "0"))
        if _uid:
            os.chown(str(T0), _uid, _gid)
    except OSError:
        pass
    path = T0 / account
    try:
        path.unlink()
    except (FileNotFoundError, OSError):
        pass
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, value.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    os.chmod(str(path), 0o600)
    # Per-consumer T0: token owned by the consumer UID (0600). Ceremony may
    # run as root; the app (appuser 1000) must read only its own file.
    uid = int(os.environ.get("BOOTSTRAP_T0_UID", "0"))
    gid = int(os.environ.get("BOOTSTRAP_T0_GID", "0"))
    if uid:
        try:
            os.chown(str(path), uid, gid)
        except OSError:
            pass


def t0_read(account: str) -> str | None:
    """Read one T0 account. Never raise on unreadable foreign-uid files.

    SOMA-STD-SECURITY-001: T0 is per-consumer private tmpfs 0700/0600. A
    PermissionError means another UID's file — treat as absent (fail-closed),
    never crash bootstrap.
    """
    path = T0 / account
    try:
        if not path.is_file():
            return None
        value = path.read_text(encoding="utf-8").strip()
        return value or None
    except (PermissionError, OSError):
        return None


def kv2_write(token: str, mount: str, path: str, data: dict) -> None:
    st, _ = vault("POST", f"{mount}/data/{path}", {"data": data}, token=token)
    if st not in (200, 204):
        die(f"KV write {mount}/{path} -> HTTP {st}")


def kv2_write_merge(token: str, mount: str, path: str, key: str, value: str) -> None:
    """KV v2 merge-safe single-key write (POST replaces the whole document).

    Read → merge map → write whole object → read-back assert new key AND all
    pre-existing sibling keys survive (SOMA-STD-BOOTSTRAP-001).
    """
    st, cur = vault("GET", f"{mount}/data/{path}", token=token)
    data: dict = {}
    if st == 200:
        data = dict((cur.get("data") or {}).get("data") or {})
    siblings_before = set(data.keys())
    data[key] = value
    kv2_write(token, mount, path, data)
    st, cur = vault("GET", f"{mount}/data/{path}", token=token)
    if st != 200:
        die(f"KV read-back {mount}/{path} -> HTTP {st}")
    stored = (cur.get("data") or {}).get("data") or {}
    if stored.get(key) != value:
        die(f"read-back mismatch at {mount}/{path}[{key}]")
    missing = siblings_before - set(stored.keys())
    if missing:
        die(f"KV merge wiped sibling keys at {mount}/{path}: {sorted(missing)}")


def kv2_read(token: str, mount: str, path: str, key: str) -> str | None:
    st, cur = vault("GET", f"{mount}/data/{path}", token=token)
    if st != 200:
        return None
    data = ((cur.get("data") or {}).get("data") or {})
    value = data.get(key)
    return str(value) if value else None


def ensure_unsealed() -> tuple[str | None, str | None]:
    """Return (root_token, unseal_key). Root stays in this process RAM only.

    Never read root from T0 or any file (enterprise security pattern). One-shot
    ENV or the sys/init response only. Unseal key may live in T0 tmpfs 0600.
    """
    root = os.environ.get("VAULT_TOKEN", "").strip()
    unseal = os.environ.get("VAULT_UNSEAL_KEY", "").strip() or t0_read(UNSEAL_ACCOUNT)

    st, initp = vault("GET", "sys/init")
    initialized = (initp or {}).get("initialized")
    if not initialized:
        st, initp = vault(
            "POST", "sys/init", {"secret_shares": 1, "secret_threshold": 1}
        )
        if st != 200:
            die(f"sys/init HTTP {st}")
        keys = initp.get("keys") or initp.get("keys_base64") or []
        root = (initp.get("root_token") or "").strip()
        unseal = keys[0] if keys else ""
        if not root or not unseal:
            die("sys/init returned no keys/root_token")
        # Unseal key stays in THIS process RAM only (never consumer T0).
        # Operator/keychain custodian for restarts (SOMA-STD-SECURITY-001 §1.2).
        vault("POST", "sys/unseal", {"key": unseal}, token=root)
        log("vault: initialised + unsealed (root+unseal in process RAM only)")
        return root, unseal

    st, hs = vault("GET", "sys/health")
    if hs.get("sealed") or st == 503:
        if not unseal:
            die("Vault sealed and no unseal key (R-SEC-01: no repo file)")
        vault("POST", "sys/unseal", {"key": unseal})
        log("vault: unsealed")

    if not root:
        die(
            "no Vault root token in process RAM or T0. First boot of an "
            "uninitialised Vault stores it here; a Vault initialised by another "
            "container cannot share that RAM. Wipe vault data volume to re-bootstrap "
            "or provide VAULT_TOKEN for this one-shot (R-SEC-03)."
        )
    return root, unseal


def seed_credentials(root: str) -> None:
    for mount in ("secret",):
        st, _ = vault("POST", f"sys/mounts/{mount}", {"type": "kv-v2"}, token=root)
        if st not in (200, 204, 400):
            die(f"mount {mount} -> HTTP {st}")

    creds = (
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
        "llm_api_key",
        "google_client_secret",
        "spicedb_token",
        "kafka_sasl_password",
        "identity_password_pepper",
    )
    for key in creds:
        existing = kv2_read(root, "secret", "agent/credentials", key)
        if existing:
            log(f"   – skipped (already in Vault): agent/credentials[{key}]")
            continue
        value = py_secrets.token_urlsafe(32)
        kv2_write_merge(root, "secret", "agent/credentials", key, value)
        log(f"   ✔ generated + seeded agent/credentials[{key}]")
        del value

    for provider in ("groq", "openai", "elevenlabs", "anthropic"):
        key = f"{provider}_api_key"
        existing = kv2_read(root, "secret", "agent/api_keys", key)
        if existing:
            continue
        value = py_secrets.token_urlsafe(32)
        kv2_write_merge(root, "secret", "agent/api_keys", key, value)
        log(f"   ✔ generated + seeded agent/api_keys[{key}]")
        del value


def mint_scoped(root: str) -> None:
    if not TOKEN_TTL_HOURS:
        die("VAULT_TOKEN_TTL_HOURS is required (no default — Rule 91)")
    try:
        ttl_h = int(TOKEN_TTL_HOURS)
    except ValueError:
        die("VAULT_TOKEN_TTL_HOURS must be an integer")
    if ttl_h < 1:
        die("VAULT_TOKEN_TTL_HOURS must be >= 1")

    for policy_file in sorted(POLICY_DIR.glob("*.hcl")):
        name = policy_file.stem
        st, _ = vault(
            "POST",
            f"sys/policies/acl/{name}",
            {"policy": policy_file.read_text(encoding="utf-8")},
            token=root,
        )
        if st not in (200, 204):
            die(f"policy {name} -> HTTP {st}")
        log(f"   ✔ policy installed: {name}")

    for policy, account, comment in (
        ("agent-runtime", AGENT_TOKEN_ACCOUNT, "Agent runtime"),
        ("brain-runtime", BRAIN_TOKEN_ACCOUNT, "SomaBrain runtime"),
    ):
        existing = t0_read(account)
        if existing:
            log(f"   \u2013 skipped (token already in T0): {account}")
            continue
        st, payload = vault(
            "POST",
            "auth/token/create",
            {
                "policies": [policy],
                "ttl": f"{ttl_h}h",
                "renewable": True,
                "display_name": comment,
                "no_default_policy": True,
            },
            token=root,
        )
        if st != 200:
            die(f"token create {policy} -> HTTP {st}")
        token = (payload.get("auth") or {}).get("client_token") or ""
        if not token:
            die(f"token create {policy} returned no client_token")
        t0_write(account, token)
        log(f"   ✔ issued {policy:16} -> T0_DIR/{account}  (ttl={ttl_h}h)")
        del token


def main() -> None:
    if not VAULT:
        die("VAULT_ADDR required")
    args = sys.argv[1:]
    if "--target" not in args:
        die("--target is required")
    i = args.index("--target")
    target = args[i + 1]
    exec_args = args[i + 2 :]
    if exec_args and exec_args[0] == "--":
        exec_args = exec_args[1:]

    for _ in range(40):
        st, _ = vault("GET", "sys/health")
        if st:
            break
        time.sleep(1)
    else:
        die("Vault unreachable")

    root, _unseal = ensure_unsealed()

    # If vault was already initialised by another ceremony and we have no root,
    # reuse a scoped token already in this consumer's T0 (restart) or fail closed.
    existing = t0_read(AGENT_TOKEN_ACCOUNT)
    if root:
        seed_credentials(root)
        mint_scoped(root)
        # Channel ENV postgres password for third-party PID1 (never a file).
        try:
            pw = kv2_read(root, "secret", "agent/credentials", "postgres_password")
        except Exception:
            pw = None
    else:
        pw = None
        if not existing:
            die(
                "Vault is already initialised and this ceremony has no root "
                "(VAULT_TOKEN one-shot). Consumer T0 has no agent_runtime_token. "
                "Re-ceremony required (SOMA-STD-SECURITY-001) — do not widen policy."
            )
        log("bootstrap: reusing scoped token from private T0")

    # Mirror scoped token to another per-consumer T0 if requested (e.g. postgres).
    # Still 0600/0700. Never root. Never a password.
    mirror = os.environ.get("T0_MIRROR_DIR", "").strip()
    if mirror:
        src = T0 / AGENT_TOKEN_ACCOUNT
        dst_dir = Path(mirror)
        dst_dir.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(str(dst_dir), 0o700)
        except OSError:
            pass
        if src.is_file():
            val = src.read_text(encoding="utf-8")
            dst = dst_dir / AGENT_TOKEN_ACCOUNT
            fd = os.open(str(dst), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            try:
                os.write(fd, val.encode("utf-8"))
                os.fsync(fd)
            finally:
                os.close(fd)
            os.chmod(str(dst), 0o600)
            uid = int(os.environ.get("BOOTSTRAP_T0_UID", "0"))
            gid = int(os.environ.get("BOOTSTRAP_T0_GID", "0"))
            if uid:
                try:
                    os.chown(str(dst), uid, gid)
                except OSError:
                    pass
            log(f"   ✔ mirrored scoped token -> {dst}")
            del val

    # F-10: drop root before exec. Target gets only the scoped token via T0.
    root = None
    _unseal = None

    env = dict(os.environ)
    env.pop("VAULT_TOKEN", None)
    env.pop("VAULT_UNSEAL_KEY", None)
    env["VAULT_TOKEN_FILE"] = str(T0 / AGENT_TOKEN_ACCOUNT)
    env["T0_DIR"] = str(T0)
    if pw:
        # Channel ENV only — third-party postgres execve. Not a file.
        env["POSTGRES_PASSWORD"] = pw
        del pw

    # SOMA-STD-SECURITY-001: drop to appuser (uid 1000) before the app runs.
    drop_uid = int(os.environ.get("BOOTSTRAP_DROP_UID", "1000"))
    drop_gid = int(os.environ.get("BOOTSTRAP_DROP_GID", "1000"))
    if os.geteuid() == 0 and drop_uid != 0:
        try:
            tok = T0 / AGENT_TOKEN_ACCOUNT
            if tok.exists():
                os.chown(str(tok), drop_uid, drop_gid)
                os.chmod(str(tok), 0o600)
        except OSError:
            pass
        os.setgid(drop_gid)
        os.setuid(drop_uid)
        log(f"bootstrap: dropped privileges to uid={drop_uid}")

    log(f"bootstrap: exec {target} {' '.join(exec_args)}")
    os.execvpe(target, [target, *exec_args], env)


if __name__ == "__main__":
    main()
