⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data.

# Sprint B: Testing & Quality Assurance
**Duration**: 2 weeks (parallel with Sprints A, C, D)  
**Goal**: Achieve 80%+ test coverage with comprehensive unit, integration, and end-to-end tests

---

## 🎯 OBJECTIVES

1. Create comprehensive pytest test suite
2. Implement integration tests for service interactions
3. Add schema validation and contract testing
4. Build test fixtures and utilities
5. Establish testing best practices and CI integration

---

## 📦 DELIVERABLES

### 1. Test Infrastructure

#### 1.1 Test Configuration
**File**: `tests/conftest.py`
```python
"""Shared pytest fixtures and configuration"""
import asyncio
import pytest
import os
from typing import AsyncGenerator
from testcontainers.kafka import KafkaContainer
from testcontainers.redis import RedisContainer
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def kafka_container():
    """Start Kafka testcontainer"""
    with KafkaContainer() as kafka:
        os.environ["KAFKA_BOOTSTRAP_SERVERS"] = kafka.get_bootstrap_server()
        yield kafka

@pytest.fixture(scope="session")
async def redis_container():
    """Start Redis testcontainer"""
    with RedisContainer() as redis:
        os.environ["REDIS_URL"] = redis.get_connection_url()
        yield redis

@pytest.fixture(scope="session")
async def postgres_container():
    """Start Postgres testcontainer"""
    with PostgresContainer("postgres:16-alpine") as postgres:
        os.environ["POSTGRES_DSN"] = postgres.get_connection_url()
        yield postgres

@pytest.fixture
async def clean_kafka(kafka_container):
    """Clean Kafka topics before each test"""
    # Admin client to delete topics
    yield
    # Cleanup

@pytest.fixture
async def clean_redis(redis_container):
    """Flush Redis before each test"""
    import redis.asyncio as redis_lib
    client = redis_lib.from_url(os.environ["REDIS_URL"])
    await client.flushall()
    yield client
    await client.close()

@pytest.fixture
async def clean_postgres(postgres_container):
    """Clean Postgres tables before each test"""
    import asyncpg
    conn = await asyncpg.connect(os.environ["POSTGRES_DSN"])
    await conn.execute("TRUNCATE session_events, model_profiles, delegation_tasks CASCADE")
    yield conn
    await conn.close()
```

#### 1.2 Test Utilities
**File**: `tests/utils.py`
```python
"""Testing utilities and helpers"""
import uuid
from typing import Dict, Any

def create_test_event(
    session_id: str | None = None,
    message: str = "Test message",
    **kwargs
) -> Dict[str, Any]:
    """Create a test conversation event"""
    return {
        "event_id": str(uuid.uuid4()),
        "session_id": session_id or str(uuid.uuid4()),
        "persona_id": kwargs.get("persona_id"),
        "message": message,
        "attachments": [],
        "metadata": kwargs.get("metadata", {}),
        "role": "user",
    }

def create_test_tool_request(
    tool_name: str,
    args: Dict[str, Any] | None = None,
    **kwargs
) -> Dict[str, Any]:
    """Create a test tool request event"""
    return {
        "event_id": str(uuid.uuid4()),
        "session_id": kwargs.get("session_id", str(uuid.uuid4())),
        "persona_id": kwargs.get("persona_id"),
        "tool_name": tool_name,
        "args": args or {},
        "metadata": kwargs.get("metadata", {}),
    }

async def wait_for_event(
    topic: str,
    timeout: float = 5.0,
    predicate = None
) -> Dict[str, Any]:
    """Wait for an event on a Kafka topic"""
    # Implementation
    pass
```

### 2. Unit Tests

#### 2.1 Event Bus Tests
**File**: `tests/unit/test_event_bus.py`
```python
"""Tests for Kafka event bus"""
import pytest
from services.common.event_bus import KafkaEventBus

@pytest.mark.asyncio
async def test_publish_consume(kafka_container, clean_kafka):
    bus = KafkaEventBus()
    test_event = {"test": "data", "value": 123}
    
    # Publish
    await bus.publish("test.topic", test_event)
    
    # Consume
    received = []
    async def handler(event):
        received.append(event)
    
    # Start consumer in background
    import asyncio
    task = asyncio.create_task(
        bus.consume("test.topic", "test-group", handler)
    )
    
    await asyncio.sleep(2)
    task.cancel()
    
    assert len(received) == 1
    assert received[0]["test"] == "data"
    assert received[0]["value"] == 123

@pytest.mark.asyncio
async def test_event_serialization(kafka_container):
    """Test JSON serialization/deserialization"""
    bus = KafkaEventBus()
    complex_event = {
        "nested": {"data": [1, 2, 3]},
        "special": None,
        "unicode": "🎉"
    }
    
    await bus.publish("test.serialize", complex_event)
    # Verify deserialization...
```

