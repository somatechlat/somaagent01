from typing import List, Optional
from ninja import Router, Schema
from datetime import datetime, timedelta

# --- Schemas ---

class TenantMetric(Schema):
    total_tenants: int
    active_tenants: int
    total_agents: int
    total_mrr: float
    growth_rate: float

class Tenant(Schema):
    id: str
    name: str
    status: str
    plan: str
    created_at: datetime
    agent_count: int
    last_active: Optional[datetime]
    email: str

class TenantCreate(Schema):
    name: str
    email: str
    plan: str = "pro"

class ActivityLog(Schema):
    id: str
    tenant_id: str
    action: str
    resource: str
    timestamp: datetime
    status: str
    details: Optional[str]

class EnterpriseSettings(Schema):
    sso_enabled: bool = False
    sso_provider: Optional[str] = None
    sso_client_id: Optional[str] = None
    sso_authority: Optional[str] = None
    mfa_enforced: bool = False
    session_timeout_minutes: int = 60
    ip_allowlist: List[str] = []
    enterprise_mode_enabled: bool = False
    custom_domain: Optional[str] = None

# --- Router ---

router = Router(tags=["SaaS Platform"])

# --- Endpoints ---

@router.get("/metrics", response=TenantMetric)
def get_platform_metrics(request):
    """
    Get high-level platform metrics for the God Mode dashboard.
    """
    return {
        "total_tenants": 124,
        "active_tenants": 118,
        "total_agents": 4502,
        "total_mrr": 24500.00,
        "growth_rate": 12.5
    }

@router.get("/tenants", response=List[Tenant])
def list_tenants(request, status: Optional[str] = None):
    """
    List all tenants with support for status filtering.
    """
    tenants = [
        {
            "id": "t-alpha",
            "name": "Alpha Corp",
            "status": "active",
            "plan": "enterprise",
            "created_at": datetime.now() - timedelta(days=90),
            "agent_count": 50,
            "last_active": datetime.now(),
            "email": "admin@alpha.com"
        },
        {
            "id": "t-beta",
            "name": "Beta Inc",
            "status": "active",
            "plan": "pro",
            "created_at": datetime.now() - timedelta(days=45),
            "agent_count": 12,
            "last_active": datetime.now() - timedelta(hours=2),
            "email": "ops@beta.com"
        },
        {
            "id": "t-gamma",
            "name": "Gamma LLC",
            "status": "suspended",
            "plan": "basic",
            "created_at": datetime.now() - timedelta(days=120),
            "agent_count": 2,
            "last_active": datetime.now() - timedelta(days=5),
            "email": "billing@gamma.com"
        }
    ]
    if status:
        return [t for t in tenants if t["status"] == status]
    return tenants

@router.post("/tenants", response=Tenant)
def create_tenant(request, payload: TenantCreate):
    """
    Provision a new tenant.
    """
    new_tenant = {
        "id": f"t-{payload.name.lower().replace(' ', '-')}",
        "name": payload.name,
        "status": "active",
        "plan": payload.plan,
        "created_at": datetime.now(),
        "agent_count": 0,
        "last_active": None,
        "email": payload.email
    }
    return new_tenant

@router.post("/tenants/{tenant_id}/{action}")
def manage_tenant(request, tenant_id: str, action: str):
    """
    Perform administrative actions on a tenant.
    """
    return {"success": True, "tenant_id": tenant_id, "new_status": "suspended" if action == "suspend" else "active"}

@router.get("/activity", response=List[ActivityLog])
def get_platform_activity(request):
    """
    Get recent global activity logs.
    """
    return [
        {
            "id": "audit-101",
            "tenant_id": "t-alpha",
            "action": "agent.provision",
            "resource": "agent-007",
            "timestamp": datetime.now() - timedelta(minutes=5),
            "status": "success",
            "details": "Provisioned new Sales Agent"
        },
        {
            "id": "audit-102",
            "tenant_id": "t-beta",
            "action": "billing.invoice.paid",
            "resource": "inv-2024-12",
            "timestamp": datetime.now() - timedelta(hours=1),
            "status": "success",
            "details": "$499.00 paid"
        }
    ]

# --- Enterprise Settings ---

@router.get("/settings", response=EnterpriseSettings)
def get_enterprise_settings(request):
    """
    Retrieve global Enterprise configuration.
    """
    return {
        "sso_enabled": True,
        "sso_provider": "keycloak",
        "mfa_enforced": True,
        "enterprise_mode_enabled": True,
        "session_timeout_minutes": 30
    }

@router.post("/settings", response=EnterpriseSettings)
def update_enterprise_settings(request, payload: EnterpriseSettings):
    """
    Update global Enterprise configuration.
    """
    return payload
