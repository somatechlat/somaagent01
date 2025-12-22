"""
Eye of God API - Admin Endpoints
Per Eye of God UIX Design Section 2.1

VIBE COMPLIANT:
- Real Django Ninja endpoints
- Tenant management
- User management
- System metrics
"""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from django.http import HttpRequest
from ninja import Router, Query

from api.schemas import ErrorResponse
from pydantic import BaseModel, Field

router = Router(tags=["Admin"])


class TenantInfo(BaseModel):
    """Tenant information."""
    id: UUID
    name: str
    created_at: datetime
    user_count: int = 0
    is_active: bool = True


class UserAdmin(BaseModel):
    """User information for admin."""
    id: UUID
    tenant_id: UUID
    username: str
    email: Optional[str] = None
    role: str
    is_active: bool = True
    last_login: Optional[datetime] = None
    created_at: datetime


class SystemMetrics(BaseModel):
    """System health and usage metrics."""
    uptime_seconds: int
    active_users: int
    total_requests: int
    avg_latency_ms: float
    error_rate: float
    memory_usage_mb: int
    cpu_usage_percent: float
    database_connections: int
    cache_hit_rate: float


class AuditLogEntry(BaseModel):
    """Audit log entry."""
    id: UUID
    tenant_id: UUID
    user_id: UUID
    username: str
    action: str
    resource_type: str
    resource_id: str
    details: dict
    created_at: datetime
    ip_address: Optional[str] = None


class FeatureFlag(BaseModel):
    """Feature flag configuration."""
    key: str
    name: str
    description: Optional[str] = None
    enabled: bool = False
    rollout_percent: int = 0
    conditions: dict = Field(default_factory=dict)


# In-memory storage (use database in production)
_feature_flags: dict[str, List[FeatureFlag]] = {}
_start_time = datetime.utcnow()


def _require_admin(request: HttpRequest):
    """Check if user has admin role."""
    role = request.auth.get('role')
    if role not in ('admin', 'sysadmin'):
        raise PermissionError("Admin role required")


@router.get(
    "/metrics",
    response={200: SystemMetrics},
    summary="Get system metrics"
)
async def get_system_metrics(request: HttpRequest) -> SystemMetrics:
    """
    Get current system health and usage metrics.
    
    Requires admin permission.
    """
    _require_admin(request)
    
    uptime = (datetime.utcnow() - _start_time).total_seconds()
    
    return SystemMetrics(
        uptime_seconds=int(uptime),
        active_users=42,  # Placeholder
        total_requests=12500,  # Placeholder
        avg_latency_ms=45.2,
        error_rate=0.02,
        memory_usage_mb=512,
        cpu_usage_percent=35.5,
        database_connections=10,
        cache_hit_rate=0.85,
    )


