# Operations Runbooks

## Table of Contents
1. [Start / Stop Stack](#start--stop-stack)
2. [Smoke Tests](#smoke-tests)
3. [Realtime Speech Troubleshooting](#realtime-speech-troubleshooting)
4. [Database Maintenance](#database-maintenance)
5. [Kafka Recovery](#kafka-recovery)
6. [Observability Checks](#observability-checks)
7. [Disaster Recovery](#disaster-recovery)

## Start / Stop Stack

### Start
```bash
make dev-up
```
- Reserves host ports, prunes old containers, brings up `core` + `dev` profiles.
- Waits for Postgres to report `healthy` before returning.

### Stop
```bash
make dev-down
```
- Stops Gateway/UI while preserving volumes.

### Clean (wipe volumes)
```bash
make dev-clean
```
- **Warning:** removes Postgres/Kafka/Redis state.

### Status
```bash
make dev-status
```
- Lists container state with health indicators.

## Smoke Tests

Run after stack startup or deployment:
```bash
pytest tests/integration/test_gateway_public_api.py
pytest tests/playwright/test_realtime_speech.py --headed
```
- First test validates API contract.
- Second ensures realtime speech provider works end-to-end.

## Realtime Speech Troubleshooting

| Symptom | Check | Action |
| --- | --- | --- |
| UI toast "Realtime session error" | Gateway logs (`docker logs somaAgent01_gateway`) | Validate OpenAI API key, network access |
| No audio playback | Browser console | Ensure user interaction unlocked audio context |
| WebRTC negotiation stuck | Gateway `/realtime_session` response | Inspect endpoint/voice parameters |

## Database Maintenance

- Backups: `docker exec somaAgent01_postgres pg_dump somaagent01 > backup.sql`.
- Restore: `docker exec -i somaAgent01_postgres psql somaagent01 < backup.sql`.
- Vacuum/analyze weekly or after large data loads.

## Kafka Recovery

1. Check broker health: `docker logs somaAgent01_kafka`.
2. Restart broker: `docker restart somaAgent01_kafka`.
3. If topics missing, re-run provisioning script (coming soon).
4. For stuck consumers, inspect lag: `kcat -b localhost:29092 -Q -t somastack.tools`.

## Observability Checks

- Metrics: `http://localhost:<PrometheusPort>/graph` (port printed by startup script).
- Logs: `docker logs -f somaAgent01_gateway`.
- Alerts: configure Alertmanager routes (see `docs/operations/observability.md`).

## Disaster Recovery

| Asset | Restore Procedure |
| --- | --- |
| Postgres | Restore latest SQL dump, restart Gateway |
| Redis | Accept cache loss; rebuild from Postgres/SomaBrain |
| Kafka | Restore from backup snapshot; reprocess DLQ |
| OpenFGA | Re-apply migration scripts (`docker compose run openfga-migrate`) |
| Config files | Git restore specific version (`git checkout HEAD -- conf/tenants.yaml`) |

## Doc References

- Architecture: `docs/architecture/overview.md`
- API specs: `docs/apis/`
- Features guides: `docs/features/`
- Troubleshooting: `docs/troubleshooting.md`
