"""Conftest for integration tests.

Sets up environment for SomaBrain integration tests.
"""

import os
import socket


def pytest_configure(config):
    """Configure pytest for integration tests."""
    # If SA01_SOMA_BASE_URL is not set, try to use localhost
    if not os.environ.get("SA01_SOMA_BASE_URL"):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(("localhost", 9696))
            sock.close()
            if result == 0:
                os.environ["SA01_SOMA_BASE_URL"] = "http://localhost:9696"
        except Exception:
            pass
