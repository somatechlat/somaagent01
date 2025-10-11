# Developer Setup Guide

## Prerequisites

- macOS/Linux (Windows via WSL2)
- Docker Desktop 4.36+
- Python 3.12+
- Node.js 18+ (for UI builds)
- VS Code (recommended) with Python & Docker extensions

## Initial Clone

```bash
git clone https://github.com/agent0ai/agent-zero.git
cd agent-zero
```

## Python Environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Frontend Dependencies

```bash
cd webui
npm install
cd ..
```

## Stack Startup

```bash
make dev-up
```
- Brings up complete SomaAgent01 stack with realtime speech defaults.
- UI available at `http://localhost:7002`.

## IDE Configuration

- VS Code: open workspace, accept recommended extensions.
- Configure Python interpreter (`.venv`).
- Debug config: `.vscode/launch.json` provides launchers for `run_ui.py`, `run_tunnel.py`.

## Environment Variables

- Copy `.env.example` to `.env` (create if missing).
- Key variables: `OPENAI_API_KEY`, `POSTGRES_DSN`, `REDIS_URL`.

## Running Tests

```bash
pytest
pytest tests/playwright/test_realtime_speech.py --headed
```

## Common Tasks

| Task | Command |
| --- | --- |
| Start stack | `make dev-up` |
| Stop stack | `make dev-down` |
| Tail logs | `make dev-logs` |
| Wipe volumes | `make dev-clean` |
| Status | `make dev-status` |

## Troubleshooting

- Missing Docker? Install from https://www.docker.com/products/docker-desktop/
- Port conflicts? Free port 7002 or adjust `WEB_UI_PORT` before startup.
- Realtime speech failing? Verify API key, inspect `python/api/realtime_session.py` logs.

## Next Steps

- Read `docs/architecture/overview.md` for system context.
- Follow `docs/development/coding-standards.md` before submitting PRs.
