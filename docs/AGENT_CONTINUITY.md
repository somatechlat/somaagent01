---
title: Agent Continuity Handoff
last-updated: 2025-10-25
owner: platform
status: living-handoff
---

# Purpose

This document is a detailed handoff for the next agent/operator after a reset. It captures the current state of SomaAgent01, what is implemented, what remains, how to run the full developer cluster, how to validate the memory plane end‑to‑end, and the exact next steps to ship a production‑ready agent.

All content reflects the repository state as of 2025‑10‑25.

## High‑Level Overview

- Single front door: Gateway (FastAPI) at `/v1/*` handles auth/OPA, enqueues events (Kafka/outbox), performs write‑through to SomaBrain, publishes `memory.wal`, and exposes admin/health endpoints.
- Conversation Worker and Tool Executor consume events, persist memories (SomaBrain HTTP via SomaClient), publish `memory.wal` on success.
- Memory Replicator consumes `memory.wal` and writes Postgres `memory_replica` (for admin browse/audit); DLQ on failure.
- NEW: True fail‑safe memory persistence via a Postgres `memory_write_outbox` + `memory_sync` worker that retries remembers and publishes `memory.wal` on success.
- Web UI (Flask static app + API handlers) can now operate in Gateway mode: UI messages post to Gateway and stream replies via a proxy to Gateway SSE.
- Observability is Prometheus‑only (no Grafana code in this repo). Export signals are sufficient for external dashboards.

## What’s Implemented (Key Deltas)

1) Memory client & resiliency
- `python/integrations/soma_client.py`
  - Retry w/ `Retry-After`, circuit breaker, trace propagation, Prometheus metrics, logging redaction.
  - Correct handling of universe (`SOMA_NAMESPACE`) vs. memory sub‑namespace (`SOMA_MEMORY_NAMESPACE`).

2) Fail‑safe memory writes (NEW)
- `services/common/memory_write_outbox.py` (Postgres outbox for failed `remember()` calls).
- `services/memory_sync/main.py` (worker): drains outbox, calls `remember()` and publishes `memory.wal` on success.
- Wired enqueue on SomaClientError in:
  - Gateway write‑through paths (`/v1/session/message`, `/v1/session/action`).
  - Conversation Worker (user+assistant memory writes).
  - Tool Executor (tool result memory writes).

3) Memory plane
- `services/memory_replicator/main.py`: WAL consumer → replica; emits `memory_replicator_lag_seconds`.
- `services/common/memory_replica_store.py`:
  - `insert_from_wal`, `latest_wal_timestamp`, `get_by_event_id`, `list_memories`.
  - Structured filters for `universe` and `namespace` using JSON expressions.
  - Indexes: tenant/persona/created_at/wal_ts, JSONB GIN on payload, and JSON expression indexes for universe/namespace.

4) Gateway APIs
- Admin endpoints:
  - GET `/v1/admin/memory` (filters: tenant/persona/role/session/q/min_ts/max_ts/after/limit + universe/namespace).
  - GET `/v1/admin/memory/{event_id}`
  - POST `/v1/memory/batch` (server idempotency if missing; WAL publish on success; enqueue on failure).
  - DELETE `/v1/memory/{id}` (recall_delete proxy).
  - GET `/v1/memory/export` (streamed NDJSON paging; limits, optional tenant scoping; concurrency bound).
- Foundations:
  - GET `/ui/config.json` (runtime config for UI).
  - DLQ depth refresher task → `gateway_dlq_depth{topic}`.
  - Env‑driven CORS and optional CSRF (cookie‑based).

5) Web UI integration (Gateway mode)
- `python/api/message.py`: Gateway mode (env `UI_USE_GATEWAY`). When true, posts to Gateway `/v1/session/message` and falls back to local Agent mode on failure.
- `python/api/gateway_stream.py`: `/gateway_stream?session_id=...` proxies Gateway SSE `/v1/session/{id}/events` for the browser.
- Docker compose sets for `agent-ui`: `UI_USE_GATEWAY=true`, `UI_GATEWAY_BASE=http://gateway:8010`.
- Fixed UI extension warnings by adding `simpleeval` to the image.

6) Observability (Prometheus metrics)
- Gateway write‑through: `gateway_write_through_attempts_total{path}`, `gateway_write_through_results_total{path,result}`, `gateway_write_through_wal_results_total{path,result}`.
- DLQ: `gateway_dlq_depth{topic}` (refreshed periodically or via `/v1/health`).
- Replicator: `memory_replicator_lag_seconds`, `memory_replicator_events_total{result}`.
- SomaClient: `somabrain_request_seconds_bucket{method,path,status}`+ `_sum/_count`, `somabrain_requests_total{method,path,status}`.
- Memory Sync: `memory_sync_jobs_total{result}`, `memory_sync_seconds`, `memory_sync_backlog`.
- Outbox Sync: `outbox_sync_*`, `somabrain_health_state{state}`.

## How To Run (Dev)

1) One‑time network
```
docker network create somaagent01
```

2) Build (first build is long; allow 10–15 minutes for ML deps)
```
docker compose -f docker-compose.yaml --profile core --profile dev build
```

3) Up
```
docker compose -f docker-compose.yaml --profile core --profile dev up -d
```

4) Health
```
curl -s http://localhost:${GATEWAY_PORT:-20016}/v1/health | jq
curl -s http://localhost:${GATEWAY_PORT:-20016}/healthz | jq
curl -s http://localhost:${GATEWAY_PORT:-20016}/ui/config.json | jq
```

5) UI (gateway mode enabled by compose)
- Open: `http://localhost:${AGENT_UI_PORT:-20015}`
- Send a message; you’ll get `{accepted: true, session_id, event_id}`.
- Subscribe SSE in the SPA to: `/gateway_stream?session_id=<id>` (proxy) for live updates.

