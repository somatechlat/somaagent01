# Coding Standards

## Python

- Follow PEP 8 with Black formatting (`black .`).
- Run Ruff linting (`ruff check .` or `make lint`) before submitting patches.
- Type hints required; run `mypy` before PRs.
- Prefer dataclasses/Pydantic models for structured data.
- Avoid global state; use dependency injection (FastAPI) or context objects.
- Log with structured contexts (`logger.info("message", extra={...})`).
 - Follow PEP 8 with Black formatting (`black .`).
 - Run Ruff linting (`ruff check .` or `make lint`) before submitting patches.
 - Type hints required; run `mypy` before PRs.
 - Prefer dataclasses/Pydantic models for structured data.
 - Avoid global state; use dependency injection (FastAPI) or context objects.
 - Log with structured contexts (`logger.info("message", extra={...})`).
 - **Never use a bare ``except:``** – replace it with ``except Exception:`` (or a more specific exception) to satisfy Ruff ``E722`` and keep error handling explicit.
 - When defining inner functions that reference loop‑level variables (e.g., ``printer``), capture them via default arguments (``def callback(..., printer=printer)``) to avoid Ruff ``B023`` warnings about unbound loop variables.

## JavaScript

- ES2020 modules, no global scope pollution.
- Use const/let appropriately, avoid `var`.
- Keep functions pure where possible, isolate DOM side effects.
- Document complex flows with inline comments or JSDoc.

## Tests

- Pytest + Playwright required for new features.
- Name tests with clear scenario description.
- Use real services; do not mock external APIs unless absolutely necessary (per README directive).
- Provide fixtures under `tests/fixtures/` for reusable setup.

## Documentation

- Every feature PR must update relevant docs (`docs/features/`, `docs/apis/`, changelog).
- Maintain architecture diagrams in Mermaid or source format.
- Screenshots should be stored under `docs/res/` with descriptive names.

## Git Workflow

- Branch naming: `feature/<name>`, `fix/<issue>`, `docs/<area>`.
- Commit style: imperative mood (`Add realtime speech docs`).
- Include tests and documentation updates in same PR when possible.

## Security

- Never hardcode secrets; use `python/helpers/secrets.py`.
- Input validation mandatory for API endpoints.
- Sanitize logs to avoid leaking sensitive data.

## Code Reviews

- Provide context, screenshots, and test evidence in PR description.
- Reviewers focus on correctness, clarity, performance, and doc coverage.

## Automation Agents

- When building automated contributors, ensure they observe same standards.
- Agents should reference this document before committing changes.
