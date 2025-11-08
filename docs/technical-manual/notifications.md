# UI Notifications (SSE + REST)

This document describes the end-to-end Notifications system: storage schema, REST API, SSE streaming events, and the Web UI integration (badge, modal, toasts).

## Overview
- Transport: Server-Sent Events (single `EventSource` per session) multiplexing conversation + `ui.notification` events.
- Storage: Postgres table `ui_notifications` with TTL; periodic janitor deletes expired rows.
- Publish: Kafka topic `ui.notifications`, also merged onto the session SSE stream.
- API surface: REST for CRUD; SSE for realtime delivery.

## REST API
- Create notification
  - `POST /v1/ui/notifications`
  - Body: `{ "type": "string", "title": "string", "body": "string", "severity": "info|success|warning|error", "ttl_seconds": 3600, "meta": { ... } }`
  - 201 → `{ notification: { id, type, title, body, severity, created_at, read_at, meta } }`

- List notifications
  - `GET /v1/ui/notifications?limit=50&unread_only=true`
  - 200 → `{ notifications: [ ... ], next_cursor: { created_at, id } | null }`

- Mark as read
  - `POST /v1/ui/notifications/{id}/read`
  - 200 → `{ ok: true }`

- Clear all
  - `DELETE /v1/ui/notifications/clear`
  - 200 → `{ cleared: <int> }`

Authorization and tenant scoping mirror the session SSE access rules.

## SSE Events
- Event type: `ui.notification`
- Payloads:
  - Created: `{ type: "ui.notification", action: "created", notification: { ... } }`
  - Read: `{ type: "ui.notification", action: "read", id: "..." }`
  - Cleared: `{ type: "ui.notification", action: "cleared" }`

These events are emitted on the same SSE stream as chat events: `GET /v1/session/{session_id}/events`.

## Web UI Integration
- Single SSE client in `webui/js/stream.js` dispatches events to an event bus (`sse:event`).
- Notifications store: `webui/components/notifications/notificationsStore.js` consumes REST + bus and maintains a reactive state `{ list, unreadCount }`.
- Alpine bridge: `webui/index.js` bridges store -> `$store.notificationSse` for templates (badge + modal) and exposes `globalThis.notificationsSse` helpers.
- Badge: `webui/components/notifications/notification-icons.html` binds to `$store.notificationSse.unreadCount` and shows `#notification-badge`.
- Modal: `webui/components/notifications/notification-modal.html` lists `$store.notificationSse.list` and uses `globalThis.notificationsSse.markRead/clearAll`.
- Toasts: the unified `notificationsStore.js` also manages a lightweight toast stack (frontend) and mirrors actions to REST where possible. Modal open will mark unread as read via the SSE-backed store.

## Observability
- Prometheus counter `ui_notifications_total{event,severity,type}` increments on create/read/clear.
- SSE connection metrics and heartbeat monitoring exist in the gateway.

## Expiry & Cleanup
- Notifications include an optional TTL (`ttl_seconds`).
- A background janitor deletes rows past expiry; this does not emit SSE events.

## Troubleshooting
- No badge updates: ensure the SSE stream is connected (look for connection to `/v1/session/.../events`) and that the badge element exists.
- Create works but no realtime: check Kafka availability and that the gateway merges the `ui.notifications` consumer into the session multiplexer.
- 401/403 on API calls: verify JWT/session and tenant access checks; the notifications endpoints reuse the standard authorization path.

## Example (curl)
```bash
curl -sS -X POST \
  -H 'Content-Type: application/json' \
  --cookie 'session=...' \
  http://localhost:21016/v1/ui/notifications \
  -d '{"type":"demo","title":"Hi","body":"Hello","severity":"info"}'
```
