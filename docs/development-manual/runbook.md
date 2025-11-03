# Operational Runbook: Local Docker Stack

This runbook ensures you can consistently bring up a fully working local cluster with official open-source images for infrastructure and the gateway/tooling built from source.

## Prerequisites

- Docker and Docker Compose V2
- Python 3.11 (for optional local tests)
- macOS or Linux host

## Images used

- Kafka: `confluentinc/cp-kafka:7.4.0` (official)
- Redis: `redis:7-alpine` (official)
- Postgres: `postgres:16-alpine` (official)
- OPA: `openpolicyagent/opa:0.64.0` (official)
- Gateway/Workers: built from this repo using `python:3.11-slim` base (official)

## One-time network setup

- Ensure the external Docker networks exist (Compose expects them):
  - `somaagent01`
  - `somaagent01_dev`

If missing, create:

```
docker network create somaagent01 || true
docker network create somaagent01_dev || true
```

## Build and start

- Build the application image (includes all services):

```
docker compose build
```

- Start core infra and dev services (gateway, workers, outbox-sync):

```
docker compose --profile core --profile dev up -d
```

- Initialize Kafka topics (runs automatically when `kafka-init` is present):

```
docker compose run --rm kafka-init
```

## Verify health

- Gateway health:

```
curl -s http://localhost:${GATEWAY_PORT:-21016}/v1/health | jq .
```

- Web UI:
  - Open http://localhost:21016/ui/
  - You should see the chat UI. Open DevTools → Console; it should be clean.

## Key settings (dev defaults)

- Gateway writes-through to SomaBrain: `GATEWAY_WRITE_THROUGH=true`
- Uploads enabled: `GATEWAY_DISABLE_FILE_SAVING=false` and UI Uploads settings default enabled
- Internal token for S2S: `GATEWAY_INTERNAL_TOKEN=dev-internal-token`
- SomaBrain URL: `SOMA_BASE_URL=http://host.docker.internal:9696`

## Troubleshooting quick checks

- Outbox backlog: messages stuck? Check `outbox-sync` logs and DB `message_outbox` table.
- SSE not streaming:
  - `GET /v1/session/{id}/events` must be reachable (network/proxy ok)
  - `conversation.outbound` events must be produced (tool/worker healthy)
- Memory dashboard checks:
  - Read APIs under `/v1/memories*` should respond (e.g., `GET /v1/memories`, `GET /v1/memories/subdirs`).
  - Replica store table `memory_replica` should exist and have rows if WAL is running.

## Graceful restart

```
docker compose restart gateway outbox-sync tool-executor conversation-worker
```

## Clean up

```
docker compose down -v
```

## Notes

- All infra images are official upstream. The application image is built from source with `python:3.11-slim` base.
- For production, pin image digests and configure mTLS, OIDC, and appropriate browser auth (same-origin cookies or header tokens). No custom CSRF endpoints are used.
