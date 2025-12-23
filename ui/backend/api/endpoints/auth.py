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
    
    Returns redirect_path based on role:
    - saas_admin/sysadmin -> /select-mode
    - others -> /chat
    """
    from core.models import AuditLog
    import logging
    
    LOGGER = logging.getLogger(__name__)
    
    try:
        user = await User.objects.aget(username=payload.username)
        
        # Verify password
        if not _verify_password(payload.password, user.salt, user.password_hash):
            # Audit failed login attempt
            await AuditLog.objects.acreate(
                tenant_id=user.tenant_id,
                user_id=str(user.id),
                action="auth.login_failed",
                resource_type="user",
                resource_id=str(user.id),
                details={"reason": "invalid_password", "username": payload.username},
            )
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
        
        # Determine redirect path based on role
        # SAAS admins (sysadmin, saas_admin) go to mode selection
        saas_admin_roles = ['sysadmin', 'saas_admin']
        if user.role in saas_admin_roles:
            redirect_path = '/select-mode'
        else:
            redirect_path = '/chat'
        
        # Audit successful login
        await AuditLog.objects.acreate(
            tenant_id=user.tenant_id,
            user_id=str(user.id),
            action="auth.login_success",
            resource_type="session",
            resource_id=str(user.id),
            details={
                "role": user.role,
                "redirect_path": redirect_path,
                "ip_address": request.META.get('REMOTE_ADDR', 'unknown'),
            },
        )
        
        LOGGER.info(f"User {user.username} logged in successfully, redirecting to {redirect_path}")
        
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=JWT_EXPIRY_HOURS * 3600,
            role=user.role,
            redirect_path=redirect_path,
        )
        
    except User.DoesNotExist:
        # Generic error to prevent user enumeration
        LOGGER.warning(f"Login attempt for non-existent user: {payload.username}")
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


# =============================================================================
# GOOGLE OAUTH
# =============================================================================

GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '')
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:5173/auth/callback')


class GoogleCallbackRequest(BaseModel):
    """Google OAuth callback request."""
    code: str
    redirect_uri: Optional[str] = None


class GoogleCallbackResponse(BaseModel):
    """Google OAuth callback response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    role: str
    redirect_path: str
    user: dict


from pydantic import BaseModel as PydanticBaseModel

class BaseModel(PydanticBaseModel):
    class Config:
        extra = 'allow'


@router.post(
    "/google/callback",
    response={200: dict, 400: ErrorResponse},
    auth=None,
    summary="Handle Google OAuth callback"
)
async def google_callback(request: HttpRequest, payload: GoogleCallbackRequest) -> dict:
    """
    Exchange Google authorization code for tokens and create/login user.
    
    Flow:
    1. Exchange code for Google tokens
    2. Get user info from Google
    3. Find or create user in database
    4. Generate JWT token
    5. Return token with role-based redirect
    """
    import httpx
    import logging
    from core.models import Tenant, AuditLog
    from uuid import uuid4
    
    LOGGER = logging.getLogger(__name__)
    
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise ValueError("Google OAuth not configured")
    
    try:
        # Exchange code for tokens
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                'https://oauth2.googleapis.com/token',
                data={
                    'code': payload.code,
                    'client_id': GOOGLE_CLIENT_ID,
                    'client_secret': GOOGLE_CLIENT_SECRET,
                    'redirect_uri': payload.redirect_uri or GOOGLE_REDIRECT_URI,
                    'grant_type': 'authorization_code',
                }
            )
            
            if token_response.status_code != 200:
                LOGGER.error(f"Google token exchange failed: {token_response.text}")
                raise ValueError("Failed to exchange authorization code")
            
            tokens = token_response.json()
            
            # Get user info from Google
            user_response = await client.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f"Bearer {tokens['access_token']}"}
            )
            
            if user_response.status_code != 200:
                raise ValueError("Failed to get user info from Google")
            
            google_user = user_response.json()
        
        # Find or create user
        email = google_user.get('email')
        if not email:
            raise ValueError("Google account has no email")
        
        try:
            user = await User.objects.aget(email=email)
            LOGGER.info(f"Existing user logged in via Google: {email}")
        except User.DoesNotExist:
            # Create new user from Google account
            # First, get or create default tenant
            default_tenant, _ = await Tenant.objects.aget_or_create(
                name='Default',
                defaults={'slug': 'default'}
            )
            
            user = await User.objects.acreate(
                id=uuid4(),
                tenant_id=default_tenant.id,
                username=email.split('@')[0],
                email=email,
                password_hash='',  # No password for OAuth users
                salt='',
                role='member',
                current_mode='STD',
            )
            LOGGER.info(f"New user created via Google: {email}")
        
        # Update last login
        user.last_login = datetime.utcnow()
        await user.asave(update_fields=['last_login'])
        
        # Generate JWT token
        token = _create_token(
            user_id=str(user.id),
            tenant_id=str(user.tenant_id),
            role=user.role,
            email=user.email,
        )
        
        # Determine redirect path
        saas_admin_roles = ['sysadmin', 'saas_admin']
        redirect_path = '/select-mode' if user.role in saas_admin_roles else '/chat'
        
        # Audit log
        await AuditLog.objects.acreate(
            tenant_id=user.tenant_id,
            user_id=str(user.id),
            action="auth.google_login",
            resource_type="session",
            resource_id=str(user.id),
            details={
                "provider": "google",
                "google_id": google_user.get('id'),
                "redirect_path": redirect_path,
            },
        )
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": JWT_EXPIRY_HOURS * 3600,
            "role": user.role,
            "redirect_path": redirect_path,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": google_user.get('name', ''),
                "picture": google_user.get('picture', ''),
            }
        }
        
    except Exception as e:
        LOGGER.error(f"Google OAuth failed: {e}")
        raise ValueError(f"Google authentication failed: {str(e)}")

