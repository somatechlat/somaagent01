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
from services.common.authorization import authorize
from admin.common.exceptions import ServiceUnavailableError, UnauthorizedError

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
    # Self-service: acts on the caller's own principal. Identity, not elevated authority.
    await authorize(request, action="identity:self", resource="identity")

    if not getattr(request.auth, "email", None):
        raise UnauthorizedError("Email not found in auth context")

    # Persistence for MFA secrets is not wired (no MFASetup/UserProfile store).
    # Refuse BEFORE any TOTP secret, QR code, or backup-code material is
    # generated — computing secrets on a path that always fails is dead work
    # and hands callers nothing (SIMP-02 / R-1 no stubs).
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
    # Self-service: acts on the caller's own principal. Identity, not elevated authority.
    await authorize(request, action="identity:self", resource="identity")

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
    # Self-service: acts on the caller's own principal. Identity, not elevated authority.
    await authorize(request, action="identity:self", resource="identity")
    raise ServiceUnavailableError(
        "mfa",
         "MFA status is not implemented: user record store is not wired.")


@router.post(
    "/disable",
    summary="Disable MFA",
    auth=AuthBearer(),
)
async def disable_mfa(request, payload: MFAVerifyRequest) -> dict:
    """Disable MFA (requires current TOTP code)."""
    # Self-service: acts on the caller's own principal. Identity, not elevated authority.
    await authorize(request, action="identity:self", resource="identity")

    # Fail-closed: disabling MFA must verify against the user's real stored secret
    raise ServiceUnavailableError("mfa", "MFA disable: secret storage not yet implemented.")


@router.post(
    "/backup-code",
    summary="Use backup code",
)
async def use_backup_code(request, code: str) -> dict:
    """Use a backup code for recovery."""
    # FAIL-CLOSED: Backup code validation requires the MFASetup database
    # model to verify the code against stored (hashed) backup codes.
    # Until persistence is wired, backup codes cannot be validated.
    raise ServiceUnavailableError(
        "mfa",
        "Backup code validation: secret storage not yet implemented.",
    )


# =============================================================================
# HELPERS
# =============================================================================


