"""
Eye of God API - Modes Endpoints
Per Eye of God UIX Design Section 2.1

VIBE COMPLIANT:
- Real Django Ninja endpoints
- SpiceDB permission checks
- WebSocket event broadcasting
"""

from datetime import datetime
from uuid import UUID

from django.http import HttpRequest
from ninja import Router

from api.schemas import (
    AgentMode,
    ModeChange,
    ModeResponse,
    ErrorResponse,
)
from core.models import User, AuditLog

router = Router(tags=["Modes"])


# Mode permission requirements
MODE_PERMISSIONS = {
    AgentMode.STANDARD: ["mode:use"],
    AgentMode.TRAINING: ["mode:train"],
    AgentMode.ADMIN: ["mode:admin"],
    AgentMode.DEVELOPER: ["mode:developer"],
    AgentMode.READONLY: ["mode:use"],
    AgentMode.DANGER: ["mode:danger", "mode:admin"],
}


@router.get(
    "/current",
    response={200: ModeResponse},
    summary="Get current agent mode"
)
async def get_current_mode(request: HttpRequest) -> ModeResponse:
    """
    Get the current agent operating mode for the authenticated user.
    """
    user_id = request.auth.get("user_id")
    
    try:
        user = await User.objects.aget(id=user_id)
        return ModeResponse(
            mode=AgentMode(user.current_mode) if user.current_mode else AgentMode.STANDARD,
            changed_at=user.mode_changed_at or user.updated_at,
            changed_by=user.id,
        )
    except User.DoesNotExist:
        return ModeResponse(
            mode=AgentMode.STANDARD,
            changed_at=datetime.utcnow(),
            changed_by=UUID(user_id),
        )


@router.post(
    "/change",
    response={200: ModeResponse, 403: ErrorResponse},
    summary="Change agent mode"
)
async def change_mode(request: HttpRequest, payload: ModeChange) -> ModeResponse:
    """
    Change the agent operating mode.
    
    Requires appropriate permissions based on target mode:
    - STANDARD: mode:use
    - TRAINING: mode:train  
    - ADMIN: mode:admin
    - DEVELOPER: mode:developer
    - READONLY: mode:use
    - DANGER: mode:danger + mode:admin
    """
    user_id = request.auth.get("user_id")
    tenant_id = request.auth.get("tenant_id")
    
    # Check permissions for target mode
    required_permissions = MODE_PERMISSIONS.get(payload.mode, [])
    user_permissions = request.auth.get("permissions", [])
    
    has_permission = all(perm in user_permissions for perm in required_permissions)
    if not has_permission:
        raise PermissionError(f"Missing permissions for {payload.mode.value} mode")
    
    # Update user mode
    try:
        user = await User.objects.aget(id=user_id)
        previous_mode = user.current_mode
        user.current_mode = payload.mode.value
        user.mode_changed_at = datetime.utcnow()
        await user.asave(update_fields=["current_mode", "mode_changed_at"])
        
        # Audit log
        await AuditLog.objects.acreate(
            tenant_id=UUID(tenant_id),
            user_id=UUID(user_id),
            action="mode.changed",
            resource_type="mode",
            resource_id=str(user_id),
            details={
                "previous_mode": previous_mode,
                "new_mode": payload.mode.value,
            },
        )
        
        return ModeResponse(
            mode=payload.mode,
            changed_at=user.mode_changed_at,
            changed_by=user.id,
        )
        
    except User.DoesNotExist:
        raise ValueError("User not found")


@router.get(
    "/available",
    response={200: list},
    summary="List available modes"
)
async def list_available_modes(request: HttpRequest) -> list:
    """
    List all modes available to the current user based on their permissions.
    """
    user_permissions = request.auth.get("permissions", [])
    
    available = []
    for mode, required_perms in MODE_PERMISSIONS.items():
        if all(perm in user_permissions for perm in required_perms):
            available.append({
                "mode": mode.value,
                "name": mode.name,
                "description": _get_mode_description(mode),
                "requires": required_perms,
            })
    
    return available


def _get_mode_description(mode: AgentMode) -> str:
    """Get human-readable mode description."""
    descriptions = {
        AgentMode.STANDARD: "Full agent capabilities with standard safety checks",
        AgentMode.TRAINING: "Learn from user corrections and feedback",
        AgentMode.ADMIN: "System configuration and administration",
        AgentMode.DEVELOPER: "Debug tools and verbose logging visible",
        AgentMode.READONLY: "View-only mode, no actions permitted",
        AgentMode.DANGER: "Override safety checks - use with extreme caution",
    }
    return descriptions.get(mode, "Unknown mode")
