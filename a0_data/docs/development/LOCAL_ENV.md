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
The compose file in `infra/docker-compose.somaagent01.yaml` boots the OSS baseline (Kafka, Redis, Postgres, ClickHouse, Qdrant, Whisper CPU) plus the delegation gateway/worker pair and the Agent UI (Flask + Supervisor). The conversational SLM is accessed via the managed Soma SLM API configured through `SLM_BASE_URL`, and long-term memory traffic is routed to the managed SomaBrain endpoint at `http://localhost:9696`.

### End-to-end startup
1. **Verify the SomaBrain endpoint** – the agent only talks to the live brain at `http://localhost:9696`. Confirm it responds before starting Compose:
	```bash
	curl -sf http://localhost:9696/healthz
	```
	A successful health check ensures the delegation services can reach the real memory provider.
  	> **Container note:** When those services run inside Docker they automatically remap the brain URL to `http://host.docker.internal:9696` so containers can reach the host network. Override the alias with `SOMA_CONTAINER_HOST_ALIAS`, disable the heuristic via `SOMA_DISABLE_CONTAINER_CHECK=1`, or force it on (useful for local tests) with `SOMA_FORCE_CONTAINER=1`.
2. **Free the Agent UI port** – port **7002** is reserved permanently for the local Agent UI. Stop any process bound to that port (`lsof -i :7002`).
3. **Launch the stack** – the helper script preflights every dependency and enforces the static UI port:
	```bash
	./scripts/run_dev_cluster.sh
	```
	The script prints the effective host bindings for Kafka, Postgres, delegation gateway, etc. If port 7002 is unavailable the script aborts so you can remediate before retrying.
4. **Verify services** – once Compose reports all containers as started, validate the allocations:
	```bash
	cd infra
	docker compose -f docker-compose.somaagent01.yaml ps
	curl -I http://127.0.0.1:7002/
	```
	A `200 OK` confirms the Agent UI is reachable on the expected port.

### Manual Compose launch
If you invoke Compose yourself, export the same static binding first and then start the stack:

```bash
export WEB_UI_PORT=7002
cd infra
docker compose -f docker-compose.somaagent01.yaml up -d
```

Retrieve dynamic port assignments as needed with `docker compose port SERVICE CONTAINER_PORT` (for example `docker compose -f docker-compose.somaagent01.yaml port delegation-gateway 8015`).

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
Define a helper to retrieve the delegated gateway port:

```bash
GATEWAY_PORT=$(docker compose -f infra/docker-compose.somaagent01.yaml port delegation-gateway 8015 | awk -F: '{print $2}')
```

- **WebSocket**: `ws://localhost:${GATEWAY_PORT}/v1/session/<SESSION_ID>/stream`
- **SSE**: `http://localhost:${GATEWAY_PORT}/v1/session/<SESSION_ID>/events`

The Agent UI is always available at `http://localhost:7002/`.

Use tools like `wscat` or `curl`:
```bash
wscat -c ws://localhost:${GATEWAY_PORT}/v1/session/$SESSION_ID/stream
curl -N http://localhost:${GATEWAY_PORT}/v1/session/$SESSION_ID/events
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

### SomaClient Event‑Loop Compatibility

The recent fix to `integrations/soma_client.py` makes the client **per‑event‑loop** – each `asyncio` loop gets its own HTTP client and lock stored in a `WeakKeyDictionary`. This prevents the classic `RuntimeError: Event loop is closed` / `Event bound to a different loop` errors when the same client instance is used across multiple loops (e.g., in tests, the gateway and workers, or when re‑using the client in a REPL).

**Local validation**
After rebuilding the Docker images (see the runbook entry) you can run a quick inline probe to ensure the patched client works:

```bash
source .venv/bin/activate && python - <<'PY'
from integrations.soma_client import SomaClient
from asyncio import new_event_loop

client = SomaClient()
for _ in range(2):
    loop = new_event_loop()
    # The client lazily creates a lock per‑loop; this call exercises that path.
    loop.run_until_complete(client._get_lock())
    loop.close()
print('ok')
PY
```

You should see `ok` printed with no traceback. If you still encounter loop‑binding errors, ensure you have rebuilt the shared image (`docker compose -f infra/docker-compose.somaagent01.yaml build delegation-gateway delegation-worker agent-ui`) and that the running containers are using the latest code.

## Stopping the Stack
```bash
cd infra
docker compose -f docker-compose.somaagent01.yaml down
```

## Troubleshooting
| Symptom | Check |
|---------|-------|
| Kafka connection refused | Ensure the compose stack is running and `KAFKA_BOOTSTRAP_SERVERS` matches the host binding from `docker compose port kafka 9092`. |
| Redis auth errors | Match `REDIS_URL` in `.env` with the compose-provisioned credentials. |
| Tool executor fails to validate result | Confirm `schemas/tool_result.json` exists and package dependencies (`jsonschema`) installed. |

Keep this guide updated as additional services (SomaKamachiq orchestrator, UI) come online.
