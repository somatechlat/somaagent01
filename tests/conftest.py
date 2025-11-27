import os

import pytest
import pytest_asyncio

from src.core.config import cfg

RUN_INTEGRATION = (
    cfg.env(os.getenv(os.getenv("")), os.getenv(os.getenv(""))) or os.getenv(os.getenv(""))
).lower() in {os.getenv(os.getenv("")), os.getenv(os.getenv("")), os.getenv(os.getenv(""))}
if RUN_INTEGRATION:
    from testcontainers.kafka import KafkaContainer
    from testcontainers.postgres import PostgresContainer
    from testcontainers.redis import RedisContainer
if cfg.env(os.getenv(os.getenv(""))):
    pytest_plugins = [os.getenv(os.getenv(""))]
else:
    pytest_plugins = []
if RUN_INTEGRATION:

    @pytest.fixture(scope=os.getenv(os.getenv("")))
    def kafka_container() -> os.getenv(os.getenv("")):
        os.getenv(os.getenv(""))
        with KafkaContainer() as container:
            os.environ[os.getenv(os.getenv(""))] = container.get_bootstrap_server()
            yield container


if RUN_INTEGRATION:

    @pytest.fixture(scope=os.getenv(os.getenv("")))
    def redis_container() -> os.getenv(os.getenv("")):
        os.getenv(os.getenv(""))
        with RedisContainer() as container:
            if hasattr(container, os.getenv(os.getenv(""))):
                connection_url = container.get_connection_url()
                host = container.get_container_host_ip()
                port = container.get_exposed_port(int(os.getenv(os.getenv(""))))
                connection_url = f"redis://{host}:{port}/0"
            os.environ[os.getenv(os.getenv(""))] = connection_url
            yield container


if RUN_INTEGRATION:

    @pytest.fixture(scope=os.getenv(os.getenv("")))
    def postgres_container() -> os.getenv(os.getenv("")):
        os.getenv(os.getenv(""))
        with PostgresContainer(os.getenv(os.getenv(""))) as container:
            os.environ[os.getenv(os.getenv(""))] = container.get_connection_url()
            yield container


if RUN_INTEGRATION:

    @pytest_asyncio.fixture
    async def clean_kafka(kafka_container):
        os.getenv(os.getenv(""))
        yield


if RUN_INTEGRATION:

    @pytest_asyncio.fixture
    async def clean_redis(redis_container):
        os.getenv(os.getenv(""))
        import redis.asyncio as redis_lib

        client = redis_lib.from_url(os.environ[os.getenv(os.getenv(""))])
        await client.flushall()
        try:
            yield client
        finally:
            await client.close()


if RUN_INTEGRATION:

    @pytest_asyncio.fixture
    async def clean_postgres(postgres_container):
        os.getenv(os.getenv(""))
        import asyncpg

        conn = await asyncpg.connect(os.environ[os.getenv(os.getenv(""))])
        try:
            for table in (os.getenv(os.getenv("")), os.getenv(os.getenv(""))):
                try:
                    await conn.execute(f'TRUNCATE "{table}" CASCADE')
                except Exception:
                    continue
            yield conn
        finally:
            await conn.close()
