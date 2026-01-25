"""Unified Test Configuration - SomaAgent01

VIBE Coding Rules Compliant:
- Real infrastructure only (NO mocks)
- AAAS/Standalone mode separation
- Centralized environment configuration

Test Structure:
- tests/aaas/      - SOMA_AAAS_MODE=true tests
- tests/standalone/ - SOMA_AAAS_MODE=false tests
- tests/unit/      - Pure unit tests (no infra)
- tests/integration/ - Cross-service tests
- tests/e2e/       - Full end-to-end flows
"""

import os
import pytest

# ===========================================================================
# ENVIRONMENT CONFIGURATION - AAAS INFRASTRUCTURE (Port 639xx)
# ===========================================================================

AAAS_ENV = {
    # PostgreSQL (somastack_postgres)
    "SA01_DB_HOST": "localhost",
    "SA01_DB_PORT": "63932",
    "SA01_DB_USER": "soma",
    "SA01_DB_PASSWORD": "soma",
    "SA01_DB_NAME": "somaagent",
    "SA01_DB_DSN": "postgresql://soma:soma@localhost:63932/somaagent",
    # Redis (somastack_redis)
    "SA01_REDIS_URL": "redis://localhost:63979/0",
    # Milvus (somastack_milvus)
    "MILVUS_HOST": "localhost",
    "MILVUS_PORT": "63953",
    # Kafka (somastack_kafka)
    "SA01_KAFKA_BOOTSTRAP_SERVERS": "localhost:63992",
    # SomaBrain (internal)
    "SA01_SOMA_BASE_URL": "http://localhost:63996",
    # Mode flags
    "SOMA_AAAS_MODE": "true",
    "SA01_DEPLOYMENT_MODE": "AAAS",
    "SOMA_API_TOKEN": "test-token-aaas",
}

STANDALONE_ENV = {
    "SA01_DB_HOST": "localhost",
    "SA01_DB_PORT": "5432",
    "MILVUS_PORT": "19530",
    "SOMA_AAAS_MODE": "false",
    "SA01_DEPLOYMENT_MODE": "STANDALONE",
}


def _apply_env(env_dict: dict) -> None:
    """Apply environment variables."""
    for key, value in env_dict.items():
        os.environ[key] = value


# ===========================================================================
# PYTEST CONFIGURATION
# ===========================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "aaas: AAAS mode tests (requires Docker infra)")
    config.addinivalue_line("markers", "standalone: Standalone mode tests")
    config.addinivalue_line("markers", "slow: Long-running tests")
    config.addinivalue_line("markers", "infra: Requires real infrastructure")
    config.addinivalue_line("markers", "unit: Pure unit tests (no infrastructure)")


@pytest.fixture(scope="session", autouse=True)
def configure_test_environment(request):
    """Auto-configure environment based on test markers."""
    # Default to AAAS mode for integration tests
    _apply_env(AAAS_ENV)

    # Setup Django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django
    django.setup()


@pytest.fixture
def aaas_mode():
    """Fixture to ensure AAAS mode environment."""
    _apply_env(AAAS_ENV)
    yield


@pytest.fixture
def standalone_mode():
    """Fixture to ensure Standalone mode environment."""
    _apply_env(STANDALONE_ENV)
    yield


# ===========================================================================
# INFRASTRUCTURE HEALTH CHECKS
# ===========================================================================

@pytest.fixture(scope="session")
def postgres_available():
    """Check if PostgreSQL is available."""
    import socket
    host = os.environ.get("SA01_DB_HOST", "localhost")
    port = int(os.environ.get("SA01_DB_PORT", "63932"))
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except (socket.error, socket.timeout):
        pytest.skip(f"PostgreSQL not available at {host}:{port}")


@pytest.fixture(scope="session")
def milvus_available():
    """Check if Milvus is available."""
    import socket
    host = os.environ.get("MILVUS_HOST", "localhost")
    port = int(os.environ.get("MILVUS_PORT", "63953"))
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except (socket.error, socket.timeout):
        pytest.skip(f"Milvus not available at {host}:{port}")


@pytest.fixture(scope="session")
def redis_available():
    """Check if Redis is available."""
    import socket
    try:
        with socket.create_connection(("localhost", 63979), timeout=2):
            return True
    except (socket.error, socket.timeout):
        pytest.skip("Redis not available at localhost:63979")


@pytest.fixture(scope="session")
def somabrain_available():
    """Check if SomaBrain API is available."""
    import socket
    try:
        with socket.create_connection(("localhost", 63996), timeout=2):
            return True
    except (socket.error, socket.timeout):
        pytest.skip("SomaBrain not available at localhost:63996")
