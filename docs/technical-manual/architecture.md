# Architecture

**Standards**: ISO/IEC 42010

## System Context

SomaAgent01 is a distributed conversational AI platform using microservices architecture with event-driven communication via Kafka.

## Components

### Gateway (`services/gateway/main.py`)

**Purpose**: Public-facing HTTP API with SSE streaming

**Responsibilities**:
- Accept user messages via POST /v1/session/message
- Publish to conversation.inbound topic
- Stream responses from conversation.outbound via SSE (WebSocket may be added later)
- Authenticate requests (JWT/API keys)
- Enforce OPA policies
- Manage sessions in PostgreSQL
- Cache session metadata in Redis

**Technology**: FastAPI, aiokafka, asyncpg, redis-py

**Ports**:
- HTTP: 21016 (default; configurable via `GATEWAY_PORT`)
- Metrics: 9600 (Prometheus)

### Conversation Worker (`services/conversation_worker/main.py`)

**Purpose**: Process user messages and generate responses

**Responsibilities**:
- Consume conversation.inbound topic
- Analyze message intent/sentiment
- Fetch conversation history from PostgreSQL
- Call SLM (OpenAI-compatible API) for response generation
- Publish response to conversation.outbound
- Write user and assistant messages to SomaBrain via HTTP
- Emit memory.wal events
- Handle escalation to larger models
- Track token budgets per tenant/persona

**Technology**: aiokafka, httpx, asyncpg

**Metrics**: 9601

### Tool Executor (`services/tool_executor/main.py`)

**Purpose**: Execute tools requested by conversation worker

**Responsibilities**:
- Consume tool.requests topic
- Execute tool functions (code execution, web search, etc.)
- Publish results to tool.results topic
- Sandbox execution environment

**Technology**: aiokafka, subprocess

**Metrics**: 9602

### Memory Replicator (`services/memory_replicator/main.py`)

**Purpose**: Replicate memory events to PostgreSQL

**Responsibilities**:
- Consume memory.wal topic
- Insert events into memory_replica table
- Track replication lag
- Send failed events to memory.wal.dlq

**Technology**: aiokafka, asyncpg

**Metrics**: 9603

### Memory Sync (`services/memory_sync/main.py`)

**Purpose**: Retry failed memory writes

**Responsibilities**:
- Poll memory_write_outbox table
- Retry SomaBrain HTTP calls
- Emit memory.wal on success
- Exponential backoff for retries

**Technology**: asyncpg, httpx

**Metrics**: 9604

### Outbox Sync (`services/outbox_sync/main.py`)

**Purpose**: Retry failed Kafka publishes

**Responsibilities**:
- Poll outbox table
- Retry Kafka publish
- Delete on success
- Exponential backoff

**Technology**: aiokafka, asyncpg

**Metrics**: 9415

## Data Stores

### PostgreSQL

**Schema**:
- `sessions`: session_id, persona_id, tenant, metadata, created_at, updated_at
- `session_events`: id, session_id, occurred_at, payload
- `outbox`: id, topic, payload, dedupe_key, created_at, published_at
- `memory_replica`: id, event_id, session_id, persona_id, tenant, role, payload, wal_timestamp, created_at
- `memory_write_outbox`: id, payload, tenant, session_id, persona_id, idempotency_key, created_at, retry_count
- `dlq`: id, topic, event, error, created_at
- `model_profiles`: role, deployment_mode, model, base_url, temperature, kwargs
- `ui_settings`: id, document (JSONB)
- `attachments`: id, tenant, session_id, filename, mime, size, sha256, status, content, created_at

### Redis

**Keys**:
- `session:{session_id}:meta`: Session metadata cache
- `api_key:{key_id}`: API key details
- `llm_cred:{provider}`: Encrypted LLM credentials (Fernet)
- `budget:{tenant}:{persona_id}`: Token usage counters

### Kafka

**Configuration**:
- Mode: KRaft (no Zookeeper)
- Partitions: 3 per topic
- Replication: 1 (single broker)
- Retention: 168 hours (7 days)

## Communication Patterns

### Request-Response (HTTP)

```
Client → Gateway → SomaBrain HTTP API
```

### Event-Driven (Kafka)

```
Gateway → conversation.inbound → Conversation Worker → conversation.outbound → Gateway
```

### Outbox Pattern

```
Service → PostgreSQL outbox → Outbox Sync → Kafka
```

## Deployment Modes

- **DEV**: Local development, env-based LLM keys
- **STAGING**: Pre-production, Gateway-managed credentials
- **PROD**: Production, Gateway-managed credentials, strict auth

## Observability

- **Metrics**: Prometheus (per-service ports 9600-9610)
- **Tracing**: OpenTelemetry (OTLP endpoint configurable)
- **Logging**: Structured JSON logs to stdout

## Standards Compliance

- **ISO/IEC 42010**: Architecture viewpoints (functional, deployment, information)
- **ISO/IEC 12207§6.3.3**: Software architectural design
