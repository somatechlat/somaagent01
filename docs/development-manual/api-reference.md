# API Reference

**Standards**: ISO/IEC 29148§5.4

## Base URL

```
http://localhost:${GATEWAY_PORT:-21016}
```

## Authentication

### JWT Token

```bash
curl -H "Authorization: Bearer <jwt-token>" \
  http://localhost:${GATEWAY_PORT:-21016}/v1/session/message
```

### API Key

```bash
curl -H "Authorization: Bearer sk-soma-<key>" \
  http://localhost:${GATEWAY_PORT:-21016}/v1/session/message
```

## Endpoints

### Health Check

**GET** `/v1/health`

Check service health.

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-01-24T12:00:00Z"
}
```

---

### Start a Session (first message)

**POST** `/v1/session/message`

Send the first message with `session_id` omitted or null to create a session.

**Request**:
```json
{
  "session_id": null,
  "message": "Hello"
}
```

**Response** (truncated):
```json
{
  "session_id": "abc123",
  "enqueued": true
}
```

---

### Send Message

**POST** `/v1/session/message`

Send a message to the agent.

**Request**:
```json
{
  "message": "What is the weather today?",
  "attachments": [
    {
      "filename": "data.csv",
      "content": "base64-encoded-content",
      "mime_type": "text/csv"
    }
  ]
}
```

**Response**:
```json
{
  "message_id": "msg123",
  "session_id": "abc123",
  "response": "Let me check the weather for you...",
  "metadata": {
    "tokens_used": 150,
    "duration_ms": 1234
  }
}
```

---

### Get Session History

**GET** `/v1/sessions/{session_id}/history`

Retrieve conversation history.

**Query Parameters**:
- `limit` (optional): Max messages to return (default: 50)
- `offset` (optional): Pagination offset (default: 0)

**Response**:
```json
{
  "session_id": "abc123",
  "messages": [
    {
      "role": "user",
      "content": "Hello",
      "timestamp": "2025-01-24T12:00:00Z"
    },
    {
      "role": "assistant",
      "content": "Hi! How can I help?",
      "timestamp": "2025-01-24T12:00:01Z"
    }
  ],
  "total": 2
}
```

---

### Delete Session

**DELETE** `/v1/sessions/{session_id}`

Delete a session and all associated data.

**Response**:
```json
{
  "status": "deleted",
  "session_id": "abc123"
}
```

---

### Upload File(s)

**POST** `/v1/uploads`

Upload a file for use in conversations.

**Request** (multipart/form-data):
```
file: <binary-data>
session_id: abc123
```

**Response**:
```json
[
  {
    "id": "att_123",
    "filename": "document.pdf",
    "size": 102400,
    "content_type": "application/pdf",
    "path": "/v1/attachments/att_123"
  }
]
```

---

### Download Attachment

**GET** `/v1/attachments/{attachment_id}`

Download a previously uploaded file.

**Response**: Binary file content

---

### List Sessions

**GET** `/v1/sessions`

List all sessions for the authenticated user.

**Query Parameters**:
- `tenant` (optional): Filter by tenant
- `limit` (optional): Max sessions (default: 50)
- `offset` (optional): Pagination offset

**Response**:
```json
{
  "sessions": [
    {
      "session_id": "abc123",
      "tenant": "acme",
      "persona_id": "default",
      "created_at": "2025-01-24T12:00:00Z",
      "updated_at": "2025-01-24T12:30:00Z"
    }
  ],
  "total": 1
}
```

---

### Memory (Read APIs for UI)

Read-only endpoints used by the UI memory dashboard:

- **GET** `/v1/memories` — list/search
- **GET** `/v1/memories/subdirs` — available subdirectories
- **GET** `/v1/memories/current-subdir` — current browsing context
- **DELETE** `/v1/memories/{id}` — delete memory (policy-gated)
- **PATCH** `/v1/memories/{id}` — update memory metadata/content (policy-gated)
- **POST** `/v1/memories/bulk-delete` — delete multiple memories (policy-gated)

---

### UI Settings

Settings and credentials are managed via the Gateway UI Settings APIs.

**GET** `/v1/ui/settings`

Returns the effective agent configuration and model profile.

**PUT** `/v1/ui/settings`

Accepts `model_profile`, `agent`, and related sections from the UI.

Related endpoints:

- **GET** `/v1/ui/settings/credentials` — presence map of stored provider secrets
- **POST** `/v1/llm/credentials` — store/update a provider secret
- **POST** `/v1/llm/test` — validate active model profile and provider reachability

## Streaming (SSE)

The UI uses Server-Sent Events for streaming responses.

### Subscribe

```javascript
const es = new EventSource(`http://localhost:${GATEWAY_PORT || 21016}/v1/session/${sessionId}/events`);
es.onmessage = (evt) => {
  const payload = JSON.parse(evt.data);
  // Handle assistant/tool/util events
};
es.onerror = () => {
  // Handle reconnect/backoff
};
```

## Export Jobs

Asynchronous export of memory replica rows to NDJSON. Disabled by default.

Enable with:

```
DISABLE_FILE_SAVING=false
EXPORT_JOBS_ENABLED=true
```

Endpoints (admin scope):

- **POST** `/v1/memory/export/jobs` — create a job
- **GET** `/v1/memory/export/jobs/{job_id}` — get status
- **GET** `/v1/memory/export/jobs/{job_id}/download` — download NDJSON

Example:

```bash
JOB_ID=$(curl -s -X POST http://localhost:${GATEWAY_PORT:-21016}/v1/memory/export/jobs \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <admin-jwt>' \
  -d '{"tenant":"acme","q":"timeout","limit_total":2000}' | jq -r '.job_id')

