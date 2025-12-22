"""
Eye of God API - Auth Endpoints
Per Eye of God UIX Design Section 2.1

VIBE COMPLIANT:
- Real Django Ninja endpoints
- JWT token generation
- Password hashing
"""

from datetime import datetime, timedelta
from typing import Optional
import os
import jwt
import hashlib
import secrets

from django.http import HttpRequest
from ninja import Router

from api.schemas import (
    TokenRequest,
    TokenResponse,
    UserInfo,
    ErrorResponse,
)
from core.models import User

router = Router(tags=["Authentication"])

JWT_SECRET = os.getenv('JWT_SECRET', 'dev-secret-change-in-production')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
JWT_EXPIRY_HOURS = int(os.getenv('JWT_EXPIRY_HOURS', '24'))


def _hash_password(password: str, salt: str) -> str:
    """Hash password with salt using SHA-256."""
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()


def _verify_password(password: str, salt: str, hashed: str) -> bool:
    """Verify password against hash."""
    return _hash_password(password, salt) == hashed


def _create_token(user_id: str, tenant_id: str, role: str, email: Optional[str] = None) -> str:
    """Create JWT token."""
    now = datetime.utcnow()
    payload = {
        'sub': user_id,
        'tenant_id': tenant_id,
        'role': role,
        'email': email,
        'iat': now,
        'exp': now + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


@router.post(
    "/token",
    response={200: TokenResponse, 401: ErrorResponse},
    auth=None,
    summary="Obtain JWT token"
)
async def login(request: HttpRequest, payload: TokenRequest) -> TokenResponse:
    """
    Authenticate user and obtain JWT access token.
    
    The token includes:
    - sub: User ID
    - tenant_id: Tenant ID
    - role: User role
    - exp: Expiration timestamp
    """
    try:
        user = await User.objects.aget(username=payload.username)
        
        # Verify password
        if not _verify_password(payload.password, user.salt, user.password_hash):
            raise ValueError("Invalid credentials")
        
        # Generate token
        token = _create_token(
            user_id=str(user.id),
            tenant_id=str(user.tenant_id),
            role=user.role,
            email=user.email,
        )
        
        # Update last login
        user.last_login = datetime.utcnow()
        await user.asave(update_fields=['last_login'])
        
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=JWT_EXPIRY_HOURS * 3600,
        )
        
    except User.DoesNotExist:
        raise ValueError("Invalid credentials")


@router.post(
    "/refresh",
    response={200: TokenResponse, 401: ErrorResponse},
    summary="Refresh JWT token"
)
async def refresh_token(request: HttpRequest) -> TokenResponse:
    """
    Refresh JWT token before expiration.
    
    Returns a new token with extended expiration.
    """
    user_id = request.auth.get('user_id')
    tenant_id = request.auth.get('tenant_id')
    role = request.auth.get('role')
    email = request.auth.get('email')
    
    if not user_id or not tenant_id:
        raise ValueError("Invalid token")
    
    token = _create_token(
        user_id=user_id,
        tenant_id=tenant_id,
        role=role,
        email=email,
    )
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=JWT_EXPIRY_HOURS * 3600,
    )


@router.get(
    "/me",
    response={200: UserInfo, 401: ErrorResponse},
    summary="Get current user info"
)
async def get_current_user(request: HttpRequest) -> UserInfo:
    """
    Get information about the currently authenticated user.
    
    Includes permissions based on role.
    """
    user_id = request.auth.get('user_id')
    
    try:
        user = await User.objects.aget(id=user_id)
        
        # Get permissions based on role
        permissions = _get_role_permissions(user.role)
        
        return UserInfo(
            id=user.id,
            tenant_id=user.tenant_id,
            username=user.username,
            email=user.email,
            role=user.role,
            mode=user.current_mode or 'STD',
            permissions=permissions,
        )
        
    except User.DoesNotExist:
        raise ValueError("User not found")


