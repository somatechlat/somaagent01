# Runbook: Propagation Service

## Service Overview
The propagation service handles real-time event distribution across the SomaAgent01 platform.

## Health Checks
```bash
# Check service health
curl -f http://localhost:21016/v1/health

# Check SSE endpoint
curl -N http://localhost:21016/v1/sessions/test-session/events?stream=true
```

## Common Issues

### SSE Connection Drops
**Symptoms**: Clients report disconnections, heartbeat failures

**Diagnosis**:
```bash
# Check active connections
curl http://localhost:8000/metrics | grep gateway_sse_connections

# Check error logs
docker logs gateway | grep -i "sse\|stream"
```

**Resolution**:
1. Verify network stability
2. Check `SSE_HEARTBEAT_SECONDS` configuration
3. Review client reconnection logic
4. Restart gateway if needed: `make dev-restart`

### High Latency
**Symptoms**: Slow message delivery, increased p95 latency

**Diagnosis**:
```bash
# Check message duration metrics
curl http://localhost:8000/metrics | grep sse_message_duration_seconds
```

**Resolution**:
1. Check Kafka consumer lag
2. Verify Redis connectivity
3. Review Gateway resource usage
4. Scale horizontally if needed

## Monitoring Queries

### Prometheus Queries
```promql
# Active SSE connections
gateway_sse_connections

# Message send rate
rate(sse_messages_sent_total[5m])

# p95 message latency
histogram_quantile(0.95, rate(sse_message_duration_seconds_bucket[5m]))
```

## Escalation
For persistent issues, contact the platform team with:
- Service logs from the last 30 minutes
- Prometheus metrics screenshots
- Client-side error details
