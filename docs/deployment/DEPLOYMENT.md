# 🚀 Deployment Guide

**Target Environment**: Docker / AWS ECS (Fargate) / EKS / EC2  
**Stack**: Django 5.0, PostgreSQL 16, Redis 7

---

## 1. Environment Variables
Configure these variables in your CI/CD pipeline or `.env` file. For software
deployment modes (Standalone vs SomaStackClusterMode), see
`docs/deployment/SOFTWARE_DEPLOYMENT_MODES.md`.

| Variable | Description | Required | Default |
| :--- | :--- | :--- | :--- |
| `SA01_DEPLOYMENT_MODE` | `PROD` or `DEV` | Yes | `DEV` |
| `SA01_DEPLOYMENT_TARGET` | `LOCAL`, `FARGATE`, `EKS`, `ECS_EC2`, `EC2`, `APP_RUNNER` | No | `LOCAL` |
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

**Local Resource Target (Testing like Production)**:
- Host memory budget: **15 GB** total across containers.

## 3. AWS Fargate Deployment (Primary)

**Target**: Production-aligned testing in AWS using ECS Fargate.

**Minimum Task Resources (per service)**:
- Memory: **16 GB**
- Disk: **30 GB**

**Notes**:
- Use an ALB for HTTP + WebSocket traffic to the gateway service.
- Use managed services for Postgres (RDS), Redis (ElastiCache), Kafka (MSK), and S3 storage.
- Store secrets in AWS Secrets Manager or SSM.

## 4. Database Migrations (Resilient)
**CRITICAL**: Migrations are the "Beat" of the system.

### Local Development (Tilt)
Tilt uses the **"Perfect Startup"** protocol to automate this.
- **Resource**: `database-migrations`
- **Mode**: `SA01_DEPLOYMENT_MODE=PROD` (Enforced)
- **Sequence**: Memory → Brain → Agent (Strict Order)
- **Constraint**: Application services **WILL NOT START** until this resource completes successfully.

### Production (Manual/CI)
Run migrations explicitly before rolling updates:
```bash
# Run migrations via the Gateway service
docker-compose exec gateway python manage.py migrate
```

## 5. Health Checks
- **Combined Health**: `http://localhost:8010/health`
- **Metrics**: `http://localhost:8010/metrics`

## 6. Security Checklist
- [ ] Ensure `DEBUG=False` in production.
- [ ] Rotate `SECRET_KEY` via env var.
- [ ] Limit `ALLOWED_HOSTS` to your domain.
- [ ] Use SSL/TLS termination at load balancer.

---
**Standard Operating Procedure v2.0**
