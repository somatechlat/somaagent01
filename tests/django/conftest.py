"""Test configuration for Django Ninja migration tests."""

from __future__ import annotations

import os
import sys

import pytest

# Ensure the project is in the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


# Configure Django before any tests run
def pytest_configure(config):
    """Configure Django settings before tests."""
    # Import django_setup to trigger configuration
    import services.gateway.django_setup  # noqa: F401


@pytest.fixture
def api_client():
    """Create a test client for the Django Ninja API."""
    from ninja.testing import TestClient
    from admin.api import api
    
    return TestClient(api)


@pytest.fixture
def auth_token():
    """Create a mock auth token for testing."""
    return "mock-bearer-token-for-testing"


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    from unittest.mock import AsyncMock, MagicMock
    
    session = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    
    return session
