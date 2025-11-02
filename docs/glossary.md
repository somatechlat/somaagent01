# Glossary

**Standards**: ISO/IEC 12207§4.2

## Terms

### A

**Agent**: Autonomous software component that processes conversations and executes tasks.

**API Key**: Authentication credential for accessing the gateway API.

### C

**Conversation Worker**: Kafka consumer service that processes inbound conversation events and generates responses using LLM.

### D

**DLQ (Dead Letter Queue)**: PostgreSQL-backed storage for failed Kafka messages requiring manual intervention.

**Durable Publisher**: Component ensuring message delivery via Kafka with PostgreSQL outbox fallback.

### G

**Gateway**: FastAPI service exposing HTTP/WebSocket endpoints for client interactions (port 20016).

### K

**Kafka**: Distributed event streaming platform used for inter-service communication.

### M

**Memory Replicator**: Service consuming memory.wal topic and persisting events to PostgreSQL replica store.

**Memory Sync**: Service processing memory write outbox for retry logic.

### O

**OPA (Open Policy Agent)**: Policy engine for authorization decisions.

**Outbox Pattern**: Transactional pattern ensuring message delivery by writing to database before publishing.

### P

**Persona**: User identity context for conversations and memory scoping.

**PostgreSQL**: Relational database storing sessions, events, memory replicas, and outbox entries.

### R

**Redis**: In-memory data store used for session caching and API key storage.

### S

**Session**: Conversation context identified by session_id.

**SLM (Small Language Model)**: LLM client for generating conversation responses.

**SomaBrain**: Centralized memory backend accessed via HTTP API.

### T

**Tenant**: Multi-tenancy isolation boundary for data and policies.

**Tool Executor**: Service processing tool execution requests from conversation worker.

### W

**WAL (Write-Ahead Log)**: Event log (memory.wal topic) recording all memory operations.
