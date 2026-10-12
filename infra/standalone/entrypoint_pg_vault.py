#!/usr/bin/env python3
"""Postgres entrypoint — Channel ENV from Vault (SOMA-STD-BOOTSTRAP-001 §2.5).

R-SEC-01: no secret ever written to disk. bootstrap_exec.py seeds
``postgres_password`` and mints a scoped token into T0 tmpfs. This process
reads that password with the scoped token (never root) and execve's postgres
with POSTGRES_PASSWORD in process RAM only.

Flow:
  1. Read scoped token from VAULT_TOKEN_FILE (T0 tmpfs).
  2. Read postgres_password from Vault into a local variable.
  3. os.execve(postgres, …, env with POSTGRES_PASSWORD only).
"""
from __future__ import annotations
import json, os, sys, urllib.request, urllib.error
from pathlib import Path

VAULT = (os.environ.get("VAULT_ADDR") or "").rstrip("/")
TARGET = os.environ.get("PG_ENTRYPOINT", "/usr/local/bin/docker-entrypoint.sh")
PG_ARGS = sys.argv[1:] or ["postgres"]
TOKEN_FILE = os.environ.get("VAULT_TOKEN_FILE") or ""

def log(m): print(m, file=sys.stderr, flush=True)

def vault(method, path, body=None, token=None):
    req = urllib.request.Request(f"{VAULT}/v1/{path}",
        data=json.dumps(body).encode() if body is not None else None, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("X-Vault-Token", token)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read()
            return r.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read()
        try: return e.code, json.loads(raw) if raw else {}
        except Exception: return e.code, {}
    except Exception as e:
        raise SystemExit(f"vault {method} {path}: {type(e).__name__}")

def main() -> None:
    if not VAULT:
        raise SystemExit("VAULT_ADDR required")
    if not TOKEN_FILE or not Path(TOKEN_FILE).is_file():
        raise SystemExit("VAULT_TOKEN_FILE required (scoped token from bootstrap_exec)")
    token = Path(TOKEN_FILE).read_text(encoding="utf-8").strip()
    if not token:
        raise SystemExit("VAULT_TOKEN_FILE empty")

    st, cur = vault("GET", "secret/data/agent/credentials", token=token)
    data = ((cur.get("data") or {}).get("data") or {}) if st == 200 else {}
    pw = data.get("postgres_password")
    if not pw:
        raise SystemExit("postgres_password missing in Vault (run bootstrap_exec first)")

    # F-10: drop token before exec. Target gets only the password.
    token = None

    env = dict(os.environ)
    env.pop("VAULT_TOKEN", None)
    env.pop("VAULT_TOKEN_FILE", None)
    env.pop("VAULT_UNSEAL_KEY", None)
    env["POSTGRES_PASSWORD"] = pw
    env.setdefault("POSTGRES_USER", "somaagent")
    env.setdefault("POSTGRES_DB", "somaagent")

    log("exec postgres (Channel ENV — password only in process RAM)")
    os.execvpe(TARGET, [TARGET, *PG_ARGS], env)

if __name__ == "__main__":
    main()
