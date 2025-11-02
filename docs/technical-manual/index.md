# Technical Manual

**Standards**: ISO/IEC 12207§6, ISO/IEC 42010, ISO/IEC 29148

## Overview

SomaAgent01 is a microservices-based conversational AI platform implementing event-driven architecture with Kafka as the message bus.

## Architecture

### System Components

| Component | Type | Port | Purpose |
|-----------|------|------|---------|
| Gateway | FastAPI | 21016 | HTTP/WebSocket API, authentication, routing |
| Conversation Worker | Kafka Consumer | - | Process user messages, generate LLM responses |
| Tool Executor | Kafka Consumer | - | Execute tools requested by conversations |
| Memory Replicator | Kafka Consumer | - | Replicate memory.wal events to PostgreSQL |
| Memory Sync | Background Worker | - | Retry failed memory writes from outbox |
| Outbox Sync | Background Worker | - | Retry failed Kafka publishes from outbox |
| UI Proxy | FastAPI Router | - | Aggregate UI polling and message endpoints |

### Infrastructure

| Service | Port | Purpose |
|---------|------|---------|
| Kafka | 20000 | Event streaming (KRaft mode, single broker) |
| Redis | 20001 | Session cache, API keys |
| PostgreSQL | 20002 | Sessions, events, memory replica, outbox |
| OPA | 20009 | Policy evaluation |

### Kafka Topics

- `conversation.inbound`: User messages from gateway
- `conversation.outbound`: Assistant responses to clients
- `tool.requests`: Tool execution requests
- `tool.results`: Tool execution results
- `memory.wal`: Write-ahead log for all memory operations
- `memory.wal.dlq`: Dead letter queue for failed memory events
- `config_updates`: Runtime configuration changes

## Data Flow

```
User → Gateway → conversation.inbound → Conversation Worker → SLM → conversation.outbound → Gateway → User
                                              ↓
                                         SomaBrain (HTTP)
                                              ↓
                                         memory.wal → Memory Replicator → PostgreSQL
```

## Security

- **Authentication**: JWT (HS256/RS256) or API keys
- **Authorization**: OPA policy evaluation, OpenFGA (optional)
- **Encryption**: TLS termination at reverse proxy, Fernet for stored secrets
- **Browser auth**: Same-origin cookies or header/bearer tokens (no custom CSRF endpoint)

## Standards Compliance

- **ISO/IEC 12207§6**: Software construction and integration
- **ISO/IEC 42010**: Architecture description with stakeholder concerns
- **ISO/IEC 29148**: Requirements traceability
- **ISO/IEC 27001**: Information security controls

## Related Documents

- [Architecture Details](./architecture.md)
- [Outbound Events](./outbound-events.md)
- [Security Controls](./security.md)
- [Deployment Guide](./deployment.md)
