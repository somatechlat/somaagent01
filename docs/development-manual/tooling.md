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
  - `make dev-up`, `make dev-down`, `make dev-logs`.
  - `make fmt`, `make lint`, `make test`, `make docs-verify`.
- **Poetry** (if enabled): `poetry install`, `poetry run pytest`.
- **Node toolchain:** `npm run lint`, `npm run build` under `webui/`.

## Linting & Formatting

| Language | Tool | Command |
| -------- | ---- | ------- |
| Python | Black, Ruff, Mypy | `make fmt fmt-check lint mypy` |
| JavaScript/TypeScript | ESLint, Prettier | `npm run lint`, `npm run format` |
| Markdown | markdownlint-cli2 | `make docs-verify` |

## Documentation Pipeline

- MkDocs configuration: `mkdocs.yml` (added in docs sprint).
- Diagram rendering: `mmdc` (Mermaid CLI) invoked via `make docs-diagrams`.
- Link checking: `lychee` executed in docs CI workflow.

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

- Run `make tooling-audit` (script added in this sprint) to ensure required binaries are present and versions are compatible.
