"""SAAS Admin Model Choices (Enums)."""

from django.db import models


class TenantStatus(models.TextChoices):
    """Tenant lifecycle status."""

    ACTIVE = "active", "Active"
    SUSPENDED = "suspended", "Suspended"
    PENDING = "pending", "Pending Activation"
    CHURNED = "churned", "Churned"


class AgentStatus(models.TextChoices):
    """Agent instance status."""

    ACTIVE = "active", "Active"
    PAUSED = "paused", "Paused"
    ARCHIVED = "archived", "Archived"


class TenantRole(models.TextChoices):
    """Roles within a tenant organization."""

    OWNER = "owner", "Owner"
    ADMIN = "admin", "Admin"
    MEMBER = "member", "Member"
    VIEWER = "viewer", "Viewer"


class AgentRole(models.TextChoices):
    """User roles for agent access."""

    MANAGER = "manager", "Manager"
    OPERATOR = "operator", "Operator"
    VIEWER = "viewer", "Viewer"


class BillingInterval(models.TextChoices):
    """Billing cycle intervals."""

    MONTHLY = "monthly", "Monthly"
    YEARLY = "yearly", "Yearly"
    WEEKLY = "weekly", "Weekly"


class QuotaEnforcementPolicy(models.TextChoices):
    """How quota limits are enforced."""

    HARD = "hard", "Hard Block"
    SOFT = "soft", "Soft Warn"
    NONE = "none", "Unlimited"


class FeatureCategory(models.TextChoices):
    """Capability categories for features."""

    VOICE = "voice", "Voice & Speech"
    MEMORY = "memory", "Memory & Context"
    MCP = "mcp", "MCP Servers"
    VISION = "vision", "Vision & Image"
    MODELS = "models", "AI Models"
    BROWSER = "browser", "Browser Automation"
    CODE_EXEC = "code_exec", "Code Execution"
    TOOLS = "tools", "Tool Access"
    DELEGATION = "delegation", "Agent Delegation"
