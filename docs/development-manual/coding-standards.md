---
title: Coding Standards
slug: dev-coding-standards
version: 1.0.0
last-reviewed: 2025-10-15
audience: contributors
owner: developer-experience
reviewers:
  - platform-engineering
prerequisites:
  - Read [Contribution Workflow](./contribution-workflow.md)
verification:
  - `make lint` and `mypy` succeed
  - Code review checklist complete
---

# Coding Standards

These standards ensure SomaAgent01 code remains consistent, testable, and secure. The automation pipeline enforces many of these rules via `ruff`, `black`, and `mypy`.

## Python

- Format with `black` and lint using `ruff`. Run `make fmt && make lint` before pushing.
- Use type hints everywhere; CI blocks PRs failing `mypy`.
- Prefer dataclasses or Pydantic models for structured payloads.
- Avoid global state; inject dependencies via FastAPI or dedicated factories.
- Log with structured contexts (`logger.info("message", extra={"task_id": task_id})`).
- Never use `except:`; catch specific exceptions to satisfy `ruff` rule `E722`.
- Capture loop variables when defining closures (`def fn(_, printer=printer)` to avoid `ruff` rule `B023`).

## JavaScript / TypeScript (Web UI)

- Target ES2020 modules. Use `const`/`let`; avoid `var`.
- Keep functions pure when possible; isolate DOM manipulation.
- Document complex flows with JSDoc or inline comments.
- Run `npm run lint` and `npm run test` before pushing UI changes.

## Testing

- Use Pytest for backend; Playwright for UI flows.
- Every feature requires tests covering happy path and failure modes.
- Prefer integration tests over heavy mocking—aligns with Agent Zero's philosophy.
- Store reusable fixtures in `tests/fixtures/`.

## Documentation

- Update relevant manuals (User, Technical, Development, Onboarding) for every feature.
- Maintain diagrams in Mermaid with source tracked under `docs/diagrams/`.
- Place screenshots under `docs/res/` with descriptive filenames.
- Run `make docs-verify` to lint Markdown, validate links, and build MkDocs.

## Git Hygiene

- Branch names follow `feature/<id>-<slug>` or `bugfix/<id>-<slug>`.
- Commit messages use imperative mood (`Add realtime speech docs`).
- Include tests and documentation updates in the same PR when feasible.

## Security

- Never hardcode secrets. Use `python/helpers/secrets.py` or environment variables.
- Validate all API inputs and sanitize logs.
- Run Trivy scans locally for critical services when touching Dockerfiles.

## Code Reviews

- PR description must include context, screenshots (if UI), and test evidence.
- Reviewers focus on correctness, performance, security, and documentation coverage.
- Resolve comments via follow-up commits; squash at merge time.
