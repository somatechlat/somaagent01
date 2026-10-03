"""LLM Django Admin."""

from django.contrib import admin
from django.utils.html import format_html

from admin.llm.models import LLMModelConfig


@admin.register(LLMModelConfig)
class LLMModelConfigAdmin(admin.ModelAdmin):
    """Full Django Admin for LLM Model Configurations."""

    list_display = [
        "name",
        "provider",
        "model_type",
        "ctx_length_display",
        "vision_badge",
        "is_active",
        "created_at",
    ]
    list_filter = ["provider", "model_type", "vision", "is_active", "created_at"]
    search_fields = ["name", "provider", "api_base"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["provider", "name"]
    list_per_page = 50

    fieldsets = (
        (
            "Model Information",
            {
                "fields": ("name", "provider", "model_type"),
            },
        ),
        (
            "API Configuration",
            {
                "fields": ("api_base", "kwargs"),
            },
        ),
        (
            "Limits",
            {
                "fields": (
                    "ctx_length",
                    "limit_requests",
                    "limit_input",
                    "limit_output",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Capabilities",
            {
                "fields": ("vision",),
            },
        ),
        (
            "Status",
            {
                "fields": ("is_active",),
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

    actions = ["activate_models", "deactivate_models", "enable_vision", "disable_vision"]

    @admin.display(description="Context")
    def ctx_length_display(self, obj):
        """Execute ctx length display.

        Args:
            obj: The obj.
        """

        if obj.ctx_length >= 100000:
            return f"{obj.ctx_length // 1000}K"
        elif obj.ctx_length >= 1000:
            return f"{obj.ctx_length // 1000}K"
        return str(obj.ctx_length)

    @admin.display(description="Vision")
    def vision_badge(self, obj):
        """Execute vision badge.

        Args:
            obj: The obj.
        """

        if obj.vision:
            return format_html(
                '<span style="background: #22c55e; color: white; padding: 2px 8px; '
                'border-radius: 4px; font-size: 11px;">👁️ Yes</span>'
            )
        return format_html(
            '<span style="background: #94a3b8; color: white; padding: 2px 8px; '
            'border-radius: 4px; font-size: 11px;">No</span>'
        )

    @admin.action(description="Activate selected models")
    def activate_models(self, request, queryset):
        """Execute activate models.

        Args:
            request: The request.
            queryset: The queryset.
        """

        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} models activated.")

    @admin.action(description="Deactivate selected models")
    def deactivate_models(self, request, queryset):
        """Execute deactivate models.

        Args:
            request: The request.
            queryset: The queryset.
        """

        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} models deactivated.")

    @admin.action(description="Enable vision capability")
    def enable_vision(self, request, queryset):
        """Mark selected models as vision-capable.

        Writes ``capabilities``, not the ``vision`` column: ``vision`` is
        derived from ``capabilities`` on save (``LLMModelConfig.save``), so the
        old ``queryset.update(vision=True)`` bypassed that and left the two
        disagreeing. ``capabilities`` is the source of truth.
        """
        for obj in queryset:
            caps = list(obj.capabilities or [])
            if "vision" not in caps:
                caps.append("vision")
            obj.capabilities = caps
            obj.save(update_fields=["capabilities", "vision", "updated_at"])
        self.message_user(request, f"{queryset.count()} models marked vision-capable.")

    @admin.action(description="Disable vision capability")
    def disable_vision(self, request, queryset):
        """Clear the vision capability. Same source-of-truth rule as above."""
        for obj in queryset:
            caps = [c for c in (obj.capabilities or []) if c != "vision"]
            obj.capabilities = caps
            obj.save(update_fields=["capabilities", "vision", "updated_at"])
        self.message_user(request, f"{queryset.count()} models cleared of vision.")

