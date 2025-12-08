# SomaAgent01 Coding Standards

**Standards**: ISO/IEC 12207§8.3

## Core Philosophy: Code is Truth

- **No AI Slop**: Do not add comments that merely restate the code. If the code is clear, no comment is needed.
- **Why, Not What**: Comments must explain the *reasoning* behind the logic, not the logic itself.
- **Documentation**: Documentation must strictly match the implementation. If there is a discrepancy, the code is the source of truth, and the documentation must be updated.

## Python Style Guide

### PEP 8 Compliance

All Python code must follow [PEP 8](https://peps.python.org/pep-0008/).

**Enforced by**:
- `black` (formatter)
- `ruff` (linter)
- `pyright` (type checker)

### Formatting

```bash
# Format code
black .

# Check formatting
black --check .

# Lint
ruff check --fix

# Type check
pyright .
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Module | `snake_case` | `conversation_worker.py` |
| Class | `PascalCase` | `ConversationWorker` |
| Function | `snake_case` | `process_message()` |
| Variable | `snake_case` | `session_id` |
| Constant | `UPPER_SNAKE_CASE` | `MAX_RETRIES` |
| Private | `_leading_underscore` | `_internal_method()` |

### Type Hints

**Required** for all public functions:

```python
def process_message(
    session_id: str,
    message: str,
    timeout: float = 30.0
) -> dict[str, Any]:
    """Process a user message.
    
    Args:
        session_id: Unique session identifier
        message: User message text
        timeout: Processing timeout in seconds
        
    Returns:
        Response dictionary with 'content' and 'metadata'
        
    Raises:
        TimeoutError: If processing exceeds timeout
        ValueError: If message is empty
    """
    pass
```

### Docstrings & Comments

**Google style** for all modules, classes, and public functions.

**Rules for Comments:**
1.  **No Redundancy**: Avoid comments like `# Increment i` for `i += 1`.
2.  **Explain Why**: Focus on architectural decisions, trade-offs, and complex logic.
    *   *Bad*: `# Check if n is prime`
    *   *Good*: `# Using deterministic Miller-Rabin for performance on large inputs.`
3.  **No "AI Slop"**: Remove verbose, generated-sounding fluff. Keep it professional and concise.

```python
"""Module for conversation processing.

This module handles user messages, LLM calls, and response generation.
It consumes from conversation.inbound and publishes to conversation.outbound.
"""

def calculate_backoff(retry_count: int) -> float:
    # Exponential backoff with jitter to prevent thundering herd problem
    base = 2 ** retry_count
    return base + random.uniform(0, 0.1)
```

### Imports

**Order**:
1. Standard library
2. Third-party
3. Local

**Alphabetical** within each group:

```python
# Standard library
import asyncio
import logging
from typing import Any

# Third-party
import httpx
from aiokafka import AIOKafkaConsumer

# Local
from services.common.event_bus import EventBus
from services.common.logging_config import setup_logging
```

### Error Handling

**Explicit exception types**:

```python
# ❌ Bad
try:
    result = await call_llm()
except:
    pass

# ✅ Good
try:
    result = await call_llm()
except httpx.TimeoutException as e:
    logger.error("LLM call timed out", error=str(e))
    raise
except httpx.HTTPStatusError as e:
    logger.error("LLM API error", status_code=e.response.status_code)
    raise
```

### Logging

**Structured logging** with context:

```python
import structlog

logger = structlog.get_logger(__name__)

# ✅ Good
logger.info(
    "message_processed",
    session_id=session_id,
    message_length=len(message),
    duration_ms=duration * 1000
)

# ❌ Bad
logger.info(f"Processed message for {session_id}")
```

### Async/Await

**Prefer async** for I/O operations:

```python
# ✅ Good
async def fetch_session(session_id: str) -> Session:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"/sessions/{session_id}")
        return Session(**response.json())

# ❌ Bad (blocking)
def fetch_session(session_id: str) -> Session:
    response = requests.get(f"/sessions/{session_id}")
    return Session(**response.json())
```

## Code Organization

### File Structure

```
services/
├── gateway/
│   ├── __init__.py
│   ├── main.py           # Entry point
│   ├── dependencies.py   # FastAPI dependencies
│   └── routes/
│       ├── __init__.py
│       ├── health.py
│       └── session.py
├── conversation_worker/
│   ├── __init__.py
│   ├── main.py
│   └── policy_integration.py
└── common/
    ├── __init__.py
    ├── event_bus.py
    └── logging_config.py
```

### Module Size

- **Max 500 lines** per file
- **Max 50 lines** per function
- **Max 10 parameters** per function

If exceeded, refactor into smaller modules.

## Testing Standards

### Test Structure

```python
import pytest

class TestConversationWorker:
    """Tests for ConversationWorker."""
    
    @pytest.fixture
    async def worker(self):
        """Create worker instance."""
        return ConversationWorker()
    
    async def test_process_message_success(self, worker):
        """Test successful message processing."""
        # Arrange
        message = "Hello"
        
        # Act
        result = await worker.process_message(message)
        
        # Assert
        assert result["status"] == "success"
        assert "content" in result
```

### Test Coverage

- **Minimum 80%** line coverage
- **100%** for critical paths (auth, payment, data loss)

```bash
# Run with coverage
pytest --cov=services --cov-report=html

# View report
open htmlcov/index.html
```

## Security Standards

### Input Validation

```python
from pydantic import BaseModel, Field, validator

class MessageRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1, max_length=10000)
    
    @validator("session_id")
    def validate_session_id(cls, v):
        if not v.isalnum():
            raise ValueError("session_id must be alphanumeric")
        return v
```

### Secrets Handling

```python
# ❌ Bad
logger.info(f"Using API key: {api_key}")

# ✅ Good
logger.info("Using API key", key_prefix=api_key[:8])
```

### SQL Injection Prevention

```python
# ✅ Good (parameterized)
await conn.execute(
    "SELECT * FROM sessions WHERE id = $1",
    session_id
)

# ❌ Bad (vulnerable)
await conn.execute(
    f"SELECT * FROM sessions WHERE id = '{session_id}'"
)
