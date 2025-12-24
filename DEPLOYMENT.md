# 🚀 Deployment Guide

**Target Environment**: Docker Swarm / Kubernetes / AWS ECS  
**Stack**: Django 5.0, PostgreSQL 16, Redis 7

---

## 1. Environment Variables
Configure these variables in your CI/CD pipeline or `.env` file.

| Variable | Description | Required | Default |
| :--- | :--- | :--- | :--- |
| `DEPLOYMENT_MODE` | `PROD` or `DEV` | Yes | `DEV` |
| `SA01_DB_DSN` | Postgres Connection String | Yes | `postgresql://user:pass@host:5432/db` |
| `SA01_REDIS_URL` | Redis URL | Yes | `redis://host:6379/0` |
| `SAAS_DEFAULT_CHAT_MODEL` | Default LLM Model | Yes | `gpt-4o` |
| `OPENAI_API_KEY` | For LLM Services | Yes | - |

## 2. Docker Deployment

### Build
We use a multi-stage Dockerfile optimized for security and size.
```bash
docker build -t somaagent:latest -f Dockerfile .
```

### Run (Docker Compose)
Use the included `docker-compose.yml` for production-aligned orchestration.
```bash
docker-compose up -d
```

## 3. Database Migrations
**CRITICAL**: Migrations must run on every deployment before traffic is switched.
```bash
# Run migrations via the Gateway service
docker-compose exec gateway python manage.py migrate
```

## 4. Health Checks
- **Combined Health**: `http://localhost:8010/health`
- **Metrics**: `http://localhost:8010/metrics`

## 5. Security Checklist
- [ ] Ensure `DEBUG=False` in production.
- [ ] Rotate `SECRET_KEY` via env var.
- [ ] Limit `ALLOWED_HOSTS` to your domain.
- [ ] Use SSL/TLS termination at load balancer.

---
**Standard Operating Procedure v2.0**
