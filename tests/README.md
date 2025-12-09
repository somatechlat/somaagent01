# Test Organization

This directory contains all tests for SomaAgent01, organized by test type and infrastructure requirements.

## Test Categories

### Unit Tests (`tests/unit/`)
**Infrastructure Required:** NONE

Isolated tests that do not require any real infrastructure. These tests:
- Use mocked/stubbed dependencies where needed
- Set minimal environment variables via conftest.py
- Run fast and can be executed anywhere
- Test individual functions, classes, and modules in isolation

```bash
# Run unit tests only
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=src --cov=services
```

### Property Tests (`tests/properties/`)
**Infrastructure Required:** NONE

Property-based tests that verify architectural invariants:
- Configuration single source (Property 4)
- Domain isolation
- File size limits
- Repository pattern compliance

```bash
pytest tests/properties/ -v
```

### Integration Tests (`tests/integration/`)
**Infrastructure Required:** PostgreSQL, Redis, Kafka

Tests that verify integration between components with real infrastructure:
- API contract tests
- Gateway tests
- Session repository tests
- Health endpoint tests

```bash
# Start infrastructure first
make deps-up

# Run integration tests
pytest tests/integration/ -v
```

### Functional Tests (`tests/functional/`)
**Infrastructure Required:** ALL (PostgreSQL, Redis, Kafka, SomaBrain, OPA)

Complete functional tests against real infrastructure:
- End-to-end workflows
- Real SomaBrain memory operations
- Real policy enforcement
- Full system behavior validation

```bash
# Start full stack
make dev-up

# Run functional tests
pytest tests/functional/ -v
```

### E2E Tests (`tests/e2e/`)
**Infrastructure Required:** Full running system

End-to-end tests using Playwright for browser automation:
- UI interaction tests
- Full user journey tests

```bash
# Start full stack
make dev-up

# Run e2e tests
pytest tests/e2e/ -v
```

### Smoke Tests (`tests/smoke/`)
**Infrastructure Required:** Running services

Quick sanity checks to verify services are operational:
- Health checks
- Basic connectivity
- Service availability

```bash
pytest tests/smoke/ -v
```

### Load Tests (`tests/load/`)
**Infrastructure Required:** Full running system

Performance and load testing:
- Concurrent request handling
- Memory usage under load
- Response time benchmarks

```bash
python tests/load/load_test_suite.py
```

## Environment Variables

### Required for Unit Tests
None - unit tests set their own minimal environment via conftest.py

### Required for Integration/Functional Tests
```bash
SA01_SOMA_BASE_URL=http://localhost:9696
SA01_DB_DSN=postgresql://soma:soma@localhost:5432/somaagent01
SA01_REDIS_URL=redis://localhost:6379/0
SA01_KAFKA_BOOTSTRAP_SERVERS=localhost:9092
SA01_POLICY_URL=http://localhost:8181
```

## Running All Tests

```bash
# Unit tests only (no infrastructure)
pytest tests/unit/ tests/properties/ -v

# With infrastructure
make deps-up
pytest tests/integration/ -v

# Full test suite
make dev-up
pytest tests/ -v
```

## Test Markers

Use pytest markers to select test categories:

```bash
# Skip slow tests
pytest -m "not slow"

# Run only smoke tests
pytest -m smoke

# Skip tests requiring SomaBrain
pytest -m "not somabrain"
```

## VIBE Compliance

All tests follow VIBE Coding Rules:
- NO mocks in production code (tests may use mocks for isolation)
- NO placeholders or stubs
- Real infrastructure for integration/functional tests
- Clear separation between isolated and infrastructure-dependent tests
