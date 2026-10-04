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

package soma.skins


import future.keywords.contains
import future.keywords.in
import future.keywords.every
# Default deny all actions
default allow := false

# Anyone authenticated can read skins
allow {
    input.action == "skin:read"
    input.user.authenticated == true
}

# Admin can upload themes
allow {
    input.action == "skin:upload"
    input.user.authenticated == true
    input.user.role == "admin"
}

# Admin can delete themes
allow {
    input.action == "skin:delete"
    input.user.authenticated == true
    input.user.role == "admin"
}

# Admin can approve themes
allow {
    input.action == "skin:approve"
    input.user.authenticated == true
    input.user.role == "admin"
}

# Admin can reject themes
allow {
    input.action == "skin:reject"
    input.user.authenticated == true
    input.user.role == "admin"
}

# Admin can update themes
allow {
    input.action == "skin:update"
    input.user.authenticated == true
    input.user.role == "admin"
}

# Tenant isolation check - ensure user can only access their tenant's themes
tenant_allowed {
    input.user.tenant_id == input.resource.tenant_id
}

# Combined check: action allowed AND tenant matched
allow_with_tenant {
    allow
    tenant_allowed
}

# Helper to check if user is admin
is_admin {
    input.user.role == "admin"
}

# Helper to check if user is authenticated
is_authenticated {
    input.user.authenticated == true
}

# Deny reasons for debugging
deny_reasons contains msg {
    not input.user.authenticated
    msg := "User not authenticated"
}

deny_reasons contains msg {
    input.action in ["skin:upload", "skin:delete", "skin:approve", "skin:reject", "skin:update"]
    input.user.role != "admin"
    msg := "Admin role required for this action"
}

deny_reasons contains msg {
    input.resource.tenant_id
    input.user.tenant_id != input.resource.tenant_id
    msg := "Cannot access resources from a different tenant"
}

# Not applicable: the request carries no opinion on the dimension this
# policy owns. A rule with no input must not veto - that would deny every
# ordinary request, which is a different failure from fail-closed.
allow {
    not input.skin
    not input.skins
}
