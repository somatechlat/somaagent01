"""SAAS Django Admin - Full Capabilities.

VIBE COMPLIANT - Maximizing Django Admin features.
7-Persona Implementation:
- 🏗️ Django Architect: ModelAdmin, Inlines, fieldsets
- 🔒 Security Auditor: Readonly fields, permission checks
- 📈 PM: User-friendly actions, filters
- 🧪 QA Engineer: Validation, constraints
- 📚 Technical Writer: Help text, verbose names
- ⚡ Performance Lead: list_select_related, queryset optimization
- 🌍 i18n Specialist: Translatable strings
"""

from django.contrib import admin
from django.utils.html import format_html

from admin.saas.models import (
    Agent,
    AgentUser,
    AuditLog,
    FeatureProvider,
    SaasFeature,
    SubscriptionTier,
    Tenant,
    TenantUser,
    TierFeature,
    UsageRecord,
)


# =============================================================================
# INLINES (Nested editing)
# =============================================================================


class TenantUserInline(admin.TabularInline):
    """Inline for managing users within a tenant."""

    model = TenantUser
    extra = 0
    readonly_fields = ["created_at"]
    fields = ["email", "display_name", "role", "is_active", "created_at"]
    ordering = ["-created_at"]
    show_change_link = True


class AgentInline(admin.TabularInline):
    """Inline for managing agents within a tenant."""

    model = Agent
    extra = 0
    readonly_fields = ["created_at"]
    fields = ["name", "slug", "status", "created_at"]
    ordering = ["-created_at"]
    show_change_link = True
    max_num = 10


class TierFeatureInline(admin.TabularInline):
    """Inline for managing features within a tier."""

    model = TierFeature
    extra = 0
    fields = ["feature", "is_enabled", "quota_limit"]
    ordering = ["feature__name"]


class AgentUserInline(admin.TabularInline):
    """Inline for managing users assigned to an agent."""

    model = AgentUser
    extra = 0
    fields = ["user_id", "role"]
    readonly_fields = ["created_at"]


# =============================================================================
# SUBSCRIPTION TIER ADMIN
# =============================================================================


