"""Permissions Django Admin.


7-Persona Implementation for Granular Permissions System.
"""

from django.contrib import admin
from django.utils.html import format_html

from admin.permissions.models import (
    GranularPermission,
    PermissionAction,
    PermissionCheckLog,
    PermissionGrant,
    PermissionResource,
    Role,
    UserRoleAssignment,
)


# =============================================================================
# INLINES
# =============================================================================


class GranularPermissionInline(admin.TabularInline):
    """Inline for viewing permissions in a resource."""

    model = GranularPermission
    extra = 0
    fields = ["action", "codename", "description"]
    readonly_fields = ["codename"]
    ordering = ["action__name"]


class UserRoleAssignmentInline(admin.TabularInline):
    """Inline for viewing role assignments."""

    model = UserRoleAssignment
    extra = 0
    fields = ["user_id", "scope_type", "scope_id", "granted_by", "created_at"]
    readonly_fields = ["created_at"]


# =============================================================================
# PERMISSION RESOURCE ADMIN
# =============================================================================


@admin.register(PermissionResource)
class PermissionResourceAdmin(admin.ModelAdmin):
    """Django Admin for Permission Resources."""

    list_display = ["name", "display_name", "category", "permission_count", "content_type"]
    list_filter = ["category"]
    search_fields = ["name", "display_name", "description"]
    ordering = ["category", "name"]

    inlines = [GranularPermissionInline]

    @admin.display(description="Permissions")
    def permission_count(self, obj):
        """Execute permission count.

            Args:
                obj: The obj.
            """

        return obj.permissions.count() if hasattr(obj, "permissions") else 0


# =============================================================================
# PERMISSION ACTION ADMIN
# =============================================================================


@admin.register(PermissionAction)
class PermissionActionAdmin(admin.ModelAdmin):
    """Django Admin for Permission Actions."""

    list_display = ["name", "display_name", "is_destructive_badge"]
    list_filter = ["is_destructive"]
    search_fields = ["name", "display_name"]
    ordering = ["name"]

    @admin.display(description="Destructive")
    def is_destructive_badge(self, obj):
        """Check if destructive badge.

            Args:
                obj: The obj.
            """

        if obj.is_destructive:
            return format_html(
                '<span style="background: #ef4444; color: white; padding: 2px 8px; '
                'border-radius: 4px; font-size: 11px;">⚠️ Yes</span>'
            )
        return format_html(
            '<span style="background: #22c55e; color: white; padding: 2px 8px; '
            'border-radius: 4px; font-size: 11px;">Safe</span>'
        )


# =============================================================================
# GRANULAR PERMISSION ADMIN
# =============================================================================


@admin.register(GranularPermission)
class GranularPermissionAdmin(admin.ModelAdmin):
    """Django Admin for Granular Permissions."""

    list_display = ["codename", "resource", "action", "description"]
    list_filter = ["resource", "action"]
    search_fields = ["codename", "description"]
    ordering = ["resource__name", "action__name"]
    list_select_related = ["resource", "action"]


