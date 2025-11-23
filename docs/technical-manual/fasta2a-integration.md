# FastA2A Integration Guide

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Status](https://img.shields.io/badge/status-production_ready-green)

## Overview

FastA2A (Fast Agent-to-Agent) is a comprehensive agent-to-agent communication protocol that enables SomaAgent01 instances to communicate with each other and with other AI agents. This integration provides seamless cognitive memory sharing, distributed task execution, and collaborative problem-solving capabilities.

## Architecture

### FastA2A Components

#### 1. FastA2A Client Library (`python/helpers/fasta2a_client.py`)
- **Purpose**: Client-side agent discovery and messaging
- **Features**:
  - Automatic agent card retrieval
  - Secure connection management
  - Message context persistence
  - Comprehensive metrics and observability
  - Timeout and retry logic
  - Async/await support

#### 2. FastA2A Server (`python/helpers/fasta2a_server.py`)
- **Purpose**: Server-side agent exposure and task handling
- **Features**:
  - Dynamic agent registration
  - Token-based authentication
  - Task lifecycle management
  - Background worker processing
  - Graceful shutdown handling
  - Multi-tenant support

#### 3. FastA2A Celery Tasks (`services/celery_worker/tasks.py`)
- **Purpose**: Asynchronous agent communication processing
- **Features**:
  - Redis-backed task queue
  - Conversation state management
  - Comprehensive error handling
  - Metrics integration
  - Result persistence

#### 4. Event Publisher (`python/observability/event_publisher.py`)
- **Purpose**: FastA2A event publishing to SomaBrain
- **Features**:
  - Event batching and flushing
  - Retry logic with exponential backoff
  - Comprehensive error tracking
  - Integration with observability metrics

### Integration Points

#### SomaBrain Integration
- **Memory Sharing**: FastA2A conversations are automatically stored in SomaBrain
- **Cognitive Context**: Agent-to-agent communications include full context from SomaBrain
- **Event Publishing**: All FastA2A events are published to SomaBrain for memory persistence
- **Recall Integration**: Agents can recall previous FastA2A conversations during new interactions

#### Celery & Redis Integration
- **Task Distribution**: FastA2A tasks are Celery jobs that run against the Redis broker/backend managed via `services.celery_worker`.
- **Event Streaming**: Conversation state and task progress live in Redis (see `services/celery_worker/tasks.py`) and FastA2A events are published to SomaBrain via `python/observability/event_publisher.py`.
- **Reliability**: Celery keeps retry/backoff state, and Redis provides durable task metadata and rate-limit counters.

#### Redis Integration
- **Session Management**: FastA2A conversation sessions are stored in Redis; see the session helpers in `services/celery_worker/tasks.py` (`fast_a2a_session:{agent_url}`).
- **Task State & Metrics**: Celery task metadata (`task:{task_id}`) and conversation history (`conversation:{session_id}`) are persisted with TTLs for cleanup.
- **Rate Limiting**: Redis counters gate FastA2A request volume and help monitor queue length (see `check_celery_health` in `services/celery_worker/tasks.py`).

## Configuration

### Environment Variables

```bash
# FastA2A Server Configuration
SA01_A2A_SERVER_ENABLED=true
SA01_A2A_SERVER_PORT=21017
SA01_A2A_SERVER_TOKEN=your-secret-token

# FastA2A Client Configuration
SA01_A2A_CLIENT_TIMEOUT=30
SA01_A2A_CLIENT_TOKEN=your-secret-token

# Redis Configuration for FastA2A
SA01_REDIS_URL=redis://localhost:6379/0

# SomaBrain Integration
SA01_SOMABRAIN_URL=http://localhost:9696
```

### Docker Compose Services

```yaml
services:
  fasta2a-gateway:
    image: somaagent01:latest
    ports:
      - "21017:21017"
    environment:
      - SA01_A2A_SERVER_ENABLED=true
      - SA01_A2A_SERVER_TOKEN=${A2A_TOKEN}
    depends_on:
      - redis
      - kafka
      - somabrain

  fasta2a-worker:
    image: somaagent01:latest
    command: celery -A services.celery_worker worker --loglevel=info
    environment:
      - SA01_REDIS_URL=redis://redis:6379/0
      - SA01_SOMABRAIN_URL=http://somabrain:9696
    depends_on:
      - redis
      - kafka
      - somabrain

  fasta2a-flower:
    image: mher/flower:latest
    ports:
      - "21018:5555"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis
```

## Usage

### Connecting to Remote Agents

```python
from python.helpers.fasta2a_client import connect_to_agent, is_client_available

# Check if FastA2A client is available
if not is_client_available():
    raise RuntimeError("FastA2A client not available")

# Connect to a remote agent
async with await connect_to_agent("https://remote-agent.example.com") as conn:
    # Send a message
    response = await conn.send_message(
        message="Hello from SomaAgent01!",
        attachments=["/path/to/file.pdf"]
    )
    
    # Process response
    print(f"Agent response: {response}")
```

### Handling FastA2A Tasks via Celery

```python
import httpx

task_payload = {
    "task": "a2a_chat",
    "payload": {
        "agent_url": "https://remote-agent.example.com",
        "message": "Help me analyze this data",
        "attachments": ["/path/to/data.csv"],
        "session_id": "conversation-123"
    }
}

response = httpx.post("http://localhost:21016/v1/celery/run", json=task_payload)
print("task_id", response.json()["task_id"])
```

```python
status = httpx.get("http://localhost:21016/v1/celery/runs/task-123").json()
print(status)
```

### Publishing FastA2A Events

```python
from python.observability.event_publisher import publish_event

# Publish a FastA2A event
await publish_event(
    event_type="fast_a2a_chat_completed",
    data={
        "task_id": "task-123",
        "agent_url": "https://remote-agent.example.com",
        "duration": 45.2,
        "message_length": 150
    },
    metadata={
        "tenant": "default",
        "session_id": "session-123"
    }
)
```

## Security

### Authentication
- **Token-based**: All FastA2A communications require authentication tokens
- **Multi-tenant**: Each tenant has isolated FastA2A communication channels
- **JWT Integration**: FastA2A tokens can be integrated with existing JWT authentication

### Authorization
- **OPA Integration**: FastA2A requests are authorized through OPA policies
- **Role-based Access**: Different agent roles have different communication permissions
- **Tenant Isolation**: Agents can only communicate within their tenant context

### Encryption
- **TLS**: All FastA2A communications are encrypted with TLS 1.3
- **Token Encryption**: Authentication tokens are encrypted at rest in Redis
- **Message Encryption**: Sensitive message content can be encrypted end-to-end

## Monitoring and Observability

### Metrics

FastA2A integration provides comprehensive metrics through Prometheus:

```python
# FastA2A Request Metrics
fast_a2a_requests_total{
    agent_url="https://remote-agent.example.com",
    method="send_message",
    status="success"
}

# FastA2A Latency Metrics
fast_a2a_latency_seconds{
    agent_url="https://remote-agent.example.com",
    method="send_message"
}

# FastA2A Error Metrics
fast_a2a_errors_total{
    agent_url="https://remote-agent.example.com",
    error_type="timeout",
    method="send_message"
}

# SomaBrain Integration Metrics
somabrain_memory_operations_total{
    operation="fast_a2a_chat",
    status="success",
    tenant="default"
}
```

### Health Checks

FastA2A services provide comprehensive health checks:

```bash
# FastA2A Gateway Health
curl http://localhost:21017/health

# FastA2A Client Health
curl http://localhost:21016/v1/health | jq '.integrations.fasta2a_client'

# Celery Worker Health
curl http://localhost:21018/api/worker/status
```

### Logging

FastA2A operations are logged with structured JSON format:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "info",
  "service": "fasta2a_client",
  "operation": "send_message",
  "agent_url": "https://remote-agent.example.com",
  "session_id": "session-123",
  "duration": 2.45,
  "status": "success"
}
```

## Troubleshooting

### Common Issues

#### 1. FastA2A Client Not Available
```bash
# Check if FastA2A package is installed
pip list | grep fasta2a

