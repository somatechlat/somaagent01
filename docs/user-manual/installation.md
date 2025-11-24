# Installation Guide

![Version](https://img.shields.io/badge/version-1.0.0-blue)

## Prerequisites

- **Docker** 20.10+ and **Docker Compose** 2.0+
- **Python** 3.11+ (for local development)
- **Git**
- **Make** (optional, for convenience commands)
- **8GB RAM minimum** (16GB recommended)

## Quick Start (Docker)

```bash
# Clone the repository
git clone https://github.com/agent0ai/agent-zero.git
cd agent-zero

# Start the stack
make dev-up

# Wait for health check
make health-wait

# Access the UI
open http://localhost:21016/
```

## Environment Setup

### 1. Create `.env` File

The Makefile auto-creates a minimal `.env`. For custom configuration:

```bash
# Gateway
GATEWAY_PORT=21016
SA01_GATEWAY_BASE_URL=http://localhost:21016
WEB_UI_BASE_URL=http://localhost:21016/

# Encryption key for LLM credentials (Fernet urlsafe base64)
SA01_CRYPTO_FERNET_KEY=O6qM9Oe7zB3w6CqQFctciVwEciXxV9nOcDSBxPTsPOg=

# Internal token for service-to-service calls
SA01_AUTH_INTERNAL_TOKEN=dev-internal-token

# SomaBrain
SA01_SOMA_BASE_URL=http://host.docker.internal:9696
SA01_SOMA_TENANT_ID=public
SA01_SOMA_NAMESPACE=somabrain_ns:public

# Kafka
KAFKA_PORT=21000

# Redis
REDIS_PORT=20001

# PostgreSQL
POSTGRES_PORT=20002

# OPA
OPA_PORT=20009
```

### 2. Configure LLM Provider (via UI)

1. Start the stack: `make dev-up`
2. Open UI: http://localhost:21016/
3. Navigate to **Settings → Model**
4. Set **Provider**: `groq` (or `openai`, `openrouter`, etc.)
5. Set **Model**: `llama-3.1-8b-instant`
6. Navigate to **Settings → API Keys**
7. Add key: `api_key_groq` with your Groq API key
8. Click **Save** (keys are stored server-side; no `.env` secrets are used)

**Note**: Credentials are encrypted in Redis. Never put API keys in `.env`.

## Installation Methods

### Method 1: Docker Compose (Recommended)

```bash
# Start all services
make dev-up

# Check status
docker compose -p somaagent01_dev ps

# View logs
make dev-logs

# Stop services
make dev-down
```

### Method 2: Local Development (Python)

```bash
# 1. Start infrastructure only
make deps-up

# 2. Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start services locally
make stack-up

# 5. In another terminal, run UI (optional)
make ui
```

### Method 3: Hybrid (Infra in Docker, Services Local)

```bash
# Start Kafka/Redis/Postgres/OPA
make deps-up

# Run gateway + workers locally (Ctrl+C to stop)
make stack-up
```

## Verification

### Health Checks

```bash
# Gateway health
curl http://localhost:21016/v1/health

# Expected response:
# {"status":"healthy","timestamp":"2025-01-24T...","services":{...}}
```

### UI Smoke Test

```bash
make ui-smoke
```

### E2E Tests

```bash
make test-e2e
```

## Port Reference

| Service | Port | URL |
|---------|------|-----|
| Gateway + UI | 21016 | http://localhost:21016/ |
| Kafka (external) | 21000 | localhost:21000 |
| Redis | 20001 | localhost:20001 |
| PostgreSQL | 20002 | localhost:20002 |
| OPA | 20009 | http://localhost:20009 |
| Gateway Metrics | 8000 | http://localhost:8000/metrics |
| Conversation Worker Metrics | 9410 | http://localhost:9410/metrics |
| Tool Executor Metrics | 9411 | http://localhost:9411/metrics |

## Troubleshooting

### Port Conflicts

If ports are already in use, override in `.env`:

```bash
GATEWAY_PORT=8080
KAFKA_PORT=9092
```

### Container Name Conflicts

```bash
# Force cleanup
make dev-down-clean

# Restart
make dev-up
```

### Kafka Not Ready

```bash
# Check Kafka health
docker logs somaAgent01_kafka

# Wait for "Kafka Server started"
```

### Gateway 502 Errors

```bash
# Check if Kafka is reachable
docker exec somaAgent01_gateway curl -f http://kafka:9092

# Check Gateway logs
docker logs somaAgent01_gateway
```

### SomaBrain Connection Failed

Ensure SomaBrain is running on port 9696:

```bash
curl http://localhost:9696/health
```

If not running, start SomaBrain separately or adjust `SA01_SOMA_BASE_URL`.

## Next Steps

- [Quick Start Tutorial](./quick-start-tutorial.md)
- [Features Overview](./features.md)
- [Troubleshooting Guide](./troubleshooting.md)
- [Development Setup](../development-manual/local-setup.md)
