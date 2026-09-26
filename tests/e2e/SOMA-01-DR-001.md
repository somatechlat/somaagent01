# SOMAAGENT01 — DISASTER RECOVERY PROCEDURES

## Document Control

| Field | Value |
|-------|-------|
| Document Title | Disaster Recovery Procedures |
| Document Identifier | SOMA-01-DR-001 |
| Version | 1.0.0 |
| Date | 2026-06-15 |
| Status | Active |

---

## 1. RECOVERY OBJECTIVES

| Metric | Target | Notes |
|--------|--------|-------|
| RPO (Recovery Point Objective) | 1 hour | Maximum data loss |
| RTO (Recovery Time Objective) | 4 hours | Maximum downtime |
| MTTR (Mean Time To Recover) | 2 hours | Average recovery time |

---

## 2. BACKUP SCHEDULE

| Component | Method | Frequency | Retention | Storage |
|-----------|--------|-----------|-----------|---------|
| PostgreSQL | pg_dump + WAL archiving | Hourly incremental, daily full | 30 days | S3/MinIO |
| Redis | RDB snapshot + AOF | Every 5 minutes | 7 days | Local + S3 |
| Kafka | Topic replication (factor=3) | Continuous | 7 days | Kafka cluster |
| Milvus | Milvus backup tool | Daily | 30 days | S3/MinIO |
| Vault | Vault snapshot | Daily | 90 days | Secure storage |
| Config files | Git | Every change | Forever | GitHub |
| Docker images | Registry push | Every build | 30 days | GHCR/DockerHub |

---

## 3. SCENARIO 1: DATABASE FAILURE

### Detection
- Health check endpoint returns `database: unhealthy`
- Prometheus alert: `SomaAgentDown` fires
- Grafana dashboard shows DB connection errors

### Recovery Steps
```bash
# 1. Assess damage
pg_isready -h postgres -p 5432

# 2. If PostgreSQL is down, restart
docker compose restart postgres

# 3. If data corruption, restore from backup
pg_restore -h postgres -U somaagent -d somaagent latest_backup.dump

# 4. Verify data integrity
docker compose exec somaagent python manage.py check
docker compose exec somaagent python manage.py migrate --check

# 5. Restart application
docker compose restart somaagent

# 6. Verify health
curl http://localhost:63900/api/health/
```

### Data Loss Assessment
- Check WAL archive for transactions since last backup
- Compare `pg_stat_activity` with monitoring timestamps
- Document any lost transactions in incident report

---

## 4. SCENARIO 2: REDIS FAILURE

### Detection
- Rate limiter returns `allowed: false` for all requests (fail-closed)
- Session validation fails
- Health check shows `redis: unhealthy`

### Recovery Steps
```bash
# 1. Restart Redis
docker compose restart redis

# 2. If data loss acceptable, clear and restart
docker compose exec redis redis-cli FLUSHDB
docker compose restart somaagent

# 3. If RDB backup exists, restore
docker compose stop redis
cp /backup/dump.rdb /data/dump.rdb
docker compose start redis

# 4. Verify
docker compose exec redis redis-cli PING
```

### Impact
- Active sessions lost → users must re-login
- Rate limit counters reset → temporary unlimited access (mitigated by fail-closed)
- Circuit breaker states lost → default to CLOSED

---

## 5. SCENARIO 3: SOMABRAIN FAILURE

### Detection
- Health monitor shows `somabrain: unhealthy`
- Circuit breaker opens after 5 failures
- Degradation monitor shows MODERATE degradation

### Recovery Steps
```bash
# 1. Check SomaBrain status
curl http://somabrain:63996/health

# 2. Restart if unresponsive
docker compose restart somabrain

# 3. Verify memory recall works
curl -X POST http://somabrain:63996/api/v1/memory/recall \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "top_k": 1}'

# 4. Check PendingMemory queue for missed writes
docker compose exec somaagent python manage.py shell -c "
from admin.core.models import PendingMemory
print(f'Pending: {PendingMemory.objects.filter(synced=False).count()}')
"
```

### Fallback Behavior (Automatic)
- Memory recall: Falls back to SomaFractalMemory
- Memory store: Queued to PendingMemory for later sync
- Context evaluation: Skipped (default confidence 0.5)
- Chat: Continues without cognitive memory

---

## 6. SCENARIO 4: SOMAFRACTALMEMORY FAILURE

### Detection
- Health check shows `sfm: unhealthy`
- SFM adapter raises connection errors

### Recovery Steps
```bash
# 1. Check SFM status
curl http://somafractalmemory:63901/healthz

# 2. Restart
docker compose restart somafractalmemory

# 3. Verify vector store
curl http://somafractalmemory:63901/healthz
# Expected: {"kv_store": true, "vector_store": true, "graph_store": true}
```

### Fallback Behavior (Automatic)
- Memory store: Queued to PendingMemory
- Memory recall: Returns empty (no fallback below SFM)
- Chat: Continues without vector memory

---

## 7. SCENARIO 5: KEYCLOAK FAILURE

### Detection
- Login attempts fail
- Token refresh fails
- Health check shows `keycloak: unhealthy`

### Recovery Steps
```bash
# 1. Check Keycloak status
curl http://keycloak:8080/health/ready

# 2. Restart
docker compose restart keycloak

# 3. Wait for Keycloak to be ready (may take 2-3 minutes)
sleep 180

# 4. Verify realm exists
curl http://keycloak:8080/realms/somaagent/.well-known/openid-configuration
```

### Impact
- New logins blocked until Keycloak recovers
- Existing JWT tokens remain valid until expiry (15 minutes)
- Refresh tokens fail → users must re-login after access token expires

---

## 8. SCENARIO 6: FULL STACK FAILURE

### Recovery Steps
```bash
# 1. Stop everything
docker compose down

# 2. Restore databases from backup
# (Follow Scenario 1 + Scenario 2 procedures)

# 3. Start infrastructure first
docker compose up -d postgres redis keycloak vault

# 4. Wait for infrastructure health
sleep 60

# 5. Run migrations
docker compose exec somaagent python manage.py migrate

# 6. Start application services
docker compose up -d

# 7. Verify full stack
curl http://localhost:63900/api/health/
curl http://localhost:63996/health
curl http://localhost:63901/healthz
```

---

## 9. INCIDENT RESPONSE

### Severity Levels

| Level | Definition | Response Time | Escalation |
|-------|-----------|---------------|------------|
| SEV-1 | Full outage, data loss | 15 minutes | Engineering Director + CTO |
| SEV-2 | Partial outage, degraded | 1 hour | Engineering Lead |
| SEV-3 | Single component down | 4 hours | On-call engineer |
| SEV-4 | Non-critical issue | Next business day | Team |

### Communication Template
```
INCIDENT: [SEV-X] Brief description
STATUS: [INVESTIGATING / IDENTIFIED / MONITORING / RESOLVED]
IMPACT: [What is affected]
START TIME: [YYYY-MM-DD HH:MM UTC]
ETA: [Estimated resolution time]
UPDATE: [Next update in N minutes]
```

---

End of Document
