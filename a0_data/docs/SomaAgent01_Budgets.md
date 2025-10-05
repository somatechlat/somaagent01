⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data.

# SomaAgent 01 Token Budgets & Telemetry

## Budget Manager
- Implemented in `services/common/budget_manager.py` using Redis.
- Token totals tracked per tenant/persona/day (`budget:tokens:<tenant>:<persona>:<YYYYMMDD>`).
- Limits configured via environment variables:
  - `BUDGET_LIMIT_TOKENS` (global default)
  - `BUDGET_LIMIT_<TENANT>` or `BUDGET_LIMIT_<TENANT>_<PERSONA>` for overrides.
- Conversation worker consumes tokens after each SLM call. If the limit is exceeded the worker returns “Token budget exceeded…”.

## Telemetry Events
- `services/common/telemetry.py` publishes JSON events to Kafka topics:
  - `slm.metrics`: `{session_id, model, latency_seconds, input_tokens, output_tokens, total_tokens}`
  - `budget.events`: `{tenant, persona_id, delta_tokens, total_tokens, limit_tokens, status}`
- These topics feed downstream analytics (ClickHouse) and alerting in later sprints.

## Conversation Worker Changes
- Measures SLM latency and token usage from the managed Soma SLM API response (`usage.prompt_tokens`, `usage.completion_tokens`).
- Emits telemetry and budget events via the shared publisher.
- Applies model profiles per deployment mode (LOCAL/DEV/TRAINING/PRODUCTION).

## Roadmap
- Future work will build dashboards, automatic scaling policies, and anomaly detection on top of these events (Sprint 3B).
