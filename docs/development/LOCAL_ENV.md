# SomaAgent 01 – Local Developer Environment

## Prerequisites
- Docker Desktop or Docker Engine (v20+)
- Python 3.11 (via pyenv or system install)
- Node 18+ (for web UI builds)
- `make`, `jq`, `yq` for helper scripts (optional but recommended)

## Repository Setup
```bash
pyenv local 3.11.6
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copy environment defaults:
```bash
cp example.env .env
```
Update `.env` with local API keys or service endpoints as needed.

## Docker Compose Stack
The compose file in `infra/docker-compose.somaagent01.yaml` boots the OSS baseline (Kafka, Redis, Postgres, ClickHouse, Qdrant, Whisper CPU). The conversational SLM is accessed via the managed Soma SLM API configured through `SLM_BASE_URL`, so no local LLM container is pulled.

```bash
cd infra
docker compose -f docker-compose.somaagent01.yaml up -d
```

### Smoke Test
With the stack running, exercise the event pipeline:
```bash
# Start the gateway (new shell)
python -m services.gateway.main

# Start the conversation worker and tool executor in separate shells
python -m services.conversation_worker.main
python -m services.tool_executor.main

# Send a sample message
python scripts/send_message.py "Ping"

# Validate JSON schemas
python scripts/schema_smoke_test.py

# Replay events (optional)
python scripts/replay_session.py $SESSION_ID --follow
```

### Streaming Interfaces
- **WebSocket**: `ws://localhost:8001/v1/session/<SESSION_ID>/stream`
- **SSE**: `http://localhost:8001/v1/session/<SESSION_ID>/events`

Use tools like `wscat` or `curl`:
```bash
wscat -c ws://localhost:8001/v1/session/$SESSION_ID/stream
curl -N http://localhost:8001/v1/session/$SESSION_ID/events
```

### Authentication & Policy (optional)
- Enable JWT enforcement: set `GATEWAY_REQUIRE_AUTH=true` and provide either `GATEWAY_JWT_SECRET` (HS*) or `GATEWAY_JWT_PUBLIC_KEY`/`GATEWAY_JWKS_URL` (RS*/ES*).
- Configure audience/issuer with `GATEWAY_JWT_AUDIENCE` and `GATEWAY_JWT_ISSUER`.
- Route authorization through OPA by setting `OPA_URL` (defaults decision path `/v1/data/somastack/allow`).
- When auth is enabled, incoming requests must include an `Authorization: Bearer <token>` header.

Verify:
- Gateway logs show an inbound event and WebSocket acknowledgement.
- Conversation worker logs emit an assistant response.
- Tool executor remains idle (no tool requests yet).
- Inspect `logs/` or Postgres `session_events` to confirm persistence.

## Stopping the Stack
```bash
cd infra
docker compose -f docker-compose.somaagent01.yaml down
```

## Troubleshooting
| Symptom | Check |
|---------|-------|
| Kafka connection refused | Ensure compose stack is running and `KAFKA_BOOTSTRAP_SERVERS` points to `localhost:9092`. |
| Redis auth errors | Match `REDIS_URL` in `.env` with the compose-provisioned credentials. |
| Tool executor fails to validate result | Confirm `schemas/tool_result.json` exists and package dependencies (`jsonschema`) installed. |

Keep this guide updated as additional services (SomaKamachiq orchestrator, UI) come online.
