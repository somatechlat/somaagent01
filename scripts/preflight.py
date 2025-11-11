#!/usr/bin/env python3
"""
Preflight validation for SomaAgent01 runtime.

- Enforces canonical environment taxonomy (SA01_*).
- Fails if legacy env names are present.
- Verifies required canonical variables are set (non-empty).
- Optionally probes OPA health and decision path when URLs are present.

Exit codes:
  0: OK
  1: Missing required variables / legacy variables present
  2: Dependency check failed (OPA unreachable)
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

# Legacy names we forbid entirely (non-SA01_ variables)
LEGACY_ENV = {
    "POSTGRES_DSN",
    "REDIS_URL",
    "KAFKA_BOOTSTRAP_SERVERS",
    "GATEWAY_BASE_URL",
    "GATEWAY_INTERNAL_TOKEN",
    "GATEWAY_ENC_KEY",
    "DISABLE_FILE_SAVING",
    "GATEWAY_WRITE_THROUGH",
    "GATEWAY_WRITE_THROUGH_ASYNC",
    "ENABLE_EMBED_ON_INGEST",
    "FEATURE_AUDIO",
    "FEATURE_BROWSER",
    "WORKER_GATEWAY_BASE",
    "SOMA_ENABLED",
    "OPENROUTER_REFERER",
    "OPENROUTER_TITLE",
    "ENABLE_TEST_POLICY_BYPASS",
}

REQUIRED_CANONICAL = [
    "SA01_DEPLOYMENT_MODE",
    "SA01_AUTH_REQUIRED",
    "SA01_AUTH_JWT_SECRET",
    "SA01_AUTH_INTERNAL_TOKEN",
    "SA01_CRYPTO_FERNET_KEY",
    "SA01_POLICY_URL",
    "SA01_POLICY_DECISION_PATH",
    "SA01_DB_DSN",
    "SA01_REDIS_URL",
    "SA01_KAFKA_BOOTSTRAP_SERVERS",
]

OPTIONAL = {
    "SA01_DB_POOL_MIN_SIZE",
    "SA01_DB_POOL_MAX_SIZE",
    "SA01_KAFKA_PUBLISH_TIMEOUT_SECONDS",
    "SA01_GATEWAY_PORT",
    "SA01_FILE_SAVING_DISABLED",
    "SA01_GATEWAY_WRITE_THROUGH",
    "SA01_GATEWAY_WRITE_THROUGH_ASYNC",
    "SA01_GATEWAY_BASE_URL",
    "SA01_SOMA_ENABLED",
    "SA01_SOMA_BASE_URL",
    "SA01_SOMA_TENANT_ID",
    "SA01_SOMA_NAMESPACE",
    "SA01_SOMA_MEMORY_NAMESPACE",
    "SA01_LOG_LEVEL",
    "SA01_OBS_TRACE_SAMPLER",
}


def fail(msg: str, code: int = 1) -> None:
    sys.stderr.write(msg + "\n")
    sys.exit(code)


def check_legacy_present() -> list[str]:
    present = []
    for k in LEGACY_ENV:
        if k in os.environ and os.environ[k] != "":
            present.append(k)
    return present


def check_required_present() -> list[str]:
    missing = []
    for k in REQUIRED_CANONICAL:
        if not os.environ.get(k):
            missing.append(k)
    return missing


def validate_mode_and_auth() -> list[str]:
    errs: list[str] = []
    mode = os.environ.get("SA01_DEPLOYMENT_MODE", "").upper()
    if mode not in {"DEV", "PROD"}:
        errs.append(f"SA01_DEPLOYMENT_MODE must be DEV or PROD (got '{mode or 'empty'}')")
    auth = os.environ.get("SA01_AUTH_REQUIRED", "").lower()
    if auth not in {"true", "1", "yes"}:
        errs.append("SA01_AUTH_REQUIRED must be true|1|yes to enforce auth in all modes")
    return errs


def probe_opa() -> tuple[bool, str]:
    base = os.environ.get("SA01_POLICY_URL", "").rstrip("/")
    path = os.environ.get("SA01_POLICY_DECISION_PATH", "")
    if not base or not path:
        return True, "OPA probe skipped (no URL/path)"
    # health check
    try:
        with urllib.request.urlopen(f"{base}/health", timeout=3) as resp:
            if resp.status >= 400:
                return False, f"OPA health returned {resp.status}"
    except Exception as e:
        return False, f"OPA health error: {e}"
    # decision probe (synthetic input)
    try:
        req = urllib.request.Request(
            f"{base}{path}",
            data=json.dumps({"input": {"startup": "probe"}}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status >= 400:
                return False, f"OPA decision probe returned {resp.status}"
    except urllib.error.HTTPError as he:
        # 200..399 ok; 4xx means decision path exists but denied; still OK
        if 400 <= he.code < 500:
            return True, f"OPA decision probe denied ({he.code}) — path present"
        return False, f"OPA decision probe HTTP error: {he.code}"
    except Exception as e:
        return False, f"OPA decision probe error: {e}"
    return True, "OPA healthy and decision path reachable"


def main() -> None:
    legacy = check_legacy_present()
    if legacy:
        fail("Legacy environment variables present: " + ", ".join(sorted(legacy)), 1)
    missing = check_required_present()
    if missing:
        fail("Missing required canonical env vars: " + ", ".join(sorted(missing)), 1)
    val_errs = validate_mode_and_auth()
    if val_errs:
        fail("; ".join(val_errs), 1)
    ok, msg = probe_opa()
    if not ok:
        fail(msg, 2)
    print("preflight OK: canonical env set, no legacy vars, OPA reachable")


if __name__ == "__main__":
    main()