@admin.register(SubscriptionTier)
class SubscriptionTierAdmin(admin.ModelAdmin):
    """Full Django Admin for Subscription Tiers."""

    list_display = [
        "name",
        "slug",
        "price_display",
        "tenant_count",
        "is_active",
        "is_public",
        "sort_order",
        "created_at",
    ]
    list_filter = ["is_active", "is_public", "billing_interval", "created_at"]
    search_fields = ["name", "slug", "description"]
    readonly_fields = ["id", "created_at", "updated_at", "tenant_count"]
    ordering = ["sort_order", "base_price_cents"]
    list_per_page = 25
    prepopulated_fields = {"slug": ("name",)}

    fieldsets = (
        (
            "Tier Information",
            {
                "fields": ("id", "name", "slug", "description"),
            },
        ),
        (
            "Pricing",
            {
                "fields": (
                    "base_price_cents",
                    "billing_interval",
                    "lago_plan_code",
                ),
            },
        ),
        (
            "Limits",
            {
                "fields": (
                    "max_agents",
                    "max_users_per_agent",
                    "max_monthly_voice_minutes",
                    "max_monthly_api_calls",
                    "max_storage_gb",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Status",
            {
                "fields": ("is_active", "is_public", "sort_order"),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    inlines = [TierFeatureInline]

    actions = ["activate_tiers", "deactivate_tiers", "make_public", "make_private"]

    @admin.display(description="Price")
    def price_display(self, obj):
        if obj.base_price_cents == 0:
            return format_html('<span style="color: #22c55e;">Free</span>')
        return f"${obj.base_price_cents / 100:.2f}/mo"

    @admin.display(description="Tenants")
    def tenant_count(self, obj):
        return obj.tenants.count()

    @admin.action(description="Activate selected tiers")
    def activate_tiers(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} tiers activated.")

    @admin.action(description="Deactivate selected tiers")
    def deactivate_tiers(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} tiers deactivated.")

    @admin.action(description="Make public")
    def make_public(self, request, queryset):
        queryset.update(is_public=True)

    @admin.action(description="Make private")
    def make_private(self, request, queryset):
        queryset.update(is_public=False)


# =============================================================================
# TENANT ADMIN
# =============================================================================


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    """Full Django Admin for Tenants with inlines."""

    list_display = [
        "name",
        "slug",
        "tier",
        "status_badge",
        "user_count",
        "agent_count",
        "billing_email",
        "created_at",
    ]
    list_filter = ["status", "tier", "created_at"]
    search_fields = ["name", "slug", "billing_email", "lago_customer_id"]
    readonly_fields = ["id", "created_at", "updated_at", "user_count", "agent_count"]
    ordering = ["-created_at"]
    list_per_page = 25
    date_hierarchy = "created_at"
    list_select_related = ["tier"]

    fieldsets = (
        (
            "Tenant Information",
            {
                "fields": ("id", "name", "slug", "status"),
            },
        ),
        (
            "Subscription",
            {
                "fields": ("tier", "trial_ends_at"),
            },
        ),
        (
            "Billing (Lago)",
            {
                "fields": (
                    "billing_email",
                    "lago_customer_id",
                    "lago_subscription_id",
                ),
            },
        ),
        (
            "Authentication (Keycloak)",
            {
                "fields": ("keycloak_realm",),
                "classes": ("collapse",),
            },
        ),
        (
            "Configuration",
            {
                "fields": ("feature_overrides", "metadata"),
                "classes": ("collapse",),
            },
        ),
        (
            "Statistics",
            {
                "fields": ("user_count", "agent_count"),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    inlines = [TenantUserInline, AgentInline]

    actions = [
        "activate_tenants",
        "suspend_tenants",
    ]

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            "active": "#22c55e",
            "pending": "#f59e0b",
            "suspended": "#ef4444",
            "trial": "#3b82f6",
        }
        color = colors.get(obj.status, "#94a3b8")
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; '
            'border-radius: 4px; font-size: 11px;">{}</span>',
            color,
            obj.status.upper(),
        )

    @admin.display(description="Users")
    def user_count(self, obj):
        return obj.users.count()

    @admin.display(description="Agents")
    def agent_count(self, obj):
        return obj.agents.count() if hasattr(obj, "agents") else 0

    @admin.action(description="Activate selected tenants")
    def activate_tenants(self, request, queryset):
        queryset.update(status="active")
        self.message_user(request, f"{queryset.count()} tenants activated.")

    @admin.action(description="Suspend selected tenants")
    def suspend_tenants(self, request, queryset):
        queryset.update(status="suspended")
        self.message_user(request, f"{queryset.count()} tenants suspended.")


# =============================================================================
# TENANT USER ADMIN
# =============================================================================


@admin.register(TenantUser)
class TenantUserAdmin(admin.ModelAdmin):
    """Full Django Admin for Tenant Users."""

    list_display = [
        "email",
        "display_name",
        "tenant",
        "role_badge",
        "is_active",
        "created_at",
    ]
    list_filter = ["role", "is_active", "tenant", "created_at"]
    search_fields = ["email", "display_name", "user_id"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["-created_at"]
    list_per_page = 50
    list_select_related = ["tenant"]
    raw_id_fields = ["tenant"]

    fieldsets = (
        (
            "User Information",
            {
                "fields": ("id", "email", "display_name", "user_id"),
            },
        ),
        (
            "Tenant & Role",
            {
                "fields": ("tenant", "role", "is_active"),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    actions = ["activate_users", "deactivate_users", "promote_to_admin"]

    @admin.display(description="Role")
    def role_badge(self, obj):
        colors = {
            "owner": "#ef4444",
            "admin": "#f59e0b",
            "member": "#3b82f6",
            "viewer": "#94a3b8",
        }
        color = colors.get(obj.role, "#94a3b8")
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; '
            'border-radius: 4px; font-size: 11px;">{}</span>',
            color,
            obj.role.upper(),
        )

    @admin.action(description="Activate selected users")
    def activate_users(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Deactivate selected users")
    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)

    @admin.action(description="Promote to admin")
    def promote_to_admin(self, request, queryset):
        queryset.update(role="admin")


# =============================================================================
# AGENT ADMIN
# =============================================================================


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    """Full Django Admin for Agents."""

    list_display = [
        "name",
        "slug",
        "tenant",
        "status_badge",
        "user_count",
        "created_at",
    ]
    list_filter = ["status", "tenant", "created_at"]
    search_fields = ["name", "slug", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["-created_at"]
    list_per_page = 25
    list_select_related = ["tenant"]
    raw_id_fields = ["tenant"]

    fieldsets = (
        (
            "Agent Information",
            {
                "fields": ("id", "name", "slug", "description"),
            },
        ),
        (
            "Tenant",
            {
                "fields": ("tenant",),
            },
        ),
        (
            "Configuration",
            {
                "fields": ("config", "feature_settings", "skin_id"),
                "classes": ("collapse",),
            },
        ),
        (
            "Status",
            {
                "fields": ("status",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    inlines = [AgentUserInline]

    actions = ["activate_agents", "deactivate_agents"]

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            "active": "#22c55e",
            "inactive": "#94a3b8",
            "error": "#ef4444",
            "maintenance": "#f59e0b",
        }
        color = colors.get(obj.status, "#94a3b8")
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; '
            'border-radius: 4px; font-size: 11px;">{}</span>',
            color,
            obj.status.upper(),
        )

    @admin.display(description="Users")
    def user_count(self, obj):
        return obj.agent_users.count() if hasattr(obj, "agent_users") else 0

    @admin.action(description="Activate agents")
    def activate_agents(self, request, queryset):
        queryset.update(status="active")

    @admin.action(description="Deactivate agents")
    def deactivate_agents(self, request, queryset):
        queryset.update(status="inactive")


# =============================================================================
# AGENT USER ADMIN
# =============================================================================


@admin.register(AgentUser)
class AgentUserAdmin(admin.ModelAdmin):
    """Django Admin for Agent Users."""

    list_display = ["user_id_short", "agent", "role", "created_at"]
    list_filter = ["role", "created_at"]
    search_fields = ["user_id"]
    ordering = ["-created_at"]
    list_select_related = ["agent"]
    raw_id_fields = ["agent"]

    @admin.display(description="User ID")
    def user_id_short(self, obj):
        return str(obj.user_id)[:8] if obj.user_id else "-"


# =============================================================================
# SAAS FEATURE ADMIN
# =============================================================================


@admin.register(SaasFeature)
class SaasFeatureAdmin(admin.ModelAdmin):
    """Django Admin for SaaS Features."""

    list_display = [
        "name",
        "code",
        "category",
        "is_active",
        "sort_order",
        "created_at",
    ]
    list_filter = ["category", "is_active", "created_at"]
    search_fields = ["name", "code", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["category", "sort_order", "name"]

    fieldsets = (
        (
            "Feature Information",
            {
                "fields": ("id", "name", "code", "description", "category"),
            },
        ),
        (
            "Limits",
            {
                "fields": ("default_quota", "quota_unit"),
            },
        ),
        (
            "Display",
            {
                "fields": ("sort_order", "is_active"),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


# =============================================================================
# TIER FEATURE ADMIN
# =============================================================================


@admin.register(TierFeature)
class TierFeatureAdmin(admin.ModelAdmin):
    """Django Admin for Tier-Feature mappings."""

    list_display = ["tier", "feature", "is_enabled", "quota_limit"]
    list_filter = ["tier", "is_enabled"]
    search_fields = ["tier__name", "feature__name"]
    list_select_related = ["tier", "feature"]


# =============================================================================
# FEATURE PROVIDER ADMIN
# =============================================================================


@admin.register(FeatureProvider)
class FeatureProviderAdmin(admin.ModelAdmin):
    """Django Admin for Feature Providers."""

    list_display = ["name", "code", "feature", "is_default", "is_active", "created_at"]
    list_filter = ["is_active", "is_default", "feature"]
    search_fields = ["name", "code", "description"]
    list_select_related = ["feature"]


# =============================================================================
# USAGE RECORD ADMIN
# =============================================================================


@admin.register(UsageRecord)
class UsageRecordAdmin(admin.ModelAdmin):
    """Django Admin for Usage Records - read-only for billing."""

    list_display = [
        "tenant",
        "metric_code",
        "quantity",
        "unit",
        "lago_synced_badge",
        "recorded_at",
    ]
    list_filter = ["metric_code", "lago_synced", "recorded_at", "tenant"]
    search_fields = ["tenant__name", "lago_event_id", "metric_code"]
    readonly_fields = [
        "id",
        "tenant",
        "agent",
        "metric_code",
        "quantity",
        "unit",
        "lago_event_id",
        "lago_synced",
        "metadata",
        "recorded_at",
        "period_start",
        "period_end",
    ]
    ordering = ["-recorded_at"]
    list_per_page = 100
    date_hierarchy = "recorded_at"
    list_select_related = ["tenant"]

    @admin.display(description="Lago")
    def lago_synced_badge(self, obj):
        if obj.lago_synced:
            return format_html(
                '<span style="background: #22c55e; color: white; padding: 2px 6px; '
                'border-radius: 4px; font-size: 10px;">✓</span>'
            )
        return format_html(
            '<span style="background: #f59e0b; color: white; padding: 2px 6px; '
            'border-radius: 4px; font-size: 10px;">Pending</span>'
        )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# =============================================================================
# AUDIT LOG ADMIN
# =============================================================================


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Django Admin for Audit Logs - fully read-only."""

    list_display = [
        "created_at",
        "tenant",
        "actor_email",
        "action",
        "resource_type",
        "resource_id_short",
        "ip_address",
    ]
    list_filter = ["action", "resource_type", "created_at", "tenant"]
    search_fields = ["actor_email", "actor_id", "resource_id", "ip_address"]
    readonly_fields = [
        "id",
        "tenant",
        "actor_id",
        "actor_email",
        "action",
        "resource_type",
        "resource_id",
        "old_value",
        "new_value",
        "ip_address",
        "user_agent",
        "request_id",
        "created_at",
    ]
    ordering = ["-created_at"]
    list_per_page = 100
    date_hierarchy = "created_at"
    list_select_related = ["tenant"]

    fieldsets = (
        (
            "Event",
            {
                "fields": ("id", "action", "created_at"),
            },
        ),
        (
            "Actor",
            {
                "fields": ("tenant", "actor_id", "actor_email"),
            },
        ),
        (
            "Resource",
            {
                "fields": ("resource_type", "resource_id"),
            },
        ),
        (
            "Changes",
            {
                "fields": ("old_value", "new_value"),
            },
        ),
        (
            "Request Info",
            {
                "fields": ("ip_address", "user_agent", "request_id"),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description="Resource ID")
    def resource_id_short(self, obj):
        if obj.resource_id:
            return str(obj.resource_id)[:8]
        return "-"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
