"""SOMA Token Format Standard Implementation.

This module provides utilities for generating and validating SOMA-compliant
tokens across all token types: API keys, service tokens, memory tokens, and
session tokens.

VIBE Rule 164: All tokens follow SOMA_TOKEN_FORMAT standard.

Example:
    >>> from services.common.token_format import generate_soma_token, TokenType
    >>> api_key = generate_soma_token(TokenType.API_KEY, "dev")
    >>> print(api_key)  # soma_api_dev_a1b2c3d4e5f6g7h8i9j0k1l2

See Also:
    docs/standards/SOMA_TOKEN_FORMAT.md - Full specification
"""

import re
import secrets
import string
from enum import Enum
from typing import Optional


class TokenType(Enum):
    """Enumeration of SOMA token types."""

    API_KEY = "api"
    SERVICE = "svc"
    MEMORY = "mem"
    SESSION = "ses"


# Token format patterns for validation
TOKEN_PATTERNS: dict[TokenType, str] = {
    TokenType.API_KEY: r"^soma_api_(dev|pro|ent)_[a-z0-9]{24}$",
    TokenType.SERVICE: r"^soma_svc_(agent|brain|memory)_[a-z0-9]{24}$",
    TokenType.MEMORY: r"^soma_mem_(read|write|admin)_[a-z0-9]{24}$",
    TokenType.SESSION: r"^soma_ses_(chat|voice|event)_[a-z0-9]{24}$",
}

# Valid qualifiers for each token type
VALID_QUALIFIERS: dict[TokenType, list[str]] = {
    TokenType.API_KEY: ["dev", "pro", "ent"],
    TokenType.SERVICE: ["agent", "brain", "memory"],
    TokenType.MEMORY: ["read", "write", "admin"],
    TokenType.SESSION: ["chat", "voice", "event"],
}


def generate_soma_token(
    token_type: TokenType,
    qualifier: str,
    length: int = 24,
) -> str:
    """Generate SOMA-compliant token.

    Generates a cryptographically secure token following the SOMA_TOKEN_FORMAT
    standard. Uses the `secrets` module for CSPRNG-based random generation.

    Args:
        token_type: Type of token (API_KEY, SERVICE, MEMORY, SESSION).
        qualifier: Sub-type qualifier (tier/service/scope/channel).
            - API_KEY: "dev", "pro", "ent"
            - SERVICE: "agent", "brain", "memory"
            - MEMORY: "read", "write", "admin"
            - SESSION: "chat", "voice", "event"
        length: Length of random portion (default: 24 = 144 bits entropy).

    Returns:
        Formatted token string (e.g., "soma_api_dev_a1b2c3d4e5f6g7h8i9j0k1l2").

    Raises:
        ValueError: If qualifier is not valid for the token type.

    Example:
        >>> generate_soma_token(TokenType.API_KEY, "dev")
        'soma_api_dev_...'
        >>> generate_soma_token(TokenType.SERVICE, "brain")
        'soma_svc_brain_...'
    """
    valid_qualifiers = VALID_QUALIFIERS.get(token_type, [])
    if qualifier not in valid_qualifiers:
        raise ValueError(
            f"Invalid qualifier '{qualifier}' for {token_type.name}. Valid options: {valid_qualifiers}"
        )

    # Use lowercase alphanumeric for URL-safe tokens
    alphabet = string.ascii_lowercase + string.digits
    random_part = "".join(secrets.choice(alphabet) for _ in range(length))

    return f"soma_{token_type.value}_{qualifier}_{random_part}"