@router.post(
    "/logout",
    response={200: dict},
    summary="Logout (client-side token invalidation)"
)
async def logout(request: HttpRequest) -> dict:
    """
    Logout endpoint.
    
    Note: JWT tokens are stateless. This endpoint is for audit logging.
    Client should discard the token.
    """
    user_id = request.auth.get('user_id')
    tenant_id = request.auth.get('tenant_id')
    
    # Import here to avoid circular imports
    from core.models import AuditLog
    
    await AuditLog.objects.acreate(
        tenant_id=tenant_id,
        user_id=user_id,
        action="auth.logout",
        resource_type="session",
        resource_id=user_id,
        details={},
    )
    
    return {"success": True, "message": "Logged out successfully"}


@router.post(
    "/register",
    response={201: UserInfo, 400: ErrorResponse},
    auth=None,
    summary="Register new user (dev only)"
)
async def register(
    request: HttpRequest,
    username: str,
    password: str,
    email: Optional[str] = None,
    tenant_id: Optional[str] = None,
) -> UserInfo:
    """
    Register a new user.
    
    Note: In production, registration should be controlled by admin.
    This endpoint is for development/testing purposes.
    """
    # Check if user exists
    if await User.objects.filter(username=username).aexists():
        raise ValueError("Username already exists")
    
    # Generate salt and hash password
    salt = secrets.token_hex(16)
    password_hash = _hash_password(password, salt)
    
    # Create default tenant if not specified
    from core.models import Tenant
    from uuid import UUID, uuid4
    
    if tenant_id:
        tenant_uuid = UUID(tenant_id)
    else:
        # Create new tenant for user
        tenant = await Tenant.objects.acreate(
            name=f"{username}'s Tenant",
        )
        tenant_uuid = tenant.id
    
    # Create user
    user = await User.objects.acreate(
        tenant_id=tenant_uuid,
        username=username,
        email=email,
        password_hash=password_hash,
        salt=salt,
        role='member',
        current_mode='STD',
    )
    
    permissions = _get_role_permissions(user.role)
    
    return UserInfo(
        id=user.id,
        tenant_id=user.tenant_id,
        username=user.username,
        email=user.email,
        role=user.role,
        mode=user.current_mode,
        permissions=permissions,
    )


def _get_role_permissions(role: str) -> list[str]:
    """Get permissions for a role."""
    role_permissions = {
        'sysadmin': [
            'mode:use', 'mode:train', 'mode:admin', 'mode:developer', 'mode:danger',
            'settings:read', 'settings:write', 'settings:admin',
            'themes:read', 'themes:write', 'themes:approve', 'themes:delete',
            'memory:read', 'memory:write', 'memory:delete',
            'tools:use', 'tools:admin',
            'cognitive:read', 'cognitive:write',
            'admin:access', 'audit:read',
        ],
        'admin': [
            'mode:use', 'mode:train', 'mode:admin',
            'settings:read', 'settings:write', 'settings:admin',
            'themes:read', 'themes:write', 'themes:approve',
            'memory:read', 'memory:write', 'memory:delete',
            'tools:use', 'tools:admin',
            'cognitive:read', 'cognitive:write',
            'admin:access', 'audit:read',
        ],
        'developer': [
            'mode:use', 'mode:developer',
            'settings:read', 'settings:write',
            'themes:read', 'themes:write',
            'memory:read', 'memory:write',
            'tools:use',
            'cognitive:read',
        ],
        'trainer': [
            'mode:use', 'mode:train',
            'settings:read',
            'themes:read',
            'memory:read', 'memory:write',
            'tools:use',
        ],
        'member': [
            'mode:use',
            'settings:read',
            'themes:read', 'themes:write',
            'memory:read', 'memory:write',
            'tools:use',
        ],
        'viewer': [
            'settings:read',
            'themes:read',
            'memory:read',
        ],
    }
    return role_permissions.get(role, [])
