"""AAAS Django Admin - Main entry point.

Registers Django admin for this agent's own records: its agents, their
assigned users, and the audit trail.

No SaaS or billing is administered here. Subscription tiers, plan feature
gating and usage metering exist as data models only — this product is a
standalone agent and has no billing administration surface. See AGENT.md §1.1.
"""

try:

    # Import all admin classes to register with Django admin
    from admin.aaas.admin_agents import (
        AgentAdmin,
        AgentInline,
        AgentUserAdmin,
        AgentUserInline,
        AuditLogAdmin,
    )

    __all__ = [
        "AgentAdmin",
        "AgentUserAdmin",
        "AgentInline",
        "AgentUserInline",
        "AuditLogAdmin",
    ]
except Exception:
    pass
