# Testing Architecture (Live-First)

This repository adopts a live-first testing strategy: tests are designed to exercise real services (Gateway, workers, Postgres, Kafka, OPA, Redis) without mocks, matching how the stack runs in development and production.

## Test Layers
- Unit (fast, pure-Python logic) — used sparingly; prefer live modules where possible.
- Integration (`@pytest.mark.live`, `@pytest.mark.db`, `@pytest.mark.kafka`, `@pytest.mark.gateway`) — validate concrete flows against running services.
- E2E (`@pytest.mark.e2e`) — cross-service journeys (document ingest, memory write-through, chat SSE flows, UI checks).

## Markers
Registered in `pytest.ini`:
- `live`: requires full stack.
- `db`, `kafka`, `gateway`: target specific subsystems.
- `e2e`, `playwright`: cross-service + UI flows.
- `smoke`, `slow`, `performance`, `critical`, `flaky`, `optional`.

## Running Against Real Services
Use Make targets to bring up the stack and run tests against it.

```sh
# Start deps + stack, then run full suite
make test-live

# Or run only e2e
make deps-up-live && pytest -vv -m e2e

# Health check
make health
```

## Reliability Patterns
- Prefer event-driven waiting over sleeps. Use `tests/utils.py::wait_for` and `wait_for_event`.
- Avoid swallowing exceptions in tests. Convert to explicit assertions or reasoned skips (with message).
- Consolidate duplicate coverage into parametrized tests.

## Deletions & Quarantine
- Capsule-related tests are obsolete and will be removed.
- Heavy live-only suites can be tagged `e2e` or `optional` depending on CI profile. The default developer workflow is live-first; CI may run a selected subset as smoke.

## Next Steps
- Replace ad-hoc `sleep` polling with `wait_for`.
- Strengthen trivial "length-only" assertions with structural guarantees (schema, ordering, types).
- Reduce unknown mark warnings by using registered markers.
