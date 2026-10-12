"""Shared fixtures for Agent Chat integration tests.

VIBE COMPLIANT:
- Real infrastructure only (PostgreSQL, Redis, SomaBrain, Milvus)
- No mocks, no fakes
- Tests against live docker-compose services

Requirements:
- SA01_INFRA_AVAILABLE=1 environment variable
- Live standalone stack: infra/standalone/docker-compose.yml (somaagent_*)
"""

from __future__ import annotations

import asyncio
import os
import secrets as _secrets
from typing import AsyncIterator, TYPE_CHECKING
from uuid import uuid4

import pytest

if TYPE_CHECKING:
    from services.common.chat_service import ChatService

# Skip all tests if infrastructure not available
INFRA_AVAILABLE = os.environ.get("SA01_INFRA_AVAILABLE") == "1"

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not INFRA_AVAILABLE, reason="Requires SA01_INFRA_AVAILABLE=1"),
]


# =============================================================================
# Infrastructure Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def real_infrastructure():
    """Validate that required infrastructure is running."""
    import socket

    services = [
        ("somaagent_postgres", 5432, "PostgreSQL"),
        ("somaagent_redis", 6379, "Redis"),
        ("somaagent_standalone", 9000, "Agent API"),
    ]

    for host, port, name in services:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        if result != 0:
            pytest.skip(f"{name} not available at {host}:{port}")

    return True


@pytest.fixture(scope="session", autouse=True)
def django_db_setup():
    """Configure Django for testing.

    VIBE COMPLIANT: Uses live standalone PostgreSQL (somaagent_postgres:5432)

    VIBE Rule 7: Uses real Docker Compose PostgreSQL - NO mocks!

    autouse=True ensures Django is configured before any test runs.
    """
    import django
    from django.conf import settings

    # Only configure if not already configured
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            SECRET_KEY=_secrets.token_urlsafe(50),
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.postgresql",
                    "HOST": "somaagent_postgres",
                    "PORT": 5432,
                    "NAME": "somaagent",
                    "USER": "somaagent",
                    "PASSWORD": os.environ.get("TEST_DB_PASSWORD", ""),  # From Vault, never a literal
                    "CONN_MAX_AGE": 60,  # Connection pooling
                    "OPTIONS": {
                        "connect_timeout": 5,
                    },
                    "ATOMIC_REQUESTS": False,  # Disable for manual transaction handling
                },
            },
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
                "django.contrib.postgres",
                "admin.core",
                "admin.aaas",
                "admin.chat",
                "admin.agents",
            ],
            USE_TZ=True,
            TIME_ZONE="UTC",
            LOGGING={
                "version": 1,
                "handlers": {
                    "console": {
                        "class": "logging.StreamHandler",
                    },
                },
                "loggers": {
                    "django.db.backends": {
                        "handlers": ["console"],
                        "level": "INFO",
                    },
                },
            },
        )
        django.setup()

        # Tables already exist in real AAAS database
        # No need to create them - they're managed by Django migrations in the running container
        # VIBE Rule 7: Real infrastructure means real databases with real schema


# =============================================================================
# Authentication Fixtures
# =============================================================================


@pytest.fixture
def test_tenant_id() -> str:
    return os.environ.get("TEST_TENANT_ID", str(uuid4()))


@pytest.fixture
def test_user_id() -> str:
    return os.environ.get("TEST_USER_ID", str(uuid4()))


@pytest.fixture
def test_agent_id() -> str:
    return os.environ.get("TEST_AGENT_ID", str(uuid4()))


@pytest.fixture
def auth_token() -> str:
    # In production tests, this would authenticate against Keycloak
    # For integration tests, use test token from environment
    return os.environ.get("TEST_AUTH_TOKEN", "test_integration_token")


# =============================================================================
# Service Fixtures
# =============================================================================


@pytest.fixture
def chat_service() -> "ChatService":
    """Get configured ChatService instance.

    VIBE COMPLIANT: Uses real ChatService implementation with actual infrastructure
    (no mocks, no fakes, real PostgreSQL, Redis, SomaBrain).
    """
    from services.common.chat_service import ChatService

    # ChatService only accepts somabrain_url and timeout parameters
    # Memory operations use SomaBrainClient internally
    return ChatService(
        somabrain_url=os.environ.get("SA01_SOMA_BASE_URL", "http://somabrain-somabrain_standalone_app-1:30101"),
        timeout=30.0,
    )


@pytest.fixture
async def governor(real_infrastructure):
    from services.common.simple_governor import get_governor, SimpleGovernor

    # SimpleGovernor doesn't require complex dependencies
    # It uses binary health/degraded decision model
    gov = get_governor()

    assert isinstance(gov, SimpleGovernor), "Should return SimpleGovernor instance"

    yield gov


@pytest.fixture
def context_builder(real_infrastructure):
    """Get a ContextBuilder.

    It takes no client: the memory lane is fed by ``memory_hits`` at build
    time, from ``MemoryGateway.recall()``. There is no DI slot to configure.
    """
    from admin.core.context.builder import ContextBuilder

    return ContextBuilder()


# =============================================================================
# Conversation Fixtures
# =============================================================================


@pytest.fixture
async def conversation_id(chat_service, test_agent_id, test_user_id, test_tenant_id) -> str:
    """Create a test conversation."""
    conversation = await chat_service.create_conversation(
        agent_id=test_agent_id,
        user_id=test_user_id,
        tenant_id=test_tenant_id,
    )
    return str(conversation.id)


# =============================================================================
# WebSocket Fixtures
# =============================================================================


@pytest.fixture
def websocket_url(auth_token) -> str:
    base = os.environ.get("SA01_WS_URL", "ws://somaagent_standalone:9000")
    return f"{base}/ws/v2/chat/?token={auth_token}"


# =============================================================================
# Helper Functions
# =============================================================================


async def collect_stream(stream: AsyncIterator[str], limit: int = 100) -> list[str]:
    """Collect tokens from a stream."""
    tokens = []
    async for token in stream:
        tokens.append(token)
        if len(tokens) >= limit:
            break
    return tokens
