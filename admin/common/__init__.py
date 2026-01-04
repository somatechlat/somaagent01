"""Common Django Ninja infrastructure for SomaAgent01.

This package provides shared utilities, middleware, schemas, and
exception handling for all Django apps in the migration.
"""

from admin.common.exceptions import ApiError, ForbiddenError, NotFoundError, ValidationError
from admin.common.responses import api_response, paginated_response
from admin.common.schemas import ErrorResponse, PaginatedRequest, PaginatedResponse

__all__ = [
    # Exceptions
    "ApiError",
    "NotFoundError",
    "ForbiddenError",
    "ValidationError",
    # Responses
    "api_response",
    "paginated_response",
    # Schemas
    "PaginatedRequest",
    "PaginatedResponse",
    "ErrorResponse",
]