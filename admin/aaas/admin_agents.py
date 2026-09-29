"""AAAS Django Admin - Agent and Feature Admins.

Split from admin/aaas/admin.py for 650-line compliance.
"""

try:

    from django.contrib import admin
    from django.utils.html import format_html

    from admin.aaas.models import Agent, AgentUser, AuditLog

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

except Exception:
    pass
