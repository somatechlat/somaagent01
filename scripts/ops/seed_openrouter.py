"""DEPRECATED: Seeding scripts are disabled.

Usage (CLI):

    python scripts/ops/seed_openrouter.py --api-key $OPENROUTER_API_KEY \
        [--gateway-base http://127.0.0.1:21016] \
        [--internal-token $GATEWAY_INTERNAL_TOKEN] \
        [--model openai/gpt-oss-120b] \
        [--base https://openrouter.ai/api] \
        [--api-path /v1/chat/completions]

This script stores the provider credential via /v1/llm/credentials and updates
the dialogue model via /v1/ui/settings/sections (without sending secrets).
It then calls /v1/llm/test (if --internal-token is provided) to verify reachability/auth.
"""

raise SystemExit(
    "Seeding via scripts is disabled. Use the Settings UI → External → API Keys."
)


def build_sections_payload(*, model: str, base_url: str, api_path: str | None) -> Dict[str, Any]:
    fields = []
    # Model settings: explicitly select OpenRouter provider
    fields.append({"id": "chat_model_provider", "value": "openrouter"})
    fields.append({"id": "chat_model_name", "value": model})
    # Leave base blank to let Gateway normalize provider default when omitted,
    # but allow override when provided.
    if base_url:
        fields.append({"id": "chat_model_api_base", "value": base_url})
    if api_path:
        fields.append({"id": "chat_model_api_path", "value": api_path})
    return {"sections": [{"id": "model", "fields": fields}]}


async def seed(
    gateway_base: str,
    model: str,
    base_url: str,
    api_path: str | None,
    api_key: str,
    internal_token: str | None,
) -> int:
    gw = gateway_base.rstrip("/")
    payload = build_sections_payload(model=model, base_url=base_url, api_path=api_path)
    async with httpx.AsyncClient(timeout=10.0) as client:
        # 1) Persist provider credential via credentials endpoint
        try:
            rc = await client.post(f"{gw}/v1/llm/credentials", json={"provider": "openrouter", "secret": api_key})
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
                    params={"validate_auth": "true"},
                )
                if r2.is_error:
                    print(f"warn: /v1/llm/test failed: HTTP {r2.status_code}: {(r2.text or '')[:400]}")
                else:
                    data = r2.json()
                    print("llm.test:", data)
                    ok = bool(data.get("ok")) and bool(data.get("credentials_present")) and (data.get("status_code") in (200, 401, 403))
                    if not ok:
                        print("warn: credentials may be missing or upstream unreachable; check gateway logs")
            except Exception as exc:
                print(f"warn: failed running /v1/llm/test: {exc}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed OpenRouter credentials and model profile")
    parser.add_argument("--api-key", required=True, help="OpenRouter API key to store in Gateway")
    parser.add_argument("--gateway-base", default="http://127.0.0.1:21016", help="Gateway base URL")
    parser.add_argument("--internal-token", default=None, help="Internal token for /v1/llm/test (optional)")
    parser.add_argument("--model", default="openai/gpt-oss-120b", help="Dialogue model name")
    parser.add_argument("--base", default="https://openrouter.ai/api", help="Provider base URL (normalized by Gateway)")
    parser.add_argument("--api-path", default=None, help="Override chat API path (defaults to profile/api)")
    args = parser.parse_args()
    try:
        return asyncio.run(
            seed(args.gateway_base, args.model, args.base, args.api_path, args.api_key, args.internal_token)
        )
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
