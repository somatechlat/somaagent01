# Installation Guide

**Standards**: ISO/IEC 12207§6.4

## Prerequisites

- **Docker**: 20.10+ (for containerized deployment)
- **Python**: 3.11+ (for local development)
- **Memory**: 8GB RAM minimum
- **Storage**: 10GB available space
- **OS**: macOS, Linux, or Windows with WSL2

## Quick Start (Docker)

```bash
# Pull the image
docker pull agent0ai/agent-zero

# Run the container
docker run -p 50001:80 agent0ai/agent-zero

# Verify
curl -f http://localhost:50001/health || echo "❌ Health check failed"
```

**Result**: Visit `http://localhost:50001` to access the UI.

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/somatechlat/somaagent01.git
cd somaagent01
```

### 2. Create Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit with your API keys
nano .env  # or use your preferred editor
```

Required variables:
- `OPENROUTER_API_KEY` - LLM provider API key
- `AUTH_PASSWORD` - UI authentication password
- `SOMABRAIN_BASE_URL` - Memory service URL (default: http://localhost:9696)

### 4. Start Infrastructure

```bash
# Start Kafka, Redis, PostgreSQL, OPA
make deps-up

# Verify services are healthy
docker ps | grep -E "kafka|redis|postgres|opa"
```

### 5. Start Services

```bash
# Launch gateway + workers
make stack-up

# Verify gateway is running
curl http://localhost:${GATEWAY_PORT:-21016}/v1/health
```

### 6. Start UI

```bash
# In a new terminal
make ui

# Verify UI is accessible
open http://127.0.0.1:3000
```

## Port Reference

| Service | Port | Purpose |
|---------|------|---------|
| UI | 20015 | Web interface (Docker) |
| UI | 3000 | Web interface (local dev) |
| Gateway | 21016 | API endpoint (configurable via GATEWAY_PORT) |
| Kafka | 20000 | Event streaming |
| Redis | 20001 | Cache |
| PostgreSQL | 20002 | Database |
| OPA | 20009 | Policy engine |
| SomaBrain | 9696 | Memory service |

## Verification

```bash
# Check all services
make check-stack

# Expected output:
# ✅ Kafka: healthy
# ✅ Redis: healthy
# ✅ PostgreSQL: healthy
# ✅ Gateway: healthy
```

## Troubleshooting

### Port Already in Use

```bash
# Find process using port
lsof -i :21016

# Kill process
kill -9 <PID>
```

### Docker Compose Fails

```bash
# Clean up and restart
make down
docker system prune -f
make up
```

### Database Connection Errors

```bash
# Reset database
docker compose down -v
docker compose up -d postgres
sleep 5
make stack-up
```

## Next Steps

- [Quick Start Tutorial](./quick-start-tutorial.md)
- [Features Overview](./features.md)
- [FAQ](./faq.md)
