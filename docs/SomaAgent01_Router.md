⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data.

# SomaAgent 01 Dynamic Router Service

`services/router/main.py` provides a pure OSS router for selecting the best model among candidates based on telemetry scores.

## Endpoints
- `POST /v1/route`
  ```json
  {
    "role": "dialogue",
    "deployment_mode": "PRODUCTION",
    "candidates": ["meta-llama/Meta-Llama-3.1-70B-Instruct", "mistral/Mistral-7B-Instruct"]
  }
  ```
  Returns `{ "model": "...", "score": 0.87 }`.

## Implementation
- Queries `model_scores` table populated by the scoring job. If no telemetry exists, falls back to the first candidate.
- Conversation worker consults the router when `ROUTER_URL` env var is set.
- All communication uses OSS `httpx` client.

## Deployment
- Run with `uvicorn services.router.main:app --port 8013`.
- Register in kubernetes/compose stacks to provide multi-provider routing capabilities.

This service is a stepping stone toward the full Litellm/Groq/HF routing layer referenced in the roadmap.
