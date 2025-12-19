# System Architecture

![Version](https://img.shields.io/badge/version-1.0.0-blue)

## Overview

SomaAgent01 is a microservices-based conversational AI platform built on event-driven architecture with perfect memory persistence via SomaBrain.

## Core Services

### Gateway (`services/gateway/main.py`)
- **Port**: 21016 (default)
- **Role**: FastAPI edge API handling HTTP/WebSocket/SSE
- **Responsibilities**:
  - User message ingestion (`POST /v1/sessions/message`)
  - SSE streaming (`GET /v1/sessions/{session_id}/events?stream=true`)
  - Settings management (UI-driven, encrypted in Redis)
  - LLM credential storage (encrypted with `SA01_CRYPTO_FERNET_KEY`)
  - Write-through to SomaBrain
  - Rate limiting, JWT auth, OPA/OpenFGA policy enforcement

### Conversation Worker (`services/conversation_worker/main.py`)
- **Kafka Topics**: Consumes `conversation.inbound`, publishes to `conversation.outbound`
- **Role**: Orchestrates LLM calls and tool execution
- **Responsibilities**:
  - Process user messages from Kafka
  - Call Gateway `/v1/llm/invoke/stream` with stored credentials
  - Emit tool requests to `tool.requests` topic
  - Stream assistant responses to `conversation.outbound`
  - Write memories to SomaBrain

### Tool Executor (`services/tool_executor/main.py`)
- **Kafka Topics**: Consumes `tool.requests`, publishes to `tool.results`
- **Role**: Deterministic tool execution
- **Responsibilities**:
  - Execute registered tools (code execution, search, memory, etc.)
  - Sandbox management
  - Resource limits enforcement
  - Audit logging

### Memory Services
- **Memory Replicator** (`services/memory_replicator/main.py`): Consumes `memory.wal`, replicates to Postgres
- **Memory Sync** (`services/memory_sync/main.py`): Retry failed SomaBrain writes from outbox
- **Outbox Sync** (`services/outbox_sync/main.py`): Ensures at-least-once Kafka delivery

## Infrastructure

### Kafka (KRaft mode)
- **Internal**: `kafka:9092` (PLAINTEXT)
- **External**: `localhost:21000` (EXTERNAL)
- **Topics**: `conversation.inbound`, `conversation.outbound`, `tool.requests`, `tool.results`, `memory.wal`
- **Partitions**: 3 (default)

### Redis
- **Port**: 20001
- **Usage**: Session cache, LLM credentials (encrypted), rate limiting

### PostgreSQL
- **Port**: 20002
- **Databases**: `somaagent01`, `openfga`
- **Tables**: `sessions`, `session_events`, `memory_replica`, `attachments`, `outbox`, `audit_log`

### OPA (Open Policy Agent)
- **Port**: 20009
- **Policy**: `policy/tool_policy.rego`
- **Decision Path**: `/v1/data/soma/policy/allow`

### SomaBrain
- **URL**: `http://host.docker.internal:9696`
- **Role**: Perfect memory storage and recall
- **Endpoints**: `/remember`, `/recall`, `/constitution/*`

## Data Flow

1. **User Message Ingestion**:
   ```
   UI → Gateway POST /v1/sessions/message → Kafka (conversation.inbound)
   ```

2. **Conversation Processing**:
   ```
   Conversation Worker ← Kafka (conversation.inbound)
   → Gateway /v1/llm/invoke/stream (with credentials)
   → Kafka (tool.requests) if tools needed
   → Kafka (conversation.outbound) for streaming
   → SomaBrain /remember for persistence
   ```

3. **Tool Execution**:
   ```
   Tool Executor ← Kafka (tool.requests)
   → Execute tool in sandbox
   → Kafka (tool.results)
   ```

4. **Memory Persistence**:
   ```
   Gateway/Worker → SomaBrain /remember
   → Kafka (memory.wal)
   → Memory Replicator → Postgres (memory_replica)
   ```

5. **SSE Streaming**:
   ```
   UI ← Gateway SSE /v1/sessions/{session_id}/events?stream=true
   ← Kafka (conversation.outbound)
   ```

## Security

- **Authentication**: JWT (cookie or Bearer token)
- **Authorization**: OPA policy + OpenFGA tenant access
-- **Secrets**: Encrypted in Redis with Fernet (`SA01_CRYPTO_FERNET_KEY`)
- **Rate Limiting**: Redis-based fixed-window (configurable)
- **Audit**: All actions logged to `audit_log` table

## Observability

- **Metrics**: Prometheus on port 8000 (Gateway), 9410-9413 (workers)
- **Tracing**: OpenTelemetry with W3C Trace Context
- **Logging**: Structured JSON logs
- **Health**: `/v1/health`, `/ready`, `/live` endpoints

### Somabrain Degradation Metrics (new)
- `conversation_worker_somabrain_status` – worker-level gauge (1=Somabrain reachable).
- `conversation_worker_somabrain_buffered_items` – pending memory writes waiting for replay.
- `conversation_worker_tokens_received_total` – raw token count of inbound user text.
- `thinking_policy_seconds{policy="conversation|memory.write"}` – latency of each OPA policy decision.
- `conversation_worker_llm_calls_total{model,result}` and `conversation_worker_llm_latency_seconds{model}` – track LLM invocation health and latency.
- `conversation_worker_llm_input_tokens_total` / `conversation_worker_llm_output_tokens_total` – enforce prompt/completion budgets per model.

## Configuration

- **Runtime Config**: `src.core.config` (centralized env facade)
- **Feature Flags**: `SA01_ENABLE_*` environment variables
- **Model Profiles**: Managed via UI Settings → Model
- **Tool Catalog**: Centralized in Gateway, distributed to workers

See `architecture.puml` for C4 diagram.
