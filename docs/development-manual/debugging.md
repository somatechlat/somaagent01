---
title: Debugging Guide
slug: dev-debugging
version: 1.0.0
last-reviewed: 2025-10-15
audience: contributors, sre
owner: developer-experience
reviewers:
  - platform-engineering
  - product
prerequisites:
  - Local stack running (`make dev-up`)
verification:
  - Reproduce and resolve at least one issue using steps below
---

# Debugging Guide

Practical steps for diagnosing SomaAgent01 issues across services.

## Logging Shortcuts

| Service | Command |
| --- | --- |
| Gateway | `docker compose -f docker-compose.somaagent01.yaml logs -f gateway` |
| Tool Executor | `docker compose -f docker-compose.somaagent01.yaml logs -f tool-executor` |
| Conversation Worker | `docker compose -f docker-compose.somaagent01.yaml logs -f conversation-worker` |
| UI | Browser DevTools console (`speech-store` namespace for realtime) |

## Common Scenarios

| Symptom | Diagnosis | Fix |
| --- | --- | --- |
| 500 on `/chat` | Gateway logs, Redis/Postgres reachability | Restart dependency, verify env vars |
| Missing memories | Inspect Postgres `memory_items`, Redis cache | Re-run memory save, confirm tenant/persona IDs |
| Realtime speech silent | Browser console + network tab | Validate `/realtime_session` response, unlock audio playback |
| Kafka lag growing | Check consumer offsets, worker logs | Scale executors, resolve failing tasks |

## Breakpoints

- **Python:** Attach VS Code debugger via `python -m services.gateway.main` or remote attach to container.
- **UI:** Use Chrome DevTools; set breakpoints in `webui/components/chat/*`.

## Profiling Tools

- Python CPU hotspots: `py-spy top --pid <PID>` or `yappi` snapshots.
- Browser rendering: Chrome Performance tab.

## Feature Flags & Toggles

- Runtime managed through `python/helpers/settings.py` and `/settings_set` API.
- Inspect effective configuration via `/settings_get` or logs emitted at startup.

## Remote Debugging

- Shell access: `docker exec -it somaAgent01_gateway /bin/bash`.
- Remote debugger: configure `debugpy` in `.vscode/launch.json`, forward port from container.

## Reproduce Issues Reliably

1. Capture exact request and headers.
2. Save relevant logs with timestamps.
3. Snapshot dependent service status (`docker compose ps`).
4. Convert fix into regression test before merge.

## Helpful Scripts

- `scripts/run_dev_cluster.sh` for verbose startup diagnostics.
- `scripts/kafka_partition_scaler.py` to inspect topic stats.
- `scripts/probes/check_slm.py` to validate LLM reachability.
