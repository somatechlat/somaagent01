# 🚀 Deployment Guide

**Target Environment**: Docker / AWS ECS (Fargate) / EKS / EC2  
**Stack**: Django 5.0, PostgreSQL 16, Redis 7

---

## 1. Port Namespace Strategy

SomaStack uses defined port namespaces for all services to enable local development and production deployments.

| Service | Namespace | Port Range | Notes |
|----------|-----------|------------|-------|
| **SomaAgent01 (Control Plane)** | 20xxx | 20020-20199 | Main API, admin, gateway |
| **SomaBrain (Cognitive)** | 30xxx | 30000-30199 | Cognitive services, embeddings |
| **SomaFractalMemory**, 50xxx, 6379, 9092 | Various | Vector DB, cache, messaging |

### 1.1 Critical Port Mappings

| Service/API | Port | Container | Purpose |
|-------------|------|-----------|---------|
| Gateway | 20020 | gateway | Main entry point, WebSocket traffic |
| Admin API | 20042 | admin | Django Ninja admin APIs |
| Keycloak (Auth) | 20880 | keycloak | OIDC authentication (port 20880) |
| SpiceDB (Authorization) | 20051 | spicedb | Zanzibar-style permissions |
| OPA (Policy Engine) | 20181 | opa | Open Policy Agent |
| SomaBrain API | 30101 | brain | Cognitive services |
| SomaFractalMemory API | 10101 | memory | Memory/vector services |
| Milvus (Vector DB) | 19530 | milvus | Vector embeddings storage |
| PostgreSQL | 5432 | postgres | Primary database |
| Redis | 6379 | redis | Cache, session storage |
| Kafka | 9092 | kafka | Event streaming, message bus |

### 1.2 Infrastructure Ports (External)

| Service | Port | Purpose |
|---------|------|---------|
| MinIO (S3-compatible) | 9000 | Object storage, file uploads |
| MinIO Console | 9001 | Web UI for MinIO |
| Grafana | 49100 | Metrics dashboards |
| Prometheus | 49090 | Metrics collection |
| Jaeger | 49431 | Distributed tracing |
| Temporal UI | 49823 | Workflow management |

---

## 2. Environment Variables

Configure these variables in your CI/CD pipeline or `.env` file. For software
deployment modes (Standalone vs SomaStackClusterMode), see
`docs/deployment/SOFTWARE_DEPLOYMENT_MODES.md`.

### 2.1 Core Deployment Variables

| Variable | Description | Required | Default |
| :--- | :--- | :--- | :--- |
| `SA01_DEPLOYMENT_MODE` | `PROD` or `DEV` | Yes | `DEV` |
| `SA01_DEPLOYMENT_TARGET` | `LOCAL`, `FARGATE`, `EKS`, `ECS_EC2`, `EC2`, `APP_RUNNER` | No | `LOCAL` |
| `SOMA_SAAS_MODE` | In-process coupling: `true` or `false` | No | `false` |
| `SOMASTACK_SOFTWARE_MODE` | `StandAlone` or `SomaStackClusterMode` | No | `StandAlone` |

### 2.2 Database Variables

| Variable | Description | Required | Default |
| :--- | :--- | :--- | :--- |
| `SA01_DB_DSN` | Postgres Connection String | Yes | `postgresql://user:pass@host:5432/db` |
| `SA01_REDIS_URL` | Redis URL | Yes | `redis://host:6379/0` |
| `SA01_DB_HOST` | PostgreSQL host | No | `postgres` |
| `SA01_DB_PORT` | PostgreSQL port | No | `5432` |
| `SA01_DB_NAME` | Database name | No | `somaagent01` |
| `SA01_DB_USER` | Database user | No | `soma` |
| `SA01_DB_PASSWORD` | Database password | Yes | - |

### 2.3 Authentication & Authorization

| Variable | Description | Required | Default |
| :--- | :--- | :--- | :--- |
| `KEYCLOAK_URL` | Keycloak server URL | Yes | `http://keycloak:20880` |
| `KEYCLOAK_REALM` | Keycloak realm name | Yes | `somastack` |
| `KEYCLOAK_CLIENT_ID` | OIDC client ID | Yes | `soma-agent` |
| `SPICEDB_URL` | SpiceDB server URL | Yes | `http://spicedb:20051` |
| `SPICEDB_API_KEY` | SpiceDB API key | Yes | - |
| `OPA_URL` | OPA policy server URL | Yes | `http://opa:20181` |

