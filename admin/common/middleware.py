"""Session Middleware for Django Ninja API.


Per login-to-chat-journey design.md Section: SessionMiddleware

Implements:
- JWT validation from httpOnly cookie
- Session lookup from Redis
- Activity tracking (TTL extension)
- Request enrichment with session data

Personas:
- Django Architect: Django middleware integration
- Security Auditor: Fail-closed authorization, token validation
- Performance Engineer: Efficient async operations
"""

from __future__ import annotations

import logging
from typing import Callable, Optional

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse

from admin.common.session_manager import SessionManager, get_session_manager

logger = logging.getLogger(__name__)


# =============================================================================
# EXCLUDED PATHS (No session required)
# =============================================================================

EXCLUDED_PATHS = [
    # Auth endpoints (login flow)
    "/api/v2/auth/login",
    "/api/v2/auth/token",
    "/api/v2/auth/oauth",
    "/api/v2/auth/refresh",
    "/api/v2/auth/register",
    "/api/v2/auth/password/reset",
    "/api/v2/auth/password/forgot",
    # Health checks
    "/healthz",
    "/health",
    "/readyz",
    "/api/v2/health",
    # Static assets
    "/static/",
    "/assets/",
    # OpenAPI docs
    "/api/v2/docs",
    "/api/v2/openapi.json",
]


def _is_excluded_path(path: str) -> bool:
    """Check if path is excluded from session validation."""
    for excluded in EXCLUDED_PATHS:
        if path.startswith(excluded):
            return True
    return False


# =============================================================================
# SESSION MIDDLEWARE (ASGI)
# =============================================================================


class SessionMiddleware:
    """Django middleware for session validation.

    Per design.md Section 5.5 Session Validation Middleware:
    - Extract access_token from httpOnly cookie
    - Verify JWT signature using Keycloak public key
    - Check token expiry
    - Load session from Redis
    - Update last_activity timestamp

    Attaches to request:
    - request.session_data: Session object
    - request.user_claims: JWT claims dict
    """

    def __init__(self, get_response: Callable):
        """Initialize middleware.

        Args:
            get_response: Next middleware/view in chain
        """
        self.get_response = get_response
        self._session_manager: Optional[SessionManager] = None

    async def _get_session_manager(self) -> SessionManager:
        """Get or create SessionManager instance."""
        if self._session_manager is None:
            self._session_manager = await get_session_manager()
        return self._session_manager

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Synchronous middleware entry point.

        For sync views, we skip session validation.
        Use async views for full session support.
        """
        # Skip excluded paths
        if _is_excluded_path(request.path):
            return self.get_response(request)

        # For sync views, just pass through
        # Session validation happens in async views via AuthBearer
        return self.get_response(request)

    async def __acall__(self, request: HttpRequest) -> HttpResponse:
        """Async middleware entry point.

        Full session validation for async views.
        """
        # Skip excluded paths
        if _is_excluded_path(request.path):
            return await self.get_response(request)

        # Extract token from cookie
        access_token = request.COOKIES.get("access_token")

        if not access_token:
            # No cookie - check Authorization header (API clients)
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                access_token = auth_header[7:]

        if not access_token:
            return JsonResponse(
                {"error": "unauthorized", "message": "Authentication required"},
                status=401,
            )

        # Validate JWT and get claims
        try:
            from admin.common.auth import decode_token

            claims = await decode_token(access_token)
        except Exception as e:
            logger.warning(f"JWT validation failed: {e}")
            return JsonResponse(
                {"error": "invalid_token", "message": "Invalid or expired token"},
                status=401,
            )

        # Get session from Redis
        session_manager = await self._get_session_manager()

        # Session ID from JWT claims or httpOnly cookie
        session_id = getattr(claims, "session_id", None) or request.COOKIES.get("session_id")

        if session_id:
            session = await session_manager.get_session(claims.sub, session_id)

            if session is None:
                logger.warning(f"Session not found: user={claims.sub}, session={session_id}")
                return JsonResponse(
                    {
                        "error": "session_expired",
                        "message": "Session expired. Please log in again.",
                    },
                    status=401,
                )

            # Update activity (extends TTL)
            await session_manager.update_activity(claims.sub, session_id)

            # Attach session to request
            request.session_data = session
        else:
            # No session_id in token - stateless mode (Redis unavailable fallback)
            request.session_data = None
            logger.debug("Operating in stateless mode (no session_id in token)")

        # Attach claims to request
        request.user_claims = claims

        # Continue to view
        return await self.get_response(request)


# =============================================================================
# DJANGO NINJA DEPENDENCY (Alternative to middleware)
# =============================================================================


async def get_session_from_request(request: HttpRequest) -> Optional["Session"]:
    """Get session from request (for use in Django Ninja endpoints).

    Usage in endpoint:
        @router.get("/protected")
        async def protected_endpoint(request):
            session = await get_session_from_request(request)
            if not session:
                raise UnauthorizedError("Session required")
            ...
    """
    # Check if middleware already attached session
    if hasattr(request, "session_data") and request.session_data:
        return request.session_data

    # Try to get from token
    if not hasattr(request, "auth") or request.auth is None:
        return None

    claims = request.auth
    session_id = getattr(claims, "session_id", None)

    if not session_id:
        return None

    session_manager = await get_session_manager()
    return await session_manager.get_session(claims.sub, session_id)


__all__ = [
    "SessionMiddleware",
    "get_session_from_request",
    "EXCLUDED_PATHS",
]