# =============================================================================
# ROLE ADMIN
# =============================================================================


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Full Django Admin for Roles with permission assignment."""

    list_display = [
        "name",
        "slug",
        "scope_badge",
        "permission_count",
        "is_system_badge",
        "is_default",
        "created_at",
    ]
    list_filter = ["scope", "is_system", "is_default", "created_at"]
    search_fields = ["name", "slug", "description", "tenant_id"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["scope", "name"]
    filter_horizontal = ["permissions"]  # 🔴 Multi-select widget

    fieldsets = (
        (
            "Role Information",
            {
                "fields": ("id", "name", "slug", "description"),
            },
        ),
        (
            "Scope",
            {
                "fields": ("scope", "tenant_id"),
            },
        ),
        (
            "Permissions",
            {
                "fields": ("permissions",),
                "description": "Select permissions for this role",
            },
        ),
        (
            "Status",
            {
                "fields": ("is_system", "is_default"),
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

    inlines = [UserRoleAssignmentInline]

    actions = ["set_as_default", "unset_default", "clone_role"]

    @admin.display(description="Scope")
    def scope_badge(self, obj):
        """Execute scope badge.

            Args:
                obj: The obj.
            """

        colors = {
            "platform": "#ef4444",
            "tenant": "#3b82f6",
            "agent": "#22c55e",
        }
        color = colors.get(obj.scope, "#94a3b8")
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; '
            'border-radius: 4px; font-size: 11px;">{}</span>',
            color,
            obj.scope.upper(),
        )

    @admin.display(description="Permissions")
    def permission_count(self, obj):
        """Execute permission count.

            Args:
                obj: The obj.
            """

        return obj.permissions.count()

    @admin.display(description="System")
    def is_system_badge(self, obj):
        """Check if system badge.

            Args:
                obj: The obj.
            """

        if obj.is_system:
            return format_html(
                '<span style="background: #f59e0b; color: white; padding: 2px 6px; '
                'border-radius: 4px; font-size: 10px;">🔒 System</span>'
            )
        return "Custom"

    @admin.action(description="Set as default role")
    def set_as_default(self, request, queryset):
        """Set as default.

            Args:
                request: The request.
                queryset: The queryset.
            """

        queryset.update(is_default=True)

    @admin.action(description="Unset default")
    def unset_default(self, request, queryset):
        """Execute unset default.

            Args:
                request: The request.
                queryset: The queryset.
            """

        queryset.update(is_default=False)

    @admin.action(description="Clone role (creates copy)")
    def clone_role(self, request, queryset):
        """Execute clone role.

            Args:
                request: The request.
                queryset: The queryset.
            """

        for role in queryset:
            permissions = list(role.permissions.all())
            role.pk = None
            role.name = f"{role.name} (Copy)"
            role.slug = f"{role.slug}-copy"
            role.is_system = False
            role.is_default = False
            role.save()
            role.permissions.set(permissions)
        self.message_user(request, f"{queryset.count()} roles cloned.")


# =============================================================================
# USER ROLE ASSIGNMENT ADMIN
# =============================================================================


@admin.register(UserRoleAssignment)
class UserRoleAssignmentAdmin(admin.ModelAdmin):
    """Django Admin for User Role Assignments."""

    list_display = [
        "user_id_short",
        "role",
        "tenant_id_short",
        "scope_type",
        "scope_id_short",
        "granted_by_short",
        "expires_at",
        "created_at",
    ]
    list_filter = ["scope_type", "role", "created_at"]
    search_fields = ["user_id", "scope_id", "granted_by", "tenant_id"]
    ordering = ["-created_at"]
    list_select_related = ["role"]
    raw_id_fields = ["role"]

    @admin.display(description="User")
    def user_id_short(self, obj):
        """Execute user id short.

            Args:
                obj: The obj.
            """

        return str(obj.user_id)[:12] if obj.user_id else "-"

    @admin.display(description="Tenant")
    def tenant_id_short(self, obj):
        """Execute tenant id short.

            Args:
                obj: The obj.
            """

        return str(obj.tenant_id)[:8] if obj.tenant_id else "-"

    @admin.display(description="Scope ID")
    def scope_id_short(self, obj):
        """Execute scope id short.

            Args:
                obj: The obj.
            """

        return str(obj.scope_id)[:8] if obj.scope_id else "-"

    @admin.display(description="Granted By")
    def granted_by_short(self, obj):
        """Execute granted by short.

            Args:
                obj: The obj.
            """

        return str(obj.granted_by)[:8] if obj.granted_by else "-"


# =============================================================================
# PERMISSION GRANT ADMIN
# =============================================================================


@admin.register(PermissionGrant)
class PermissionGrantAdmin(admin.ModelAdmin):
    """Django Admin for individual Permission Grants."""

    list_display = [
        "user_id_short",
        "permission",
        "tenant_id_short",
        "scope_type",
        "scope_id_short",
        "expires_at",
        "created_at",
    ]
    list_filter = ["scope_type", "permission", "created_at"]
    search_fields = ["user_id", "scope_id", "tenant_id"]
    ordering = ["-created_at"]
    list_select_related = ["permission"]

    @admin.display(description="User")
    def user_id_short(self, obj):
        """Execute user id short.

            Args:
                obj: The obj.
            """

        return str(obj.user_id)[:12] if obj.user_id else "-"

    @admin.display(description="Tenant")
    def tenant_id_short(self, obj):
        """Execute tenant id short.

            Args:
                obj: The obj.
            """

        return str(obj.tenant_id)[:8] if obj.tenant_id else "-"

    @admin.display(description="Scope ID")
    def scope_id_short(self, obj):
        """Execute scope id short.

            Args:
                obj: The obj.
            """

        return str(obj.scope_id)[:8] if obj.scope_id else "-"


# =============================================================================
# PERMISSION CHECK LOG ADMIN (Audit)
# =============================================================================


@admin.register(PermissionCheckLog)
class PermissionCheckLogAdmin(admin.ModelAdmin):
    """Django Admin for Permission Check Logs - fully read-only audit."""

    list_display = [
        "timestamp",
        "user_id_short",
        "permission_codename",
        "allowed_badge",
        "reason",
        "ip_address",
    ]
    list_filter = ["allowed", "reason", "timestamp"]
    search_fields = ["user_id", "permission_codename", "ip_address"]
    readonly_fields = [
        "id",
        "timestamp",
        "user_id",
        "tenant_id",
        "permission_codename",
        "resource_id",
        "allowed",
        "reason",
        "ip_address",
    ]
    ordering = ["-timestamp"]
    list_per_page = 100
    date_hierarchy = "timestamp"

    @admin.display(description="User")
    def user_id_short(self, obj):
        """Execute user id short.

            Args:
                obj: The obj.
            """

        return str(obj.user_id)[:12] if obj.user_id else "-"

    @admin.display(description="Allowed")
    def allowed_badge(self, obj):
        """Execute allowed badge.

            Args:
                obj: The obj.
            """

        if obj.allowed:
            return format_html(
                '<span style="background: #22c55e; color: white; padding: 2px 8px; '
                'border-radius: 4px; font-size: 11px;">✓ Yes</span>'
            )
        return format_html(
            '<span style="background: #ef4444; color: white; padding: 2px 8px; '
            'border-radius: 4px; font-size: 11px;">✗ No</span>'
        )

    def has_add_permission(self, request):
        """Check if add permission.

            Args:
                request: The request.
            """

        return False  # Logs are system-generated

    def has_change_permission(self, request, obj=None):
        """Check if change permission.

            Args:
                request: The request.
                obj: The obj.
            """

        return False

    def has_delete_permission(self, request, obj=None):
        """Check if delete permission.

            Args:
                request: The request.
                obj: The obj.
            """

        return False  # Compliance - cannot delete audit logs