### 2.4 SaaS Integration Variables

| Variable | Description | Required | Default |
| :--- | :--- | :--- | :--- |
| `SAAS_DEFAULT_CHAT_MODEL` | Default LLM Model | Yes | `openai/gpt-4.1` |
| `SA01_CHAT_PROVIDER` | Chat model provider (openrouter/openai) | No | `openrouter` (code default) |
| `OPENAI_API_KEY` | OpenAI API key | Yes | - |
| `ANTHROPIC_API_KEY` | Anthropic API key | No | - |
| `LAGO_API_URL` | Billing (Lago) API URL | No | `http://lago:3000` |
| `LAGO_API_KEY` | Lago API key | No | - |
| `SMTP_HOST` | Email server host | No | `smtp.sendgrid.net` |
| `SMTP_PORT` | Email server port | No | `587` |
| `SMTP_USER` | Email username | No | - |
| `SMTP_PASSWORD` | Email password | No | - |

### 2.5 Cross-Service Variables (SomaStackClusterMode)

| Variable | Description | Required | Default |
| :--- | :--- | :--- | :--- |
| `SOMABRAIN_API_URL` | SomaBrain API URL | No | `http://somabrain:30101` |
| `SOMAMEMORY_API_URL` | SomaFractalMemory API URL | No | `http://somafractalmemory:10101` |
| `SOMA_MEMORY_API_TOKEN`, SomaFractalMemory API requires auth token | No | - |
| `MILVUS_HOST` | Milvus vector DB host | No | `milvus` |
| `MILVUS_PORT` | Milvus vector DB port | No | `19530` |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka brokers | No | `kafka:9092` |

### 2.6 Feature Flags

| Variable | Description | Required | Default |
| :--- | :--- | :--- | :--- |
| `MEMORY_ENABLED` | Enable Memory service | No | `true` |
| `VOICE_ENABLED` | Enable Voice services | No | `false` |
| `MCP_ENABLED` | Enable MCP servers | No | `true` |
| `CODE_EXECUTION_ENABLED` | Enable code execution | No | `false` |

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

## 3. Deployment Modes

### 3.1 Local Development (Docker Compose)

**Target**: Local development and testing.

**Prerequisites**:
- Docker 24+, Docker Compose 2.24+
- 16GB+ RAM available
- 50GB+ disk space

**Services Running**:
- Gateway (port 20020)
- Admin API (port 20042)
- Keycloak (port 20880)
- PostgreSQL (port 5432)
- Redis (port 6379)
- SpiceDB (port 20051)
- OPA (port 20181)
- SomaBrain (port 30101) - optional
- SomaFractalMemory (port 10101) - optional

**Startup**:
```bash
docker-compose up -d
```

### 3.2 AWS Fargate Deployment (Primary Production)

**Target**: Production-aligned testing in AWS using ECS Fargate.

**Minimum Task Resources (per service)**:
- CPU: **4 vCPU**
- Memory: **16 GB**
- Disk: **30 GB**

**Infrastructure**:
- Application Load Balancer (ALB) for HTTP + WebSocket traffic
- RDS PostgreSQL (Multi-AZ, pg16)
- ElastiCache Redis (cluster mode)
- MSK Kafka (3 brokers)
- S3 for file storage
- Secrets Manager for secrets

**Deployment Flow**:
1. Build and push Docker images to ECR
2. Create ECS task definitions with resource limits
3. Deploy services using ECS blue-green deployments
4. Configure ALB target groups with health checks

### 3.3 AWS EKS Deployment (Advanced)

**Target**: Full Kubernetes orchestration with advanced networking.

**Prerequisites**:
- EKS cluster (1.28+)
- AWS Load Balancer Controller installed
- Cert-Manager for TLS certificates
- External DNS for automated DNS management

**Infrastructure**:
- Ingress Controller (AWS Load Balancer Controller)
- Certified Kubernetes Operator integration
- Vertical Pod Autoscaler
- Horizontal Pod Autoscaler

**Deployment Flow**:
1. Apply Kubernetes manifests via Helm charts
2. Wait for pods to become ready and healthy
3. Verify external endpoints and health checks
4. Configurations and secrets managed securely
5. Resource utilization optimized with auto-scaling

**Kubernetes Operations**:
- Rollback and configuration management
- Monitoring and performance tracking
- Namespace and ingress configuration
- Persistent volume strategy for storage

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