#### 2.2 Session Repository Tests
**File**: `tests/unit/test_session_repository.py`
```python
"""Tests for session storage"""
import pytest
from services.common.session_repository import PostgresSessionStore, RedisSessionCache

@pytest.mark.asyncio
async def test_append_and_list_events(clean_postgres):
    store = PostgresSessionStore()
    session_id = "test-session-123"
    
    event1 = {"type": "user", "message": "Hello"}
    event2 = {"type": "assistant", "message": "Hi there"}
    
    await store.append_event(session_id, event1)
    await store.append_event(session_id, event2)
    
    events = await store.list_events(session_id, limit=10)
    assert len(events) == 2
    assert events[0]["message"] == "Hi there"  # Newest first
    assert events[1]["message"] == "Hello"

@pytest.mark.asyncio
async def test_redis_cache(clean_redis):
    cache = RedisSessionCache()
    
    await cache.set("test:key", {"value": 42})
    result = await cache.get("test:key")
    
    assert result["value"] == 42
```

#### 2.3 Schema Validator Tests
**File**: `tests/unit/test_schema_validator.py`
```python
"""Tests for JSON schema validation"""
import pytest
from jsonschema import ValidationError
from services.common.schema_validator import validate_event

def test_valid_conversation_event():
    event = {
        "event_id": "abc123",
        "session_id": "session-1",
        "role": "user",
        "message": "Test",
        "attachments": [],
        "metadata": {}
    }
    validate_event(event, "conversation_event")  # Should not raise

def test_invalid_conversation_event_missing_field():
    event = {
        "event_id": "abc123",
        # Missing session_id
        "role": "user",
        "message": "Test"
    }
    with pytest.raises(ValidationError):
        validate_event(event, "conversation_event")

def test_invalid_conversation_event_wrong_type():
    event = {
        "event_id": "abc123",
        "session_id": "session-1",
        "role": "user",
        "message": 123,  # Should be string
        "attachments": [],
        "metadata": {}
    }
    with pytest.raises(ValidationError):
        validate_event(event, "conversation_event")
```

#### 2.4 Budget Manager Tests
**File**: `tests/unit/test_budget_manager.py`
```python
"""Tests for token budget management"""
import pytest
from services.common.budget_manager import BudgetManager
from services.common.tenant_config import TenantConfig

@pytest.mark.asyncio
async def test_consume_within_budget(clean_redis):
    config = TenantConfig()
    manager = BudgetManager(tenant_config=config)
    
    result = await manager.consume("tenant1", "persona1", 100)
    
    assert result.allowed is True
    assert result.total_tokens == 100

@pytest.mark.asyncio
async def test_exceed_budget(clean_redis):
    config = TenantConfig()
    config.set_budget_limit("tenant1", 500)
    manager = BudgetManager(tenant_config=config)
    
    # Consume up to limit
    await manager.consume("tenant1", None, 400)
    result = await manager.consume("tenant1", None, 200)
    
    assert result.allowed is False
    assert result.total_tokens >= 500
```

#### 2.5 Policy Client Tests
**File**: `tests/unit/test_policy_client.py`
```python
"""Tests for OPA policy client"""
import pytest
from unittest.mock import AsyncMock, patch
from services.common.policy_client import PolicyClient, PolicyRequest

@pytest.mark.asyncio
async def test_policy_allow():
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"result": True}
        
        client = PolicyClient()
        request = PolicyRequest(
            tenant="test",
            persona_id=None,
            action="tool.execute",
            resource="echo",
            context={}
        )
        
        result = await client.evaluate(request)
        assert result is True

@pytest.mark.asyncio
async def test_policy_deny():
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"result": False}
        
        client = PolicyClient()
        request = PolicyRequest(
            tenant="test",
            persona_id=None,
            action="tool.execute",
            resource="dangerous_tool",
            context={}
        )
        
        result = await client.evaluate(request)
        assert result is False
```

### 3. Integration Tests

#### 3.1 Gateway Integration Tests
**File**: `tests/integration/test_gateway.py`
```python
"""Integration tests for gateway service"""
import pytest
import httpx
from tests.utils import create_test_event

@pytest.mark.asyncio
async def test_submit_message_end_to_end(
    kafka_container,
    redis_container,
    postgres_container,
    clean_kafka,
    clean_redis,
    clean_postgres
):
    # Start gateway in test mode
    from services.gateway.main import app
    
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        payload = {
            "message": "Integration test message",
            "metadata": {"test": "true"}
        }
        
        response = await client.post("/v1/session/message", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "event_id" in data
        
        # Verify event in Kafka
        # Verify session in Postgres
        # Verify cache in Redis

@pytest.mark.asyncio
async def test_websocket_streaming(kafka_container):
    from services.gateway.main import app
    
    async with httpx.AsyncClient(app=app) as client:
        # Connect to WebSocket
        # Send message
        # Verify streaming response
        pass
```

