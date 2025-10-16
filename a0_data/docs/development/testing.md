# Testing Strategy

## Test Pyramid

```mermaid
graph TD
    E2E[End-to-End (Playwright)]
    Integration[Integration (pytest)]
    Unit[Unit Tests]

    Unit --> Integration --> E2E
```

- **Unit Tests:** Functions, helpers, model validations.
- **Integration Tests:** Gateway routes, settings, memory, tool executor contracts.
- **End-to-End:** Playwright scenarios covering UI + backend.

## Command Summary

| Suite | Command |
| --- | --- |
| All tests | `pytest` |
| Integration only | `pytest tests/integration` |
| Playwright | `pytest tests/playwright --headed` |
| Targeted test | `pytest tests/integration/test_gateway_public_api.py::test_health` |

## Fixtures

- `tests/conftest.py`: shared fixtures (client, settings overrides).
- `tests/context/`: long-running context tests (goal switching, callbacks).
- Use factory functions for generating data (e.g., memory items).

## Real Services Policy

- Tests interact with live dependencies (Postgres, Redis, Kafka).
- Ensure stack running via `make dev-up` before executing tests.
- Use dedicated test tenants to avoid mutating production data.

## CI Strategy

- Pipeline stages:
  1. Lint (`black --check`, `flake8`, `eslint`).
  2. Unit + integration tests.
  3. Playwright (headless, with xvfb or browser container).
- Collect artifacts: screenshots on failure, logs.

## Regression Tracking

- Tag failing scenarios with issue IDs (`pytest.mark.issue123`).
- Maintain history in `docs/changelog.md`.

## Load & Stress Testing

- Use `locust` or `k6` scripts (to be added) with real providers.
- Monitor metrics to detect bottlenecks.

## Adding New Tests

1. Identify coverage gap.
2. Add test file with descriptive name.
3. Update docs if feature involves UI/API.
4. Run relevant suites locally before PR.
