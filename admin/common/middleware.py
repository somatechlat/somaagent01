"""Session Middleware for Django Ninja API."""

from __future__ import annotations

import logging
from typing import Callable, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from admin.common.session_manager import Session

from django.http import HttpRequest, HttpResponse, JsonResponse

from admin.common.session_manager import get_session_manager, SessionManager

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
            logger.warning("Auth failure: no access token")
            return JsonResponse(
                {"error": "unauthorized", "message": "Authentication required"},
                status=401,
            )

        # Validate JWT and get claims
        try:
            from admin.common.auth import decode_token

            claims = await decode_token(access_token)
        except Exception as e:
            logger.warning("JWT validation failed: %s", e)
            try:
                from asgiref.sync import sync_to_async
                from admin.aaas.models import AuditLog
                from uuid import uuid4
                await sync_to_async(AuditLog.objects.create, thread_sensitive=False)(
                    actor_id="anonymous",
                    actor_email="",
                    action="auth.middleware_token_failed",
                    resource_type="auth",
                    resource_id=None,
                    new_value={"error": str(e)},
                    ip_address=request.META.get("REMOTE_ADDR"),
                    user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
                    request_id=str(uuid4()),
                )
            except Exception as audit_exc:
                logger.warning("Auth audit logging failed: %s", audit_exc)
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
                logger.warning("Session not found: user=%s, session=%s", claims.sub, session_id)
                try:
                    from asgiref.sync import sync_to_async
                    from admin.aaas.models import AuditLog
                    from uuid import uuid4
                    await sync_to_async(AuditLog.objects.create, thread_sensitive=False)(
                        actor_id=str(claims.sub),
                        actor_email="",
                        action="auth.session_expired",
                        resource_type="auth",
                        resource_id=None,
                        new_value={"session_id": session_id},
                        ip_address=request.META.get("REMOTE_ADDR"),
                        user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
                        request_id=str(uuid4()),
                    )
                except Exception as audit_exc:
                    logger.warning("Auth audit logging failed: %s", audit_exc)
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
            request.session_data = session  # type: ignore[attr-defined]
        else:
            # No session_id in token - stateless mode (Redis unavailable fallback)
            request.session_data = None  # type: ignore[attr-defined]
            logger.debug("Operating in stateless mode (no session_id in token)")

        # Attach claims to request
        request.user_claims = claims  # type: ignore[attr-defined]

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
    if hasattr(request, "session_data") and request.session_data:  # type: ignore[attr-defined]
        return request.session_data  # type: ignore[attr-defined]

    # Try to get from token
    if not hasattr(request, "auth") or request.auth is None:  # type: ignore[attr-defined]
        return None

    claims = request.auth  # type: ignore[attr-defined]
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
