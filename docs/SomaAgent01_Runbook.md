# SomaAgent 01 Operations Runbook

This runbook summarises day-2 operations for the core SomaAgent services across development and production environments.

## Common Services

| Service | Responsibility | Health Indicators |
|---------|----------------|-------------------|
| Gateway (`run_ui.py` / FastAPI) | Accept user/API traffic, publish chat events, expose `/health` | Prometheus `up` metric, `/health` endpoint, HTTP 200s |
| Conversation Worker | Consume chat events, call SLM, emit telemetry | Prometheus `telemetry_worker_events_total`, Kafka consumer lag |
| Telemetry Worker | Persist metrics to Postgres, expose `/metrics` | Prometheus scrape success, `telemetry_worker_failures_total` should remain 0 |
| Delegation Gateway | Accept task submissions, push to Kafka, record metadata | `/v1/delegation/task` 200s, Postgres `delegation_tasks` row growth |
| Delegation Worker | Consume delegation topic and persist tasks | Kafka consumer lag, logs showing task receipts |
| Redis | Session cache | Redis `ping` success, low memory usage |
| Postgres | Session/delegation store | `pg_is_in_recovery()` false, disk utilisation |
| Kafka | Event backbone | Consumer lag dashboards, broker uptime |
| Alertmanager | Route Prometheus alerts to downstream systems | `/-/healthy` readiness, Alertmanager UI shows active alerts |

## Incident Response Cheatsheet

| Scenario | Symptoms | First Actions | Follow-up |
|----------|----------|--------------|-----------|
| Telemetry worker offline | `/health` degraded, Prometheus alert `TelemetryWorkerDown` | `docker compose restart delegation-worker` (local) or `kubectl rollout restart deploy/telemetry-worker` | Review worker logs, ensure Postgres reachable |
| Kafka outage | Agents stall, `/health` reports Kafka down | Restart Kafka container/pod; ensure topic persistence | Replay missed events once broker stable |
| Budget hard-stop | Users receive “Token budget exceeded” immediately | Inspect `conf/tenants.yaml` for budget overrides | Adjust limits and redeploy, confirm Redis counters reset |
| Delegation backlog | `delegation_tasks` status stuck in `queued` | Confirm worker running; check downstream processors | Manually replay tasks via `UPDATE` or re-enqueue |
| Canvas disconnects | UI canvas badge turns amber | Check `/v1/canvas/{session}/stream` connectivity | Restart canvas service, refresh UI |
| Circuit breaker openings | Prometheus `CircuitBreakerOpenEvents` alert, gateway logs show `CircuitOpenError` | Inspect upstream service health, confirm breaker counters settle | Once mitigated, silence or expire the alert; capture RCA in incident log |
| SomaClient event-loop binding error | Gateway or worker logs show `RuntimeError: Event loop is closed` or `Event bound to a different loop`; outbound memory calls stall | Rebuild the shared image `docker compose -f infra/docker-compose.somaagent01.yaml build delegation-gateway delegation-worker agent-ui` and redeploy the trio; ensure `.venv` pulls the patched `SomaClient` | Run the multi-loop probe:<br>`source .venv/bin/activate && python scripts/checks/somaclient_event_loop.py` (prints `ok`) and watch container logs for healthy memory calls |

## Deployment Playbook

1. Confirm `/health` is green.
2. Scale new deployment (docker compose up / kustomize apply).
3. Monitor Prometheus alerts and `/health` for 5 minutes.
4. Run smoke test: `python scripts/send_message.py "Ping"` and verify response.
5. Validate telemetry by checking Prometheus target status.

## Security Hooks

- Rotate secrets (`VAULT_DEV_ROOT_TOKEN_ID`, Kafka SASL creds) via environment variables or Kubernetes Secrets.
- Update tenant governance in `conf/tenants.yaml`; production changes require approval and redeploy.
- Ensure OPA and OpenFGA endpoints are reachable before relaxing fail-open.

## Useful Commands

```bash
# Inspect delegation tasks
psql $POSTGRES_DSN -c "SELECT task_id,status,updated_at FROM delegation_tasks ORDER BY updated_at DESC LIMIT 10;"

# Replay pending requeue entries via API
echo '{"allow": true}' | http POST http://localhost:8012/v1/requeue/<id>/resolve

# Run Prometheus in docker-compose and view alerts
open http://localhost:9090/alerts

# Inspect Alertmanager UI
open http://localhost:9093/#/alerts
```

Keep this runbook close; extend it with tenant-specific procedures as they evolve.
