# Messaging Stack Baseline (Wave 0)

This document captures the current local runtime expectations for the messaging stack during **Wave 0 / Sprint 0**. It is the source of truth for verifying that the docker-compose stack starts, the key dependencies are reachable, and the conversational pipeline is ready for subsequent refactors.

## Compose Services (developer profile)

| Service | Purpose | Host Port |
| --- | --- | --- |
| `kafka` | Single-node KRaft broker (`confluentinc/cp-kafka:7.4.0`) | `${KAFKA_PORT:-20000}` |
| `kafka-init` | Bootstraps baseline topics via `infra/kafka/init-topics.sh` | — |
| `postgres` | Primary metadata store (`postgres:16-alpine`) | `${POSTGRES_PORT:-20002}` |
| `redis` | Session cache and budget tracker (`redis:7-alpine`) | `${REDIS_PORT:-20001}` |
| `opa` | Policy engine (`openpolicyagent/opa:0.64.0`) | `${OPA_PORT:-20009}` |
| `gateway` | FastAPI ingress (`services/gateway/main.py`) | `${GATEWAY_PORT:-20016}` |
| `conversation-worker` | Kafka consumer producing SLM/tool outputs | — |
| `tool-executor` | Runs registered tools and emits `tool.results` | — |
<!-- memory-service removed; SomaBrain HTTP is used by services directly -->

> **Profiles:** Launch with `docker compose --profile core --profile dev up -d` to include all messaging services without mocks.

## Environment Contract

| Variable | Default | Notes |
| --- | --- | --- |
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka:9092` (in-container) / `localhost:20000` (host) | Shared across gateway, worker, tool executor. |
| `CONVERSATION_INBOUND` | `conversation.inbound` | Gateway publishes inbound chat here. |
| `CONVERSATION_OUTBOUND` | `conversation.outbound` | Worker streams responses on this topic. |
| `TOOL_REQUESTS_TOPIC` | `tool.requests` | Worker ➜ tool executor traffic. |
| `TOOL_RESULTS_TOPIC` | `tool.results` | Tool executor ➜ worker/gateway responses. |
| `REDIS_URL` | `redis://redis:6379/0` | Cache + budget ledger. |
| `POSTGRES_DSN` | `postgresql://soma:soma@postgres:5432/somaagent01` | Session/event persistence. |
| `GATEWAY_PORT` | `20016` | Exposes FastAPI ingress to the host. |
| `WEB_UI_BASE_URL` | `http://127.0.0.1:${GATEWAY_PORT}` | UI is served by Gateway (single origin). |

## Smoke Checks

Run the automated smoke script after launching the stack:

```bash
python scripts/check_stack.py
```

The script validates:

1. **Gateway health** — `GET /health` returns `200 OK`.
2. **Kafka connectivity** — required topics exist and the `conversation-worker` consumer group is registered.
3. **Redis availability** — `PING` succeeds using the configured URL.
4. **Postgres connectivity** — connection to the configured DSN succeeds and `sessions.events` table exists.

A non-zero exit code indicates a blocking issue. Review the troubleshooting section below and re-run once resolved.

## Troubleshooting

- **Gateway health fails**: Inspect `docker compose logs gateway` and ensure no port conflicts with `${GATEWAY_PORT}`.
- **Kafka topics missing**: Confirm `kafka-init` completed successfully and re-run via `docker compose run --rm kafka-init`.
- **Consumer group not registered**: Verify the `conversation-worker` logs for startup errors; the service must commit offsets at least once to appear.
- **Redis unavailable**: Check for port conflicts or persistent volume corruption at `redis_data`; clearing the volume may help.
- **Postgres failures**: Ensure the `postgres` container is healthy and migrations in `infra/postgres/init` executed.

## Maintenance Checklist

- Update this document whenever service ports or topic names change.
- Keep smoke checks aligned with `scripts/check_stack.py` behavior.
- Reference sprint IDs (e.g., `W0-S0`) in Git history when updating baseline requirements.
