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

- UI available at `http://localhost:7002`.
- Logs tail via `make dev-logs`.

**Verification:**
- `make dev-status` shows services healthy.
- `curl http://localhost:8010/health` returns `200`.

## 6. Testing

```bash
pytest
pytest tests/playwright/test_realtime_speech.py --headed
```

## 7. Common Tasks

| Task | Command |
| ---- | ------- |
| Stop stack | `make dev-down` |
| Clean volumes | `make dev-clean` |
| Format Python | `make fmt` |
| Lint | `make lint` |
| Apply lint fixes | `make lint-fix` |

## 8. Local Docker Compose Reference

- **Lightweight developer stack** (`docker-compose.dev.yaml`): trimmed to Postgres, Redis, Kafka, OPA, Gateway, Conversation Worker, Tool Executor, optional UI. Default host ports live in the `608xx` range (e.g., gateway on `http://localhost:60816`). Handy shortcuts: `make dev-up`, `make dev-logs`, `make dev-down`.
- **Full stack** (`docker-compose.somaagent01.yaml`): enables all profiles (`vectorstore`, `observability`, `kafka`) for parity with staging/production (`docker compose --profile vectorstore up`).
- Recommended Docker Desktop allocation: ≥8 CPUs, ≥12 GB RAM to keep Kafka/Postgres healthy.
- Frequently used containers:
  - `somaAgent01_gateway` → `http://localhost:8010`
  - `somaAgent01_agent-ui` → `http://localhost:7002`
  - `somaAgent01_tool-executor`
  - `somaAgent01_conversation-worker`
- Verification checklist after `docker compose up`:
  1. `curl http://localhost:8010/health`
  2. `docker compose ps` shows services `healthy`
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
