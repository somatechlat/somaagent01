"""Response helpers for Django Ninja endpoints.

Provides standardized response formatting across all API endpoints.
"""

from __future__ import annotations

from typing import Any, TypeVar, Generic
from datetime import datetime

T = TypeVar("T")


def api_response(
    data: Any,
    *,
    message: str | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create standardized API response.
    
    Args:
        data: Response payload
        message: Optional success message
        meta: Optional metadata
        
    Returns:
        Standardized response dictionary
    """
    response: dict[str, Any] = {
        "success": True,
        "data": data,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    if message:
        response["message"] = message
    if meta:
        response["meta"] = meta
    return response


def paginated_response(
    items: list[Any],
    *,
    total: int,
    page: int = 1,
    page_size: int = 20,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create standardized paginated response.
    
    Args:
        items: List of items for current page
        total: Total number of items across all pages
        page: Current page number (1-indexed)
        page_size: Items per page
        meta: Optional additional metadata
        
    Returns:
        Paginated response dictionary
    """
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    
    pagination = {
        "page": page,
        "page_size": page_size,
        "total_items": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1,
    }
    
    response: dict[str, Any] = {
        "success": True,
        "data": items,
        "pagination": pagination,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    
    if meta:
        response["meta"] = meta
    
    return response


def error_response(
    error: str,
    message: str,
    *,
    details: dict[str, Any] | None = None,
    status_code: int = 400,
) -> dict[str, Any]:
    """Create standardized error response.
    
    Args:
        error: Machine-readable error code
        message: Human-readable error message
        details: Optional error details
        status_code: HTTP status code
        
    Returns:
        Error response dictionary
    """
    response: dict[str, Any] = {
        "success": False,
        "error": error,
        "message": message,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    if details:
        response["details"] = details
    return response


def created_response(
    data: Any,
    *,
    resource: str,
    identifier: str | None = None,
) -> dict[str, Any]:
    """Create response for newly created resource.
    
    Args:
        data: Created resource data
        resource: Type of resource created
        identifier: Optional identifier of created resource
        
    Returns:
        Created response dictionary
    """
    message = f"{resource} created successfully"
    if identifier:
        message = f"{resource} '{identifier}' created successfully"
    return api_response(data, message=message)


def deleted_response(
    resource: str,
    identifier: str | None = None,
) -> dict[str, Any]:
    """Create response for deleted resource.
    
    Args:
        resource: Type of resource deleted
        identifier: Optional identifier of deleted resource
        
    Returns:
        Deleted response dictionary
    """
    message = f"{resource} deleted successfully"
    if identifier:
        message = f"{resource} '{identifier}' deleted successfully"
    return api_response(None, message=message)


def updated_response(
    data: Any,
    *,
    resource: str,
    identifier: str | None = None,
) -> dict[str, Any]:
    """Create response for updated resource.
    
    Args:
        data: Updated resource data
        resource: Type of resource updated
        identifier: Optional identifier of updated resource
        
    Returns:
        Updated response dictionary
    """
    message = f"{resource} updated successfully"
    if identifier:
        message = f"{resource} '{identifier}' updated successfully"
    return api_response(data, message=message)