curl -s http://localhost:${GATEWAY_PORT:-21016}/v1/memory/export/jobs/$JOB_ID \
  -H 'Authorization: Bearer <admin-jwt>' | jq .

curl -L http://localhost:${GATEWAY_PORT:-21016}/v1/memory/export/jobs/$JOB_ID/download \
  -H 'Authorization: Bearer <admin-jwt>' -o export.ndjson
```

## Error Responses

### 400 Bad Request

```json
{
  "error": "validation_error",
  "message": "Invalid session_id format",
  "details": {
    "field": "session_id",
    "constraint": "alphanumeric"
  }
}
```

### 401 Unauthorized

```json
{
  "error": "unauthorized",
  "message": "Invalid or expired token"
}
```

### 403 Forbidden

```json
{
  "error": "forbidden",
  "message": "Insufficient permissions for this operation"
}
```

### 404 Not Found

```json
{
  "error": "not_found",
  "message": "Session not found",
  "resource": "session",
  "id": "abc123"
}
```

### 429 Too Many Requests

```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests",
  "retry_after": 60
}
```

### 500 Internal Server Error

```json
{
  "error": "internal_error",
  "message": "An unexpected error occurred",
  "request_id": "req123"
}
```

## Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/v1/session/message` | 60 requests | 1 minute |
| `/v1/memory/search` | 100 requests | 1 minute |
| `/v1/uploads` | 10 requests | 1 minute |
| All others | 300 requests | 1 minute |

**Headers**:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1706140800
```

## Pagination

**Request**:
```
GET /v1/sessions?limit=20&offset=40
```

**Response**:
```json
{
  "sessions": [...],
  "total": 150,
  "limit": 20,
  "offset": 40,
  "next": "/v1/sessions?limit=20&offset=60",
  "previous": "/v1/sessions?limit=20&offset=20"
}
```

## Versioning

API version is in the URL path: `/v1/`

**Deprecation**: 6 months notice before removal

**Headers**:
```
X-API-Version: 1.0.0
X-API-Deprecated: false
```

## OpenAPI Spec

Full OpenAPI 3.0 specification:

```bash
curl http://localhost:${GATEWAY_PORT:-21016}/openapi.json
```

Or view interactive docs:

```
http://localhost:${GATEWAY_PORT:-21016}/docs
```

## SDKs

### Python

```python
from somaagent import Client

client = Client(api_key="sk-soma-...")

# Create session
session = client.sessions.create(tenant="acme")

# Send message
response = client.messages.send(
    session_id=session.id,
    message="Hello!"
)

print(response.content)
```

### JavaScript

```javascript
import { SomaClient } from '@somaagent/sdk';

const client = new SomaClient({ apiKey: 'sk-soma-...' });

// Create session
const session = await client.sessions.create({ tenant: 'acme' });

// Send message
const response = await client.messages.send({
  sessionId: session.id,
  message: 'Hello!'
});

console.log(response.content);
```

## Examples

### Complete Conversation Flow

```bash
# 1. Create session
SESSION_ID=$(curl -X POST http://localhost:${GATEWAY_PORT:-21016}/v1/session/message \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello"}' \
  | jq -r '.session_id')

# 2. Send message
curl -X POST http://localhost:${GATEWAY_PORT:-21016}/v1/session/message \
  -H "Content-Type: application/json" \
  -d "{\"session_id\":\"$SESSION_ID\",\"message\":\"What is 2+2?\"}" \
  | jq '.response'

# 3. Get history
curl http://localhost:${GATEWAY_PORT:-21016}/v1/sessions/$SESSION_ID/history \
  | jq '.messages'

# 4. Delete session
curl -X DELETE http://localhost:${GATEWAY_PORT:-21016}/v1/sessions/$SESSION_ID
```

### File Upload and Query

```bash
# 1. Upload file
ATT_ID=$(curl -X POST http://localhost:${GATEWAY_PORT:-21016}/v1/uploads \
  -F "file=@document.pdf" \
  -F "session_id=$SESSION_ID" \
  | jq -r '.[0].id')

# 2. Query document
curl -X POST http://localhost:${GATEWAY_PORT:-21016}/v1/session/message \
  -H "Content-Type: application/json" \
  -d "{\"session_id\":\"$SESSION_ID\",\"message\":\"Summarize the document\",\"attachments\":[\"$ATT_ID\"]}"
```
