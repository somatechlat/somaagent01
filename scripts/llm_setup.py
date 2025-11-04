#!/usr/bin/env python3
"""
Dev helper to set LLM provider credentials in the Gateway and verify connectivity.

Usage (env-driven):
  - GATEWAY_BASE: Base URL for Gateway (default: http://127.0.0.1:${GATEWAY_PORT:-21016})
  - GATEWAY_INTERNAL_TOKEN: Internal token for /v1/llm/test (defaults to dev compose value)
  - PROVIDER: Explicit provider to set (openai|groq|openrouter|other)
  - SECRET: API key/secret for the provider

Auto-detection (when PROVIDER/SECRET not set):
  - Fetches /v1/ui/settings to detect model_profile.base_url and infers provider
  - Reads provider-specific env secrets:
      OPENAI_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY
  - As a last resort, uses SLM_API_KEY and infers provider from SLM_BASE_URL

Outputs a concise summary and exits non-zero on hard errors (e.g., missing secret).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


def _env(name: str, default: str | None = None) -> str | None:
    val = os.getenv(name)
    return val if (val is not None and str(val).strip() != "") else default


def _gateway_base() -> str:
    base = _env("GATEWAY_BASE")
    if base:
        return base.rstrip("/")
    port = _env("GATEWAY_PORT", "21016")
    return f"http://127.0.0.1:{port}".rstrip("/")


def _http_json(method: str, url: str, *, headers: dict[str, str] | None = None, body: dict | None = None) -> tuple[int, dict]:
    data = None
    req_headers = {"Accept": "application/json"}
    if headers:
        req_headers.update(headers)
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        req_headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:  # nosec B310
            raw = resp.read()
            status = getattr(resp, "status", 200) or 200
            try:
                parsed = json.loads(raw.decode("utf-8")) if raw else {}
            except Exception:
                parsed = {}
            return status, parsed
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            parsed = json.loads(raw.decode("utf-8")) if raw else {}
        except Exception:
            parsed = {"error": raw.decode("utf-8", errors="ignore")[:200]}
        return e.code or 500, parsed
    except Exception as e:
        return 0, {"error": str(e)}


def _detect_provider(base_url: str) -> str:
    try:
        host = urllib.parse.urlparse(base_url).netloc.lower()
    except Exception:
        host = (base_url or "").lower()
    if "groq" in host:
        return "groq"
    if "openrouter" in host:
        return "openrouter"
    if "openai" in host:
        return "openai"
    return "other"


def main() -> int:
    base = _gateway_base()
    internal = _env("GATEWAY_INTERNAL_TOKEN", "dev-internal-token")

    # 1) Fetch UI settings to infer provider from model_profile.base_url
    ui_url = f"{base}/v1/ui/settings"
    status, ui = _http_json("GET", ui_url)
    model_profile = (ui or {}).get("model_profile") or {}
    base_url = (model_profile or {}).get("base_url") or ""
    provider = _env("PROVIDER") or _detect_provider(str(base_url))

    # 2) Resolve secret
    secret = _env("SECRET")
    if not secret:
        if provider == "openai":
            secret = _env("OPENAI_API_KEY")
        elif provider == "groq":
            secret = _env("GROQ_API_KEY")
        elif provider == "openrouter":
            secret = _env("OPENROUTER_API_KEY")
        # Fallback from SLM_* envs
        if not secret:
            secret = _env("SLM_API_KEY")
            slm_base = _env("SLM_BASE_URL", "") or ""
            if not provider or provider == "other":
                provider = _detect_provider(slm_base)

    if not provider:
        print("[llm-setup] Could not determine provider. Set PROVIDER=openai|groq|openrouter and SECRET=...", file=sys.stderr)
        return 2
    if not secret:
        print(f"[llm-setup] Missing secret for provider '{provider}'. Set SECRET=... or a provider-specific env.", file=sys.stderr)
        return 3

    # 3) Upsert credentials
    cred_url = f"{base}/v1/llm/credentials"
    c_status, c_resp = _http_json("POST", cred_url, body={"provider": provider, "secret": secret})
    if c_status not in (200, 201):
        print(f"[llm-setup] Failed to upsert credentials ({c_status}): {c_resp}", file=sys.stderr)
        return 4
    print(f"[llm-setup] Stored credentials for provider='{provider}'.")

    # 4) Quick test via internal token
    t_url = f"{base}/v1/llm/test"
    t_status, t_resp = _http_json("POST", t_url, headers={"X-Internal-Token": internal}, body={"role": "dialogue"})
    ok = bool(t_resp.get("ok")) and t_status == 200
    cred_present = bool(t_resp.get("credentials_present"))
    reachable = bool(t_resp.get("reachable"))
    print("[llm-test] ", json.dumps({
        "status": t_status,
        "ok": ok,
        "provider": t_resp.get("provider"),
        "credentials_present": cred_present,
        "reachable": reachable,
        "status_code": t_resp.get("status_code"),
        "detail": t_resp.get("detail"),
    }, ensure_ascii=False))

    return 0 if (ok and cred_present) else (5 if not ok else 6)


if __name__ == "__main__":
    raise SystemExit(main())
