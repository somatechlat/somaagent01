# Gateway LLM Routing & Settings

This document explains how the Gateway resolves model settings, normalizes provider base URLs, selects credentials, and performs LLM invocations for both streaming and non‑streaming paths.

## Overview

- Single entry points for LLM calls:
  - POST `/v1/llm/invoke` (non‑stream)
  - POST `/v1/llm/invoke/stream` (SSE stream)
- The dialogue model profile is the source of truth and is saved via the UI Settings API.
- Provider credentials are stored centrally in the Gateway and are never read from service env vars in normal operation.

## Model Profile and Credentials

Endpoints used by the Web UI and operators (centralized settings-only flow):

- GET `/v1/ui/settings` → returns the effective UI agent config, model profile, and credential presence map.
- PUT `/v1/ui/settings` → accepts `model_profile` and `agent` payloads (legacy direct `llm_credentials` removed; use sections).
- GET `/v1/ui/settings/sections` → full modal sections schema for the SPA.
- POST `/v1/ui/settings/sections` → single writer: persists agent settings, model profile, and any `api_key_*` credential fields (encrypted). This replaces legacy `/v1/llm/credentials`.
- GET `/v1/ui/settings/credentials` → status map of stored provider secrets (`present` + `updated_at`; never returns actual secrets).
- POST `/v1/llm/test` → resolves the active profile for the role (e.g., `dialogue`), detects provider, checks that credentials exist, and performs a reachability probe.

Notes:
- Workers no longer fetch credentials via internal endpoints; they only invoke `/v1/llm/invoke` and let the Gateway inject secrets.
- Legacy endpoints `/v1/llm/credentials` and `/v1/llm/credentials/{provider}` have been removed; documentation and scripts should use the sections save path exclusively.

## Base URL Normalization

The Gateway normalizes OpenAI‑compatible base URLs before use to avoid common misconfigurations.

Normalization rules (simplified):
- Trim whitespace and trailing slashes.
- Strip a trailing `/v1` and/or `/chat/completions` from the path.
- Map provider‑specific pitfalls:
  - OpenRouter: inputs ending in `/openai` are rewritten to `/api` so that appending `/v1/chat/completions` works. Example:
    - Input: `https://openrouter.ai/openai` → Normalized: `https://openrouter.ai/api`
- In non‑DEV deployments, if a scheme is present and not `https`, enforce `https`.

Provider detection is based on the base URL host:
- `*.groq.com` → `groq`
- `openrouter.ai` → `openrouter`
- `api.openai.com` → `openai`
- otherwise → `other`

Default base URLs (when needed):
- groq → `https://api.groq.com/openai/v1`
- openai → `https://api.openai.com/v1`
- openrouter → `https://openrouter.ai/api/v1`

## Base URL Overrides

Callers cannot override the profile’s base URL. The Gateway always uses the value saved in the profile and ignores any `overrides.base_url` provided by clients. This ensures a single source of truth for provider routing.

## End‑to‑End Flow

1) UI saves Settings:
   - PUT `/v1/ui/settings` with `model_profile` and (optionally) `llm_credentials`.
2) Worker consumes canonical runtime settings from the Gateway (internal token) and routes all LLM calls via the Gateway’s `/v1/llm/invoke(/stream)`.
3) Gateway resolves the profile, normalizes the base URL, detects the provider, fetches the secret, and calls the provider’s OpenAI‑compatible `/v1/chat/completions` endpoint.
4) Results are audited under action `llm.invoke` with status, latency, usage, and provider metadata.

## Troubleshooting

### Symptoms and Fixes

- 401 Unauthorized from provider
  - Cause: Invalid/expired API key or lack of access to the selected model.
  - Fix: Re‑enter the provider key via the Settings modal and Save (sections flow persists + encrypts the key).
  - Verify: POST `/v1/llm/test` should show `credentials_present: true` and the provider host.

- 405 Method Not Allowed on OpenRouter
  - Cause: Using `/openrouter.ai/openai` as base, which is not compatible when composing the full path.
  - Fix: Normalization maps `/openai` → `/api`. Save Settings again so the profile base URL normalizes to `https://openrouter.ai/api`.

- Chat path returns standardized error
  - Check audit: `GET /v1/admin/audit/export?action=llm.invoke | tail`
  - If you see `http_status=401` or `405`, follow the specific fixes above.

### Quick sanity checks

```bash
# 1. Inspect settings
curl -s http://localhost:21016/v1/ui/settings | jq .

# 2. Credentials presence map
curl -s http://localhost:21016/v1/ui/settings/credentials | jq .

# 3. Provider test
curl -s -X POST http://localhost:21016/v1/llm/test \
  -H 'Content-Type: application/json' \
  -d '{"role":"dialogue"}' | jq .

# 4. Tail recent LLM audits
curl -s "http://localhost:21016/v1/admin/audit/export?action=llm.invoke" | tail -n 10
```

## Examples

Set Groq as the dialogue model (UI or API):

```bash
curl -s -X PUT http://localhost:21016/v1/ui/settings \
  -H 'Content-Type: application/json' \
  -d '{
        "model_profile": {
          "model": "llama-3.1-8b-instant",
          "base_url": "https://api.groq.com/openai/v1",
          "temperature": 0.2
        }
      }'
```

Store Groq API key via Settings sections (centralized):

```bash
curl -s -X POST http://localhost:21016/v1/ui/settings/sections \
  -H 'Content-Type: application/json' \
  -d '{
        "sections": [
          {"id":"llm","fields":[
            {"id":"chat_model_provider","value":"groq"},
            {"id":"chat_model_name","value":"llama-3.1-8b-instant"},
            {"id":"chat_model_api_base","value":"https://api.groq.com/openai/v1"},
            {"id":"api_key_groq","value":"<GROQ_API_KEY>"}
          ]}
        ]
      }'
```

Validate and invoke:

```bash
curl -s -X POST http://localhost:21016/v1/llm/test \
  -H 'Content-Type: application/json' \
  -d '{"role":"dialogue"}' | jq .

curl -s -X POST http://localhost:21016/v1/llm/invoke \
  -H 'Content-Type: application/json' \
  -H 'X-Internal-Token: dev-internal-token' \
  -d '{"role":"dialogue","messages":[{"role":"user","content":"Say hi in one word."}]}' | jq .
```
