#!/usr/bin/env python3
"""vault-inject — Channel ENV for third-party images (SOMA-STD-BOOTSTRAP-001 §2.5).

Postgres/Keycloak/MinIO accept a password only via process environment.
This injector:

1. Authenticates to Vault with the one-shot bootstrap token (R-SEC-03).
2. Fetches the secret into process memory (JSON body, never argv).
3. execve's the target with ONLY the secret keys in its environment.
4. The bootstrap token is NOT passed to the target.

The secret exists only in the exec'd process's RAM environment block.
It is not in compose, not in config.v2.json, not on disk.

Usage:
    vault_inject.py --target /usr/local/bin/docker-entrypoint.sh -- postgres
"""
from __future__ import annotations
import json, os, sys, urllib.request, urllib.error

def fail(msg: str) -> None:
    print(f"vault-inject: {msg}", file=sys.stderr)
    raise SystemExit(1)

def main() -> None:
    args = sys.argv[1:]
    if "--target" not in args:
        fail("--target is required")
    i = args.index("--target")
    target = args[i + 1]
    exec_args = args[i + 2:]

    vault_addr = (os.environ.get("VAULT_ADDR") or "").rstrip("/")
    if not vault_addr:
        fail("VAULT_ADDR required (R-SEC-03 topology)")

    # Bootstrap token: env one-shot OR token file (R-SEC-03).
    token = (os.environ.get("VAULT_TOKEN") or "").strip()
    tok_file = os.environ.get("VAULT_TOKEN_FILE") or ""
    if not token and tok_file:
        try:
            token = open(tok_file).read().strip()
        except OSError as e:
            fail(f"cannot read VAULT_TOKEN_FILE: {e}")
    if not token:
        fail("no Vault bootstrap token (VAULT_TOKEN or VAULT_TOKEN_FILE)")

    # Map: env key to mount/path/key to fetch
    # Example: POSTGRES_PASSWORD = somafractalmemory/database/password
    inject_spec = (os.environ.get("VAULT_INJECT") or "").strip()
    if not inject_spec:
        fail("VAULT_INJECT required (e.g. POSTGRES_PASSWORD=somafractalmemory/database/password)")
    mappings = []
    for part in inject_spec.split(","):
        part = part.strip()
        if not part or "=" not in part:
            continue
        env_name, path_key = part.split("=", 1)
        mappings.append((env_name.strip(), path_key.strip()))

    env = dict(os.environ)
    # Strip bootstrap token from the target's environment (F-10).
    env.pop("VAULT_TOKEN", None)
    env.pop("VAULT_TOKEN_FILE", None)
    env.pop("VAULT_INJECT", None)

    for env_name, path_key in mappings:
        # path_key = mount/secret_path/field  e.g. secret/agent/credentials/postgres_password
        # KV v2: GET {addr}/v1/{mount}/data/{path}
        bits = path_key.split("/")
        if len(bits) < 3:
            fail(f"bad VAULT_INJECT entry {path_key!r}")
        mount, rest, field = bits[0], "/".join(bits[1:-1]), bits[-1]
        url = f"{vault_addr}/v1/{mount}/data/{rest}"
        req = urllib.request.Request(url, method="GET")
        req.add_header("X-Vault-Token", token)
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                payload = json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            fail(f"Vault read {url} -> HTTP {e.code}")
        except Exception as e:
            fail(f"Vault read {url} -> {type(e).__name__}")
        data = (payload.get("data") or {}).get("data") or {}
        value = data.get(field)
        if not value:
            fail(f"{path_key} missing or empty in Vault")
        env[env_name] = str(value)

    # Channel ENV: secret only in the exec'd process environment.
    os.execvpe(target, [target, *exec_args], env)

if __name__ == "__main__":
    main()
