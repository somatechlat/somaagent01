"""AAAS Django Admin - Agent and Feature Admins.

Split from admin/aaas/admin.py for 650-line compliance.
"""

from django.contrib import admin
from django.utils.html import format_html

from admin.aaas.models import (
    Agent,
    AgentUser,
    AuditLog,
    FeatureProvider,
    AaasFeature,
    TierFeature,
    UsageRecord,
)


class AgentUserInline(admin.TabularInline):
    """Inline for managing users assigned to an agent."""

    model = AgentUser
    extra = 0
    fields = ["user_id", "role"]
    readonly_fields = ["created_at"]


class AgentInline(admin.TabularInline):
    """Inline for managing agents within a tenant."""

    model = Agent
    extra = 0
    readonly_fields = ["created_at"]
    fields = ["name", "slug", "status", "created_at"]
    ordering = ["-created_at"]
    show_change_link = True
    max_num = 10


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    """Full Django Admin for Agents."""

    list_display = ["name", "slug", "tenant", "status_badge", "user_count", "created_at"]
    list_filter = ["status", "tenant", "created_at"]
    search_fields = ["name", "slug", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["-created_at"]
    list_per_page = 25
    list_select_related = ["tenant"]
    raw_id_fields = ["tenant"]
    inlines = [AgentUserInline]
    actions = ["activate_agents", "deactivate_agents"]

    fieldsets = (
        ("Agent Information", {"fields": ("id", "name", "slug", "description")}),
        ("Tenant", {"fields": ("tenant",)}),
        (
            "Configuration",
            {"fields": ("config", "feature_settings", "skin_id"), "classes": ("collapse",)},
        ),
        ("Status", {"fields": ("status",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

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
            '<span style="background: {}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px;">{}</span>',
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


@admin.register(AaasFeature)
class AaasFeatureAdmin(admin.ModelAdmin):
    """Django Admin for AAAS Features."""

    list_display = ["name", "code", "category", "is_active", "sort_order", "created_at"]
    list_filter = ["category", "is_active", "created_at"]
    search_fields = ["name", "code", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["category", "sort_order", "name"]

    fieldsets = (
        ("Feature Information", {"fields": ("id", "name", "code", "description", "category")}),
        ("Limits", {"fields": ("default_quota", "quota_unit")}),
        ("Display", {"fields": ("sort_order", "is_active")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(TierFeature)
class TierFeatureAdmin(admin.ModelAdmin):
    """Django Admin for Tier-Feature mappings."""

    list_display = ["tier", "feature", "is_enabled", "quota_limit"]
    list_filter = ["tier", "is_enabled"]
    search_fields = ["tier__name", "feature__name"]
    list_select_related = ["tier", "feature"]


@admin.register(FeatureProvider)
class FeatureProviderAdmin(admin.ModelAdmin):
    """Django Admin for Feature Providers."""

    list_display = ["name", "code", "feature", "is_default", "is_active", "created_at"]
    list_filter = ["is_active", "is_default", "feature"]
    search_fields = ["name", "code", "description"]
    list_select_related = ["feature"]


@admin.register(UsageRecord)
class UsageRecordAdmin(admin.ModelAdmin):
    """Django Admin for Usage Records - read-only for billing."""

    list_display = ["tenant", "metric_code", "quantity", "unit", "lago_synced_badge", "recorded_at"]
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
                '<span style="background: #22c55e; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px;">✓</span>'
            )
        return format_html(
            '<span style="background: #f59e0b; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px;">Pending</span>'
        )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


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

    @admin.display(description="Resource")
    def resource_id_short(self, obj):
        return str(obj.resource_id)[:8] if obj.resource_id else "-"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
