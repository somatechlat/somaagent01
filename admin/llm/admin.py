"""LLM Django Admin.

VIBE COMPLIANT - Full Django Admin capabilities.
7-Persona Implementation for LLM Model Configuration.
"""

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
        if obj.ctx_length >= 100000:
            return f"{obj.ctx_length // 1000}K"
        elif obj.ctx_length >= 1000:
            return f"{obj.ctx_length // 1000}K"
        return str(obj.ctx_length)

    @admin.display(description="Vision")
    def vision_badge(self, obj):
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
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} models activated.")

    @admin.action(description="Deactivate selected models")
    def deactivate_models(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} models deactivated.")

    @admin.action(description="Enable vision capability")
    def enable_vision(self, request, queryset):
        queryset.update(vision=True)

    @admin.action(description="Disable vision capability")
    def disable_vision(self, request, queryset):
        queryset.update(vision=False)
