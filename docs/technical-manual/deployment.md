# Deployment Guide

**Standards**: ISO/IEC 12207§6.4

## Deployment Modes

### DEV (Local Development)

**Purpose**: Local development and testing

**Configuration**:
```bash
# .env
DEPLOYMENT_MODE=DEV
AUTH_ENABLED=false
OPENROUTER_API_KEY=<your-key>
```

**Start**:
```bash
make deps-up
make stack-up
make ui
```

### STAGING (Pre-Production)

**Purpose**: Integration testing, QA validation

**Configuration**:
```bash
# .env
DEPLOYMENT_MODE=STAGING
AUTH_ENABLED=true
JWT_SECRET=<random-256-bit-key>
GATEWAY_MANAGED_CREDENTIALS=true
```

**Deploy**:
```bash
# Recommended: Kubernetes (staging overlay)
kubectl apply -k infra/k8s/overlays/staging/

# Or: Docker Compose using the base manifest with env overrides
# (No dedicated staging compose file is provided.)
docker compose up -d
```

### PROD (Production)

**Purpose**: Live production environment

**Configuration**:
```bash
# .env (use secrets manager in production)
DEPLOYMENT_MODE=PROD
AUTH_ENABLED=true
JWT_SECRET=<vault://secret/jwt-secret>
OPENROUTER_API_KEY=<vault://secret/openrouter-key>
TLS_ENABLED=true
```

**Deploy**:
```bash
# Using Helm
helm upgrade --install soma-stack infra/helm/soma-stack/ \
  --namespace production \
  --values infra/helm/overlays/prod/values.yaml

# Verify
kubectl get pods -n production
kubectl logs -n production deployment/gateway
```

## Infrastructure Requirements

### Minimum Resources

| Component | CPU | Memory | Storage |
|-----------|-----|--------|---------|
| Gateway | 0.5 | 512MB | - |
| Conversation Worker | 1.0 | 1GB | - |
| Tool Executor | 0.5 | 512MB | - |
| Kafka | 1.0 | 2GB | 10GB |
| PostgreSQL | 1.0 | 2GB | 20GB |
| Redis | 0.5 | 512MB | 1GB |

### Recommended Resources (Production)

| Component | CPU | Memory | Storage | Replicas |
|-----------|-----|--------|---------|----------|
| Gateway | 2.0 | 2GB | - | 3 |
| Conversation Worker | 2.0 | 4GB | - | 5 |
| Tool Executor | 1.0 | 2GB | - | 3 |
| Kafka | 4.0 | 8GB | 100GB | 3 |
| PostgreSQL | 4.0 | 8GB | 200GB | 1 (with replicas) |
| Redis | 2.0 | 4GB | 10GB | 1 (with sentinel) |

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `DEPLOYMENT_MODE` | Deployment environment | `DEV`, `STAGING`, `PROD` |
| `OPENROUTER_API_KEY` | LLM provider API key | `sk-or-v1-...` |
| `AUTH_PASSWORD` | UI authentication password | `<strong-password>` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `<random-password>` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `GATEWAY_PORT` | Gateway HTTP port | `21016` |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka brokers | `localhost:20000` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:20001` |
| `SOMABRAIN_BASE_URL` | Memory service URL | `http://localhost:9696` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Docker Compose Deployment

### Single-Node Setup

```bash
# 1. Configure environment
cp .env.example .env
nano .env

# 2. Start stack
docker compose up -d

# 3. Verify
docker compose ps
curl http://localhost:${GATEWAY_PORT:-21016}/v1/health
```

### Multi-Node Setup

```bash
# 1. Start infrastructure on node1
docker compose -f infra/docker/shared-infra.compose.yaml up -d

# 2. Start services on node2, node3
export KAFKA_BOOTSTRAP_SERVERS=node1:20000
export POSTGRES_HOST=node1
export REDIS_URL=redis://node1:20001

docker compose up -d gateway conversation-worker tool-executor
```

## Kubernetes Deployment

### Prerequisites

- Kubernetes 1.24+
- Helm 3.10+
- kubectl configured

