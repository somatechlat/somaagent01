"""Environment configuration helper for required variables.


Security Auditor: Enforces explicit environment configuration.
"""

import os
from typing import Optional


def get_required_env(key: str, service_name: str) -> str:
    """Get required environment variable with clear error message.

    Args:
        key: Environment variable name
        service_name: Human-readable service description for error message

    Returns:
        Environment variable value

    Raises:
        ValueError: If environment variable is not set

    Example:
        >>> SOMABRAIN_URL = get_required_env("SA01_SOMA_BASE_URL", "SomaBrain connection")
    """
    value = os.environ.get(key)
    if not value:
        raise ValueError(
            f"❌ Missing required environment variable: {key}\n"
            f"   Required for: {service_name}\n"
            f"   Set in: .env file or docker-compose environment section\n"
            f"   Example: {key}=http://somabrain:9696"
        )
    return value


def get_optional_env(
    key: str, default: Optional[str] = None, description: str = ""
) -> Optional[str]:
    """Get optional environment variable with optional default.

    Args:
        key: Environment variable name
        default: Default value if not set (None allowed)
        description: Human-readable description for documentation

    Returns:
        Environment variable value or default

    Example:
        >>> DEBUG = get_optional_env("DEBUG", "False", "Enable debug mode")
    """
    return os.environ.get(key, default)


__all__ = ["get_required_env", "get_optional_env"]