## Validation Scenarios

1) Happy path (SomaBrain up)
- Post message via UI or Gateway:
  - `curl -s -X POST "http://localhost:${GATEWAY_PORT:-20016}/v1/session/message" -H 'Content-Type: application/json' -d '{"message":"hello","metadata":{"tenant":"t1"}}' | jq`
- Browse replica (filters):
  - `curl -s "http://localhost:${GATEWAY_PORT:-20016}/v1/admin/memory?tenant=t1&universe=u-1&namespace=wm&limit=20" | jq`
- Expect: memory present, WAL emitted, replicator lag reasonable (< 2s steady‑state in dev).

2) Fail‑safe drill (SomaBrain down → recover)
- Stop SomaBrain or point `SOMA_BASE_URL` to a dead host; post a message.
- Expect: `memory_sync_backlog` > 0; user flow still 200‑OK.
- Restore SomaBrain; expect backlog to drain and replica rows to appear.

3) Admin features
- Batch: `POST /v1/memory/batch` with items; expect WAL on success and enqueue on failure.
- Delete: `DELETE /v1/memory/{id}`; expect recall_delete result.
- Export: `GET /v1/memory/export?tenant=t1&universe=u-1&namespace=wm&limit_total=50000` → NDJSON file; concurrency limited and max rows enforced.

## Security & AuthN/AuthZ

- Dev: `GATEWAY_REQUIRE_AUTH=false` (open). Prod must set it to true and enforce JWT + OPA.
- Cookies + CSRF supported if browser session is used; configure CORS explicitly for UI origin.
- Admin endpoints require admin scope when auth is enabled.

## Redis Usage (Control Plane)

- Session context cache (Gateway + Worker): `RedisSessionCache`.
- API key store: `RedisApiKeyStore`.
- Requeue store: `RequeueStore`.
- Budget manager: `BudgetManager`.
- Not used for durable write path (Kafka + Postgres handle durability).

## Outstanding Work (Next Sprints)

Sprint S2 – UI Streaming Client
- Add tiny EventSource initializer in the SPA to consume `/gateway_stream?session_id=...` with reconnect/backoff; render incremental events.
- Acceptance: live replies paint reliably; transient disconnects auto‑recover.

Sprint S5 – Export Hardening
- Optional: rate limit export per tenant/user (e.g., Redis token bucket) and surface 429 on exceed.
- Optional: async export job for very large datasets (manifest + status + download URL). Current sync streaming is efficient but a job runner scales better for multi‑tenant.

Sprint S6 – AuthN/AuthZ & Policy UX
- Turn on `GATEWAY_REQUIRE_AUTH=true` in staging/prod; JWT → cookie sessions for the SPA; enforce CSRF.
- Policy surfaces in the UI (display denied reasons); hide admin UI without scope.

Sprint S7 – E2E & Perf
- Extend Testcontainers e2e: verify memory_write_outbox → memory_sync drains on SomaBrain recovery.
- Soak tests (write‑through async): prove p50/p95 latency targets and bounded replication lag.

## Known Pitfalls & Fixes

- First docker build is long: torch/transformers/faiss wheels take time. Solution: allow 10–15 minutes; ensure Docker Desktop has ≥ 8 GB RAM and ≥ 4 vCPUs.
- SomaBrain localhost vs. host.docker.internal: inside containers, use `http://host.docker.internal:9696` (already set by compose).
- CORS/CSRF: if the SPA calls the Gateway directly in the browser, set `GATEWAY_CORS_ORIGINS` and enable CSRF (cookies). The provided `/gateway_stream` avoids SSE CORS hassles.
- Export breadth: use `tenant`, `universe`, `namespace` filters and set `GATEWAY_EXPORT_REQUIRE_TENANT=true` + `MEMORY_EXPORT_MAX_ROWS` to prevent massive accidental exports.

## Quick Glossary

- **Remember**: Persist memory via SomaBrain HTTP.
- **WAL**: Memory write‑ahead log event published to Kafka (`memory.wal`).
- **Replica**: Postgres table (`memory_replica`) of normalized memory events.
- **DLQ**: Dead Letter Queue; Kafka `*.dlq` topic + Postgres `dlq_messages` table.
- **Outbox**: Postgres `message_outbox` for durable Kafka publish fallback.
- **Memory Write Outbox**: Postgres `memory_write_outbox` for failed remembers.

## Contact Points

- Gateway service: `services/gateway/main.py` (APIs, health, CORS/CSRF, DLQ refresh, admin endpoints).
- Replicator: `services/memory_replicator/main.py`.
- Memory Sync: `services/memory_sync/main.py`.
- Outbox repository: `services/common/outbox_repository.py`.
- DLQ store: `services/common/dlq_store.py`.
- Replica store: `services/common/memory_replica_store.py`.
- SomaBrain client: `python/integrations/soma_client.py`.
- Web UI API handlers: `python/api/*.py`.

## Final Checklist Before You Start

- [ ] SomaBrain reachable (`/health` or `/healthz`).
- [ ] Docker Desktop resources set appropriately.
- [ ] `docker network create somaagent01` executed once.
- [ ] Build images and bring up stack.
- [ ] Post a message (UI or Gateway) and verify replica rows appear when SomaBrain is up.
- [ ] Run outage drill and confirm memory_sync drains backlog on recovery.
- [ ] Enable auth in staging/prod and verify admin scope enforcement.

This is the living handoff. Update it as you complete S2 (UI streaming), S5 (export hardening), S6 (auth polish), and S7 (e2e/perf) so the next reset is seamless.

