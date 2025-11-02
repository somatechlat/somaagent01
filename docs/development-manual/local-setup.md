# Local Development Setup

**Standards**: ISO/IEC 29148§5.2

## One-Page Setup Guide

### Prerequisites Check

```bash
# Python 3.11+
python3.11 --version

# Docker 20.10+
docker --version

# Make
make --version

# Git
git --version
```

### Quick Setup (5 minutes)

```bash
# 1. Clone
git clone https://github.com/somatechlat/somaagent01.git
cd somaagent01

# 2. Virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure
cp .env.example .env
nano .env  # Add your OPENROUTER_API_KEY

# 5. Start infrastructure
make deps-up

# 6. Start services
make stack-up

# 7. Start UI (new terminal)
make ui
```

### Verification

```bash
# Check all services
make check-stack

# Expected output:
# ✅ Kafka: healthy
# ✅ Redis: healthy
# ✅ PostgreSQL: healthy
# ✅ OPA: healthy
# ✅ Gateway: healthy

# Test API
curl http://localhost:20016/v1/health

# Open UI
open http://127.0.0.1:3000
```

## Detailed Setup

### 1. Python Environment

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install -r requirements-dev.txt  # if exists
```

### 2. Environment Configuration

```bash
# Copy example
cp .env.example .env

# Edit configuration
nano .env
```

**Required variables**:
```bash
# LLM Provider
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Authentication
AUTH_PASSWORD=your-secure-password

# Deployment
DEPLOYMENT_MODE=DEV
```

**Optional variables**:
```bash
# Ports (defaults shown)
GATEWAY_PORT=20016
KAFKA_PORT=20000
REDIS_PORT=20001
POSTGRES_PORT=20002

# Logging
LOG_LEVEL=DEBUG  # DEV mode: DEBUG, PROD: INFO

# Memory
SOMABRAIN_BASE_URL=http://localhost:9696
```

### 3. Infrastructure Services

```bash
# Start Kafka, Redis, PostgreSQL, OPA
make deps-up

# Verify services
docker compose ps

# Check logs
docker compose logs kafka
docker compose logs postgres
docker compose logs redis
```

**Wait for services to be ready** (30-60 seconds):
```bash
# Kafka ready when you see:
# "Kafka Server started"

# PostgreSQL ready when you see:
# "database system is ready to accept connections"
```

### 4. Database Schema

```bash
# Schema is auto-created on first gateway start
# Or manually initialize:
python scripts/ensure_outbox_schema.py
```

### 5. Start Services

```bash
# Terminal 1: Gateway + Workers
make stack-up

# This starts:
# - Gateway (port 20016)
# - Conversation Worker
# - Tool Executor
# - Memory Replicator
# - Memory Sync
# - Outbox Sync
```

### 6. Start UI

```bash
# Terminal 2: UI
make ui

# UI runs on http://127.0.0.1:3000
```

## Development Workflow

### Running Individual Services

```bash
# Gateway only
python -m services.gateway.main

# Conversation worker only
python -m services.conversation_worker.main

# With environment variables
GATEWAY_PORT=8080 python -m services.gateway.main
```

### Hot Reload

Services auto-reload on code changes when running via `make stack-up`.

To disable:
```bash
# Edit Makefile, remove --reload flag
```

### Database Access

```bash
# Connect to PostgreSQL
docker compose exec postgres psql -U somauser -d somadb

# Run queries
SELECT * FROM sessions LIMIT 10;
SELECT * FROM memory_replica ORDER BY created_at DESC LIMIT 10;
```

### Redis Access

```bash
# Connect to Redis
docker compose exec redis redis-cli

# Check keys
KEYS *
GET session:abc123:meta
```

### Kafka Access

```bash
# List topics
docker compose exec kafka kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --list

# Consume messages
docker compose exec kafka kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic conversation.inbound \
  --from-beginning
```

## Troubleshooting

### Port Conflicts

```bash
# Find process using port
lsof -i :20016

# Kill process
kill -9 <PID>

# Or change port in .env
GATEWAY_PORT=8080
```

### Import Errors

```bash
# Ensure virtual environment is activated
which python  # Should show venv path

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Database Connection Errors

```bash
# Check PostgreSQL is running
docker compose ps postgres

# Check logs
docker compose logs postgres

# Restart
docker compose restart postgres
```

### Kafka Not Ready

```bash
# Check Kafka logs
docker compose logs kafka

# Wait longer (Kafka takes 30-60s to start)
sleep 30

# Restart if needed
docker compose restart kafka
```

## IDE Configuration

### VS Code

```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true
}
```

### PyCharm

1. File → Settings → Project → Python Interpreter
2. Add Interpreter → Existing Environment
3. Select `venv/bin/python`
4. Enable "Black" formatter in Tools → Black

## Next Steps

- [First Contribution](./first-contribution.md)
- [Coding Standards](./coding-standards.md)
- [Testing Guidelines](./testing-guidelines.md)
