# Realtime Session API

A focused guide for automations and UI clients interacting with `/realtime_session`.

## Endpoint

`POST /realtime_session`

## Request Schema

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `model` | string | ✔ | Provider model identifier (`gpt-4o-realtime-preview`) |
| `voice` | string | ✔ | Voice preset (e.g., `verse`) |
| `endpoint` | string | ✖ | Override provider endpoint (defaults to OpenAI) |

### Example

```json
{
  "model": "gpt-4o-realtime-preview",
  "voice": "verse",
  "endpoint": "https://api.openai.com/v1/realtime/sessions"
}
```

## Response Schema

```json
{
  "session": {
    "id": "sess_abc123",
    "model": "gpt-4o-realtime-preview",
    "expires_at": "2025-10-09T18:00:00Z",
    "client_secret": {
      "value": "rtm_secret_token",
      "expires_at": "2025-10-09T18:00:00Z"
    }
  }
}
```

- `client_secret.value` must be supplied as Bearer token during WebRTC negotiation (`Authorization: Bearer ...`).
- Secrets expire quickly (typically 1 min). Clients should negotiate immediately.

## Error Responses

| Status | Error Code | Meaning |
| --- | --- | --- |
| 400 | `invalid_request` | Missing model/voice or invalid endpoint format |
| 401 | `unauthorized` | Missing or invalid Gateway authentication |
| 429 | `rate_limited` | Exceeded session creation rate |
| 500 | `provider_error` | Upstream provider rejected the request |

Error body:
```json
{
  "error_code": "provider_error",
  "message": "OpenAI returned 401 Unauthorized"
}
```

## Usage Flow (Machines)

1. Call `/realtime_session` with desired parameters.
2. Extract `client_secret.value`.
3. Create WebRTC peer connection, generate SDP offer.
4. POST offer to provider using `Authorization: Bearer <client_secret>`.
5. Apply answer to the peer connection.

## Usage Flow (Humans via UI)

1. Operator enables microphone in UI.
2. UI automatically calls `/realtime_session` using stored settings.
3. UI handles WebRTC negotiation, user hears synthesized speech.

## Rate Limits

- Default: 3 session creations per minute per tenant.
- Configurable via Redis rate limiter; adjust in `python/helpers/settings.py` or env vars.

## Testing

- Use Playwright test `tests/playwright/test_realtime_speech.py` for end-to-end validation.
- Mock provider by pointing `endpoint` to a local stub in development.
