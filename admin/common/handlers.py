"""Exception handlers for Django Ninja API.

Registers global exception handlers that convert exceptions to proper HTTP responses.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ninja import NinjaAPI
from django.http import JsonResponse
from pydantic import ValidationError as PydanticValidationError

from admin.common.exceptions import (
    ApiError,
    NotFoundError,
    ForbiddenError,
    ValidationError,
    UnauthorizedError,
    RateLimitError,
    ConflictError,
    ServiceUnavailableError,
)
from admin.common.responses import error_response


def register_exception_handlers(api: NinjaAPI) -> None:
    """Register all exception handlers on the Ninja API instance.

    Args:
        api: The NinjaAPI instance to register handlers on
    """

    @api.exception_handler(ApiError)
    def handle_api_error(request, exc: ApiError):
        """Handle all ApiError exceptions."""
        return JsonResponse(
            exc.to_dict(),
            status=exc.status_code,
        )

    @api.exception_handler(PydanticValidationError)
    def handle_pydantic_validation_error(request, exc: PydanticValidationError):
        """Handle Pydantic validation errors."""
        errors = []
        for error in exc.errors():
            errors.append(
                {
                    "field": ".".join(str(loc) for loc in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"],
                }
            )

        return JsonResponse(
            error_response(
                error="validation_error",
                message="Request validation failed",
                details={"errors": errors},
            ),
            status=400,
        )

    @api.exception_handler(Exception)
    def handle_generic_exception(request, exc: Exception):
        """Handle unexpected exceptions."""
        import logging
        import traceback

        logger = logging.getLogger(__name__)
        logger.error(f"Unhandled exception: {exc}\n{traceback.format_exc()}")

        return JsonResponse(
            error_response(
                error="internal_error",
                message="An unexpected error occurred",
            ),
            status=500,
        )


def create_api_with_handlers(
    title: str = "SomaAgent API",
    version: str = "2.0.0",
    description: str = "SomaAgent Platform API",
    **kwargs,
) -> NinjaAPI:
    """Create a NinjaAPI instance with all handlers registered.

    Args:
        title: API title
        version: API version
        description: API description
        **kwargs: Additional NinjaAPI arguments

    Returns:
        Configured NinjaAPI instance
    """
    api = NinjaAPI(
        title=title,
        version=version,
        description=description,
        **kwargs,
    )
    register_exception_handlers(api)
    return api
