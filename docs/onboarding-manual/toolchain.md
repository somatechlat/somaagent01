---
title: Toolchain Primer
slug: onboarding-toolchain
version: 1.0.0
last-reviewed: 2025-10-15
audience: new hires
owner: developer-experience
reviewers:
  - platform-engineering
prerequisites:
  - Orientation tasks completed
verification:
  - Toolchain commands practiced during onboarding
---

# Toolchain Primer

This primer introduces the core tools you will use daily on SomaAgent01.

## Communication & Knowledge

- Slack channels: `#soma-agent-zero`, `#soma-oncall`, `#soma-docs`.
- Documentation hub: [`docs/README.md`](../README.md) (new structure) and MkDocs site (published internally).
- Incident updates: `status.somaagent01.dev`.

## Development Tools

| Purpose | Tool | Notes |
| ------- | ---- | ----- |
| Code editor | VS Code | Recommended extensions: Python, Docker, Markdown All in One |
| Version control | Git + GitHub | Use SSH keys; enable 2FA |
| Python runtime | `pyenv` (optional) or system Python 3.12 | Virtualenv at `.venv` |
| Package mgmt | `pip`, `npm`, optional `poetry` | Install dependencies as documented |
| Containers | Docker Desktop | Allocate ≥4 CPUs, 8 GB RAM |

## Commands to Memorize

```bash
make dev-up        # Start full stack
make dev-down      # Stop stack
make dev-logs      # Tail logs
make fmt lint      # Format & lint
pytest             # Run test suites
make docs-verify   # Markdown lint, link check, MkDocs build
```

## Credentials & Access

- Request Vault access via Access Manager ticket.
- Obtain Soma SLM API key from platform team; store in 1Password and `.env`.
- GitHub membership handled by people-ops; verify org access on day one.

## Self-Checks

- Confirm `python --version` outputs 3.12.x.
- `docker info` shows minimum resource allocation.
- `npm -v` returns 8.x or later.

If any tool is missing or incompatible, contact `#soma-helpdesk`.
