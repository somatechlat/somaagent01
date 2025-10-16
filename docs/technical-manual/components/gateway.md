---
title: Gateway Component
slug: technical-gateway
version: 1.0.0
last-reviewed: 2025-10-15
audience: platform-engineers, backend developers
owner: platform-architecture
reviewers:
  - infra
  - security
prerequisites:
  - Familiarity with FastAPI conventions
  - Access to SomaAgent01 repository
verification:
  - Gateway health endpoint returns 200
  - Integration tests in `tests/integration/test_gateway_public_api.py` pass
---

# Gateway Component

## Purpose

- Serves as the primary ingress for HTTP/WebSocket traffic (humans, agents, automations).
- Enforces authentication, authorization, and policy controls before delegating to LLMs or tools.
- Orchestrates conversation flow: context assembly, tool invocation, memory persistence.

```mermaid
graph LR
    Client -->|REST/WS| Gateway
    Gateway -->|authorize| OpenFGA
    Gateway -->|evaluate| OPA
    Gateway -->|fetch| SomaBrain
    Gateway -->|call| LLMProvider
    Gateway -->|publish| Kafka
    Gateway -->|persist| Postgres
    Gateway -->|cache| Redis
```

## Module Structure

| Module | Key Responsibilities |
| --- | --- |
| `services/gateway/main.py` | FastAPI application factory, router registration |
| `services/gateway/routes/chat.py` | Chat send/stream endpoints, WebSocket handlers |
| `services/gateway/routes/settings.py` | `/settings_get`, `/settings_set`, realtime session negotiation |
| `services/gateway/auth/openfga.py` | Relationship tuples, access checks |
| `services/gateway/policies/opa_client.py` | Rego policy evaluation |
| `services/gateway/memory/service.py` | SomaBrain reads/writes |
| `services/gateway/tasks/publisher.py` | Kafka publishing helpers |

## Request Lifecycle

1. **Ingress:** Request hits FastAPI dependency stack (auth, tenant resolution).
2. **Policy:** OpenFGA checks relationship tuples; OPA enforces budgets/quotas.
3. **Context:** Gateway fetches session transcript, memories, tenant defaults.
4. **LLM Call:** Provider info comes from `python/helpers/settings.py` and LiteLLM wrapper.
5. **Tooling:** Responses containing tool directives emit Kafka messages or call tool executor.
6. **Persistence:** Updated session state stored in Postgres; new memories saved to SomaBrain.
7. **Streaming:** WebSocket clients receive partial responses and status events.

## Configuration

- `GATEWAY_REQUIRE_AUTH`, `POSTGRES_DSN`, `KAFKA_BOOTSTRAP_SERVERS`, `OPENFGA_*`.
- Settings API merges defaults from `python/helpers/settings.py` with user overrides.
- `dev` profile enables auto-reload and verbose logging.

## Observability

- Metrics: request latency, response codes, circuit breaker counters at `/metrics`.
- Logs: structured JSON per request.
- Traces: optional OTEL instrumentation via environment variables.

## Failure Modes & Mitigations

| Failure | Symptom | Mitigation |
| --- | --- | --- |
| Redis unavailable | Rate limit errors, cache misses | Gateway falls back to Postgres fetches; retries with backoff |
| LLM provider errors | 5xx streaming to UI | Circuit breaker triggers; Gateway surfaces actionable message |
| Kafka publish failure | Tool executions stall | Dead-letter queue records message; operator restarts broker |
| OpenFGA connectivity | 403 responses for all requests | Cached decisions used briefly; escalate to SRE |

## Extensibility

- Add routers under `services/gateway/routes/` and include via FastAPI.
- Define new tool schemas in `python/tools/schema/` and map to executor tasks.
- Update `conf/tenants.yaml` for tenant-specific budgets or prompts.

## Verification Checklist

- [ ] `curl http://localhost:8010/health` returns 200.
- [ ] Integration suite passes.
- [ ] Prometheus shows Gateway targets UP.
