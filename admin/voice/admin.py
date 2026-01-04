"""Voice Django Admin.


Register Voice models with rich admin interface.
"""

from django.contrib import admin
from django.utils.html import format_html

from admin.voice.models import VoiceModel, VoicePersona, VoiceSession


# =============================================================================
# VOICE PERSONA ADMIN
# =============================================================================


@admin.register(VoicePersona)
class VoicePersonaAdmin(admin.ModelAdmin):
    """Admin for VoicePersona with full Django capabilities."""

    list_display = [
        "name",
        "tenant_id",
        "voice_id",
        "stt_model",
        "llm_config_display",
        "is_active",
        "is_default",
        "created_at",
    ]
    list_filter = [
        "is_active",
        "is_default",
        "stt_model",
        "voice_id",
        "created_at",
    ]
    search_fields = [
        "name",
        "description",
        "tenant_id",
        "voice_id",
    ]
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
    ]
    ordering = ["-created_at"]
    list_per_page = 25
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Basic Info",
            {
                "fields": ("id", "name", "description", "tenant_id"),
            },
        ),
        (
            "Voice Settings (TTS)",
            {
                "fields": ("voice_id", "voice_speed"),
            },
        ),
        (
            "Speech-to-Text",
            {
                "fields": ("stt_model", "stt_language"),
            },
        ),
        (
            "LLM Configuration",
            {
                "fields": ("llm_config", "system_prompt", "temperature", "max_tokens"),
                "description": "Reference to existing LLM model - no duplication",
            },
        ),
        (
            "Turn Detection",
            {
                "fields": (
                    "turn_detection_enabled",
                    "turn_detection_threshold",
                    "silence_duration_ms",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Status",
            {
                "fields": ("is_active", "is_default"),
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

    actions = ["activate_personas", "deactivate_personas", "set_as_default"]

    @admin.display(description="LLM Config")
    def llm_config_display(self, obj):
        """Display LLM config name."""
        if obj.llm_config:
            return f"{obj.llm_config.provider}/{obj.llm_config.name}"
        return "-"

    @admin.action(description="Activate selected personas")
    def activate_personas(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} personas activated.")

    @admin.action(description="Deactivate selected personas")
    def deactivate_personas(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} personas deactivated.")

    @admin.action(description="Set as default (first selected)")
    def set_as_default(self, request, queryset):
        if queryset.exists():
            # Clear existing defaults for same tenant
            first = queryset.first()
            VoicePersona.objects.filter(tenant_id=first.tenant_id).update(is_default=False)
            first.is_default = True
            first.save()
            self.message_user(request, f"{first.name} set as default.")


# =============================================================================
# VOICE SESSION ADMIN
# =============================================================================


@admin.register(VoiceSession)
class VoiceSessionAdmin(admin.ModelAdmin):
    """Admin for VoiceSession with monitoring capabilities."""

    list_display = [
        "id_short",
        "tenant_id",
        "persona",
        "status_badge",
        "duration_display",
        "tokens_display",
        "audio_display",
        "turn_count",
        "created_at",
    ]
    list_filter = [
        "status",
        "created_at",
    ]
    search_fields = [
        "id",
        "tenant_id",
        "project_id",
        "error_message",
    ]
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "started_at",
        "terminated_at",
        "duration_seconds",
        "input_tokens",
        "output_tokens",
        "audio_input_seconds",
        "audio_output_seconds",
        "turn_count",
    ]
    ordering = ["-created_at"]
    list_per_page = 50
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Session Info",
            {
                "fields": (
                    "id",
                    "tenant_id",
                    "project_id",
                    "api_key_id",
                    "user_id",
                    "persona",
                ),
            },
        ),
        (
            "Status",
            {
                "fields": ("status", "error_code", "error_message"),
            },
        ),
        (
            "Metrics",
            {
                "fields": (
                    "duration_seconds",
                    "input_tokens",
                    "output_tokens",
                    "audio_input_seconds",
                    "audio_output_seconds",
                    "turn_count",
                ),
            },
        ),
        (
            "Config & Metadata",
            {
                "fields": ("config", "metadata"),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "started_at", "terminated_at", "updated_at"),
            },
        ),
    )

    actions = ["terminate_sessions"]

    @admin.display(description="ID")
    def id_short(self, obj):
        """Short ID display."""
        return str(obj.id)[:8]

    @admin.display(description="Status")
    def status_badge(self, obj):
        """Colored status badge."""
        colors = {
            "created": "#3498db",
            "active": "#27ae60",
            "completed": "#2ecc71",
            "error": "#e74c3c",
            "terminated": "#95a5a6",
        }
        color = colors.get(obj.status, "#95a5a6")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 4px; font-size: 11px;">{}</span>',
            color,
            obj.status.upper(),
        )

    @admin.display(description="Duration")
    def duration_display(self, obj):
        """Format duration."""
        if obj.duration_seconds:
            mins = int(obj.duration_seconds // 60)
            secs = int(obj.duration_seconds % 60)
            return f"{mins:02d}:{secs:02d}"
        return "-"

    @admin.display(description="Tokens")
    def tokens_display(self, obj):
        """Format tokens."""
        total = obj.input_tokens + obj.output_tokens
        if total:
            return f"{total:,}"
        return "-"

    @admin.display(description="Audio")
    def audio_display(self, obj):
        """Format audio seconds."""
        total = obj.audio_input_seconds + obj.audio_output_seconds
        if total:
            return f"{total:.1f}s"
        return "-"

    @admin.action(description="Terminate selected sessions")
    def terminate_sessions(self, request, queryset):
        active = queryset.filter(status__in=["created", "active"])
        count = 0
        for session in active:
            session.terminate(reason="Terminated by admin")
            count += 1
        self.message_user(request, f"{count} sessions terminated.")


# =============================================================================
# VOICE MODEL ADMIN
# =============================================================================


@admin.register(VoiceModel)
class VoiceModelAdmin(admin.ModelAdmin):
    """Admin for VoiceModel (TTS voices catalog)."""

    list_display = [
        "id",
        "name",
        "provider",
        "language",
        "gender",
        "is_active",
        "sample_link",
    ]
    list_filter = [
        "provider",
        "language",
        "gender",
        "is_active",
    ]
    search_fields = [
        "id",
        "name",
        "description",
    ]
    ordering = ["provider", "name"]
    list_per_page = 50

    fieldsets = (
        (
            "Voice Info",
            {
                "fields": ("id", "name", "description"),
            },
        ),
        (
            "Provider",
            {
                "fields": ("provider", "language", "gender"),
            },
        ),
        (
            "Sample",
            {
                "fields": ("sample_url",),
            },
        ),
        (
            "Status",
            {
                "fields": ("is_active",),
            },
        ),
    )

    actions = ["activate_voices", "deactivate_voices"]

    @admin.display(description="Sample")
    def sample_link(self, obj):
        """Clickable sample link."""
        if obj.sample_url:
            return format_html('<a href="{}" target="_blank">▶ Play</a>', obj.sample_url)
        return "-"

    @admin.action(description="Activate selected voices")
    def activate_voices(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} voices activated.")

    @admin.action(description="Deactivate selected voices")
    def deactivate_voices(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} voices deactivated.")