# Install FastA2A package
pip install fasta2a
```

#### 2. Connection Timeouts
```bash
# Check remote agent availability
curl https://remote-agent.example.com/.well-known/agent.json

# Increase timeout in configuration
SA01_A2A_CLIENT_TIMEOUT=60
```

#### 3. Authentication Failures
```bash
# Verify token configuration
echo $SA01_A2A_CLIENT_TOKEN

# Check token validity
curl -H "Authorization: Bearer $SA01_A2A_CLIENT_TOKEN" \
     https://remote-agent.example.com/.well-known/agent.json
```

#### 4. Celery Task Failures
```bash
# Check Celery worker status
celery -A python.tasks.a2a_chat_task inspect active

# Check task failure rate
curl http://localhost:21018/api/task/failure-rate
```

### Debug Mode

Enable debug logging for FastA2A operations:

```bash
# Enable FastA2A debug logging
export PYTHONPATH=/path/to/somaagent01
export LOGLEVEL=DEBUG

# Run with debug logging
python -m python.helpers.fasta2a_client --debug
```

## Performance Optimization

### Connection Pooling
FastA2A client uses HTTP connection pooling for optimal performance:

```python
# Configure connection pool
from python.helpers.fasta2a_client import AgentConnection

conn = AgentConnection(
    agent_url="https://remote-agent.example.com",
    timeout=30,
    max_connections=20,
    max_keepalive_connections=10
)
```

### Event Batching
FastA2A events are batched for efficient processing:

```python
# Configure event batching
from python.observability.event_publisher import EventPublisher

