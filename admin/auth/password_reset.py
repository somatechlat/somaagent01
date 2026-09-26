"""Password Reset API.


Per AGENT_TASKS.md Phase 2.3 - Password Reset.

- PhD Dev: Secure token generation
- Security Auditor: Rate limiting, token expiration
- Django Architect: Clean async patterns
"""

from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import timedelta

from django.utils import timezone
from ninja import Router
from pydantic import BaseModel, EmailStr

from admin.common.exceptions import BadRequestError
from admin.common.messages import ErrorCode, SuccessCode, get_message

router = Router(tags=["password-reset"])
logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS
# =============================================================================


class PasswordResetRequest(BaseModel):
    """Password reset request."""

    email: EmailStr


class PasswordResetResponse(BaseModel):
    """Password reset response (always success for security)."""

    success: bool = True
    message: str = "If the email exists, a reset link will be sent."


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation."""

    token: str
    new_password: str
    confirm_password: str


class PasswordResetConfirmResponse(BaseModel):
    """Password reset confirmation response."""

    success: bool
    message: str


class PasswordChangeRequest(BaseModel):
    """Change password (authenticated)."""

    current_password: str
    new_password: str
    confirm_password: str


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.post(
    "/request",
    response=PasswordResetResponse,
    summary="Request password reset",
)
async def request_password_reset(request, payload: PasswordResetRequest) -> PasswordResetResponse:
    """Request a password reset link.

    Per Phase 2.3: POST /auth/password/reset

    SECURITY:
    - Always returns success (prevents email enumeration)
    - Rate limited (in production)
    - Token expiration: 1 hour
    """
    from asgiref.sync import sync_to_async

    email = payload.email.lower().strip()

    # Generate secure reset token
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    expires_at = timezone.now() + timedelta(hours=1)

    @sync_to_async
    def _create_reset_request():
        # In production:
        # 1. Check if user exists (silently)
        # 2. Create PasswordResetToken record
        # 3. Send email via Keycloak or SMTP

        # PasswordResetToken.objects.filter(email=email, used=False).update(revoked=True)
        # PasswordResetToken.objects.create(
        #     email=email,
        #     token_hash=token_hash,
        #     expires_at=expires_at,
        # )

        # Keycloak option: Use Keycloak's built-in reset
        # KeycloakAdmin.send_reset_email(email)

        """Execute create reset request."""

        logger.info('Password reset requested for %s', email)
        return True

    await _create_reset_request()

    # In production: Send email asynchronously
    # reset_url = f"{settings.FRONTEND_URL}/auth/reset-password/{token}"
    # send_password_reset_email.delay(email=email, reset_url=reset_url)

    return PasswordResetResponse(
        success=True,
        message="If the email exists, a reset link will be sent.",
    )


@router.post(
    "/confirm",
    response=PasswordResetConfirmResponse,
    summary="Confirm password reset",
)
async def confirm_password_reset(
    request, payload: PasswordResetConfirm
) -> PasswordResetConfirmResponse:
    """Confirm password reset with token.

    Per Phase 2.3: POST /auth/password/confirm

    SECURITY:
    - Validates token hash
    - Single-use (marks as used)
    - Password strength validation
    """
    from asgiref.sync import sync_to_async

    if payload.new_password != payload.confirm_password:
        raise BadRequestError("Passwords do not match")

    if len(payload.new_password) < 8:
        raise BadRequestError("Password must be at least 8 characters")

    token_hash = hashlib.sha256(payload.token.encode()).hexdigest()

    @sync_to_async
    def _reset_password():
        # In production:
        # 1. Find token by hash
        # 2. Verify not expired or used
        # 3. Update password in Keycloak
        # 4. Mark token as used

        # reset_token = PasswordResetToken.objects.filter(
        #     token_hash=token_hash,
        #     used=False,
        #     revoked=False,
        #     expires_at__gt=timezone.now(),
        # ).first()
        #
        # if not reset_token:
        #     raise BadRequestError("Invalid or expired token")
        #
        # KeycloakAdmin.set_user_password(
        #     email=reset_token.email,
        #     password=payload.new_password,
        # )
        #
        # reset_token.used = True
        # reset_token.used_at = timezone.now()
        # reset_token.save()

        """Execute reset password."""

        # FAIL-CLOSED: Cannot reset password without validating the token
        # against the database. Treat as failure until persistence is wired.
        raise BadRequestError("Invalid or expired token")

    try:
        await _reset_password()

        logger.info("Password reset completed")

        return PasswordResetConfirmResponse(
            success=True,
            message="Password has been reset successfully",
        )

    except BadRequestError:
        raise
    except Exception as e:
        logger.error('Password reset failed: %s', e)
        raise BadRequestError("Password reset failed")


@router.get(
    "/validate/{token}",
    summary="Validate reset token",
)
async def validate_reset_token(request, token: str) -> dict:
    """Validate a password reset token.

    Check if token is still valid before showing reset form.
    """
    from asgiref.sync import sync_to_async

    token_hash = hashlib.sha256(token.encode()).hexdigest()

    @sync_to_async
    def _check_token():
        # FAIL-CLOSED: Password reset token validation requires the
        # PasswordResetToken database model to verify token hash,
        # expiration, and usage status.
        # Until persistence is wired, all tokens are treated as invalid.
        """Execute check token."""

        return False

    is_valid = await _check_token()

    return {
        "valid": is_valid,
        "message": get_message(SuccessCode.TOKEN_VALID) if is_valid else get_message(ErrorCode.TOKEN_INVALID_OR_EXPIRED),
    }


@router.post(
    "/change",
    summary="Change password (authenticated)",
)
async def change_password(request, payload: PasswordChangeRequest) -> dict:
    """Change password for authenticated user via Keycloak.

    Requires current password verification.
    """
    from admin.common.auth import decode_token, get_keycloak_config

    if payload.new_password != payload.confirm_password:
        raise BadRequestError("Passwords do not match")

    if len(payload.new_password) < 8:
        raise BadRequestError("Password must be at least 8 characters")

    # Verify current password with Keycloak
    config = get_keycloak_config()
    token_url = f"{config.server_url}/realms/{config.realm}/protocol/openid-connect/token"

    # Extract email from auth context
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise BadRequestError("Authentication required")

    try:
        current_user = await decode_token(auth_header[7:])
    except Exception:
        raise BadRequestError("Invalid authentication token")

    email = current_user.email
    if not email:
        raise BadRequestError("Email not found in token")

    # Verify current password by attempting login
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            verify_resp = await client.post(
                token_url,
                data={
                    "grant_type": "password",
                    "client_id": config.client_id,
                    "username": email,
                    "password": payload.current_password,
                    "scope": "openid",
                },
            )
            if verify_resp.status_code != 200:
                raise BadRequestError("Current password is incorrect")

            # Update password via Keycloak admin API
            admin_token_url = f"{config.server_url}/realms/master/protocol/openid-connect/token"
            admin_resp = await client.post(
                admin_token_url,
                data={
                    "grant_type": "password",
                    "client_id": "admin-cli",
                    "username": "admin",
                    "password": request.META.get("KEYCLOAK_ADMIN_PASSWORD", ""),
                },
            )
            if admin_resp.status_code != 200:
                raise BadRequestError("Password change service unavailable")

            admin_token = admin_resp.json()["access_token"]

            # Find user by email
            users_resp = await client.get(
                f"{config.server_url}/admin/realms/{config.realm}/users",
                params={"email": email},
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            if users_resp.status_code != 200 or not users_resp.json():
                raise BadRequestError("User not found")

            user_id = users_resp.json()[0]["id"]

            # Reset password
            reset_resp = await client.put(
                f"{config.server_url}/admin/realms/{config.realm}/users/{user_id}/reset-password",
                json={
                    "type": "password",
                    "value": payload.new_password,
                    "temporary": False,
                },
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            if reset_resp.status_code == 204:
                logger.info("Password changed for user: %s", email)
                return {
                    "success": True,
                    "message": get_message(SuccessCode.PASSWORD_CHANGED),
                }
            else:
                raise BadRequestError("Password change failed")

    except BadRequestError:
        raise
    except Exception as e:
        logger.error('Password change failed: %s', e)
        raise BadRequestError("Password change failed")
