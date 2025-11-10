# Deployment Guide

![Version](https://img.shields.io/badge/version-1.0.0-blue)

## Deployment Options

### 1. Docker Compose (Development)

```bash
make dev-up
```

### 2. Kubernetes (Production)

Helm charts available in `infra/helm/`:

```bash
# Install infrastructure
helm install soma-infra infra/helm/soma-infra

# Install application
helm install soma-stack infra/helm/soma-stack
```

## Environment Configuration

### Required Variables

```bash
# Gateway
GATEWAY_PORT=21016
GATEWAY_ENC_KEY=<fernet-key>  # Generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
GATEWAY_INTERNAL_TOKEN=<secure-token>
GATEWAY_REQUIRE_AUTH=true

# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# Redis
REDIS_URL=redis://redis:6379/0

# PostgreSQL
POSTGRES_DSN=postgresql://soma:soma@postgres:5432/somaagent01

# SomaBrain
SOMA_BASE_URL=http://somabrain:9696
SOMA_TENANT_ID=production
SOMA_NAMESPACE=somabrain_ns:production

# OPA
OPA_URL=http://opa:8181

# Observability
GATEWAY_METRICS_PORT=8000
OTLP_ENDPOINT=http://otel-collector:4317
```

### Optional Variables

```bash
# Rate Limiting
GATEWAY_RATE_LIMIT_ENABLED=true
GATEWAY_RATE_LIMIT_WINDOW_SECONDS=60
GATEWAY_RATE_LIMIT_MAX_REQUESTS=120

# Feature Flags
SA01_ENABLE_CONTENT_MASKING=true
SA01_ENABLE_ERROR_CLASSIFIER=true
SA01_ENABLE_SEQUENCE=true
SA01_ENABLE_TOKEN_METRICS=true

# Write-Through
GATEWAY_WRITE_THROUGH=true
GATEWAY_WRITE_THROUGH_ASYNC=true
```

## Docker Compose Production

`docker-compose.prod.yaml`:

```yaml
services:
  gateway:
    image: somaagent01:latest
    environment:
      GATEWAY_REQUIRE_AUTH: "true"
      GATEWAY_ENC_KEY: ${GATEWAY_ENC_KEY}
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

## Kubernetes Deployment

### Namespace

```bash
kubectl create namespace somaagent01
```

### Secrets

```bash
kubectl create secret generic gateway-secrets \
  --from-literal=enc-key=${GATEWAY_ENC_KEY} \
  --from-literal=internal-token=${GATEWAY_INTERNAL_TOKEN} \
  -n somaagent01
```

### Deploy

```bash
kubectl apply -f infra/k8s/base/ -n somaagent01
```

## Health Checks

### Liveness Probe

```yaml
livenessProbe:
  httpGet:
    path: /live
    port: 8010
  initialDelaySeconds: 30
  periodSeconds: 10
```

### Readiness Probe

```yaml
readinessProbe:
  httpGet:
    path: /ready
    port: 8010
  initialDelaySeconds: 10
  periodSeconds: 5
```

## Scaling

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: gateway-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: gateway
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Monitoring

### Prometheus Scrape Config

```yaml
scrape_configs:
  - job_name: 'gateway'
    static_configs:
      - targets: ['gateway:8000']
  - job_name: 'conversation-worker'
    static_configs:
      - targets: ['conversation-worker:9410']
  - job_name: 'tool-executor'
    static_configs:
      - targets: ['tool-executor:9411']
```

### Grafana Dashboards

Import dashboards from `infra/observability/grafana/dashboards/`.

## Backup & Recovery

### PostgreSQL Backup

```bash
docker exec somaAgent01_postgres pg_dump -U soma somaagent01 > backup.sql
```

### Redis Backup

```bash
docker exec somaAgent01_redis redis-cli SAVE
docker cp somaAgent01_redis:/data/dump.rdb ./redis-backup.rdb
```

### Restore

```bash
# PostgreSQL
docker exec -i somaAgent01_postgres psql -U soma somaagent01 < backup.sql

# Redis
docker cp ./redis-backup.rdb somaAgent01_redis:/data/dump.rdb
docker restart somaAgent01_redis
```

## Security Hardening

### TLS/SSL

Configure reverse proxy (Nginx/Traefik) for TLS termination.

### Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: gateway-policy
spec:
  podSelector:
    matchLabels:
      app: gateway
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: ingress-controller
    ports:
    - protocol: TCP
      port: 8010
```

## Troubleshooting

### Gateway Not Starting

```bash
kubectl logs -f deployment/gateway -n somaagent01
```

### Kafka Connection Issues

```bash
kubectl exec -it deployment/gateway -n somaagent01 -- curl kafka:9092
```

### Database Connection

```bash
kubectl exec -it deployment/gateway -n somaagent01 -- \
  psql postgresql://soma:soma@postgres:5432/somaagent01
```

## Next Steps

- [Monitoring Guide](./monitoring.md)
- [Security Controls](./security.md)
- [Runbooks](./runbooks/)
