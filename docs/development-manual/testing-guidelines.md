# Testing Guidelines

**Standards**: ISO/IEC 29119§4

## Testing Strategy

### Test Pyramid

```
        /\
       /E2E\      10% - End-to-end tests
      /------\
     /  INT   \   30% - Integration tests
    /----------\
   /   UNIT     \ 60% - Unit tests
  /--------------\
```

### Coverage Targets

| Type | Target | Enforcement |
|------|--------|-------------|
| Unit | 80% | CI blocks < 80% |
| Integration | 70% | CI warns < 70% |
| E2E | Critical paths | Manual review |

## Unit Tests

### Structure

```python
import pytest
from services.conversation_worker.main import ConversationWorker

class TestConversationWorker:
    """Tests for ConversationWorker."""
    
    @pytest.fixture
    async def worker(self):
        """Create worker instance."""
        return ConversationWorker()
    
    async def test_process_message_success(self, worker):
        """Test successful message processing."""
        # Arrange
        message = {"session_id": "test123", "content": "Hello"}
        
        # Act
        result = await worker.process_message(message)
        
        # Assert
        assert result["status"] == "success"
        assert "response" in result
```

### Naming Convention

```python
# Pattern: test_<function>_<scenario>_<expected>

def test_validate_session_id_valid_input_returns_true():
    pass

def test_validate_session_id_empty_string_raises_value_error():
    pass

def test_fetch_session_not_found_returns_none():
    pass
```

### Mocking

```python
from unittest.mock import AsyncMock, patch

async def test_llm_call_timeout_raises_timeout_error():
    """Test LLM call timeout handling."""
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.side_effect = httpx.TimeoutException("Timeout")
        
        with pytest.raises(TimeoutError):
            await call_llm("test prompt")
```

### Fixtures

```python
# conftest.py
import pytest
import asyncpg

@pytest.fixture
async def db_pool():
    """Create test database pool."""
    pool = await asyncpg.create_pool(
        "postgresql://test:test@localhost:5432/testdb"
    )
    yield pool
    await pool.close()

@pytest.fixture
async def clean_db(db_pool):
    """Clean database before each test."""
    async with db_pool.acquire() as conn:
        await conn.execute("TRUNCATE sessions, session_events CASCADE")
```

### Running Unit Tests

```bash
# All unit tests
pytest tests/unit/

# Specific test file
pytest tests/unit/test_gateway_authorization.py

# Specific test
pytest tests/unit/test_gateway_authorization.py::test_jwt_valid_token_allows_access

# With coverage
pytest tests/unit/ --cov=services --cov-report=html

# Parallel execution
pytest tests/unit/ -n auto
```

## Integration Tests

### Database Tests

```python
import pytest
import asyncpg

@pytest.mark.integration
async def test_session_repository_create_and_fetch(db_pool):
    """Test session creation and retrieval."""
    from services.common.session_repository import SessionRepository
    
    repo = SessionRepository(db_pool)
    
    # Create session
    session_id = await repo.create_session(
        tenant="test",
        persona_id="default"
    )
    
    # Fetch session
    session = await repo.get_session(session_id)
    
    assert session is not None
    assert session["tenant"] == "test"
    assert session["persona_id"] == "default"
```

### Kafka Tests

```python
import pytest
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer

@pytest.mark.integration
async def test_kafka_publish_and_consume():
    """Test Kafka message flow."""
    producer = AIOKafkaProducer(bootstrap_servers='localhost:20000')
    await producer.start()
    
    consumer = AIOKafkaConsumer(
        'test-topic',
        bootstrap_servers='localhost:20000',
        auto_offset_reset='earliest'
    )
    await consumer.start()
    
    # Publish
    await producer.send('test-topic', b'test message')
    
    # Consume
    msg = await consumer.getone()
    assert msg.value == b'test message'
    
    await producer.stop()
    await consumer.stop()
```

### API Tests

```python
import pytest
import httpx

@pytest.mark.integration
async def test_gateway_health_endpoint():
    """Test gateway health check."""
    async with httpx.AsyncClient() as client:
      response = await client.get(f"http://localhost:{int(os.getenv('GATEWAY_PORT', '21016'))}/v1/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
```

### Running Integration Tests

```bash
# Start test infrastructure
make deps-up

# Run integration tests
pytest tests/integration/

# With specific marker
pytest -m integration

# Skip slow tests
pytest -m "integration and not slow"
```

## End-to-End Tests

### Playwright Tests

```python
import pytest
from playwright.async_api import async_playwright

@pytest.mark.e2e
async def test_full_conversation_flow():
    """Test complete user conversation flow."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Open Web UI (served by Gateway)
        await page.goto("http://localhost:21016/")
        
        # Send message
        await page.fill("#chat-input", "Hello, agent!")
        await page.click("#send-button")
        
        # Wait for response
        response = await page.wait_for_selector(".agent-message")
        assert await response.text_content()
        
        await browser.close()
```

