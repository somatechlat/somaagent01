# API Reference

**Standards**: ISO/IEC 29148§5.4

## Base URL

```
http://localhost:20016/v1
```

## Authentication

### JWT Token

```bash
curl -H "Authorization: Bearer <jwt-token>" \
  http://localhost:20016/v1/session/message
```

### API Key

```bash
curl -H "Authorization: Bearer sk-soma-<key>" \
  http://localhost:20016/v1/session/message
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

### Create Session

**POST** `/v1/session`

Create a new conversation session.

**Request**:
```json
{
  "tenant": "acme",
  "persona_id": "default"
}
```

**Response**:
```json
{
  "session_id": "abc123",
  "tenant": "acme",
  "persona_id": "default",
  "created_at": "2025-01-24T12:00:00Z"
}
```

---

### Send Message

**POST** `/v1/session/{session_id}/message`

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

**GET** `/v1/session/{session_id}/history`

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

**DELETE** `/v1/session/{session_id}`

Delete a session and all associated data.

**Response**:
```json
{
  "status": "deleted",
  "session_id": "abc123"
}
```

---

### Upload File

**POST** `/v1/files/upload`

Upload a file for use in conversations.

**Request** (multipart/form-data):
```
file: <binary-data>
session_id: abc123
```

**Response**:
```json
{
  "file_id": "file123",
  "filename": "document.pdf",
  "size": 102400,
  "mime_type": "application/pdf",
  "url": "/v1/files/file123"
}
```

---

### Get File

**GET** `/v1/files/{file_id}`

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

### Memory Operations

**POST** `/v1/memory/save`

Save information to long-term memory.

**Request**:
```json
{
  "session_id": "abc123",
  "content": "User prefers Python over JavaScript",
  "tags": ["preference", "programming"]
}
```

**Response**:
```json
{
  "memory_id": "mem123",
  "status": "saved"
}
```

---

**GET** `/v1/memory/search`

Search long-term memory.

**Query Parameters**:
- `query`: Search query
- `session_id` (optional): Filter by session
- `limit` (optional): Max results (default: 10)

**Response**:
```json
{
  "results": [
    {
      "memory_id": "mem123",
      "content": "User prefers Python over JavaScript",
      "relevance": 0.95,
      "created_at": "2025-01-24T12:00:00Z"
    }
  ],
  "total": 1
}
```

---

### Settings

**GET** `/v1/settings`

Get current settings.

**Response**:
```json
{
  "llm_model": "openai/gpt-4",
  "temperature": 0.7,
  "max_tokens": 2000,
  "memory_enabled": true
}
```

---

**PUT** `/v1/settings`

Update settings.

**Request**:
```json
{
  "llm_model": "anthropic/claude-3-opus",
  "temperature": 0.5
}
```

**Response**:
```json
{
  "status": "updated",
  "settings": {
    "llm_model": "anthropic/claude-3-opus",
    "temperature": 0.5,
    "max_tokens": 2000,
    "memory_enabled": true
  }
}
```

## WebSocket API

### Connect

```javascript
const ws = new WebSocket('ws://localhost:20016/v1/ws/session/abc123');

ws.onopen = () => {
  console.log('Connected');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};

ws.send(JSON.stringify({
  type: 'message',
  content: 'Hello, agent!'
}));
```

### Message Types

**Client → Server**:
```json
{
  "type": "message",
  "content": "User message text"
}
```

**Server → Client**:
```json
{
  "type": "response",
  "content": "Agent response text",
  "metadata": {
    "tokens_used": 150
  }
}
```

**Server → Client (streaming)**:
```json
{
  "type": "chunk",
  "content": "Partial response...",
  "done": false
}
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
| `/v1/files/upload` | 10 requests | 1 minute |
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
curl http://localhost:20016/v1/openapi.json
```

Or view interactive docs:

```
http://localhost:20016/docs
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
SESSION_ID=$(curl -X POST http://localhost:20016/v1/session \
  -H "Content-Type: application/json" \
  -d '{"tenant":"acme","persona_id":"default"}' \
  | jq -r '.session_id')

# 2. Send message
curl -X POST http://localhost:20016/v1/session/$SESSION_ID/message \
  -H "Content-Type: application/json" \
  -d '{"message":"What is 2+2?"}' \
  | jq '.response'

# 3. Get history
curl http://localhost:20016/v1/session/$SESSION_ID/history \
  | jq '.messages'

# 4. Delete session
curl -X DELETE http://localhost:20016/v1/session/$SESSION_ID
```

### File Upload and Query

```bash
# 1. Upload file
FILE_ID=$(curl -X POST http://localhost:20016/v1/files/upload \
  -F "file=@document.pdf" \
  -F "session_id=$SESSION_ID" \
  | jq -r '.file_id')

# 2. Query document
curl -X POST http://localhost:20016/v1/session/$SESSION_ID/message \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"Summarize the document\",\"file_id\":\"$FILE_ID\"}"
```