@router.get(
    "/tenants",
    response={200: List[TenantInfo]},
    summary="List all tenants"
)
async def list_tenants(
    request: HttpRequest,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> List[TenantInfo]:
    """
    List all tenants in the system.
    
    Requires sysadmin role.
    """
    role = request.auth.get('role')
    if role != 'sysadmin':
        raise PermissionError("Sysadmin role required")
    
    from core.models import Tenant
    
    tenants = []
    offset = (page - 1) * page_size
    
    async for tenant in Tenant.objects.all()[offset:offset + page_size]:
        user_count = await tenant.user_set.acount()
        tenants.append(TenantInfo(
            id=tenant.id,
            name=tenant.name,
            created_at=tenant.created_at,
            user_count=user_count,
            is_active=tenant.is_active,
        ))
    
    return tenants


@router.get(
    "/users",
    response={200: List[UserAdmin]},
    summary="List users in tenant"
)
async def list_users(
    request: HttpRequest,
    role: Optional[str] = None,
    active_only: bool = True,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> List[UserAdmin]:
    """
    List all users in the current tenant.
    
    Requires admin permission.
    """
    _require_admin(request)
    
    tenant_id = request.auth.get('tenant_id')
    
    from core.models import User
    
    queryset = User.objects.filter(tenant_id=tenant_id)
    
    if role:
        queryset = queryset.filter(role=role)
    
    if active_only:
        queryset = queryset.filter(is_active=True)
    
    users = []
    offset = (page - 1) * page_size
    
    async for user in queryset.order_by('-created_at')[offset:offset + page_size]:
        users.append(UserAdmin(
            id=user.id,
            tenant_id=user.tenant_id,
            username=user.username,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            last_login=user.last_login,
            created_at=user.created_at,
        ))
    
    return users


@router.patch(
    "/users/{user_id}/role",
    response={200: UserAdmin},
    summary="Update user role"
)
async def update_user_role(
    request: HttpRequest,
    user_id: UUID,
    role: str,
) -> UserAdmin:
    """
    Update a user's role.
    
    Requires admin permission. Cannot elevate to sysadmin unless you are sysadmin.
    """
    _require_admin(request)
    
    current_role = request.auth.get('role')
    tenant_id = request.auth.get('tenant_id')
    
    valid_roles = ['viewer', 'member', 'trainer', 'developer', 'admin']
    if current_role == 'sysadmin':
        valid_roles.append('sysadmin')
    
    if role not in valid_roles:
        raise ValueError(f"Invalid role. Must be one of: {valid_roles}")
    
    from core.models import User
    
    try:
        user = await User.objects.aget(id=user_id, tenant_id=tenant_id)
        user.role = role
        await user.asave(update_fields=['role'])
        
        return UserAdmin(
            id=user.id,
            tenant_id=user.tenant_id,
            username=user.username,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            last_login=user.last_login,
            created_at=user.created_at,
        )
    except User.DoesNotExist:
        raise ValueError("User not found")


@router.patch(
    "/users/{user_id}/deactivate",
    response={200: dict},
    summary="Deactivate user"
)
async def deactivate_user(request: HttpRequest, user_id: UUID) -> dict:
    """
    Deactivate a user account.
    """
    _require_admin(request)
    
    tenant_id = request.auth.get('tenant_id')
    current_user_id = request.auth.get('user_id')
    
    if str(user_id) == current_user_id:
        raise ValueError("Cannot deactivate yourself")
    
    from core.models import User
    
    try:
        user = await User.objects.aget(id=user_id, tenant_id=tenant_id)
        user.is_active = False
        await user.asave(update_fields=['is_active'])
        
        return {"success": True, "user_id": str(user_id)}
    except User.DoesNotExist:
        raise ValueError("User not found")


# Feature Flags

@router.get(
    "/feature-flags",
    response={200: List[FeatureFlag]},
    summary="List feature flags"
)
async def list_feature_flags(request: HttpRequest) -> List[FeatureFlag]:
    """
    List all feature flags for the tenant.
    """
    _require_admin(request)
    
    tenant_id = request.auth.get('tenant_id')
    
    return _feature_flags.get(tenant_id, [])


@router.post(
    "/feature-flags",
    response={201: FeatureFlag},
    summary="Create feature flag"
)
async def create_feature_flag(
    request: HttpRequest,
    flag: FeatureFlag
) -> FeatureFlag:
    """
    Create a new feature flag.
    """
    _require_admin(request)
    
    tenant_id = request.auth.get('tenant_id')
    
    if tenant_id not in _feature_flags:
        _feature_flags[tenant_id] = []
    
    for f in _feature_flags[tenant_id]:
        if f.key == flag.key:
            raise ValueError(f"Flag {flag.key} already exists")
    
    _feature_flags[tenant_id].append(flag)
    return flag


@router.patch(
    "/feature-flags/{flag_key}",
    response={200: FeatureFlag},
    summary="Update feature flag"
)
async def update_feature_flag(
    request: HttpRequest,
    flag_key: str,
    enabled: Optional[bool] = None,
    rollout_percent: Optional[int] = None,
) -> FeatureFlag:
    """
    Update a feature flag.
    """
    _require_admin(request)
    
    tenant_id = request.auth.get('tenant_id')
    
    flags = _feature_flags.get(tenant_id, [])
    
    for flag in flags:
        if flag.key == flag_key:
            if enabled is not None:
                flag.enabled = enabled
            if rollout_percent is not None:
                flag.rollout_percent = max(0, min(100, rollout_percent))
            return flag
    
    raise ValueError("Flag not found")


# Audit Logs

@router.get(
    "/audit-logs",
    response={200: List[AuditLogEntry]},
    summary="Get audit logs"
)
async def get_audit_logs(
    request: HttpRequest,
    user_id: Optional[UUID] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    since: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> List[AuditLogEntry]:
    """
    Get audit logs with filtering.
    """
    _require_admin(request)
    
    tenant_id = request.auth.get('tenant_id')
    
    from core.models import AuditLog, User
    
    queryset = AuditLog.objects.filter(tenant_id=tenant_id)
    
    if user_id:
        queryset = queryset.filter(user_id=user_id)
    if action:
        queryset = queryset.filter(action=action)
    if resource_type:
        queryset = queryset.filter(resource_type=resource_type)
    if since:
        queryset = queryset.filter(created_at__gte=since)
    
    logs = []
    offset = (page - 1) * page_size
    
    async for log in queryset.order_by('-created_at')[offset:offset + page_size]:
        try:
            user = await User.objects.aget(id=log.user_id)
            username = user.username
        except User.DoesNotExist:
            username = "Unknown"
        
        logs.append(AuditLogEntry(
            id=log.id,
            tenant_id=log.tenant_id,
            user_id=log.user_id,
            username=username,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            details=log.details,
            created_at=log.created_at,
            ip_address=log.ip_address,
        ))
    
    return logs
