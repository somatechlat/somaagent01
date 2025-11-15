# Role-Based Access Control (RBAC) Matrix

## Overview
This document defines the RBAC matrix for SomaAgent01, specifying permissions for different roles.

## Roles

### User Roles
| Role | Description | Typical Users |
|------|-------------|---------------|
| **Guest** | Unauthenticated access | Public visitors |
| **User** | Standard authenticated user | End users |
| **Power User** | Advanced features access | Developers, analysts |
| **Admin** | Full system administration | System administrators |
| **Operator** | Operations and monitoring | DevOps, SRE |

## Permission Matrix

### API Endpoints

| Endpoint | Guest | User | Power User | Admin | Operator |
|----------|-------|------|------------|-------|----------|
| `GET /v1/health` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `GET /v1/healthz` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `POST /v1/session/message` | ❌ | ✅ | ✅ | ✅ | ❌ |
| `GET /v1/sessions/{id}/events` | ❌ | ✅ | ✅ | ✅ | ❌ |
| `GET /v1/sessions/{id}/history` | ❌ | ✅ | ✅ | ✅ | ❌ |
| `DELETE /v1/sessions/{id}` | ❌ | ✅ | ✅ | ✅ | ❌ |
| `POST /v1/uploads` | ❌ | ✅ | ✅ | ✅ | ❌ |
| `GET /v1/attachments/{id}` | ❌ | ✅ | ✅ | ✅ | ❌ |
| `GET /v1/tools` | ❌ | ✅ | ✅ | ✅ | ✅ |
| `POST /v1/tool/request` | ❌ | ❌ | ✅ | ✅ | ❌ |
| `GET /v1/memories` | ❌ | ✅ | ✅ | ✅ | ❌ |
| `DELETE /v1/memories/{id}` | ❌ | ✅ | ✅ | ✅ | ❌ |
| `GET /v1/ui/settings/sections` | ❌ | ✅ | ✅ | ✅ | ✅ |
| `POST /v1/ui/settings/sections` | ❌ | ❌ | ❌ | ✅ | ❌ |
| `GET /v1/model-profiles` | ❌ | ✅ | ✅ | ✅ | ✅ |
| `POST /v1/model-profiles` | ❌ | ❌ | ❌ | ✅ | ❌ |
| `GET /v1/runtime-config` | ❌ | ❌ | ✅ | ✅ | ✅ |
| `POST /v1/runtime-config/apply` | ❌ | ❌ | ❌ | ✅ | ❌ |
| `GET /metrics` | ❌ | ❌ | ❌ | ✅ | ✅ |

### Operations

| Operation | Guest | User | Power User | Admin | Operator |
|-----------|-------|------|------------|-------|----------|
| **Chat** | | | | | |
| Send message | ❌ | ✅ | ✅ | ✅ | ❌ |
| View history | ❌ | ✅ | ✅ | ✅ | ❌ |
| Delete session | ❌ | ✅ | ✅ | ✅ | ❌ |
| **Files** | | | | | |
| Upload files | ❌ | ✅ | ✅ | ✅ | ❌ |
| Download files | ❌ | ✅ | ✅ | ✅ | ❌ |
| **Tools** | | | | | |
| View tools | ❌ | ✅ | ✅ | ✅ | ✅ |
| Execute tools | ❌ | ❌ | ✅ | ✅ | ❌ |
| Manage tools | ❌ | ❌ | ❌ | ✅ | ❌ |
| **Memory** | | | | | |
| View memories | ❌ | ✅ | ✅ | ✅ | ❌ |
| Delete memories | ❌ | ✅ | ✅ | ✅ | ❌ |
| Export memories | ❌ | ❌ | ✅ | ✅ | ❌ |
| **Configuration** | | | | | |
| View settings | ❌ | ✅ | ✅ | ✅ | ✅ |
| Modify settings | ❌ | ❌ | ❌ | ✅ | ❌ |
| View runtime config | ❌ | ❌ | ✅ | ✅ | ✅ |
| Apply config updates | ❌ | ❌ | ❌ | ✅ | ❌ |
| **Monitoring** | | | | | |
| View metrics | ❌ | ❌ | ❌ | ✅ | ✅ |
| View logs | ❌ | ❌ | ❌ | ✅ | ✅ |
| View traces | ❌ | ❌ | ❌ | ✅ | ✅ |

## Scope Definitions

### JWT Scopes
```json
{
  "user": ["chat:read", "chat:write", "files:read", "files:write", "memory:read"],
  "power_user": ["chat:*", "files:*", "memory:*", "tools:execute", "config:read"],
  "admin": ["*"],
  "operator": ["health:read", "metrics:read", "logs:read", "config:read"]
}
```

### OPA Policy Example
```rego
package somaagent.authz

default allow = false

# Allow health checks for everyone
allow {
    input.path == "/v1/health"
}

# Allow authenticated users to send messages
allow {
    input.path == "/v1/session/message"
    input.method == "POST"
    input.user.role in ["user", "power_user", "admin"]
}

# Allow only admins to modify settings
allow {
    startswith(input.path, "/v1/ui/settings/sections")
    input.method == "POST"
    input.user.role == "admin"
}

# Allow operators and admins to view metrics
allow {
    input.path == "/metrics"
    input.user.role in ["operator", "admin"]
}
```

## Implementation

### FastAPI Dependency
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def require_role(required_role: str):
    async def check_role(token: str = Depends(security)):
        user = decode_token(token)
        if user.role not in get_allowed_roles(required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return user
    return check_role

# Usage
@app.post("/v1/ui/settings/sections")
async def update_settings(
    user: User = Depends(require_role("admin"))
):
    # Only admins can access this endpoint
    pass
```

## Audit Logging

All access attempts MUST be logged with:
- Timestamp
- User ID and role
- Requested resource
- Action (read/write/delete)
- Result (allowed/denied)
- IP address

Example log entry:
```json
{
  "timestamp": "2025-01-14T12:00:00Z",
  "user_id": "user123",
  "role": "user",
  "resource": "/v1/ui/settings/sections",
  "action": "POST",
  "result": "denied",
  "reason": "insufficient_permissions",
  "ip": "192.168.1.100"
}
```

## References
- [OpenFGA Documentation](https://openfga.dev/)
- [OPA Policy Language](https://www.openpolicyagent.org/docs/latest/policy-language/)
- [NIST RBAC Model](https://csrc.nist.gov/projects/role-based-access-control)