def validate_soma_token(
    token: str,
    expected_type: Optional[TokenType] = None,
) -> bool:
    """Validate token format compliance.

    Checks if a token string matches the SOMA_TOKEN_FORMAT specification.
    Can validate against a specific type or check against all types.

    Args:
        token: Token string to validate.
        expected_type: Optional specific type to validate against.
            If None, validates against all token type patterns.

    Returns:
        True if token matches SOMA format, False otherwise.

    Example:
        >>> validate_soma_token("soma_api_dev_a1b2c3d4e5f6g7h8i9j0k1l2")
        True
        >>> validate_soma_token("invalid-token")
        False
        >>> validate_soma_token("soma_api_dev_...", TokenType.SERVICE)
        False
    """
    if not token or not isinstance(token, str):
        return False

    if expected_type:
        pattern = TOKEN_PATTERNS.get(expected_type)
        if pattern:
            return bool(re.match(pattern, token))
        return False

    # Check against all patterns
    for pattern in TOKEN_PATTERNS.values():
        if re.match(pattern, token):
            return True
    return False


def parse_soma_token(token: str) -> dict[str, str]:
    """Parse SOMA token into components.

    Extracts the constituent parts of a SOMA token for inspection
    or logging purposes.

    Args:
        token: Valid SOMA token string.

    Returns:
        Dictionary containing:
            - 'type': Token type code (api/svc/mem/ses)
            - 'qualifier': Sub-type qualifier
            - 'random': Random portion (for uniqueness, not secret)
            - 'full': Original full token

    Raises:
        ValueError: If token doesn't match SOMA format.

    Example:
        >>> parse_soma_token("soma_api_dev_a1b2c3d4e5f6g7h8i9j0k1l2")
        {'type': 'api', 'qualifier': 'dev', 'random': 'a1b2...', 'full': '...'}
    """
    parts = token.split("_")
    if len(parts) != 4 or parts[0] != "soma":
        raise ValueError(f"Invalid SOMA token format: {token[:20]}...")

    return {
        "type": parts[1],
        "qualifier": parts[2],
        "random": parts[3],
        "full": token,
    }


def mask_token(token: str, visible_chars: int = 8) -> str:
    """Mask token for safe logging.

    Returns a masked version of the token suitable for logs and debugging.
    Only the prefix and first few random characters are visible.

    Args:
        token: Token to mask.
        visible_chars: Number of random chars to show (default: 8).

    Returns:
        Masked token string.

    Example:
        >>> mask_token("soma_api_dev_a1b2c3d4e5f6g7h8i9j0k1l2")
        'soma_api_dev_a1b2c3d4...***'
    """
    try:
        parsed = parse_soma_token(token)
        random_visible = parsed["random"][:visible_chars]
        return f"soma_{parsed['type']}_{parsed['qualifier']}_{random_visible}...***"
    except ValueError:
        # Fallback for non-SOMA tokens
        if len(token) > 10:
            return f"{token[:10]}...***"
        return "***"


def is_legacy_token(token: str) -> bool:
    """Check if token is pre-SOMA format (legacy).

    Used during migration to identify tokens that need upgrading.

    Args:
        token: Token string to check.

    Returns:
        True if token doesn't follow SOMA format.
    """
    return not token.startswith("soma_")


# Convenience functions for specific token types


def generate_api_key(tier: str = "dev") -> str:
    """Generate API key for developer access.

    Args:
        tier: Subscription tier ("dev", "pro", "ent").

    Returns:
        SOMA-compliant API key.
    """
    return generate_soma_token(TokenType.API_KEY, tier)


def generate_service_token(service: str) -> str:
    """Generate service token for inter-service auth.

    Args:
        service: Service name ("agent", "brain", "memory").

    Returns:
        SOMA-compliant service token.
    """
    return generate_soma_token(TokenType.SERVICE, service)


def generate_memory_token(scope: str = "read") -> str:
    """Generate memory token for SomaBrain/SFM communication.

    Args:
        scope: Access scope ("read", "write", "admin").

    Returns:
        SOMA-compliant memory token.
    """
    return generate_soma_token(TokenType.MEMORY, scope)


def generate_session_token(channel: str = "chat") -> str:
    """Generate session token for WebSocket/streaming.

    Args:
        channel: Communication channel ("chat", "voice", "event").

    Returns:
        SOMA-compliant session token.
    """
    return generate_soma_token(TokenType.SESSION, channel)
