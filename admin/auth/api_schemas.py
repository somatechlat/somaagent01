"""Authentication Schemas - Request/Response models for auth API.

Extracted from admin/auth/api.py for 650-line compliance.
"""

from typing import Optional

from ninja import Schema


# Core Auth Schemas
class TokenRequest(Schema):
    """Login request with username/password or OAuth code."""

    username: Optional[str] = None
    password: Optional[str] = None
    code: Optional[str] = None
    redirect_uri: Optional[str] = None
    grant_type: str = "password"


class TokenResponse(Schema):
    """Token response."""

    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: int
    redirect_path: str = "/chat"


class RefreshRequest(Schema):
    """Refresh token request."""

    refresh_token: Optional[str] = None


class UserResponse(Schema):
    """Current user info response."""

    id: str
    tenant_id: Optional[str] = None
    username: str
    email: Optional[str] = None
    name: Optional[str] = None
    role: str
    roles: list[str] = []
    permissions: list[str] = []


# Impersonation Schemas
class ImpersonationRequest(Schema):
    """Request to impersonate a tenant admin."""

    tenant_id: str
    reason: str


class ImpersonationResponse(Schema):
    """Impersonation token response."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    impersonating_tenant: str
    original_user_id: str
    audit_id: str


# SSO Schemas
class SSOConfigRequest(Schema):
    """SSO configuration request."""

    provider: str
    config: dict


class SSOTestRequest(Schema):
    """SSO connection test request."""

    provider: str
    config: dict


# Login/Register Schemas
class LoginRequest(Schema):
    """Email/password login request."""

    email: str
    password: str
    remember_me: bool = False


class RegisterRequest(Schema):
    """User registration request."""

    name: str
    email: str
    password: str


class PasswordResetRequest(Schema):
    """Password reset request."""

    email: str


class PasswordResetConfirm(Schema):
    """Password reset confirmation."""

    token: str
    new_password: str


class MFARequest(Schema):
    """MFA verification request."""

    method: str
    code: str


class MFASetupRequest(Schema):
    """MFA setup request."""

    method: str


class MFASetupResponse(Schema):
    """MFA setup response."""

    secret: Optional[str] = None
    qr_code_url: Optional[str] = None
    backup_codes: list[str] = []
    phone_masked: Optional[str] = None


__all__ = [
    "TokenRequest",
    "TokenResponse",
    "RefreshRequest",
    "UserResponse",
    "ImpersonationRequest",
    "ImpersonationResponse",
    "SSOConfigRequest",
    "SSOTestRequest",
    "LoginRequest",
    "RegisterRequest",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    "MFARequest",
    "MFASetupRequest",
    "MFASetupResponse",
]
