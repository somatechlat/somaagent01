# Development Manual

**Standards**: ISO 29148, IEEE 1016, ISO 29119

## Overview

This manual covers development practices, coding standards, and testing procedures for SomaAgent01.

## Development Environment

### Prerequisites

- Python 3.11+
- Docker 20.10+
- Make
- Git

### Setup

```bash
# Clone repository
git clone https://github.com/somatechlat/somaagent01.git
cd somaagent01

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Start infrastructure
make deps-up

# Run services locally
make stack-up
```

## Project Structure

```
somaAgent01/
├── services/           # Microservices
│   ├── gateway/       # HTTP/WebSocket API
│   ├── conversation_worker/  # Message processing
│   ├── tool_executor/ # Tool execution
│   ├── memory_replicator/    # Memory replication
│   ├── memory_sync/   # Memory retry logic
│   ├── outbox_sync/   # Kafka retry logic
│   └── common/        # Shared libraries
├── webui/             # Web interface
├── python/            # Legacy Agent Zero code
├── infra/             # Infrastructure configs
├── scripts/           # Utility scripts
├── tests/             # Test suites
└── docs/              # Documentation
```

## Coding Standards

- **Style**: PEP 8, enforced by `black` and `ruff`
- **Type Hints**: Required for all public functions
- **Docstrings**: Google style for modules, classes, functions
- **Imports**: Alphabetical, grouped (stdlib, third-party, local)
- **Error Handling**: Explicit exception types, structured logging

## Testing

### Unit Tests

```bash
pytest tests/unit/
```

### Integration Tests

```bash
# Start test infrastructure
make deps-up

# Run integration tests
pytest tests/integration/
```

### Load Tests

```bash
# Smoke test (5 RPS, 15s)
make load-smoke

# Soak test (configurable)
RPS=10 DURATION=60 make load-soak
```

## CI/CD

GitHub Actions workflows:

- `.github/workflows/test.yml`: Run tests on PR
- `.github/workflows/build.yml`: Build Docker images
- `.github/workflows/deploy.yml`: Deploy to staging/prod

## Related Documents

- [API Reference](./api-reference.md)
- [Coding Standards](./coding-standards.md)
- [Testing Guide](./testing.md)
- [CI/CD Pipeline](./ci-cd.md)
- [Contribution Workflow](./contribution-workflow.md)
