---
title: Environment Setup
slug: dev-environment
version: 1.0.0
last-reviewed: 2025-10-15
audience: contributors
owner: developer-experience
reviewers:
  - platform-engineering
prerequisites:
  - macOS/Linux (Windows via WSL2)
  - Docker Desktop 4.36+
  - Python 3.12+
verification:
  - `make dev-up` succeeds
  - `pytest` passes locally
---

# Environment Setup

Follow these steps to prepare a fully functional SomaAgent01 development environment.

## 1. Clone the Repository

```bash
git clone https://github.com/agent0ai/agent-zero.git
cd agent-zero
```

## 2. Python Runtime

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Verify:

```bash
python -V  # Should return 3.12.x
pip check  # No broken dependencies
```

## 3. Frontend Dependencies

```bash
cd webui
npm install
cd ..
```

Verify: `npm run lint` passes.

## 4. Environment Variables

1. Copy `.env.example` to `.env`.
2. Provide required keys:
   - `SLM_API_KEY` (or alternate model provider).
   - `POSTGRES_DSN`, `REDIS_URL` if using external services.

## 5. Start the Stack

```bash
make dev-up
```

- Gateway available at `http://localhost:${GATEWAY_PORT:-20016}`.
- UI (when started) available at `http://localhost:${AGENT_UI_PORT:-20015}`.
- Logs tail via `make dev-logs`.

**Verification:**
- `docker compose -p somaagent01 ps` shows services healthy.
- `curl http://localhost:${GATEWAY_PORT:-20016}/health` returns `200`.

## 6. Testing

```bash
pytest
pytest tests/playwright/test_realtime_speech.py --headed
```

## 7. Common Tasks

| Task | Command |
| ---- | ------- |
| Stop stack | `make dev-down` |
| Rebuild stack | `make dev-rebuild` |
| Tail a specific service | `make dev-logs-svc SERVICES=gateway` |
| Start selected services | `make dev-up-services SERVICES="gateway tool-executor"` |
| Clean volumes | `make clean` |
| Lint Python | `ruff check .` |
| Format Python | `black .` |

## 8. Local Docker Compose Reference

- Single compose file `docker-compose.yaml` drives local development.
- Profiles:
  - `core`: Kafka (`${KAFKA_PORT:-20000}`), Redis (`${REDIS_PORT:-20001}`), Postgres (`${POSTGRES_PORT:-20002}`), OPA (`${OPA_PORT:-20009}`).
  - `dev`: Gateway (`${GATEWAY_PORT:-20016}`), Conversation Worker, Tool Executor, Memory Service (`${MEMORY_SERVICE_PORT:-20017}`), Agent UI (`${AGENT_UI_PORT:-20015}`).
- Bring-up examples:
  - `docker compose -p somaagent01 --profile core --profile dev -f docker-compose.yaml up -d`
  - `docker compose -p somaagent01 --profile core -f docker-compose.yaml up -d kafka redis postgres`
- Recommended Docker Desktop allocation: ≥8 CPUs, ≥12 GB RAM to keep Kafka/Postgres healthy.
- Frequently used containers:
  - `somaAgent01_gateway` → `http://localhost:${GATEWAY_PORT:-20016}`
  - `somaAgent01_agent-ui` → `http://localhost:${AGENT_UI_PORT:-20015}`
  - `somaAgent01_tool-executor`
  - `somaAgent01_conversation-worker`
- Verification checklist after `docker compose up`:
  1. `curl http://localhost:${GATEWAY_PORT:-20016}/health`
  2. `docker compose -p somaagent01 ps` shows services `healthy`
  3. `docker exec somaAgent01_postgres psql -U soma -d somaagent01 -c "SELECT NOW();"`
- Troubleshooting quick hits:
  - Port clash on Kafka (`9092`): set `KAFKA_PORT` in `.env` or stop conflict.
  - Gateway 5xx on boot: wait for OPA/OpenFGA migrations to finish.
  - High CPU idle: disable optional profiles or lower `WHISPER_MODEL`.

## 9. IDE Configuration

- VS Code recommended with Python and Docker extensions.
- Select `.venv` interpreter.
- Use `.vscode/launch.json` launchers for `run_ui.py` and `run_tunnel.py`.

## 10. Troubleshooting

- **Docker missing:** Install from [docker.com](https://www.docker.com/products/docker-desktop/).
- **Port conflicts:** Adjust `WEB_UI_PORT` before invoking `make dev-up`.
- **Realtime speech issues:** Verify API keys and inspect `python/api/realtime_session.py` logs.

Once the environment is verified, continue with the [Contribution Workflow](./contribution-workflow.md).

## 11. Optional: Enable SSO/JWT in Dev

The gateway supports JWT auth for local development. Choose one of the following and export as environment variables before `make dev-up` (or set in your shell):

HS256 (shared secret)

```bash
export GATEWAY_REQUIRE_AUTH=true
export GATEWAY_JWT_SECRET=dev-secret
export GATEWAY_JWT_ALGORITHMS=HS256
```

JWKS (OIDC provider like Auth0/Okta/Entra)

```bash
export GATEWAY_REQUIRE_AUTH=true
export GATEWAY_JWKS_URL="https://YOUR_DOMAIN/.well-known/jwks.json"
export GATEWAY_JWT_ALGORITHMS=RS256
export GATEWAY_JWT_AUDIENCE="api://somaagent01"
export GATEWAY_JWT_ISSUER="https://YOUR_DOMAIN/"
```

Notes

- Admin-only endpoints require a scope claim containing `admin` or `keys:manage`.
- Tenant is derived from the first matching claim in `GATEWAY_JWT_TENANT_CLAIMS` (default: `tenant,org,customer`).
- Health endpoints remain open for readiness checks.
