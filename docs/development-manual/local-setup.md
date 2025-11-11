# Local Development Setup

![Version](https://img.shields.io/badge/version-1.0.0-blue)

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Git
- Make

## Setup Steps

### 1. Clone Repository

```bash
git clone https://github.com/agent0ai/agent-zero.git
cd agent-zero
```

### 2. Create Virtual Environment

```bash
python3.11 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Start Infrastructure

```bash
make deps-up
```

This starts:
- Kafka (port 21000)
- Redis (port 20001)
- PostgreSQL (port 20002)
- OPA (port 20009)

### 5. Run Services Locally

```bash
make stack-up
```

This runs:
- Gateway (port 21016)
- Conversation Worker
- Tool Executor
- Memory services

Press `Ctrl+C` to stop.

## Development Workflow

### Running Individual Services

```bash
# Gateway only
python -m uvicorn services.gateway.main:app --reload --host 0.0.0.0 --port 8010

# Conversation Worker only
python -m services.conversation_worker.main

# Tool Executor only
python -m services.tool_executor.main
```

### Environment Variables

Create `.env`:

```bash
GATEWAY_PORT=21016
SA01_AUTH_INTERNAL_TOKEN=dev-internal-token
SA01_CRYPTO_FERNET_KEY=O6qM9Oe7zB3w6CqQFctciVwEciXxV9nOcDSBxPTsPOg=
SA01_KAFKA_BOOTSTRAP_SERVERS=localhost:21000
SA01_REDIS_URL=redis://localhost:20001/0
SA01_DB_DSN=postgresql://soma:soma@localhost:20002/somaagent01
SA01_POLICY_URL=http://localhost:20009
SA01_SA01_SOMA_BASE_URL=http://localhost:9696
``` 

### Hot Reload

Gateway supports `--reload` for live code changes:

```bash
make stack-up-reload
```

### Testing

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# E2E tests
make test-e2e

# All tests
pytest
```

## IDE Configuration

### VSCode

`.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black"
}
```

### PyCharm

1. File → Settings → Project → Python Interpreter
2. Add Interpreter → Existing environment
3. Select `.venv/bin/python`

## Debugging

### Gateway

```bash
# Run with debugger
python -m debugpy --listen 5678 --wait-for-client -m uvicorn services.gateway.main:app --reload
```

### Logs

```bash
# Gateway logs
docker logs -f somaAgent01_gateway

# All services
make dev-logs

# Specific service
docker logs -f somaAgent01_conversation-worker
```

## Common Tasks

### Reset Database

```bash
make dev-down-hard
make dev-up
```

### Clear Redis Cache

```bash
docker exec somaAgent01_redis redis-cli FLUSHALL
```

### View Kafka Topics

```bash
docker exec somaAgent01_kafka kafka-topics --bootstrap-server localhost:9092 --list
```

### Consume Kafka Messages

```bash
docker exec somaAgent01_kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic conversation.inbound \
  --from-beginning
```

## Next Steps

- [Coding Standards](./coding-standards.md)
- [Testing Guidelines](./testing-guidelines.md)
- [API Reference](./api-reference.md)