### API Flow Tests

```python
@pytest.mark.e2e
async def test_message_processing_end_to_end():
    """Test message from gateway to response."""
    async with httpx.AsyncClient() as client:
        # Start a session by sending the first message (session created if omitted)
        response = await client.post(
          f"http://localhost:{int(os.getenv('GATEWAY_PORT', '21016'))}/v1/session/message",
          json={"session_id": None, "message": "What is 2+2?"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "response" in result
```

### Running E2E Tests

```bash
# Start full stack
make up

# Run E2E tests
pytest tests/e2e/

# With browser visible (headed mode)
pytest tests/e2e/ --headed

# Specific browser
pytest tests/e2e/ --browser firefox
```

## Load Tests

### K6 Script

```javascript
// scripts/loadtest_k6.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '30s', target: 10 },  // Ramp up
    { duration: '1m', target: 10 },   // Steady
    { duration: '30s', target: 0 },   // Ramp down
  ],
};

export default function () {
  let response = http.post(
    `http://localhost:${__ENV.GATEWAY_PORT || 21016}/v1/session/message`,
    JSON.stringify({ message: 'Hello' }),
    { headers: { 'Content-Type': 'application/json' } }
  );
  
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 2s': (r) => r.timings.duration < 2000,
  });
  
  sleep(1);
}
```

### Running Load Tests

```bash
# Install k6
brew install k6  # macOS
# or download from https://k6.io/

# Run load test
k6 run scripts/loadtest_k6.js

# With custom VUs and duration
k6 run --vus 50 --duration 5m scripts/loadtest_k6.js

# Output to InfluxDB
k6 run --out influxdb=http://localhost:8086/k6 scripts/loadtest_k6.js
```

## Test Data

### Factories

```python
# tests/factories.py
import factory
from datetime import datetime

class SessionFactory(factory.Factory):
    class Meta:
        model = dict
    
    session_id = factory.Faker('uuid4')
    tenant = "test"
    persona_id = "default"
    created_at = factory.LazyFunction(datetime.utcnow)

class MessageFactory(factory.Factory):
    class Meta:
        model = dict
    
    session_id = factory.Faker('uuid4')
    role = "user"
    content = factory.Faker('sentence')
```

### Usage

```python
from tests.factories import SessionFactory, MessageFactory

def test_with_factory():
    session = SessionFactory()
    message = MessageFactory(session_id=session['session_id'])
    
    assert message['session_id'] == session['session_id']
```

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
      
      kafka:
        image: apache/kafka:latest
        ports:
          - 9092:9092
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio
      
      - name: Run unit tests
        run: pytest tests/unit/ --cov=services --cov-report=xml
      
      - name: Run integration tests
        run: pytest tests/integration/
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

## Test Markers

```python
# pytest.ini
[pytest]
markers =
    unit: Unit tests (fast, no external dependencies)
    integration: Integration tests (require infrastructure)
    e2e: End-to-end tests (full stack required)
    slow: Slow tests (> 1 second)
    smoke: Smoke tests (critical paths only)
```

### Usage

```bash
# Run only unit tests
pytest -m unit

# Run integration and e2e
pytest -m "integration or e2e"

# Skip slow tests
pytest -m "not slow"

# Smoke tests only
pytest -m smoke
```

## Debugging Tests

### Verbose Output

```bash
# Show print statements
pytest -s

# Verbose mode
pytest -v

# Show locals on failure
pytest -l

# Stop on first failure
pytest -x
```

### PDB Debugging

```python
def test_with_debugging():
    result = complex_function()
    
    import pdb; pdb.set_trace()  # Breakpoint
    
    assert result == expected
```

### Logging

```python
import logging

def test_with_logging(caplog):
    """Test with log capture."""
    caplog.set_level(logging.INFO)
    
    function_that_logs()
    
    assert "Expected log message" in caplog.text
```

## Best Practices

### DO

- ✅ Write tests before fixing bugs (TDD)
- ✅ Test one thing per test
- ✅ Use descriptive test names
- ✅ Arrange-Act-Assert pattern
- ✅ Clean up resources (fixtures)
- ✅ Mock external dependencies
- ✅ Test edge cases and errors
- ✅ Keep tests fast (< 1s per test)

### DON'T

- ❌ Test implementation details
- ❌ Share state between tests
- ❌ Use sleep() for timing
- ❌ Hardcode test data
- ❌ Skip cleanup
- ❌ Test multiple things in one test
- ❌ Ignore flaky tests
- ❌ Commit commented-out tests

## Coverage Reports

```bash
# Generate HTML report
pytest --cov=services --cov-report=html

# View report
open htmlcov/index.html

# Terminal report
pytest --cov=services --cov-report=term-missing

# Fail if coverage < 80%
pytest --cov=services --cov-fail-under=80
```
