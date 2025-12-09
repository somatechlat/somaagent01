"""Functional test configuration - requires REAL infrastructure.

Functional tests run against real infrastructure:
- PostgreSQL database
- Redis cache
- Kafka message broker
- SomaBrain cognitive memory service
- OPA policy engine

These tests validate the complete system behavior with real services.

REQUIREMENTS:
- All infrastructure must be running (use `make deps-up` or `make dev-up`)
- Environment variables must be set for real service connections
- SA01_SOMA_BASE_URL must point to a running SomaBrain instance

To run functional tests:
    pytest tests/functional/ -v

To skip functional tests in CI without infrastructure:
    pytest tests/ --ignore=tests/functional/
"""

import os
import pytest
import asyncio
from typing import AsyncGenerator

# Verify required environment variables are set for real infrastructure
REQUIRED_ENV_VARS = [
    "SA01_SOMA_BASE_URL",
    "SA01_DB_DSN",
    "SA01_REDIS_URL",
]


def pytest_configure(config):
    """Verify real infrastructure environment is configured."""
    missing = [var for var in REQUIRED_ENV_VARS if not os.environ.get(var)]
    if missing:
        pytest.skip(
            f"Functional tests require real infrastructure. "
            f"Missing environment variables: {', '.join(missing)}. "
            f"Run `make deps-up` to start infrastructure."
        )


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_pool():
    """Create a real database connection pool for functional tests."""
    from src.core.config import cfg
    import asyncpg
    
    dsn = cfg.env("SA01_DB_DSN")
    pool = await asyncpg.create_pool(dsn, min_size=1, max_size=5)
    yield pool
    await pool.close()


@pytest.fixture(scope="session")
async def redis_client():
    """Create a real Redis client for functional tests."""
    from src.core.config import cfg
    import redis.asyncio as redis
    
    url = cfg.env("SA01_REDIS_URL")
    client = redis.from_url(url)
    yield client
    await client.close()


@pytest.fixture(scope="session")
async def soma_client():
    """Create a real SomaBrain client for functional tests."""
    from python.integrations.soma_client import SomaClient
    
    client = SomaClient.get()
    yield client
    await client.close()


@pytest.fixture
async def clean_test_data(db_pool):
    """Fixture to clean up test data after each test.
    
    Usage:
        async def test_something(clean_test_data):
            # Create test data
            yield
            # Data is automatically cleaned up
    """
    created_ids = []
    
    def track(table: str, id_value):
        created_ids.append((table, id_value))
    
    yield track
    
    # Cleanup
    async with db_pool.acquire() as conn:
        for table, id_value in created_ids:
            try:
                await conn.execute(f"DELETE FROM {table} WHERE id = $1", id_value)
            except Exception:
                pass  # Best effort cleanup


@pytest.fixture
async def test_tenant_id():
    """Provide a unique tenant ID for test isolation."""
    import uuid
    return f"test-tenant-{uuid.uuid4().hex[:8]}"


@pytest.fixture
async def test_session_id():
    """Provide a unique session ID for test isolation."""
    import uuid
    return f"test-session-{uuid.uuid4().hex[:8]}"