### Deploy with Helm

```bash
# 1. Add Helm repository (if external)
helm repo add soma https://charts.somaagent01.ai
helm repo update

# 2. Create namespace
kubectl create namespace somaagent01

# 3. Install
helm install soma-stack infra/helm/soma-stack/ \
  --namespace somaagent01 \
  --values infra/helm/overlays/prod/values.yaml

# 4. Verify
kubectl get pods -n somaagent01
kubectl get svc -n somaagent01
```

### Deploy with Kustomize

```bash
# 1. Apply base + overlay
kubectl apply -k infra/k8s/overlays/prod/

# 2. Verify
kubectl get all -n somaagent01

# 3. Check logs
kubectl logs -n somaagent01 deployment/gateway -f
```

## Monitoring Setup

### Prometheus

```bash
# Deploy Prometheus
kubectl apply -f infra/observability/prometheus.yml

# Verify scrape targets
kubectl port-forward -n monitoring svc/prometheus 9090:9090
# Visit http://localhost:9090/targets
```

### Grafana

```bash
# Deploy Grafana (external)
# Import dashboards from observability project
# Point at Prometheus: http://prometheus.monitoring.svc:9090
```

### Alertmanager

```bash
# Deploy Alertmanager
kubectl apply -f infra/observability/alertmanager.yml

# Configure alerts
kubectl apply -f infra/observability/alerts.yml
```

## Backup and Recovery

### PostgreSQL Backup

```bash
# Manual backup
docker compose exec postgres pg_dump -U somauser somadb > backup.sql

# Automated backup (cron)
0 2 * * * docker compose exec postgres pg_dump -U somauser somadb | gzip > /backups/somadb-$(date +\%Y\%m\%d).sql.gz
```

### Restore

```bash
# Restore from backup
docker compose exec -T postgres psql -U somauser somadb < backup.sql
```

### Kafka Topic Backup

```bash
# Export topic data
docker compose exec kafka kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic conversation.inbound \
  --from-beginning \
  --max-messages 10000 > topic-backup.json
```

## Security Hardening

### TLS Configuration

```yaml
# docker-compose.yaml
services:
  gateway:
    environment:
      - TLS_ENABLED=true
      - TLS_CERT_PATH=/certs/server.crt
      - TLS_KEY_PATH=/certs/server.key
    volumes:
      - ./certs:/certs:ro
```

### Network Isolation

```yaml
# docker-compose.yaml
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true

services:
  gateway:
    networks:
      - frontend
      - backend
  postgres:
    networks:
      - backend
```

### Secrets Management

```bash
# Using Docker secrets
echo "my-secret-key" | docker secret create jwt_secret -

# Reference in compose
services:
  gateway:
    secrets:
      - jwt_secret
    environment:
      - JWT_SECRET_FILE=/run/secrets/jwt_secret
```

## Scaling

### Horizontal Scaling

```bash
# Scale conversation workers
docker compose up -d --scale conversation-worker=5

# Kubernetes
kubectl scale deployment conversation-worker --replicas=5 -n somaagent01
```

### Vertical Scaling

```yaml
# docker-compose.yaml
services:
  conversation-worker:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

## Health Checks

### Liveness Probes

```yaml
# Kubernetes
livenessProbe:
  httpGet:
    path: /v1/health
    port: 21016
  initialDelaySeconds: 30
  periodSeconds: 10
```

### Readiness Probes

```yaml
readinessProbe:
  httpGet:
    path: /v1/ready
    port: 21016
  initialDelaySeconds: 10
  periodSeconds: 5
```

## Rollback Procedures

### Docker Compose

```bash
# Rollback to previous version
docker compose down
git checkout <previous-tag>
docker compose up -d
```

### Kubernetes

```bash
# Rollback deployment
kubectl rollout undo deployment/gateway -n somaagent01

# Check rollout status
kubectl rollout status deployment/gateway -n somaagent01
```

### Helm

```bash
# Rollback release
helm rollback soma-stack -n somaagent01

# Rollback to specific revision
helm rollback soma-stack 3 -n somaagent01
```
