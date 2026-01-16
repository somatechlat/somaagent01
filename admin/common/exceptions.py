"""Custom API exceptions for Django Ninja endpoints.

All exceptions inherit from ApiError and provide consistent HTTP error responses.
These exceptions are automatically caught and formatted by the exception handlers.
"""

from __future__ import annotations

from typing import Any


class ApiError(Exception):
    """Base exception for all API errors.

    Provides consistent error structure across all endpoints.
    """

    status_code: int = 500
    error_code: str = "internal_error"

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize API error.

        Args:
            message: Human-readable error message
            status_code: HTTP status code override
            error_code: Machine-readable error code override
            details: Additional error context
        """
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        if error_code is not None:
            self.error_code = error_code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary for JSON response."""
        result = {
            "error": self.error_code,
            "message": self.message,
        }
        if self.details:
            result["details"] = self.details
        return result


class NotFoundError(ApiError):
    """Resource not found (404)."""

    status_code = 404
    error_code = "not_found"

    def __init__(
        self,
        resource: str,
        identifier: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize not found error.

        Args:
            resource: Type of resource (e.g., "tenant", "agent")
            identifier: Optional identifier of the resource
        """
        if identifier:
            message = f"{resource} with id '{identifier}' not found"
        else:
            message = f"{resource} not found"
        super().__init__(message, **kwargs)
        self.details["resource"] = resource
        if identifier:
            self.details["identifier"] = identifier


class ForbiddenError(ApiError):
    """Access forbidden (403)."""

    status_code = 403
    error_code = "forbidden"

    def __init__(
        self,
        action: str | None = None,
        resource: str | None = None,
        message: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize forbidden error.

        Args:
            action: Action that was attempted
            resource: Resource access was attempted on
            message: Custom error message (overrides auto-generated)
        """
        if message:
            final_message = message
        elif action and resource:
            final_message = f"Access denied: cannot {action} {resource}"
        elif action:
            final_message = f"Access denied: cannot {action}"
        else:
            final_message = "Access denied"
        super().__init__(final_message, **kwargs)
        if action:
            self.details["action"] = action
        if resource:
            self.details["resource"] = resource


class ValidationError(ApiError):
    """Request validation failed (400)."""

    status_code = 400
    error_code = "validation_error"

    def __init__(
        self,
        message: str = "Validation failed",
        *,
        field: str | None = None,
        errors: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize validation error.

        Args:
            message: Error message
            field: Field that failed validation
            errors: List of validation errors
        """
        super().__init__(message, **kwargs)
        if field:
            self.details["field"] = field
        if errors:
            self.details["errors"] = errors


class ConflictError(ApiError):
    """Resource conflict (409)."""

    status_code = 409
    error_code = "conflict"

    def __init__(
        self,
        message: str,
        resource: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize conflict error."""
        super().__init__(message, **kwargs)
        if resource:
            self.details["resource"] = resource


class UnauthorizedError(ApiError):
    """Authentication required (401)."""

    status_code = 401
    error_code = "unauthorized"

    def __init__(
        self,
        message: str = "Authentication required",
        **kwargs: Any,
    ) -> None:
        """Initialize unauthorized error."""
        super().__init__(message, **kwargs)


class RateLimitError(ApiError):
    """Rate limit exceeded (429)."""

    status_code = 429
    error_code = "rate_limit_exceeded"

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        *,
        retry_after: int | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize rate limit error.

        Args:
            message: Error message
            retry_after: Seconds until retry is allowed
        """
        super().__init__(message, **kwargs)
        if retry_after:
            self.details["retry_after"] = retry_after


class ServiceUnavailableError(ApiError):
    """Service temporarily unavailable (503)."""

    status_code = 503
    error_code = "service_unavailable"

    def __init__(
        self,
        service: str,
        message: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize service unavailable error.

        Args:
            service: Name of unavailable service
            message: Optional custom message
        """
        if message is None:
            message = f"Service '{service}' is temporarily unavailable"
        super().__init__(message, **kwargs)
        self.details["service"] = service


class ServiceError(ApiError):
    """Internal service error (500).

    Used for infrastructure failures and unexpected errors.
    """

    status_code = 500
    error_code = "service_error"

    def __init__(
        self,
        message: str = "An internal service error occurred",
        **kwargs: Any,
    ) -> None:
        """Initialize service error."""
        super().__init__(message, **kwargs)


class BadRequestError(ApiError):
    """Bad request error (400).

    Used for invalid client requests.
    """

    status_code = 400
    error_code = "bad_request"

    def __init__(
        self,
        message: str = "Bad request",
        **kwargs: Any,
    ) -> None:
        """Initialize bad request error."""
        super().__init__(message, **kwargs)
