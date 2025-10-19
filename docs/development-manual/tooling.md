---
title: Developer Tooling
slug: dev-tooling
version: 1.0.0
last-reviewed: 2025-10-15
audience: contributors
owner: developer-experience
reviewers:
  - platform-engineering
prerequisites:
  - Environment set up per [Environment Setup](./environment.md)
verification:
  - Toolchain commands succeed locally
---

# Developer Tooling

This chapter lists the sanctioned tooling for SomaAgent01 development and how to use it effectively.

## Command Interface

- **Makefile targets** (see `Makefile`):
  - `make build`, `make up`, `make down`, `make logs`, `make clean`.
  - `make dev-up`, `make dev-down`, `make dev-logs`, `make dev-rebuild`, `make dev-up-services SERVICES=gateway`.
  - `make docs-install`, `make docs-build`, `make docs-verify`.
- **Python environment:** `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.
- **Node toolchain:** `npm install && npm run build` under `webui/` when working on the UI.

## Linting & Formatting

| Language | Tool | Command |
| -------- | ---- | ------- |
| Python | Ruff, Black | `ruff check .`, `black .` |
| JavaScript/TypeScript | ESLint, Prettier | `npm run lint`, `npm run format` |
| Markdown/Docs | MkDocs + markdownlint | `make docs-verify` |

## Documentation Pipeline

- MkDocs configuration: `mkdocs.yml`.
- Local authoring: `make docs-install` once, then `make docs-build` (strict) or `make docs-serve`.
- CI parity: `.github/workflows/docs.yml` runs `make docs-verify`.

## Observability & Debugging

- **Logs:** `make dev-logs` or `docker compose logs -f gateway`.
- **Profiling:** `scripts/profiling/profile_gateway.py` (use with caution in dev).
- **Tracing:** Jaeger UI at `http://localhost:16686` when observability profile enabled.

## Git Hooks

- Optional pre-commit configuration stored in `.pre-commit-config.yaml` (run `pre-commit install`).
- Hooks enforce formatting, linting, and documentation checklist reminders.

## Automation Agents

- Internal agents follow the same standards; reference this manual before enabling automated commits.
- Monitor agent contributions via `scripts/automation/report_agent_activity.py`.

## Verification

- Run `pytest` for the Python test suite.
- `make docs-verify` prior to publishing documentation changes.
- `docker compose -p somaagent01 -f docker-compose.yaml ps` to confirm service health after stack changes.
