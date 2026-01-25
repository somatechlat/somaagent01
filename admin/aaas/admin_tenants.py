"""AAAS Django Admin - Tenant and Tier AdminsSplit from admin/aaas/admin.py for 650-line compliance."""

from django.contrib import admin
from django.utils.html import format_html

from admin.aaas.models import SubscriptionTier, Tenant, TenantUser, TierFeature


class TenantUserInline(admin.TabularInline):
    """Inline for managing users within a tenant."""

    model = TenantUser
    extra = 0
    readonly_fields = ["created_at"]
    fields = ["email", "display_name", "role", "is_active", "created_at"]
    ordering = ["-created_at"]
    show_change_link = True


class TierFeatureInline(admin.TabularInline):
    """Inline for managing features within a tier."""

    model = TierFeature
    extra = 0
    fields = ["feature", "is_enabled", "quota_limit"]
    ordering = ["feature__name"]


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
    inlines = [TierFeatureInline]
    actions = ["activate_tiers", "deactivate_tiers", "make_public", "make_private"]

    fieldsets = (
        ("Tier Information", {"fields": ("id", "name", "slug", "description")}),
        ("Pricing", {"fields": ("base_price_cents", "billing_interval", "lago_plan_code")}),
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
        ("Status", {"fields": ("is_active", "is_public", "sort_order")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

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
    inlines = [TenantUserInline]
    actions = ["activate_tenants", "suspend_tenants"]

    fieldsets = (
        ("Tenant Information", {"fields": ("id", "name", "slug", "status")}),
        ("Subscription", {"fields": ("tier", "trial_ends_at")}),
        (
            "Billing (Lago)",
            {"fields": ("billing_email", "lago_customer_id", "lago_subscription_id")},
        ),
        ("Authentication (Keycloak)", {"fields": ("keycloak_realm",), "classes": ("collapse",)}),
        ("Configuration", {"fields": ("feature_overrides", "metadata"), "classes": ("collapse",)}),
        ("Statistics", {"fields": ("user_count", "agent_count")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

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
            '<span style="background: {}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px;">{}</span>',
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


@admin.register(TenantUser)
class TenantUserAdmin(admin.ModelAdmin):
    """Full Django Admin for Tenant Users."""

    list_display = ["email", "display_name", "tenant", "role_badge", "is_active", "created_at"]
    list_filter = ["role", "is_active", "tenant", "created_at"]
    search_fields = ["email", "display_name", "user_id"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["-created_at"]
    list_per_page = 50
    list_select_related = ["tenant"]
    raw_id_fields = ["tenant"]
    actions = ["activate_users", "deactivate_users", "promote_to_admin"]

    fieldsets = (
        ("User Information", {"fields": ("id", "email", "display_name", "user_id")}),
        ("Tenant & Role", {"fields": ("tenant", "role", "is_active")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    @admin.display(description="Role")
    def role_badge(self, obj):
        colors = {"owner": "#ef4444", "admin": "#f59e0b", "member": "#3b82f6", "viewer": "#94a3b8"}
        color = colors.get(obj.role, "#94a3b8")
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px;">{}</span>',
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
