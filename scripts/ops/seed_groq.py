"""Seed Groq credentials and a dialogue model profile into the Gateway.

Usage (env-driven):

  # Ensure the stack is running (gateway on localhost:21016 by default)
  # export GROQ_API_KEY=...   # required
  # export GATEWAY_BASE=http://127.0.0.1:21016   # optional
  # export INTERNAL_TOKEN=dev-internal-token     # optional (for /v1/llm/test)
  # export GROQ_MODEL=llama-3.1-8b-instant       # optional
  # export GROQ_BASE=https://api.groq.com/openai # optional (we will normalize)
  # python scripts/ops/seed_groq.py

This script posts to /v1/ui/settings/sections so it uses the same path as the UI.
It then calls /v1/llm/test (if INTERNAL_TOKEN is provided) to verify reachability.
"""

from __future__ import annotations

import asyncio
import os
import sys
from typing import Any, Dict

import httpx


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def build_sections_payload(*, model: str, base_url: str, api_path: str | None, api_key: str) -> Dict[str, Any]:
    fields = []
    # Minimal agent section (kept empty to avoid overriding other keys)
    # Model settings
    fields.append({"id": "chat_model_provider", "value": "groq"})
    fields.append({"id": "chat_model_name", "value": model})
    if base_url:
        fields.append({"id": "chat_model_api_base", "value": base_url})
    if api_path:
        fields.append({"id": "chat_model_api_path", "value": api_path})
    # API key for provider
    fields.append({"id": "api_key_groq", "value": api_key})
    return {"sections": [{"id": "model", "fields": fields}]}


async def seed(gateway_base: str, model: str, base_url: str, api_path: str | None, api_key: str, internal_token: str | None) -> int:
    gw = gateway_base.rstrip("/")
    payload = build_sections_payload(model=model, base_url=base_url, api_path=api_path, api_key=api_key)
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Persist via UI sections endpoint
        try:
            r = await client.post(f"{gw}/v1/ui/settings/sections", json=payload)
        except Exception as exc:
            print(f"error: failed to reach gateway at {gw}: {exc}")
            return 2
        if r.is_error:
            print(f"error: settings save failed: HTTP {r.status_code}: {(r.text or '')[:400]}")
            return 3
        print("settings saved via /v1/ui/settings/sections")

        # Optional verification
        if internal_token:
            try:
                r2 = await client.post(
                    f"{gw}/v1/llm/test",
                    json={"role": "dialogue"},
                    headers={"X-Internal-Token": internal_token},
                )
                if r2.is_error:
                    print(f"warn: /v1/llm/test failed: HTTP {r2.status_code}: {(r2.text or '')[:400]}")
                else:
                    data = r2.json()
                    ok = data.get("ok") and data.get("credentials_present")
                    print("llm.test:", data)
                    if not ok:
                        print("warn: credentials may be missing or upstream unreachable; check gateway logs")
            except Exception as exc:
                print(f"warn: failed running /v1/llm/test: {exc}")

    return 0


def main() -> int:
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("SLM_API_KEY")
    if not api_key:
        print("error: GROQ_API_KEY (or SLM_API_KEY) env var is required")
        return 1
    gateway_base = os.getenv("GATEWAY_BASE", "http://127.0.0.1:21016")
    internal_token = os.getenv("INTERNAL_TOKEN") or os.getenv("GATEWAY_INTERNAL_TOKEN")
    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    # Accept either full base including /openai(/v1) or host-only; gateway will normalize further
    base = os.getenv("GROQ_BASE", "https://api.groq.com/openai")
    # Allow overriding api_path explicitly; when omitted, gateway will use profile/api defaults
    api_path = os.getenv("GROQ_API_PATH") or None
    try:
        return asyncio.run(seed(gateway_base, model, base, api_path, api_key, internal_token))
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
