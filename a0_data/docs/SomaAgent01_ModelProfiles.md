⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data.

# SomaAgent 01 Model Profiles

## Overview
Model profiles let SomaAgent 01 choose different OSS models per role (dialogue, planning, code, summary, audio) and per deployment mode (LOCAL, DEVELOPMENT, TRAINING, PRODUCTION). Profiles are managed via the Settings Service and persisted in Postgres (`model_profiles` table).

## API Summary (`services/settings_service/main.py`)
- `GET /v1/model-profiles?deployment_mode=PRODUCTION`
- `POST /v1/model-profiles`
- `PUT /v1/model-profiles/{role}/{deployment_mode}`
- `DELETE /v1/model-profiles/{role}/{deployment_mode}`

Payload:
```json
{
  "role": "dialogue",
  "deployment_mode": "PRODUCTION",
  "model": "meta-llama/Meta-Llama-3.1-70B-Instruct",
  "base_url": "https://slm.somaagent01.dev/v1",
  "temperature": 0.1,
  "extra": {"top_p": 0.9}
}
```

## Conversation Worker Integration
The conversation worker (`services/conversation_worker/main.py`) fetches the active profile for the `dialogue` role based on `SOMA_AGENT_MODE`. If none is found it falls back to environment defaults (`SLM_MODEL`, `SLM_BASE_URL`). Profiles can include additional kwargs (e.g., `top_p`) which are passed directly to the Soma SLM API (OpenAI-compatible).

## Storage Schema
```
CREATE TABLE model_profiles (
    id SERIAL PRIMARY KEY,
    role TEXT NOT NULL,
    deployment_mode TEXT NOT NULL,
    model TEXT NOT NULL,
    base_url TEXT NOT NULL,
    temperature DOUBLE PRECISION DEFAULT 0.2,
    extra JSONB NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE(role, deployment_mode)
);
```

## Usage Workflow
1. Operators call the Settings Service to register or update profiles per environment.
2. Conversation worker reloads profiles on demand (each request) to pick the correct model.
3. Scoring jobs (future sprint) will update profiles automatically by calling the same API.

## Future Work
- Extend profiles to cover code, planning, audio roles.
- Add UI panel for operators to visualize cost/latency (Sprint 2B deliverable).
- Integrate scoring job outputs to automatically recommend profile upgrades.
