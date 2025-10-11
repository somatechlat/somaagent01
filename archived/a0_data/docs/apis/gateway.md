# Gateway API Reference

> **Base URL:** `http://localhost:8010`

## Authentication

- JWT bearer tokens if `GATEWAY_REQUIRE_AUTH=true`.
- Development profile can disable auth via environment variable (not recommended outside localhost).

## REST Endpoints

### `GET /healthz`
- **Purpose:** Liveness probe.
- **Response:** `{ "status": "ok", "version": "v0.1.2" }`

### `POST /chat`
- **Body:**
```json
{
  "message": "Summarize the current backlog",
  "conversation_id": "uuid-optional",
  "tenant_id": "default",
  "persona": "agent0"
}
```
- **Response:**
```json
{
  "conversation_id": "uuid",
  "message_id": "uuid",
  "output": "Tokenized stream (if synchronous)",
  "tool_calls": []
}
```

### `GET /chat/{conversation_id}/history`
- Returns full transcript with message metadata.

### `POST /settings_get`
- **Purpose:** Retrieve full settings payload for UI/automations.
- **Response:**
```json
{
  "settings": {
    "sections": [
      {
        "id": "speech",
        "fields": [
          {
            "id": "speech_provider",
            "value": "openai_realtime"
          }
        ]
      }
    ]
  }
}
```

### `POST /settings_set`
- **Body:** Entire settings structure with edited fields.
- **Side Effects:** Persists to `tmp/settings.json`, triggers runtime refresh.

### `POST /realtime_session`
- **Purpose:** Broker realtime speech session.
- **Body:**
```json
{
  "model": "gpt-4o-realtime-preview",
  "voice": "verse",
  "endpoint": "https://api.openai.com/v1/realtime/sessions"
}
```
- **Response:** Provider session payload with `client_secret`.

### `POST /memory/save`
- Saves structured memory item (see `docs/architecture/components/memory.md`).

### `POST /memory/search`
- Retrieves memories based on key / semantic query.

## WebSocket Endpoints

### `GET /chat/stream`
- **Protocol:** JSON messages with following event types:
  - `token`: partial LLM output.
  - `tool_call`: tool invocation payload.
  - `completed`: final response and metadata.
  - `error`: error information.

```json
{
  "event": "token",
  "message_id": "uuid",
  "content": "Streaming text"
}
```

## Error Codes

| HTTP Status | Meaning | Typical Cause |
| --- | --- | --- |
| 400 | Validation error | Missing required field in payload |
| 401 | Unauthorized | Missing/invalid JWT when auth enabled |
| 403 | Forbidden | OpenFGA/OPA policy denied the request |
| 429 | Rate limited | Redis-backed rate limiter hit |
| 500 | Internal error | LLM provider failure, dependency outage |

Errors include `error_code` (machine readable) and `message` (human friendly).

## Pagination & Filtering

- History endpoints support `?page=` and `?page_size=`.
- Search endpoints allow `?tenant_id=` and `?persona=` filters.

## Machine Usage Tips

- Use idempotency keys (`X-Idempotency-Key`) for retried POSTs.
- Respect rate limit headers: `X-RateLimit-Remaining`, `Retry-After`.
- Subscribe to WebSocket stream for responsive automation rather than polling.

## Human-Friendly Examples

- [Postman collection](../res/postman/SomaAgent01.postman_collection.json) (add if available).
- cURL snippet:
```bash
curl -X POST http://localhost:8010/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "Plan today\'s standup"}'
```

For deeper service interactions review `docs/apis/tool_executor_callbacks.md` and `docs/features/realtime_speech.md`.
