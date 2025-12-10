# Tool Policy for SomaAgent01
# Validates: Requirements 33.1-33.5
#
# This policy controls tool access based on:
# 1. Tool catalog enabled status
# 2. Tenant-specific tool flags
# 3. Deny list for dangerous tools

package soma.policy

import future.keywords.if
import future.keywords.in

# Default deny - fail-closed security model
default allow = false

# Allow tool request if all conditions are met
allow if {
    input.action == "tool.request"
    tool_enabled_for_tenant
    not tool_in_deny_list
}

# Allow if tool is explicitly enabled for tenant
tool_enabled_for_tenant if {
    tenant_flag := data.tenant_tool_flags[input.tenant][input.resource]
    tenant_flag.enabled == true
}

# Fallback: Allow if no tenant-specific flag and tool is globally enabled
tool_enabled_for_tenant if {
    not data.tenant_tool_flags[input.tenant][input.resource]
    catalog_entry := data.tool_catalog[input.resource]
    catalog_entry.enabled == true
}

# Fallback: Allow if tool not in catalog (dynamic/MCP tools)
tool_enabled_for_tenant if {
    not data.tenant_tool_flags[input.tenant][input.resource]
    not data.tool_catalog[input.resource]
}

# Check if tool is in the deny list
tool_in_deny_list if {
    input.resource in data.deny_list
}

# Task execution policy
allow if {
    input.action == "task.run"
    task_allowed_for_tenant
}

task_allowed_for_tenant if {
    task_entry := data.task_registry[input.resource]
    task_entry.enabled == true
}

# Delegation policy - allow delegate to subagent
allow if {
    input.action == "delegate"
    delegation_allowed
}

delegation_allowed if {
    # Check if subagent URL is in allowed list
    input.subagent_url in data.allowed_subagents
}

delegation_allowed if {
    # Allow all delegations if no restrictions configured
    not data.allowed_subagents
}

# Admin actions require admin role
allow if {
    input.action in ["task.register", "task.reload", "tool.register"]
    "admin" in input.roles
}

# View actions are generally allowed
allow if {
    input.action in ["task.view", "tool.view"]
}
