# Troubleshooting Guide

**Standards**: ISO/IEC 21500§7.4

## Common Issues

### Gateway Health Check Fails

**Symptom**: `curl http://localhost:21016/v1/health` returns error

**Diagnosis**:
```bash
# Check if gateway is running
docker compose ps gateway

# Check logs
docker compose logs gateway --tail=50
```

**Solutions**:

| Cause | Fix |
|-------|-----|
| Kafka not ready | Wait 30s, retry. Check `docker compose logs kafka` |
| PostgreSQL connection failed | Verify `docker compose ps postgres`, check credentials in `.env` |
| Port 20016 in use | `lsof -i :20016`, kill conflicting process |

### Conversation Worker Not Processing Messages

**Symptom**: Messages sent but no response

**Diagnosis**:
```bash
# Check worker logs
docker compose logs conversation-worker --tail=100

# Check Kafka topic lag
docker compose exec kafka kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --group conversation-worker-group \
  --describe
```

**Solutions**:

| Cause | Fix |
|-------|-----|
| Worker crashed | `docker compose restart conversation-worker` |
| LLM credentials missing/invalid | Open Settings → LLM Credentials, set the provider (e.g., groq) and paste the key. Alternatively, POST `/v1/llm/credentials`. |
| Kafka consumer lag | Scale workers: `docker compose up -d --scale conversation-worker=3` |

### Memory Not Persisting

**Symptom**: Agent forgets information between sessions

**Diagnosis**:
```bash
# Check SomaBrain health
curl http://localhost:9696/health

# Check memory replicator logs
docker compose logs memory-replicator --tail=50

# Check PostgreSQL memory_replica table
docker compose exec postgres psql -U somauser -d somadb \
  -c "SELECT COUNT(*) FROM memory_replica;"
```

**Solutions**:

| Cause | Fix |
|-------|-----|
| SomaBrain not running | Start: `docker compose up -d somabrain` |
| Memory replicator failed | Check logs, restart: `docker compose restart memory-replicator` |
| PostgreSQL disk full | Free space, increase volume size |

### UI Not Loading

**Symptom**: Browser shows blank page or connection error

**Diagnosis**:
```bash
# Check UI service
docker compose ps ui

# Check UI logs
docker compose logs ui --tail=50

# Check browser console (F12)
```

**Solutions**:

| Cause | Fix |
|-------|-----|
| UI service not running | `docker compose up -d ui` |
| Gateway not accessible | Verify gateway health, check network |
| Browser cache issue | Hard refresh (Ctrl+Shift+R), clear cache |
| CORS error | Check `CORS_ORIGINS` in `.env` |

### High CPU Usage

**Symptom**: System slow, high CPU in `docker stats`

**Diagnosis**:
```bash
# Check resource usage
docker stats --no-stream

# Check which service is consuming CPU
docker compose top
```

**Solutions**:

| Cause | Fix |
|-------|-----|
| Kafka rebalancing | Wait for stabilization (2-5 minutes) |
| LLM streaming | Normal during response generation |
| Memory leak | Restart affected service |
| Too many workers | Reduce scale: `docker compose up -d --scale conversation-worker=1` |

### Database Connection Pool Exhausted

**Symptom**: `asyncpg.exceptions.TooManyConnectionsError`

**Diagnosis**:
```bash
# Check active connections
docker compose exec postgres psql -U somauser -d somadb \
  -c "SELECT COUNT(*) FROM pg_stat_activity;"
```

**Solutions**:

| Cause | Fix |
|-------|-----|
| Connection leak | Restart services: `docker compose restart` |
| Too many workers | Reduce worker count or increase `max_connections` in PostgreSQL |
| Long-running queries | Check `pg_stat_activity`, kill slow queries |

## Diagnostic Commands

### Full System Health Check

```bash
# Quick health probes
curl -sS -D - http://localhost:21016/v1/health -o /dev/null | head -n 1
curl -sS http://localhost:21016/v1/ui/settings | jq .
curl -sS http://localhost:21016/v1/ui/settings/credentials | jq .

# Expected output:
# ✅ Kafka: healthy
# ✅ Redis: healthy
# ✅ PostgreSQL: healthy
# ✅ OPA: healthy
# ✅ Gateway: healthy
# ✅ SomaBrain: healthy
```

### View All Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f gateway

# Last 100 lines
docker compose logs --tail=100 conversation-worker
```

### Reset Everything

```bash
# Nuclear option: delete all data and restart
docker compose down -v
docker system prune -f
make dev-up

## LLM Issues (401/405)

### 401 Unauthorized during chat

Symptoms:
- Gateway audit shows `llm.invoke` with `http_status=401` and provider `groq`/`openrouter`.

Fix:
- Open the Settings modal → LLM Credentials and re‑enter the provider key.
- Ensure the selected model is accessible by your key.
- Verify with:
  ```bash
  curl -s -X POST http://localhost:21016/v1/llm/test -H 'Content-Type: application/json' -d '{"role":"dialogue"}' | jq .
  ```

### 405 Method Not Allowed (OpenRouter)

Symptoms:
- Audit shows provider `openrouter` with `http_status=405`.

Cause:
- Base URL saved as `https://openrouter.ai/openai`, which is not compatible when composing `/v1/chat/completions`.

Fix:
- Save Settings again; the Gateway normalizes `/openai` → `/api`.
- Confirm the effective profile:
  ```bash
  curl -s http://localhost:21016/v1/ui/settings | jq .
  ```
```

## Getting Help

If issues persist:

1. **Collect diagnostics**:
   ```bash
   docker compose logs > logs.txt
   docker compose ps > services.txt
   docker stats --no-stream > stats.txt
   ```

2. **Open GitHub issue**: https://github.com/somatechlat/somaagent01/issues

3. **Include**:
   - Steps to reproduce
   - Error messages
   - Log files
   - Environment (OS, Docker version)

4. **Join Discord**: https://discord.gg/B8KZKNsPpj
