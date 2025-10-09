⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data.

# SomaAgent 01 Gateway API (Sprint 0B)

## Base URL
- The gateway runs on FastAPI (uvicorn) and is intended to sit behind Kong/Envoy. For local development it defaults to `http://localhost:8010`.

## Endpoints

### POST `/v1/session/message`
Enqueue a user message for processing.

- **Request Body**
  ```json
  {
    "session_id": "optional-session-id",
    "persona_id": "optional-persona-id",
    "message": "User message text",
    "attachments": ["s3://..."],
    "metadata": {"tenant": "acme"}
  }
  ```
- **Response**
  ```json
  {
    "session_id": "generated-or-provided",
    "event_id": "uuid"
  }
  ```
- **Behaviour**
  - Validates JWT/headers (to be implemented in Sprint 0C/1A).
  - Publishes to Kafka topic `conversation.inbound`.
  - Caches persona metadata in Redis (`session:{id}:meta`).
  - Appends a session event in Postgres for audit.

### WebSocket `/v1/session/{session_id}/stream`
Stream assistant responses in real-time.

- Connect via WebSocket; server streams JSON payloads with fields:
  ```json
  {
    "event_id": "uuid",
    "session_id": "...",
    "persona_id": "...",
    "role": "assistant",
    "message": "partial or final text",
    "metadata": {"status": "streaming"}
  }
  ```
- The gateway uses Kafka consumer group `gateway-{session_id}` to read `conversation.outbound` and forwards matching events.
- SSE support will be added for browser compatibility.

## Kafka Topics (Current Sprint Scope)
| Topic | Producer | Consumer | Payload |
|-------|----------|----------|---------|
| `conversation.inbound` | Gateway | Conversation Worker | `{event_id, session_id, persona_id, message, attachments, metadata}` |
| `conversation.outbound` | Conversation Worker | Gateway | `{event_id, session_id, persona_id, role, message, metadata}` |

Additional topics (`tool.requests`, `tool.results`, `policy.decisions`) will be introduced in Sprint 1B.

## Session Persistence
- **Redis** stores hot metadata.
- **Postgres** `session_events` table stores ordered JSONB payloads for audit and UI replay.
- Migration provided in `services/common/session_repository.py` (`ensure_schema`).

## Error Codes
- `502` when Kafka enqueue fails.
- WebSocket closes gracefully with code 1011 on streaming errors.

## TODO (Future Sprints)
- JWT + OPA integration for request auth.
- Attachment ingestion (object storage) and reference validation.
- Backpressure / rate limiting based on tenant budgets.
- SSE fallback for browsers.
