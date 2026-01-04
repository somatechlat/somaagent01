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

### Required Environment Variables

Edit `.env` and configure:

```bash
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=somastack2024
POSTGRES_DB=somaagent

# Redis
REDIS_PASSWORD=somastack2024

# Keycloak (Identity)
KEYCLOAK_URL=http://localhost:20880
KEYCLOAK_REALM=somaagent
KEYCLOAK_CLIENT_ID=eye-of-god

# LLM Provider
OPENAI_API_KEY=your-api-key-here
SAAS_DEFAULT_CHAT_MODEL=gpt-4o
```

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

**SomaAgent01 uses port 20xxx:**

| Service | Port |
|---------|------|
| PostgreSQL | 20432 |
| Redis | 20379 |
| Kafka | 20092 |
| Milvus | 20530 |
| SpiceDB | 20051 |
| OPA | 20181 |
| Keycloak | 20880 |
| Prometheus | 20090 |
| Grafana | 20300 |
| Django API | 20020 |
| Frontend | 20080 |

**Related Services:**
- SomaBrain: Port 30xxx (API: 30101)
- SomaFractalMemory: Port 40xxx (API: 40000, PostgreSQL: 40001, Redis: 40002)

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
npm install
npm run dev
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
