# SOMAAGENT01 — OPERATIONS RUNBOOK

## Document Control

| Field | Value |
|-------|-------|
| Document Title | SomaAgent01 Operations Runbook |
| Document Identifier | SOMA-01-OPS-001 |
| Version | 1.0.0 |
| Date | 2026-06-15 |
| Status | Active |

---

## 1. QUICK REFERENCE

### 1.1 Service URLs

| Service | Standalone | AAAS | Health Check |
|---------|-----------|------|-------------|
| SomaAgent01 | http://localhost:20020 | http://localhost:63900 | GET /api/health/ |
| SomaBrain | — | http://localhost:63996 | GET /health |
| SomaFractalMemory | — | http://localhost:63901 | GET /healthz |
| Keycloak | http://localhost:20880 | http://localhost:63980 | GET /health/ready |
| Grafana | http://localhost:3000 | http://localhost:3000 | — |
| Prometheus | http://localhost:9090 | http://localhost:9090 | GET /-/healthy |

### 1.2 Emergency Contacts

| Role | Contact | When |
|------|---------|------|
| On-call Engineer | [PagerDuty] | Any incident |
| Engineering Lead | [Slack #soma-ops] | SEV-1, SEV-2 |
| Security Lead | [Slack #soma-security] | Security incidents |

---

## 2. COMMON OPERATIONS

### 2.1 Check System Health

```bash
# All services
curl -s http://localhost:63900/api/health/ | python -m json.tool
curl -s http://localhost:63996/health | python -m json.tool
curl -s http://localhost:63901/healthz | python -m json.tool

# Quick health check
make health
```

### 2.2 View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f somaagent
docker compose logs -f somabrain
docker compose logs -f somafractalmemory

# Last 100 lines
docker compose logs --tail 100 somaagent
```

### 2.3 Restart a Service

```bash
# Restart single service
docker compose restart somaagent

# Restart with fresh containers
docker compose up -d --force-recreate somaagent
```

### 2.4 Run Database Migrations

```bash
# Check pending migrations
docker compose exec somaagent python manage.py showmigrations --plan

# Apply migrations
docker compose exec somaagent python manage.py migrate

# Create superuser
docker compose exec somaagent python manage.py createsuperuser
```

### 2.5 Scale Services

```bash
# Docker Compose
docker compose up -d --scale somaagent=3

# K8s
kubectl scale deployment somaagent -n agent --replicas=5
```

---

## 3. MONITORING

### 3.1 Key Metrics

| Metric | Source | Alert Threshold |
|--------|--------|-----------------|
| Request latency (p95) | Prometheus | > 500ms for 5min |
| Error rate (5xx) | Prometheus | > 5% for 5min |
| Circuit breaker state | Prometheus | OPEN for 1min |
| WebSocket connections | Prometheus | > 1000 per instance |
| Memory usage | Prometheus | > 80% for 5min |
| CPU usage | Prometheus | > 70% for 5min |

### 3.2 Grafana Dashboards

| Dashboard | Purpose |
|-----------|---------|
| Soma Overview | Cross-service request flow, latency, error rates |
| Chat Pipeline | V3 orchestrator phase timings, token counts |
| Cognitive Load | Brain predictor accuracy, neuromodulator levels |
| Memory Operations | SFM store/recall latency, Milvus index stats |

### 3.3 Prometheus Alerts

| Alert | Severity | Description |
|-------|----------|-------------|
| SomaAgentDown | Critical | SomaAgent01 unreachable for 1min |
| SomaAgentHighLatency | Warning | p95 > 500ms for 5min |
| SomaAgentHighErrorRate | Warning | 5xx > 5% for 5min |
| SomaAgentCircuitBreakerOpen | Warning | Circuit breaker open for 1min |

---

## 4. TROUBLESHOOTING

### 4.1 Service Won't Start

```bash
# Check logs
docker compose logs somaagent

# Check environment
docker compose exec somaagent env | grep SA01_

# Check database connectivity
docker compose exec somaagent python manage.py dbshell

# Check Redis connectivity
docker compose exec somaagent python -c "import redis; r = redis.from_url('$SA01_REDIS_URL'); print(r.ping())"
```

### 4.2 High Latency

```bash
# Check circuit breakers
curl -s http://localhost:63900/api/v2/core/infrastructure/degradation/status

# Check SomaBrain
curl -s http://localhost:63996/health

# Check SFM
curl -s http://localhost:63901/healthz

# Check database
docker compose exec postgres pg_isready
```

### 4.3 Authentication Failures

```bash
# Check Keycloak
curl -s http://localhost:20880/health/ready

# Check JWT validation
curl -s http://localhost:63900/api/v2/auth/me -H "Authorization: Bearer $TOKEN"

# Check session in Redis
docker compose exec redis redis-cli KEYS "session:*"
```

### 4.4 Memory Integration Issues

```bash
# Check BrainBridge mode
docker compose exec somaagent python -c "
from services.common.deployment_mode import DeploymentMode
print(f'Mode: {DeploymentMode.get()}')
print(f'AAAS: {DeploymentMode.is_aaas()}')
"

# Check PendingMemory queue
docker compose exec somaagent python manage.py shell -c "
from admin.core.models import PendingMemory
print(f'Pending: {PendingMemory.objects.filter(synced=False).count()}')
"
```

---

## 5. MAINTENANCE

### 5.1 Certificate Renewal

```bash
# Check certificate expiry
openssl x509 -in /etc/haproxy/certs/cert.pem -noout -dates

# Renew with certbot
certbot renew --nginx
```

### 5.2 Database Maintenance

```bash
# Vacuum PostgreSQL
docker compose exec postgres vacuumdb -U somaagent -d somaagent -z

# Analyze tables
docker compose exec postgres analyze -U somaagent -d somaagent
```

### 5.3 Log Rotation

Logs are managed by Docker's json-file driver with rotation:
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

---

## 6. ROLLBACK PROCEDURE

```bash
# 1. Stop current version
docker compose down

# 2. Pull previous version
docker pull somatech/soma-agent:1.1.0

# 3. Update image tag in docker-compose.yml
# Change: image: somatech/soma-agent:2.0.0
# To:     image: somatech/soma-agent:1.1.0

# 4. Start previous version
docker compose up -d

# 5. Verify
curl http://localhost:63900/api/health/
```

---

End of Document
