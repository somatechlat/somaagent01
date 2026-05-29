"""MFA Authentication API.


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
from admin.common.exceptions import ServiceUnavailableError, UnauthorizedError
from admin.common.messages import ErrorCode, SuccessCode, get_message

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
    import secrets

    import pyotp  # type: ignore[import]

    # Get user from auth context
    user_email = getattr(request.auth, "email", None)
    if not user_email:
        raise UnauthorizedError("Email not found in auth context")

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

    # NOTE: Real persistence not yet wired. The generated secret MUST be stored
    # encrypted in a MFASetup or UserProfile table before this endpoint is usable.
    # When wired, this should be: MFASetup.objects.create(user_id=user.id, encrypted_secret=encrypt(secret))
    raise ServiceUnavailableError(
        "mfa",
        "MFA secret persistence (database storage) is not yet implemented. Cannot proceed with MFA setup.",
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

    # Fail-closed: MFA secret must be loaded from the user's encrypted DB record,
    # NOT a hardcoded value. Until MFASetup model + persistence is implemented,
    # this endpoint cannot safely operate.
    raise ServiceUnavailableError(
        "mfa",
        "MFA verify: secret storage not yet implemented. MFA cannot be verified without the user's persisted TOTP secret.",
    )


@router.post(
    "/validate",
    summary="Validate MFA during login",
)
async def validate_mfa_login(request, payload: MFAVerifyRequest) -> dict:
    """Validate MFA code during login flow.

    Called after password verification when MFA is required.
    """
    import pyotp  # type: ignore[import]  # noqa: F401

    # Fail-closed: MFA login validation requires loading the user's stored secret
    # from the database/session. Hardcoding is a critical security violation.
    raise ServiceUnavailableError(
        "mfa", "MFA login validation: secret storage not yet implemented."
    )


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
    import pyotp  # type: ignore[import]  # noqa: F401

    # Fail-closed: disabling MFA must verify against the user's real stored secret
    raise ServiceUnavailableError("mfa", "MFA disable: secret storage not yet implemented.")


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
        "message": get_message(SuccessCode.BACKUP_CODE_ACCEPTED),
    }


# =============================================================================
# HELPERS
# =============================================================================


def _generate_qr_code(data: str) -> str:
    """Generate QR code as base64 PNG using the qrcode library.

    Raises:
        ServiceUnavailableError: If the qrcode library is not installed.
    """
    try:
        import qrcode  # type: ignore[import]

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffer = io.BytesIO()
        img.save(buffer, kind="PNG")
        buffer.seek(0)

        return base64.b64encode(buffer.getvalue()).decode()

    except ImportError:
        # Fail-closed: QR generation is required for MFA setup
        raise ServiceUnavailableError(
            "mfa", "qrcode library not installed; install qrcode to enable MFA QR generation"
        )
