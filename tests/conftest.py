import asyncio
import os

import pytest
import pytest_asyncio
from testcontainers.kafka import KafkaContainer
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

# Enable Playwright pytest plugin
pytest_plugins = ["playwright.sync_api"]


@pytest.fixture(scope="session")
def event_loop():
	"""Create a fresh event loop for the test session."""

	loop = asyncio.new_event_loop()
	yield loop
	loop.close()


@pytest.fixture(scope="session")
def kafka_container() -> KafkaContainer:
	"""Spin up Kafka via testcontainers and expose its bootstrap server."""

	with KafkaContainer() as container:
		os.environ["KAFKA_BOOTSTRAP_SERVERS"] = container.get_bootstrap_server()
		yield container


@pytest.fixture(scope="session")
def redis_container() -> RedisContainer:
	"""Spin up Redis and export REDIS_URL for the application."""

	with RedisContainer() as container:
		if hasattr(container, "get_connection_url"):
			connection_url = container.get_connection_url()
		else:  # pragma: no cover - fallback for older testcontainers
			host = container.get_container_host_ip()
			port = container.get_exposed_port(6379)
			connection_url = f"redis://{host}:{port}/0"
		os.environ["REDIS_URL"] = connection_url
		yield container


@pytest.fixture(scope="session")
def postgres_container() -> PostgresContainer:
	"""Provision Postgres for integration tests."""

	with PostgresContainer("postgres:16-alpine") as container:
		os.environ["POSTGRES_DSN"] = container.get_connection_url()
		yield container


@pytest_asyncio.fixture
async def clean_kafka(kafka_container):
	"""Placeholder fixture to ensure Kafka is initialised before tests."""

	yield


@pytest_asyncio.fixture
async def clean_redis(redis_container):
	"""Flush Redis databases before each test and return a client handle."""

	import redis.asyncio as redis_lib

	client = redis_lib.from_url(os.environ["REDIS_URL"])
	await client.flushall()
	try:
		yield client
	finally:
		await client.close()


@pytest_asyncio.fixture
async def clean_postgres(postgres_container):
	"""Truncate key tables in Postgres before running assertions."""

	import asyncpg

	conn = await asyncpg.connect(os.environ["POSTGRES_DSN"])
	try:
		for table in ("session_events", "model_profiles", "delegation_tasks"):
			try:
				await conn.execute(f'TRUNCATE "{table}" CASCADE')
			except Exception:
				continue
		yield conn
	finally:
		await conn.close()