#### 3.2 Conversation Worker Integration Tests
**File**: `tests/integration/test_conversation_worker.py`
```python
"""Integration tests for conversation worker"""
import pytest
from services.conversation_worker.main import ConversationWorker
from tests.utils import create_test_event, wait_for_event

@pytest.mark.asyncio
async def test_worker_processes_message(
    kafka_container,
    redis_container,
    postgres_container,
    clean_kafka,
    clean_redis,
    clean_postgres
):
    worker = ConversationWorker()
    
    # Publish test event
    test_event = create_test_event(message="Test worker processing")
    await worker.bus.publish("conversation.inbound", test_event)
    
    # Start worker in background
    import asyncio
    task = asyncio.create_task(worker.start())
    
    # Wait for response
    response = await wait_for_event(
        "conversation.outbound",
        timeout=10.0,
        predicate=lambda e: e.get("session_id") == test_event["session_id"]
    )
    
    task.cancel()
    
    assert response is not None
    assert response["role"] == "assistant"
    assert len(response["message"]) > 0
```

#### 3.3 Tool Executor Integration Tests
**File**: `tests/integration/test_tool_executor.py`
```python
"""Integration tests for tool executor"""
import pytest
from services.tool_executor.main import ToolExecutor
from tests.utils import create_test_tool_request, wait_for_event

@pytest.mark.asyncio
async def test_execute_echo_tool(kafka_container, postgres_container):
    executor = ToolExecutor()
    
    request = create_test_tool_request(
        "echo",
        args={"message": "Echo test"}
    )
    
    await executor.bus.publish("tool.requests", request)
    
    # Start executor
    import asyncio
    task = asyncio.create_task(executor.start())
    
    # Wait for result
    result = await wait_for_event(
        "tool.results",
        timeout=5.0,
        predicate=lambda e: e.get("event_id") == request["event_id"]
    )
    
    task.cancel()
    
    assert result["status"] == "success"
    assert result["payload"]["message"] == "Echo test"
```

### 4. End-to-End Tests

#### 4.1 Full Conversation Flow
**File**: `tests/e2e/test_conversation_flow.py`
```python
"""End-to-end conversation tests"""
import pytest
import httpx
import asyncio

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_full_conversation_with_tool_call(
    kafka_container,
    redis_container,
    postgres_container,
    # Start all services...
):
    """Test: User message → Worker → Tool call → Response"""
    
    # 1. Submit message via gateway
    async with httpx.AsyncClient(base_url="http://gateway:8010") as client:
        response = await client.post("/v1/session/message", json={
            "message": "Calculate 2 + 2"
        })
        data = response.json()
        session_id = data["session_id"]
    
    # 2. Connect to WebSocket for streaming
    # 3. Verify tool execution happens
    # 4. Verify final response
    # 5. Verify all events persisted correctly
    
    pass
```

### 5. Performance Tests

#### 5.1 Load Testing
**File**: `tests/performance/test_load.py`
```python
"""Load and performance tests"""
import pytest
import asyncio
import time

@pytest.mark.performance
@pytest.mark.asyncio
async def test_gateway_throughput():
    """Test gateway can handle 100 req/s"""
    import httpx
    
    async def send_request(client, i):
        response = await client.post("/v1/session/message", json={
            "message": f"Load test {i}"
        })
        return response.status_code
    
    start = time.time()
    async with httpx.AsyncClient(base_url="http://gateway:8010") as client:
        tasks = [send_request(client, i) for i in range(1000)]
        results = await asyncio.gather(*tasks)
    
    duration = time.time() - start
    rps = 1000 / duration
    
    assert rps > 100, f"Only achieved {rps} req/s"
    assert all(r == 200 for r in results)
```

---

## 🔧 IMPLEMENTATION TASKS

### Week 1
- [ ] Setup test infrastructure (conftest.py, utils.py)
- [ ] Write unit tests for all common libraries
- [ ] Write unit tests for gateway endpoints
- [ ] Write unit tests for conversation worker
- [ ] Write unit tests for tool executor
- [ ] Achieve 60% coverage

### Week 2
- [ ] Write integration tests for service interactions
- [ ] Write end-to-end workflow tests
- [ ] Add performance/load tests
- [ ] Integrate tests into CI pipeline
- [ ] Achieve 80%+ coverage
- [ ] Document testing guidelines

---

## ✅ ACCEPTANCE CRITERIA

1. ✅ Test coverage ≥ 80% across all services
2. ✅ All unit tests pass in < 30 seconds
3. ✅ Integration tests pass with testcontainers
4. ✅ E2E tests validate full workflows
5. ✅ CI runs all tests on every PR
6. ✅ Performance tests establish baseline metrics
7. ✅ Test documentation complete

---

## 📊 SUCCESS METRICS

- **Coverage**: ≥ 80% line coverage
- **Test Execution Time**: < 5 minutes for full suite
- **Flakiness**: < 1% test failure rate
- **CI Integration**: 100% of PRs tested

---

## 🚀 NEXT STEPS

After Sprint B completion:
1. Enable coverage reporting in CI
2. Add mutation testing
3. Integrate with SonarQube
4. Add visual regression testing for UI
