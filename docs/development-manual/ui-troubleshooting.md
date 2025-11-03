# Web UI Troubleshooting and Fix Log

Date: 2025-10-29

This page documents the end-to-end troubleshooting we performed to stabilize the Web UI and streaming pipeline, what was fixed, and how to verify.

## Symptoms

- Memory Dashboard failed to open with: `Failed to get current memory subdirectory: {"detail":"Method Not Allowed"}`.
- Live updates (SSE) did not connect: the browser showed `Firefox can’t establish a connection to the server at /v1/session/{id}/events`.
- Excessive polling: the UI issued hundreds of polling requests due to missing SSE.
- Tool results and conversation events were not appearing due to outbox publish errors.

## Root causes

1) Gateway outbox publish crashed when payloads were strings instead of dicts, due to trace-context injection assuming dicts.
2) Gateway lacked minimal UI support endpoints: UI config, SSE stream, and memory endpoints. The canonical memory endpoints are under `/v1/memories/*`. A legacy compatibility shim (`/memory_dashboard`) may exist temporarily but should not be relied upon.

## Fixes applied

- Hardened Kafka publish path so it accepts strings/bytes and coerces to dict before injecting trace context:
  - Updated `services/common/event_bus.py` to normalize any payload to a dict before `inject_trace_context`.
  - Updated `services/outbox_sync/main.py` to decode JSON strings from the outbox to dict before publishing.
- Implemented Gateway UI endpoints:
  - `GET /ui/config.json`: returns base UI config including `api_base: "/v1"` and selected toggles.
  - `GET /v1/session/{session_id}/events`: SSE endpoint streaming `conversation.outbound` events filtered by `session_id`.
  - `GET /v1/memories`, `GET /v1/memories/subdirs`, `GET /v1/memories/current-subdir`, plus `DELETE/PATCH /v1/memories/{id}` and `POST /v1/memories/bulk-delete` for admin actions.

## Verification steps

- Restart the outbox-sync and gateway services.
- Upload a small file via the Web UI; send a message; ensure SSE connects (no red error in console), and tool results stream in.
- Open Settings → Memory. The dashboard should load subdirs, search results, and delete/update selected rows.

## Regression tests (manual)

- UI loads without console errors.
- `GET /v1/health` returns status ok/degraded with components.
- `GET /ui/config.json` returns an object with `api_base`.
- `GET /v1/memories/current-subdir` returns the current memory subdir context.
- `GET /v1/session/{id}/events` establishes an EventSource connection and delivers events when they are produced.

## Notes and limitations

- The Memory Dashboard shim uses the replica store; updates/delete affect the replica table (intended for dev/audit). For production, consider offering read-only UI or a governed edit path.
- SSE uses a per-connection consumer group; for high fan-out, consider a shared group with manual filtering or a WS hub.
--
