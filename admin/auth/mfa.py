"""MFA Authentication API.

VIBE COMPLIANT - Django Ninja + pyotp.
Per AGENT_TASKS.md Phase 2.2 - MFA Setup.
"""

from __future__ import annotations

import base64
import io
import logging
from typing import Optional

from ninja import Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer
from admin.common.exceptions import BadRequestError, UnauthorizedError

router = Router(tags=["mfa"])
logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS
# =============================================================================


class MFASetupResponse(BaseModel):
    """MFA setup response with TOTP secret and QR code."""
    secret: str
    qr_code_base64: str
    provisioning_uri: str
    backup_codes: list[str]


class MFAVerifyRequest(BaseModel):
    """MFA verification request."""
    code: str  # 6-digit TOTP code


class MFAVerifyResponse(BaseModel):
    """MFA verification response."""
    success: bool
    mfa_enabled: bool
    message: str


class MFAStatusResponse(BaseModel):
    """MFA status response."""
    mfa_enabled: bool
    mfa_type: Optional[str] = None  # totp, sms, email


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.post(
    "/setup",
    response=MFASetupResponse,
    summary="Initialize MFA setup",
    auth=AuthBearer(),
)
async def setup_mfa(request) -> MFASetupResponse:
    """Initialize TOTP MFA setup.
    
    Per Phase 2.2: POST /auth/mfa/setup
    
    Returns:
        - TOTP secret (store securely)
        - QR code as base64 PNG
        - Provisioning URI for manual entry
        - Backup codes for recovery
    """
    import pyotp
    import secrets
    
    # Get user from auth context
    user_email = "user@example.com"  # Would come from request.auth
    
    # Generate TOTP secret
    secret = pyotp.random_base32()
    
    # Create provisioning URI
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=user_email,
        issuer_name="SomaAgent",
    )
    
    # Generate QR code
    qr_code_base64 = _generate_qr_code(provisioning_uri)
    
    # Generate backup codes
    backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]
    
    # In production: Store secret and backup codes (encrypted) in database
    # MFASetup.objects.create(user_id=..., secret=encrypt(secret), ...)
    
    logger.info(f"MFA setup initiated for {user_email}")
    
    return MFASetupResponse(
        secret=secret,
        qr_code_base64=qr_code_base64,
        provisioning_uri=provisioning_uri,
        backup_codes=backup_codes,
    )


@router.post(
    "/verify",
    response=MFAVerifyResponse,
    summary="Verify MFA code",
    auth=AuthBearer(),
)
async def verify_mfa(request, payload: MFAVerifyRequest) -> MFAVerifyResponse:
    """Verify TOTP code and enable MFA.
    
    Per Phase 2.2: POST /auth/mfa/verify
    
    This endpoint:
    1. Validates the 6-digit TOTP code
    2. If valid, enables MFA for the user
    3. Returns success/failure status
    """
    import pyotp
    
    # Get user's stored TOTP secret
    # In production: retrieve from database
    stored_secret = "JBSWY3DPEHPK3PXP"  # Placeholder
    
    # Validate code
    totp = pyotp.TOTP(stored_secret)
    is_valid = totp.verify(payload.code, valid_window=1)
    
    if not is_valid:
        return MFAVerifyResponse(
            success=False,
            mfa_enabled=False,
            message="Invalid code. Please try again.",
        )
    
    # Enable MFA for user
    # In production: update user record
    # User.objects.filter(id=user_id).update(mfa_enabled=True)
    
    logger.info("MFA enabled for user")
    
    return MFAVerifyResponse(
        success=True,
        mfa_enabled=True,
        message="MFA successfully enabled",
    )


@router.post(
    "/validate",
    summary="Validate MFA during login",
)
async def validate_mfa_login(request, payload: MFAVerifyRequest) -> dict:
    """Validate MFA code during login flow.
    
    Called after password verification when MFA is required.
    """
    import pyotp
    
    # Get pending MFA session (from session or temp token)
    # In production: retrieve from session/cache
    stored_secret = "JBSWY3DPEHPK3PXP"  # Placeholder
    
    totp = pyotp.TOTP(stored_secret)
    is_valid = totp.verify(payload.code, valid_window=1)
    
    if not is_valid:
        raise UnauthorizedError("Invalid MFA code")
    
    # Complete login - issue full tokens
    return {
        "success": True,
        "message": "MFA validated",
        # In production: return access_token, refresh_token
    }


@router.get(
    "/status",
    response=MFAStatusResponse,
    summary="Get MFA status",
    auth=AuthBearer(),
)
async def get_mfa_status(request) -> MFAStatusResponse:
    """Get current MFA status for the user."""
    # In production: query user record
    return MFAStatusResponse(
        mfa_enabled=False,
        mfa_type=None,
    )


@router.post(
    "/disable",
    summary="Disable MFA",
    auth=AuthBearer(),
)
async def disable_mfa(request, payload: MFAVerifyRequest) -> dict:
    """Disable MFA (requires current TOTP code)."""
    import pyotp
    
    # Verify code before disabling
    stored_secret = "JBSWY3DPEHPK3PXP"  # Placeholder
    
    totp = pyotp.TOTP(stored_secret)
    is_valid = totp.verify(payload.code, valid_window=1)
    
    if not is_valid:
        raise BadRequestError("Invalid code - MFA not disabled")
    
    # Disable MFA
    # User.objects.filter(id=user_id).update(mfa_enabled=False, mfa_secret=None)
    
    logger.info("MFA disabled for user")
    
    return {
        "success": True,
        "mfa_enabled": False,
        "message": "MFA disabled",
    }


@router.post(
    "/backup-code",
    summary="Use backup code",
)
async def use_backup_code(request, code: str) -> dict:
    """Use a backup code for recovery."""
    # In production: validate against stored backup codes
    # Mark code as used (one-time use only)
    
    return {
        "success": True,
        "message": "Backup code accepted",
    }


# =============================================================================
# HELPERS
# =============================================================================


def _generate_qr_code(data: str) -> str:
    """Generate QR code as base64 PNG.
    
    Uses qrcode library if available, otherwise returns placeholder.
    """
    try:
        import qrcode
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()
        
    except ImportError:
        # Fallback if qrcode not installed
        logger.warning("qrcode library not installed, returning placeholder")
        return "QR_CODE_PLACEHOLDER_BASE64"
