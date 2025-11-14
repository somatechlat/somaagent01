import os

import pytest
import pytest_asyncio

from services.common import env

RUN_INTEGRATION = (env.get("RUN_INTEGRATION", "") or "").lower() in {"1", "true", "yes"}
if RUN_INTEGRATION:
    from testcontainers.kafka import KafkaContainer
    from testcontainers.postgres import PostgresContainer
    from testcontainers.redis import RedisContainer

# Enable Playwright pytest plugin only when explicitly requested
if env.get("RUN_PLAYWRIGHT"):
    pytest_plugins = ["playwright.sync_api"]
else:
    pytest_plugins = []


# NOTE:
# Do not override pytest-asyncio's built-in `event_loop` fixture.
# Overriding it is deprecated and will break in future versions.
# If a specific test needs a session-scoped loop, mark it with:
#   @pytest.mark.asyncio(scope="session")
# If a different loop type/policy is required, provide an
# `event_loop_policy` fixture instead.


if RUN_INTEGRATION:

    @pytest.fixture(scope="session")
    def kafka_container() -> "KafkaContainer":
        """Spin up Kafka via testcontainers and expose its bootstrap server."""

        with KafkaContainer() as container:
            os.environ["SA01_KAFKA_BOOTSTRAP_SERVERS"] = container.get_bootstrap_server()
            env.refresh()
            yield container


if RUN_INTEGRATION:

    @pytest.fixture(scope="session")
    def redis_container() -> "RedisContainer":
        """Spin up Redis and export SA01_REDIS_URL for the application."""

        with RedisContainer() as container:
            if hasattr(container, "get_connection_url"):
                connection_url = container.get_connection_url()
                host = container.get_container_host_ip()
                port = container.get_exposed_port(6379)
                connection_url = f"redis://{host}:{port}/0"
            os.environ["SA01_REDIS_URL"] = connection_url
            yield container


if RUN_INTEGRATION:

    @pytest.fixture(scope="session")
    def postgres_container() -> "PostgresContainer":
        """Provision Postgres for integration tests."""

        with PostgresContainer("postgres:16-alpine") as container:
            os.environ["SA01_DB_DSN"] = container.get_connection_url()
            yield container


if RUN_INTEGRATION:

    @pytest_asyncio.fixture
    async def clean_kafka(kafka_container):
        """Placeholder fixture to ensure Kafka is initialised before tests."""

        yield


if RUN_INTEGRATION:

    @pytest_asyncio.fixture
    async def clean_redis(redis_container):
        """Flush Redis databases before each test and return a client handle."""

        import redis.asyncio as redis_lib

        client = redis_lib.from_url(os.environ["SA01_REDIS_URL"])
        await client.flushall()
        try:
            yield client
        finally:
            await client.close()


if RUN_INTEGRATION:

    @pytest_asyncio.fixture
    async def clean_postgres(postgres_container):
        """Truncate key tables in Postgres before running assertions."""

        import asyncpg

        conn = await asyncpg.connect(os.environ["SA01_DB_DSN"])
        try:
            for table in ("session_events", "model_profiles", "delegation_tasks"):
                try:
                    await conn.execute(f'TRUNCATE "{table}" CASCADE')
                except Exception:
                    continue
            yield conn
        finally:
            await conn.close()
