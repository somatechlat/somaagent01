# Runbook: Data Ingest Service

## Service Overview
The data ingest service processes incoming messages and routes them through the conversation pipeline.

## Health Checks
```bash
# Check conversation worker health
docker ps | grep conversation-worker

# Check Kafka consumer group lag
docker exec -it kafka kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --describe --group conversation-worker
```

## Common Issues

### High Consumer Lag
**Symptoms**: Messages delayed, increasing lag metric

**Diagnosis**:
```bash
# Check consumer lag
docker exec kafka kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --describe --group conversation-worker

# Check worker logs
docker logs conversation-worker --tail 100
```

**Resolution**:
1. Scale worker instances
2. Check for slow LLM provider responses
3. Verify SomaBrain connectivity
4. Review message processing errors

### SomaBrain Connection Failures
**Symptoms**: Memory operations failing, recall timeouts

**Diagnosis**:
```bash
# Check SomaBrain health
curl http://localhost:9696/healthz

# Check worker logs for SomaBrain errors
docker logs conversation-worker | grep -i somabrain
```

**Resolution**:
1. Verify SomaBrain service is running
2. Check network connectivity
3. Review fail-safe buffer status
4. Restart worker if needed

## Monitoring Queries

### Prometheus Queries
```promql
# Message processing rate
rate(message_processing_total[5m])

# Processing errors
rate(message_processing_total{result="error"}[5m])

# SomaBrain call latency
histogram_quantile(0.95, rate(somabrain_request_duration_seconds_bucket[5m]))
```

## Backup and Recovery

### Manual Message Replay
```bash
# Export failed messages
docker exec postgres pg_dump -t failed_messages > failed_messages.sql

# Replay after fix
docker exec -i postgres psql < failed_messages.sql
```

## Escalation
Contact the platform team with:
- Consumer group lag metrics
- Worker service logs
- SomaBrain health status
- Recent configuration changes
