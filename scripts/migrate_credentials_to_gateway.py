#!/usr/bin/env python3
"""
Idempotent migration helper to push LLM credentials into the Gateway.

Usage:
  - Export a CSV or provide via CLI: provider,secret
  - By default the script will attempt to call the UI-friendly endpoint /v1/ui/settings
    (which accepts credentials) to avoid requiring admin internal tokens.
  - If /v1/ui/settings is not allowed, the script will try /v1/llm/credentials with
    X-Internal-Token from the environment variable GATEWAY_INTERNAL_TOKEN.

This script is intentionally simple and safe: it does not echo secrets to stdout
and treats network failures as retriable (exit code non-zero) so it's safe to run
multiple times.
"""
import argparse
import json
import os
import sys
from typing import List, Tuple

import requests

GATEWAY_BASE = os.getenv("GATEWAY_BASE_URL", "http://127.0.0.1:21016")
UI_SETTINGS = f"{GATEWAY_BASE}/v1/ui/settings"
CRED_ENDPOINT = f"{GATEWAY_BASE}/v1/llm/credentials"


def _push_via_ui_settings(provider: str, secret: str) -> bool:
    payload = {"llm_credentials": {"provider": provider, "secret": secret}}
    try:
        resp = requests.put(UI_SETTINGS, json=payload, timeout=5.0)
        if resp.status_code in (200, 201, 204):
            return True
        # Some deployments might reject; treat non-2xx as failure here
        return False
    except Exception:
        return False


def _push_via_admin(provider: str, secret: str) -> bool:
    token = os.getenv("GATEWAY_INTERNAL_TOKEN")
    if not token:
        return False
    headers = {"X-Internal-Token": token, "Content-Type": "application/json"}
    try:
        resp = requests.post(CRED_ENDPOINT, json={"provider": provider, "secret": secret}, headers=headers, timeout=5.0)
        return resp.status_code in (200, 201, 204)
    except Exception:
        return False


def migrate(items: List[Tuple[str, str]]) -> int:
    failed = 0
    for provider, secret in items:
        p = provider.strip().lower()
        if not p or not secret:
            print(f"Skipping invalid row provider={provider}")
            failed += 1
            continue
        ok = _push_via_ui_settings(p, secret)
        if ok:
            print(f"ok: {p} via /v1/ui/settings")
            continue
        # fallback to admin endpoint
        ok = _push_via_admin(p, secret)
        if ok:
            print(f"ok: {p} via /v1/llm/credentials (admin)")
            continue
        print(f"error: failed to push credential for provider {p}")
        failed += 1
    return failed


def parse_csv(path: str) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    with open(path, "r", encoding="utf-8") as fh:
        for ln in fh:
            s = ln.strip()
            if not s:
                continue
            parts = [p.strip() for p in s.split(",", 1)]
            if len(parts) < 2:
                continue
            out.append((parts[0], parts[1]))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", help="Path to CSV file with provider,secret per-line")
    ap.add_argument("--pair", help="Single provider:secret pair (provider:secret)")
    args = ap.parse_args()
    items: List[Tuple[str, str]] = []
    if args.csv:
        if not os.path.exists(args.csv):
            print("CSV file not found", file=sys.stderr)
            sys.exit(2)
        items = parse_csv(args.csv)
    elif args.pair:
        if ":" not in args.pair:
            print("--pair expects provider:secret", file=sys.stderr)
            sys.exit(2)
        provider, secret = args.pair.split(":", 1)
        items = [(provider, secret)]
    else:
        print("Provide --csv or --pair", file=sys.stderr)
        ap.print_help()
        sys.exit(2)

    failed = migrate(items)
    if failed:
        print(f"Completed with {failed} failures", file=sys.stderr)
        sys.exit(1)
    print("Completed successfully")


if __name__ == "__main__":
    main()
