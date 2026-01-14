"""Shared fixtures for Agent Chat integration tests.

VIBE COMPLIANT:
- Real infrastructure only (PostgreSQL, Redis, SomaBrain, Milvus)
- No mocks, no fakes
- Tests against live docker-compose services

Requirements:
- SA01_INFRA_AVAILABLE=1 environment variable
- Running: docker-compose -f infra/saas/docker-compose.yml up -d
"""

from __future__ import annotations

import asyncio
import os
from typing import TYPE_CHECKING, AsyncIterator
from uuid import uuid4

import pytest
from asgiref.sync import sync_to_async

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
        ("localhost", 63932, "PostgreSQL"),  # somastack_postgres
        ("localhost", 63979, "Redis"),  # somastack_redis
        ("localhost", 63900, "Agent API"),  # somastack_saas:9000
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
def django_db_setup(real_infrastructure):
    """Configure Django for testing.
    
    VIBE COMPLIANT: Uses real infrastructure (PostgreSQL on port 63932)
    
    VIBE Rule 7: Uses real Docker Compose PostgreSQL - NO mocks!
    
    autouse=True ensures Django is configured before any test runs.
    Depends on real_infrastructure to ensure database is accessible.
    """
    import django
    from django.conf import settings
    
    # Only configure if not already configured
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            SECRET_KEY="test-secret-key-for-e2e-tests-vibe-compliant",
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.postgresql",
                    "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
                    "PORT": int(os.environ.get("POSTGRES_PORT", "63932")),
                    "NAME": os.environ.get("POSTGRES_DB", "somaagent"),
                    "USER": os.environ.get("POSTGRES_USER", "soma"),  # Docker uses "soma"
                    "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "soma"),  # Docker uses "soma"
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
                "admin.saas",
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
        
        # Create tables with Django migrations
        from django.core.management import execute_from_command_line
        from io import StringIO
        import sys
        
        # Capture migration output
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            # Create tables directly (avoid makemigrations issue)
            from django.db import connection
            with connection.schema_editor() as schema_editor:
                # Create content types table
                from django.contrib.contenttypes.models import ContentType
                schema_editor.create_model(ContentType)
                
                # Create auth tables
                from django.contrib.auth.models import User, Permission
                schema_editor.create_model(User)
                
                # Import and create app tables
                from admin.chat.models import Conversation, Message
                from admin.agents.models import Agent, Capsule
                from admin.saas.models import Tenant, APIKey
                
                # Create in correct order (respecting foreign keys)
                schema_editor.create_model(Tenant)
                schema_editor.create_model(Agent)
                schema_editor.create_model(Capsule)
                schema_editor.create_model(Conversation)
                schema_editor.create_model(Message)
                schema_editor.create_model(APIKey)
                
        finally:
            sys.stdout = old_stdout


# =============================================================================
# Authentication Fixtures
# =============================================================================


@pytest.fixture
def test_tenant_id() -> str:
    """Get or create test tenant ID."""
    return os.environ.get("TEST_TENANT_ID", str(uuid4()))


@pytest.fixture
def test_user_id() -> str:
    """Get or create test user ID."""
    return os.environ.get("TEST_USER_ID", str(uuid4()))


@pytest.fixture
def test_agent_id() -> str:
    """Get or create test agent ID."""
    return os.environ.get("TEST_AGENT_ID", str(uuid4()))


@pytest.fixture
def auth_token() -> str:
    """Get authentication token for testing."""
    # In production tests, this would authenticate against Keycloak
    # For integration tests, use test token from environment
    return os.environ.get("TEST_AUTH_TOKEN", "test_integration_token")


# =============================================================================
# Service Fixtures
# =============================================================================


@pytest.fixture
def chat_service(real_infrastructure) -> "ChatService":
    """Get configured ChatService instance.
    
    VIBE COMPLIANT: Uses real ChatService implementation with actual infrastructure
    (no mocks, no fakes, real PostgreSQL, Redis, SomaBrain).
    """
    from services.common.chat_service import ChatService
    
    # ChatService only accepts somabrain_url and timeout parameters
    # Memory operations use SomaBrainClient internally
    return ChatService(
        somabrain_url=os.environ.get("SA01_SOMA_BASE_URL", "http://localhost:63996"),
        timeout=30.0,
    )


@pytest.fixture
async def governor(real_infrastructure):
    """Get configured AgentIQ Governor."""
    from admin.agents.services.agentiq_governor import create_governor
    from services.common.budget_manager import BudgetManager
    from services.common.capsule_store import CapsuleStore
    from services.common.degradation_monitor import DegradationMonitor
    
    capsule_store = CapsuleStore()
    degradation_monitor = DegradationMonitor()
    budget_manager = BudgetManager()
    
    await degradation_monitor.start()
    
    gov = create_governor(
        capsule_store=capsule_store,
        degradation_monitor=degradation_monitor,
        budget_manager=budget_manager,
    )
    
    yield gov
    
    await degradation_monitor.stop()


@pytest.fixture
def context_builder(real_infrastructure):
    """Get configured ContextBuilder."""
    from admin.agents.services.context_builder import ContextBuilder
    from admin.core.observability.metrics import ContextBuilderMetrics
    from admin.core.somabrain_client import SomaBrainClient
    
    return ContextBuilder(
        somabrain=SomaBrainClient(),
        metrics=ContextBuilderMetrics(),
        token_counter=lambda t: len(t.split()),
    )


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
    """Get WebSocket URL for testing."""
    base = os.environ.get("SA01_WS_URL", "ws://localhost:63900")
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
