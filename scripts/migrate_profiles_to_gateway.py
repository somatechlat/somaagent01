#!/usr/bin/env python3
"""
Idempotent migration helper to push model profiles into the Gateway.

Usage:
  - Provide a JSON file containing a list of profiles with keys: role, deployment_mode, model, base_url, temperature, kwargs
  - Or use --single to push a single profile via CLI arguments.

This script will attempt the UI-friendly /v1/ui/settings PUT first (which overlays the dialogue profile),
then fall back to the ModelProfile CRUD endpoints if necessary.
"""
import argparse
import json
import os
import sys
from typing import Any, Dict, List

import requests

from src.core.config import cfg

GATEWAY_BASE = (
    cfg.env("SA01_GATEWAY_BASE_URL")
    or cfg.env("GATEWAY_BASE_URL")
    or f"http://{cfg.settings().service.host}:{cfg.settings().service.port}"
)
UI_SETTINGS = f"{GATEWAY_BASE}/v1/ui/settings"
MODEL_PROFILES = f"{GATEWAY_BASE}/v1/model-profiles"


def _push_via_ui_settings(profile: Dict[str, Any]) -> bool:
    payload = {"model_profile": profile}
    try:
        resp = requests.put(UI_SETTINGS, json=payload, timeout=5.0)
        return resp.status_code in (200, 201, 204)
    except Exception:
        return False


def _push_via_api(profile: Dict[str, Any]) -> bool:
    # direct upsert requires two path params (role/deployment). We'll call the PUT endpoint
    role = profile.get("role") or "dialogue"
    dep = profile.get("deployment_mode") or cfg.env("DEPLOYMENT_MODE", cfg.settings().service.deployment_mode) or "DEV"
    url = f"{MODEL_PROFILES}/{role}/{dep}"
    try:
        resp = requests.put(url, json=profile, timeout=5.0)
        return resp.status_code in (200, 201, 204)
    except Exception:
        return False


def migrate(profiles: List[Dict[str, Any]]) -> int:
    failed = 0
    for p in profiles:
        ok = _push_via_ui_settings(p)
        if ok:
            print(
                f"ok: profile {p.get('role')}@{p.get('deployment_mode') or 'DEV'} via /v1/ui/settings"
            )
            continue
        ok = _push_via_api(p)
        if ok:
            print(
                f"ok: profile {p.get('role')}@{p.get('deployment_mode') or 'DEV'} via /v1/model-profiles"
            )
            continue
        print(f"error: failed to push profile {p.get('role')}@{p.get('deployment_mode')}")
        failed += 1
    return failed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="Path to JSON file with a list of profiles")
    ap.add_argument("--single", help="JSON string for a single profile")
    args = ap.parse_args()
    profiles: List[Dict[str, Any]] = []
    if args.json:
        if not os.path.exists(args.json):
            print("JSON file not found", file=sys.stderr)
            sys.exit(2)
        with open(args.json, "r", encoding="utf-8") as fh:
            profiles = json.load(fh)
    elif args.single:
        profiles = [json.loads(args.single)]
    else:
        print("Provide --json or --single", file=sys.stderr)
        ap.print_help()
        sys.exit(2)

    failed = migrate(profiles)
    if failed:
        print(f"Completed with {failed} failures", file=sys.stderr)
        sys.exit(1)
    print("Completed successfully")


if __name__ == "__main__":
    main()
