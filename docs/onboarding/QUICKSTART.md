# 🚀 SomaAgent01 Quick Start Guide

> **For Developers & AI Agents** - Get the SOMA Stack running in 10 minutes

---

## Prerequisites

| Component | Minimum Version | Check Command |
|-----------|-----------------|---------------|
| Docker | 24.0+ | `docker --version` |
| Docker Compose | 2.20+ | `docker compose version` |
| Python | 3.11+ | `python3 --version` |
| Node.js | 20+ | `node --version` |
| RAM | 16GB | - |

---

## Step 1: Clone & Configure

```bash
# Clone the repository
git clone https://github.com/somatech/somaAgent01.git
cd somaAgent01

# Copy environment template
cp .env.example .env
```

### SAAS Deployment (Recommended)

The SAAS deployment requires NO manual .env configuration for infrastructure.

**Required:**
1. **Vault must be running** with secrets pre-loaded
2. **Docker Compose** with `./infra/saas/docker-compose.yml`

**What's already configured:**
- All services auto-start with correct ports
- Vault runs at `localhost:63982`
- PostgreSQL runs at `localhost:63932` (external), `localhost:5432` (internal)

**Step-by-step:**
```bash
cd infra/saas
docker-compose up -d somastack_vault

# Save LLM API keys to Vault
docker exec -it somastack_vault sh -c '
  vault kv put secret/soma/agent/api_keys \
    openrouter_api_key="sk-or-v1-..." \
    groq_api_key="gsk_..."'

# Save memory token
docker exec -it somastack_vault sh -c '
  vault kv put secret/soma/agent/credentials \
    soma_memory_api_token="memory-token-..."'

# Start full stack
docker-compose up -d
```

**Environment Variables (Optional overrides):**
```bash
# Only needed if you want to override defaults
VAULT_ADDR=http://localhost:63982  # Already default in compose
SOMA_ALLOWED_HOSTS=localhost,127.0.0.1  # Already set
```

**No manual database setup needed!** Migrations run automatically in SAAS.

---

## Step 2: Start Infrastructure

### Option A: Clean Start (Recommended)

```bash
make reset-infra
```

This command:
1. Destroys all existing containers and volumes
2. Starts PostgreSQL and waits for readiness
3. Runs SpiceDB migrations
4. Brings up the full stack

### Option B: Normal Start

```bash
docker compose up -d
```

---

## Step 3: Verify Health

```bash
# Check all services are running
docker compose ps

# Verify API health
curl http://localhost:20020/health

# Expected response:
# {"status": "healthy", "version": "1.0.0"}
```

---

## Step 4: Run Database Migrations

```bash
# Run Django migrations
docker compose exec gateway python manage.py migrate

# Or with Tilt (automatic)
tilt up
```

---

## Step 5: Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| **API Docs** | http://localhost:20020/api/v2/docs | - |
| **Keycloak Admin** | http://localhost:20880/admin | admin / admin |
| **Grafana** | http://localhost:20300 | admin / admin |
| **Frontend** | http://localhost:20080 | - |

---

## Port Namespace Reference

**⚠️ DEPLOYMENT-SPECIFIC PORTS - CHOOSE YOUR MODE:**

### SAAS Deployment (Recommended - All-in-One)
**Location:** `./infra/saas/`  
**Port Range:** `639xx`

| Service | Internal Port | External Port |
|---------|---------------|---------------|
| PostgreSQL | 5432 | 63932 |
| Redis | 6379 | 63979 |
| Kafka | 9092 | 63992 |
| Vault | 8200 | 63982 |
| Agent API | 9000 | 63900 |
| Brain API | 9696 | 63996 |
| Memory API | 10101 | 63901 |
| Milvus | 19530 | 63953 |
| OPA | 8181 | 63904 |
| Prometheus | 9090 | 63905 |
| Grafana | 3000 | 63906 |

**Connect:** `localhost:63900` (Agent API)

### Kubernetes Deployment
**Location:** `./infra/k8s/`  
**Port Range:** `32xxx` (NodePort)

| Service | NodePort | Target |
|---------|----------|--------|
| PostgreSQL | 32432 | 5432 |
| Redis | 32379 | 6379 |
| Kafka | 32092 | 9092 |
| Agent API | 32900 | 9000 |

**Connect:** LoadBalancer IP or `kubectl port-forward`

### Local Development
**Standard ports:**
- PostgreSQL: 5432
- Redis: 6379
- Kafka: 9092
- Vault: 8200

**⚠️ NOTE:** Port 20432 is DEPRECATED and never used in current codebase.

---

## Step 6: Development Workflow

### Start Django Dev Server

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run development server
python manage.py runserver 0.0.0.0:20020
```

### Start Frontend Dev Server

```bash
cd webui
bun install
bun run dev
```

---

## Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| "Port already in use" | `docker compose down -v` then retry |
| "Database connection refused" | Wait for PostgreSQL to be ready |
| "SpiceDB invalid datastore" | Run `make reset-infra` |
| "Keycloak not responding" | Check `docker logs keycloak` |

### Reset Everything

```bash
# Nuclear option - destroys all data
docker compose down -v
docker system prune -f
make reset-infra
```

---

## Next Steps

1. Read [AGENT.md](./AGENT.md) for AI agent context
2. Read [VIBE Coding Rules](./docs/development/VIBE_CODING_RULES.md)
3. Explore [API Documentation](http://localhost:20020/api/v2/docs)

---

**Version**: 1.0.0 | **Last Updated**: 2026-01-04
