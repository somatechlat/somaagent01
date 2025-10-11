# Debugging Guide

## Logging

- Gateway: `docker logs -f somaAgent01_gateway`
- Tool Executor: `docker logs -f somaAgent01_tool-executor` (if present)
- UI: Browser DevTools console (filter by `speech-store` for realtime issues)

## Common Scenarios

| Symptom | Diagnosis Steps | Fix |
| --- | --- | --- |
| 500 on `/chat` | Check Gateway logs, ensure Redis/Postgres reachable | Restart dependency, validate env vars |
| Missing memories | Inspect `memory` table in Postgres, Redis cache | Re-run memory save, ensure tenant/persona correct |
| Realtime speech silent | Console errors, network tab | Verify `/realtime_session` response, confirm audio unlocked |
| Kafka lag growing | Check consumer offset, worker logs | Scale executors, resolve failing tasks |

## Breakpoints

- Python: Use VS Code debugger, attach to running container or run module locally (`python -m services.gateway.main`).
- UI: Use Chrome DevTools, set breakpoints in `speech-store.js`.

## Profiling

- Python: `py-spy` or `yappi` for CPU hotspots.
- JS: Chrome Performance tab to analyze rendering.

## Feature Flags & Toggles

- Review `python/helpers/settings.py` for runtime toggles.
- Use `/settings_set` to switch providers or enable kokoro TTS.

## Remote Debugging

- SSH into container: `docker exec -it somaAgent01_gateway /bin/bash`.
- Use `ptvsd`/`debugpy` for remote attach (configure in `.vscode/launch.json`).

## Reproducing Issues

1. Record exact request/command.
2. Capture logs with timestamps.
3. Note dependent services status.
4. If reproducible, add regression test.

## Helpful Tools

- `scripts/run_dev_cluster.sh` verbose output for startup issues.
- `scripts/kafka_partition_scaler.py` to inspect topic stats.
- `python/helpers/settings.py` for tracing configuration mergers.
