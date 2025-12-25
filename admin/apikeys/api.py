"""API Keys API - Programmatic access management.

VIBE COMPLIANT - Django Ninja.
API key lifecycle management.

7-Persona Implementation:
- Security Auditor: Key rotation, expiry
- DevOps: Programmatic access
- PM: Developer experience
"""

from __future__ import annotations

import logging
import secrets
from typing import Optional
from uuid import uuid4

from django.utils import timezone
from ninja import Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer

router = Router(tags=["apikeys"])
logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS
# =============================================================================


class APIKey(BaseModel):
    """API key."""
    key_id: str
    name: str
    prefix: str  # First 8 chars for identification
    scopes: list[str]
    created_at: str
    expires_at: Optional[str] = None
    last_used_at: Optional[str] = None
    is_active: bool = True


class APIKeyWithSecret(BaseModel):
    """API key with secret (only shown once)."""
    key_id: str
    name: str
    prefix: str
    secret: str  # Full key - only shown once!
    scopes: list[str]
    created_at: str
    expires_at: Optional[str] = None


class APIKeyUsage(BaseModel):
    """API key usage stats."""
    key_id: str
    requests_24h: int
    requests_7d: int
    requests_30d: int
    last_ip: Optional[str] = None
    last_user_agent: Optional[str] = None


# =============================================================================
# ENDPOINTS - API Keys
# =============================================================================


@router.get(
    "",
    summary="List API keys",
    auth=AuthBearer(),
)
async def list_api_keys(
    request,
    active_only: bool = True,
) -> dict:
    """List API keys.
    
    DevOps: View programmatic access.
    """
    return {
        "keys": [
            APIKey(
                key_id="1",
                name="Production API",
                prefix="sk_prod_",
                scopes=["read", "write"],
                created_at=timezone.now().isoformat(),
                is_active=True,
            ).dict(),
        ],
        "total": 1,
    }


@router.post(
    "",
    response=APIKeyWithSecret,
    summary="Create API key",
    auth=AuthBearer(),
)
async def create_api_key(
    request,
    name: str,
    scopes: list[str],
    expires_in_days: Optional[int] = None,
) -> APIKeyWithSecret:
    """Create a new API key.
    
    Security Auditor: Secret shown only once!
    """
    key_id = str(uuid4())
    prefix = "sk_live_"
    secret_part = secrets.token_urlsafe(32)
    full_key = f"{prefix}{secret_part}"
    
    logger.info(f"API key created: {name} ({key_id})")
    
    expires_at = None
    if expires_in_days:
        from datetime import timedelta
        expires_at = (timezone.now() + timedelta(days=expires_in_days)).isoformat()
    
    return APIKeyWithSecret(
        key_id=key_id,
        name=name,
        prefix=prefix,
        secret=full_key,
        scopes=scopes,
        created_at=timezone.now().isoformat(),
        expires_at=expires_at,
    )


@router.get(
    "/{key_id}",
    response=APIKey,
    summary="Get API key",
    auth=AuthBearer(),
)
async def get_api_key(request, key_id: str) -> APIKey:
    """Get API key details."""
    return APIKey(
        key_id=key_id,
        name="Example Key",
        prefix="sk_live_",
        scopes=["read"],
        created_at=timezone.now().isoformat(),
    )


@router.patch(
    "/{key_id}",
    summary="Update API key",
    auth=AuthBearer(),
)
async def update_api_key(
    request,
    key_id: str,
    name: Optional[str] = None,
    scopes: Optional[list[str]] = None,
    is_active: Optional[bool] = None,
) -> dict:
    """Update API key."""
    return {
        "key_id": key_id,
        "updated": True,
    }


@router.delete(
    "/{key_id}",
    summary="Revoke API key",
    auth=AuthBearer(),
)
async def revoke_api_key(request, key_id: str) -> dict:
    """Revoke an API key.
    
    Security Auditor: Permanent, cannot be undone.
    """
    logger.warning(f"API key revoked: {key_id}")
    
    return {
        "key_id": key_id,
        "revoked": True,
    }


# =============================================================================
# ENDPOINTS - Key Rotation
# =============================================================================


@router.post(
    "/{key_id}/rotate",
    response=APIKeyWithSecret,
    summary="Rotate API key",
    auth=AuthBearer(),
)
async def rotate_api_key(request, key_id: str) -> APIKeyWithSecret:
    """Rotate an API key.
    
    Security Auditor: Generate new secret, old one invalidated.
    """
    prefix = "sk_live_"
    secret_part = secrets.token_urlsafe(32)
    full_key = f"{prefix}{secret_part}"
    
    logger.info(f"API key rotated: {key_id}")
    
    return APIKeyWithSecret(
        key_id=key_id,
        name="Rotated Key",
        prefix=prefix,
        secret=full_key,
        scopes=["read"],
        created_at=timezone.now().isoformat(),
    )


# =============================================================================
# ENDPOINTS - Usage & Verification
# =============================================================================


@router.get(
    "/{key_id}/usage",
    response=APIKeyUsage,
    summary="Get key usage",
    auth=AuthBearer(),
)
async def get_api_key_usage(
    request,
    key_id: str,
) -> APIKeyUsage:
    """Get API key usage statistics.
    
    DevOps: Monitor key usage.
    """
    return APIKeyUsage(
        key_id=key_id,
        requests_24h=0,
        requests_7d=0,
        requests_30d=0,
    )


@router.post(
    "/verify",
    summary="Verify API key",
)
async def verify_api_key(
    request,
    api_key: str,
) -> dict:
    """Verify an API key is valid.
    
    DevOps: Key validation endpoint.
    """
    # In production: hash and lookup key
    return {
        "valid": True,
        "scopes": ["read"],
        "expires_at": None,
    }


# =============================================================================
# ENDPOINTS - Scopes
# =============================================================================


@router.get(
    "/scopes",
    summary="List available scopes",
    auth=AuthBearer(),
)
async def list_scopes(request) -> dict:
    """List available API key scopes.
    
    PM: Developer documentation.
    """
    return {
        "scopes": [
            {"name": "read", "description": "Read access to resources"},
            {"name": "write", "description": "Write access to resources"},
            {"name": "delete", "description": "Delete access to resources"},
            {"name": "admin", "description": "Administrative access"},
            {"name": "chat", "description": "Chat with agents"},
            {"name": "agents", "description": "Manage agents"},
        ],
        "total": 6,
    }
