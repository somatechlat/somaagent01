# Running the stack in a prod-like mode locally

This guide explains how to run the Agent Zero stack on your development machine in a "prod-like" configuration while keeping developer conveniences (local mounts, persistent logs, optional auth override).

Prerequisites
- Docker and Docker Compose v2 installed
- A `.env` file in the repository root with LLM provider keys (e.g., GROQ, OPENAI). The stack will read env vars from the environment when starting.
- Optional: `jq` installed for JSON edits (used by scripts)

Start the stack
1. Make sure your working dir is the project root (where `docker-compose.yaml` lives):

```bash
cd agent-zero
```

2. Start the stack in prod-like mode (this runs detached and persists logs to `./logs`):

```bash
./scripts/run_prod_like_dev.sh
```

Notes and tips
- By default the override sets `GATEWAY_REQUIRE_AUTH=true` to mirror production. For local debugging without JWTs, export `GATEWAY_REQUIRE_AUTH=false` before running the script, or set it in your `.env`.
- The script creates a default agent profile at `agents/agent0/profile.json` if not present and will set `tmp/settings.json` to reference `agent0`.
- Logs are collected per-service under `./logs/<service>.log` using `docker compose logs -f`. You can `tail -F` these files or run `docker compose logs -f gateway conversation-worker` for interactive logs.

Troubleshooting
- If gateway returns 500, tail `logs/gateway.log` and `logs/conversation-worker.log` while performing a POST to `/v1/session/message` to correlate publish -> consume.
- Make sure Kafka is reachable at the address set by `KAFKA_BOOTSTRAP_SERVERS` (default `kafka:9092`) and that your host isn't blocking container networking.
- Ensure LLM provider keys are present in the environment inside the worker/gateway containers. The script uses the `.env` file if you have docker configured to read it; you can also `export` env vars before starting.

Playwright and UI
- After verifying the publish->consume->LLM flow with logs, run Playwright tests (not included) or use the UI at `http://localhost:${AGENT_UI_PORT:-20015}`.
