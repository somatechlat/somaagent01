"""
AAAS Admin API Schemas
Django Ninja/Pydantic schemas for request/response validation.

Scope: schemas for administering this agent — its API keys, its model
configuration and its roles.

There are no commercial billing schemas here. This product is a standalone
agent: subscription tiers, invoices, payment methods, plan feature gating
and multi-tenant org lifecycle are not part of it and are not modelled.
See AGENT.md §1.1 (Scope).
"""

from datetime import datetime
from typing import Optional

from ninja import Schema


# =============================================================================
# API KEY SCHEMAS
# =============================================================================
class ApiKeyOut(Schema):
    """API key response schema."""

    id: str
    name: str
    prefix: str
    tenant_id: Optional[str] = None
    created_at: datetime
    last_used: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class ApiKeyCreate(Schema):
    """Create API key request.

    Scopes are mandatory. An API key is a delegation, so it carries an
    explicit subset of the issuer's authority — never an implicit "all".
    """

    name: str
    tenant_id: Optional[str] = None
    expires_in_days: Optional[int] = None
    scopes: list[str]


# =============================================================================
# MODEL CONFIG SCHEMAS
# =============================================================================
class ModelConfigOut(Schema):
    """LLM model configuration response."""

    id: str
    provider: str
    model_name: str
    display_name: str
    enabled: bool
    default_for_chat: bool = False
    default_for_completion: bool = False
    rate_limit: Optional[int] = None


class ModelConfigUpdate(Schema):
    """Update model configuration request."""

    enabled: Optional[bool] = None
    default_for_chat: Optional[bool] = None
    default_for_completion: Optional[bool] = None
    rate_limit: Optional[int] = None


# =============================================================================
# ROLE SCHEMAS
# =============================================================================
class RoleOut(Schema):
    """Role response schema."""

    id: str
    name: str
    description: str
    permissions: list[str]
    user_count: int = 0


class RoleUpdate(Schema):
    """Update role request."""

    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[list[str]] = None


# =============================================================================
# COMMON SCHEMAS
# =============================================================================
class MessageResponse(Schema):
    """Generic message response."""

    message: str
    success: bool = True


class ErrorResponse(Schema):
    """Error response schema."""

    detail: str
    code: Optional[str] = None
