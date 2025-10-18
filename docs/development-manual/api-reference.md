---
title: API Reference
audience: developers, integrators
last-reviewed: 2025-10-17
---

# API Reference

Base URL: http://localhost:8010

Authentication

- JWT Bearer tokens when GATEWAY_REQUIRE_AUTH=true or JWT config is set. Otherwise optional in local dev.
- Header: Authorization: Bearer <token>

Gateway Endpoints (FastAPI)

- POST /v1/session/message
  - Body: { session_id?, persona_id?, message, attachments: string[], metadata: object }
  - Returns: { session_id, event_id }
  - Publishes to topic conversation.inbound

- POST /v1/session/action
  - Body: { session_id?, persona_id?, action, metadata? }
  - Returns: { session_id, event_id }

- GET /v1/session/{session_id}/events (SSE)
  - Stream of conversation.outbound events for session

- WS /v1/session/{session_id}/stream
  - WebSocket JSON stream of conversation.outbound events

- GET /v1/health
  - Returns component status for postgres, redis, kafka, and optional HTTP dependencies

- API Keys
  - POST /v1/keys -> create { key_id, label, secret, prefix, ... }
  - GET /v1/keys -> list keys (admin scope required)
  - DELETE /v1/keys/{key_id} -> revoke (admin scope required)

- Model Profiles
  - GET /v1/model-profiles
  - POST /v1/model-profiles (201)
  - PUT /v1/model-profiles/{role}/{deployment_mode}
  - DELETE /v1/model-profiles/{role}/{deployment_mode}

- Routing
  - POST /v1/route -> { chosen, score? }

- Requeue
  - GET /v1/requeue -> list pending items
  - POST /v1/requeue/{requeue_id}/resolve?publish=true -> { status }
  - DELETE /v1/requeue/{requeue_id} -> { status }

- Capsules proxy
  - GET /v1/capsules
  - GET /v1/capsules/{capsule_id}
  - POST /v1/capsules/{capsule_id}/install

Notes

- Legacy endpoints like /chat, /settings_get, /settings_set, /realtime_session do not exist on the FastAPI gateway.
- Realtime session brokering and connectivity utilities live in the legacy python/api layer (see Legacy APIs below).

Event Streams

- conversation.inbound: user messages enqueued by gateway
- conversation.outbound: responses/events consumed by SSE/WS
- tool.requests: tool executor input
- tool.results: tool executor output

Legacy APIs (python/api/*)

- POST /api_message
- GET|POST /api_log_get
- POST /api_terminate_chat
- POST /api_reset_chat
- POST /api_files_get
- POST /realtime_session

These are maintained for backward compatibility and are not part of the new /v1 gateway surface.
