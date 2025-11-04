"""Seed Groq credentials and a dialogue model profile into the Gateway.

Usage (CLI):

    python scripts/ops/seed_groq.py --api-key <GROQ_API_KEY> \
        [--gateway-base http://127.0.0.1:21016] \
        [--internal-token dev-internal-token] \
        [--model llama-3.1-8b-instant] \
        [--base https://api.groq.com/openai] \
        [--api-path /v1/chat/completions]

This script stores the provider credential via /v1/llm/credentials and updates
the dialogue model via /v1/ui/settings/sections (without sending secrets).
It then calls /v1/llm/test (if --internal-token is provided) to verify reachability.
"""

from __future__ import annotations

import asyncio
import argparse
import sys
from typing import Any, Dict

import httpx


def build_sections_payload(*, model: str, base_url: str, api_path: str | None) -> Dict[str, Any]:
    fields = []
    # Minimal agent section (kept empty to avoid overriding other keys)
    # Model settings
    fields.append({"id": "chat_model_provider", "value": "groq"})
    fields.append({"id": "chat_model_name", "value": model})
    if base_url:
        fields.append({"id": "chat_model_api_base", "value": base_url})
    if api_path:
        fields.append({"id": "chat_model_api_path", "value": api_path})
    return {"sections": [{"id": "model", "fields": fields}]}


async def seed(gateway_base: str, model: str, base_url: str, api_path: str | None, api_key: str, internal_token: str | None) -> int:
    gw = gateway_base.rstrip("/")
    payload = build_sections_payload(model=model, base_url=base_url, api_path=api_path)
    async with httpx.AsyncClient(timeout=10.0) as client:
        # 1) Persist provider credential via credentials endpoint
        try:
            rc = await client.post(f"{gw}/v1/llm/credentials", json={"provider": "groq", "secret": api_key})
        except Exception as exc:
            print(f"error: failed to reach gateway at {gw}: {exc}")
            return 2
        if rc.is_error:
            print(f"error: credential save failed: HTTP {rc.status_code}: {(rc.text or '')[:400]}")
            return 3

        # 2) Persist model profile and related settings via UI sections endpoint (no secrets)
        try:
            r = await client.post(f"{gw}/v1/ui/settings/sections", json=payload)
        except Exception as exc:
            print(f"error: failed to reach gateway at {gw}: {exc}")
            return 2
        if r.is_error:
            print(f"error: settings save failed: HTTP {r.status_code}: {(r.text or '')[:400]}")
            return 3
        print("credentials saved; settings saved via /v1/ui/settings/sections")

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
    parser = argparse.ArgumentParser(description="Seed Groq credentials and model profile")
    parser.add_argument("--api-key", required=True, help="Groq API key to store in Gateway")
    parser.add_argument("--gateway-base", default="http://127.0.0.1:21016", help="Gateway base URL")
    parser.add_argument("--internal-token", default=None, help="Internal token for /v1/llm/test (optional)")
    parser.add_argument("--model", default="llama-3.1-8b-instant", help="Dialogue model name")
    parser.add_argument("--base", default="https://api.groq.com/openai", help="Provider base URL (normalized by Gateway)")
    parser.add_argument("--api-path", default=None, help="Override chat API path (defaults to profile/api)")
    args = parser.parse_args()
    try:
        return asyncio.run(seed(args.gateway_base, args.model, args.base, args.api_path, args.api_key, args.internal_token))
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
