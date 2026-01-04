"""Common Pydantic schemas for Django Ninja endpoints.

Provides reusable request/response schemas across all API endpoints.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    """Return timezone-aware UTC datetime ("""
    return datetime.now(timezone.utc)


T = TypeVar("T")


# =============================================================================
# PAGINATION SCHEMAS
# =============================================================================


class PaginatedRequest(BaseModel):
    """Standard pagination request parameters."""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    sort_by: str | None = Field(default=None, description="Field to sort by")
    sort_order: str = Field(default="asc", pattern="^(asc|desc)$", description="Sort order")

    @property
    def offset(self) -> int:
        """Calculate SQL offset from page and page_size."""
        return (self.page - 1) * self.page_size


class PaginationInfo(BaseModel):
    """Pagination metadata in response."""

    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_items: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there's a next page")
    has_previous: bool = Field(..., description="Whether there's a previous page")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated response wrapper."""

    success: bool = True
    data: list[T]
    pagination: PaginationInfo
    timestamp: datetime = Field(default_factory=_utc_now)


# =============================================================================
# ERROR SCHEMAS
# =============================================================================


class ErrorDetail(BaseModel):
    """Individual error detail."""

    field: str | None = None
    message: str
    code: str | None = None


class ErrorResponse(BaseModel):
    """Standard error response."""

    success: bool = False
    error: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: list[ErrorDetail] | dict[str, Any] | None = None
    timestamp: datetime = Field(default_factory=_utc_now)


# =============================================================================
# SUCCESS SCHEMAS
# =============================================================================


class SuccessResponse(BaseModel):
    """Standard success response without data."""

    success: bool = True
    message: str
    timestamp: datetime = Field(default_factory=_utc_now)


class DataResponse(BaseModel, Generic[T]):
    """Standard success response with data."""

    success: bool = True
    data: T
    message: str | None = None
    meta: dict[str, Any] | None = None
    timestamp: datetime = Field(default_factory=_utc_now)


# =============================================================================
# COMMON ENTITY SCHEMAS
# =============================================================================


class EntityRef(BaseModel):
    """Minimal entity reference (for foreign key displays)."""

    id: UUID
    name: str


class AuditFields(BaseModel):
    """Common audit fields for entities."""

    created_at: datetime
    updated_at: datetime
    created_by: str | None = None
    updated_by: str | None = None


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""

    created_at: datetime
    updated_at: datetime


# =============================================================================
# FILTER SCHEMAS
# =============================================================================


class DateRangeFilter(BaseModel):
    """Date range filter parameters."""

    start_date: datetime | None = None
    end_date: datetime | None = None


class SearchFilter(BaseModel):
    """Text search filter parameters."""

    query: str = Field(..., min_length=1, max_length=255)
    fields: list[str] | None = None


# =============================================================================
# HEALTH & STATUS SCHEMAS
# =============================================================================


class HealthStatus(BaseModel):
    """Health check status."""

    status: str = Field(..., pattern="^(healthy|unhealthy|degraded)$")
    latency_ms: float | None = None
    message: str | None = None


class ServiceHealth(BaseModel):
    """Individual service health."""

    name: str
    status: str
    latency_ms: float | None = None
    error: str | None = None


class AggregatedHealth(BaseModel):
    """Aggregated health of all services."""

    overall: str
    services: list[ServiceHealth]
    timestamp: datetime = Field(default_factory=_utc_now)


# =============================================================================
# BULK OPERATION SCHEMAS
# =============================================================================


class BulkOperationRequest(BaseModel):
    """Request for bulk operations."""

    ids: list[UUID] = Field(..., min_length=1, max_length=100)


class BulkOperationResult(BaseModel):
    """Result of bulk operation."""

    success: bool
    total: int
    succeeded: int
    failed: int
    errors: list[dict[str, Any]] | None = None