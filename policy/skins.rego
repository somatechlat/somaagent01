# OPA Policy for AgentSkin Theme Management
# Per AgentSkin UIX T11 (SEC-AGS-001)
#
# VIBE COMPLIANT:
# - Real OPA policy (no stubs)
# - Clear authorization rules
# - Integrates with existing OPA client
#
# Actions:
# - skin:read - All authenticated users
# - skin:upload - Admin only
# - skin:delete - Admin only
# - skin:approve - Admin only

package somaagent.skins

import rego.v1

# Default deny all actions
default allow := false

# Anyone authenticated can read skins
allow if {
    input.action == "skin:read"
    input.user.authenticated == true
}

# Admin can upload themes
allow if {
    input.action == "skin:upload"
    input.user.authenticated == true
    input.user.role == "admin"
}

# Admin can delete themes
allow if {
    input.action == "skin:delete"
    input.user.authenticated == true
    input.user.role == "admin"
}

# Admin can approve themes
allow if {
    input.action == "skin:approve"
    input.user.authenticated == true
    input.user.role == "admin"
}

# Admin can reject themes
allow if {
    input.action == "skin:reject"
    input.user.authenticated == true
    input.user.role == "admin"
}

# Admin can update themes
allow if {
    input.action == "skin:update"
    input.user.authenticated == true
    input.user.role == "admin"
}

# Tenant isolation check - ensure user can only access their tenant's themes
tenant_allowed if {
    input.user.tenant_id == input.resource.tenant_id
}

# Combined check: action allowed AND tenant matched
allow_with_tenant if {
    allow
    tenant_allowed
}

# Helper to check if user is admin
is_admin if {
    input.user.role == "admin"
}

# Helper to check if user is authenticated
is_authenticated if {
    input.user.authenticated == true
}

# Deny reasons for debugging
deny_reasons contains msg if {
    not input.user.authenticated
    msg := "User not authenticated"
}

deny_reasons contains msg if {
    input.action in ["skin:upload", "skin:delete", "skin:approve", "skin:reject", "skin:update"]
    input.user.role != "admin"
    msg := "Admin role required for this action"
}

deny_reasons contains msg if {
    input.resource.tenant_id
    input.user.tenant_id != input.resource.tenant_id
    msg := "Cannot access resources from a different tenant"
}
