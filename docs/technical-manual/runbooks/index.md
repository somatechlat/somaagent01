---
title: Runbooks
---

# Operational Runbooks

## Start / Stop Stack

Start
```bash
make dev-up
```

Stop
```bash
make dev-down
```

Clean (wipe volumes)
```bash
make dev-clean
```

Status
```bash
make dev-status
```

## Smoke Tests

```bash
pytest tests/integration/test_gateway_public_api.py
pytest tests/playwright/test_realtime_speech.py --headed
```

## Database Maintenance

- Backups: `docker exec somaAgent01_postgres pg_dump somaagent01 > backup.sql`.
- Restore: `docker exec -i somaAgent01_postgres psql somaagent01 < backup.sql`.

## Kafka Recovery

1. Check broker logs.
2. Restart broker container.
3. Verify topics and consumer lag.

## Observability Checks

- Metrics: verify Prometheus targets are UP; dashboards live in the external observability project.
- Logs: `docker logs -f somaAgent01_gateway`.
