"""Rate Limiting for Django Ninja endpoints.


Per login-to-chat-journey design.md Section 2.1: Rate Limiting

Implements:
- Per-IP rate limiting for login endpoints
- 10 requests per minute per IP for /api/v2/auth/login
- Returns 429 with retry_after when exceeded

Personas:
- Security Auditor: Brute-force protection
- Django Architect: Django Ninja integration
- Performance Engineer: Efficient Redis operations
"""

from __future__ import annotations

import logging
import os
from functools import wraps
from typing import Callable, Optional

from admin.common.exceptions import RateLimitError

logger = logging.getLogger(__name__)


# =============================================================================
# RATE LIMIT CONFIGURATION
# =============================================================================

# Per design.md Section 2.1: 10 requests per minute per IP
LOGIN_RATE_LIMIT = 10
LOGIN_RATE_WINDOW = 60  # seconds


# =============================================================================
# RATE LIMIT CHECKER
# =============================================================================


async def check_rate_limit(
    ip_address: str,
    endpoint: str,
    limit: int = LOGIN_RATE_LIMIT,
    window: int = LOGIN_RATE_WINDOW,
) -> None:
    """Check rate limit for IP/endpoint combination.

    Args:
        ip_address: Client IP address
        endpoint: Endpoint being accessed
        limit: Max requests in window
        window: Window size in seconds

    Raises:
        RateLimitError: If rate limit exceeded
    """
    from services.common.rate_limiter import get_rate_limiter

    try:
        rate_limiter = await get_rate_limiter()
        result = await rate_limiter.check(
            tenant_id=ip_address,  # Use IP as tenant for per-IP limiting
            endpoint=endpoint,
            limit=limit,
            window_seconds=window,
        )

        if not result.allowed:
            logger.warning(
                f"Rate limit exceeded: ip={ip_address}, endpoint={endpoint}, "
                f"retry_after={result.retry_after}"
            )
            raise RateLimitError(
                message="Too many requests. Please wait.",
                retry_after=result.retry_after,
            )

    except RateLimitError:
        raise
    except Exception as e:
        # Fail open - don't block requests if rate limiter fails
        logger.error(f"Rate limiter error (failing open): {e}")


def rate_limit(
    limit: int = LOGIN_RATE_LIMIT,
    window: int = LOGIN_RATE_WINDOW,
    key_func: Optional[Callable] = None,
):
    """Decorator to apply rate limiting to Django Ninja endpoints.

    Usage:
        @router.post("/login")
        @rate_limit(limit=10, window=60)
        async def login(request, payload: LoginRequest):
            ...

    Args:
        limit: Max requests in window
        window: Window size in seconds
        key_func: Optional function to extract rate limit key from request
                  Default: uses client IP address
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        """Execute decorator.

            Args:
                func: The func.
            """

        async def wrapper(request, *args, **kwargs):
            # Get IP address
            """Execute wrapper.

                Args:
                    request: The request.
                """

            if key_func:
                key = key_func(request)
            else:
                key = _get_client_ip(request)

            # Get endpoint from function name
            endpoint = f"/api/v2/auth/{func.__name__}"

            # Check rate limit
            await check_rate_limit(key, endpoint, limit, window)

            # Call original function
            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


def _get_client_ip(request) -> str:
    """Extract client IP from request.

    Handles X-Forwarded-For header for proxied requests.
    """
    # Check X-Forwarded-For header (for reverse proxy)
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        # Take first IP in chain (original client)
        return x_forwarded_for.split(",")[0].strip()

    # Fall back to REMOTE_ADDR
    return request.META.get("REMOTE_ADDR", "unknown")


__all__ = [
    "check_rate_limit",
    "rate_limit",
    "LOGIN_RATE_LIMIT",
    "LOGIN_RATE_WINDOW",
]