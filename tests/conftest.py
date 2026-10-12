"""Unified Test Configuration - SomaAgent01

REAL INFRA ONLY. One cluster: ``somaagent_*`` (infra/standalone).

There is no parallel test stack, no AAAS/``somastack`` topology, and no
``localhost`` host. Hosts are the Docker service names of the live standalone
compose project, the same names the application uses inside the container.

Tests run against live services on ``somaagent_net`` (``docker compose`` test
target or ``exec`` into ``somaagent_standalone``). If a service is down the
suite fails naming it — it does not skip to green and it does not invent a
substitute host (VIBE Rule 91 / R-TOP-03).

Secrets are deliberately absent. They come from Vault
(``secret/agent/credentials/*``) via UnifiedSecretManager (VIBE Rule 164).
"""

from __future__ import annotations

import os

import pytest

# ═══════════════════════════════════════════════════════════════════════════════
# LIVE STANDALONE CLUSTER (infra/standalone/docker-compose.yml)
# Topology only. Service DNS names on somaagent_net. No credentials.
# ═══════════════════════════════════════════════════════════════════════════════

# Topology authority is tests/_vault_topology.py (the pytest plugin, loaded
# before conftest). This module must not restate hosts/ports — two declarations
# for one cluster is drift (ADV-16).


# ═══════════════════════════════════════════════════════════════════════════════
# PYTEST CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "standalone: Standalone mode tests")
    config.addinivalue_line("markers", "slow: Long-running tests")
    config.addinivalue_line("markers", "infra: Requires live infrastructure")
    config.addinivalue_line("markers", "unit: Pure unit tests (no infrastructure)")
    config.addinivalue_line(
        "markers",
        "no_django: test is pure (stdlib-only) and must not boot Django settings",
    )


@pytest.fixture(autouse=True)
def configure_test_environment(request):
    """Set up Django (settings module configured via pytest.ini).

    Tests marked ``no_django`` are pure (e.g. coordinate hash goldens) and must
    not couple to the Vault-backed settings chain.
    """
    if request.node.get_closest_marker("no_django") is not None:
        return
    import django

    django.setup()


# ═══════════════════════════════════════════════════════════════════════════════
# INFRASTRUCTURE HEALTH — fail closed, name the service
# ═══════════════════════════════════════════════════════════════════════════════


def _require_service(host: str, port: int, label: str) -> None:
    """Raise if the live service is unreachable. Never skip to green."""
    import socket

    try:
        with socket.create_connection((host, port), timeout=2):
            return
    except (socket.error, socket.timeout) as exc:
        pytest.fail(
            f"{label} is not reachable at {host}:{port} — live infra is required. "
            f"Start the standalone stack (infra/standalone) on somaagent_net. "
            f"({exc})",
            pytrace=False,
        )


@pytest.fixture(scope="session")
def postgres_available():
    """Live Postgres must answer."""
    _require_service(
        os.environ["POSTGRES_HOST"],
        int(os.environ["POSTGRES_PORT"]),
        "PostgreSQL (somaagent_postgres)",
    )
    return True


@pytest.fixture(scope="session")
def redis_available():
    """Live Redis must answer."""
    _require_service(
        os.environ["REDIS_HOST"],
        int(os.environ["REDIS_PORT"]),
        "Redis (somaagent_redis)",
    )
    return True