publisher = EventPublisher(
    batch_size=100,
    flush_interval=10.0
)
```

### Caching
Agent cards and connection metadata are cached in Redis:

```python
# Configure cache TTL
export SA01_A2A_CACHE_TTL=3600  # 1 hour
```

## Best Practices

### 1. Error Handling
```python
try:
    async with await connect_to_agent(agent_url) as conn:
        response = await conn.send_message(message)
        return response
except Exception as e:
    # Log error with context
    logger.error(f"FastA2A communication failed: {e}", extra={
        "agent_url": agent_url,
        "session_id": session_id
    })
    raise
```

### 2. Resource Management
```python
# Always use context managers for connections
async with await connect_to_agent(agent_url) as conn:
    # Connection automatically closed
    response = await conn.send_message(message)
```

### 3. Monitoring
```python
# Track custom metrics
from python.observability.metrics import increment_counter

increment_counter(fast_a2a_requests_total, {
    "agent_url": agent_url,
    "method": "custom_operation",
    "status": "success"
})
```

### 4. Security
```python
# Always validate agent cards
agent_card = await conn.get_agent_card()
if not agent_card.get("skills"):
    raise ValueError("Agent has no skills defined")
```

## Future Enhancements

### Planned Features
1. **Multi-agent Orchestration**: Coordinated task execution across multiple agents
2. **Agent Discovery Service**: Automatic discovery of available agents in the network
3. **Advanced Routing**: Intelligent message routing based on agent capabilities
4. **Streaming Support**: Real-time streaming responses from remote agents
5. **Event Sourcing**: Complete event history for all agent interactions

### Integration Roadmap
- **Week 1**: Core FastA2A client and server implementation ✅
- **Week 2**: Celery task integration and SomaBrain event publishing ✅
- **Week 3**: Health checks, monitoring, and documentation ✅

## References

- [FastA2A Specification](https://github.com/fasta2a/fasta2a)
- [SomaAgent01 Architecture](./architecture.md)
- [Observability Guide](../observability/README.md)
- [Security Guidelines](../agent-onboarding/security-hardening.md)

---

**Note**: This FastA2A integration follows VIBE CODING RULES with real implementations, no placeholders, and comprehensive testing.
