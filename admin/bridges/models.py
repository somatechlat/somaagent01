"""Bridge Capsule data model (SOMA-A0-PARITY-001 §6.3, normative).

Entities
--------
- ``Channel``          — a bound messaging channel (WhatsApp/Telegram/Email/Slack/Web)
- ``BridgeSession``    — external user/chat conversation state on a channel
- ``InboundMessage``   — message received from the external network
- ``OutboundMessage``  — message queued/sent back out (with retries + idempotency)

Security (T-5, fail-closed):
- ``Channel.tenant`` is REQUIRED — there is no default tenant anywhere in this
  model or in the API layer. Missing tenant binding is a hard error.
- ``Channel.capsule`` binds the channel to the Capsule that answers on it;
  unbound channels must not dispatch (fail-closed on missing binding).
- Credentials are referenced (``credentials_ref`` = Vault path), never stored.
"""

from __future__ import annotations

import uuid

from django.db import models


class Channel(models.Model):
    """A messaging channel bound to a Capsule and a tenant.

    Fields (normative §6.3): id, tenant FK, capsule FK, kind, status,
    config JSON, credentials ref (Vault), created_at.
    """

    KIND_WHATSAPP = "whatsapp"
    KIND_TELEGRAM = "telegram"
    KIND_EMAIL = "email"
    KIND_SLACK = "slack"
    KIND_WEB = "web"
    KIND_CHOICES = [
        (KIND_WHATSAPP, "WhatsApp"),
        (KIND_TELEGRAM, "Telegram"),
        (KIND_EMAIL, "Email"),
        (KIND_SLACK, "Slack"),
        (KIND_WEB, "Web"),
    ]

    STATUS_DISABLED = "disabled"
    STATUS_PENDING = "pending"
    STATUS_ACTIVE = "active"
    STATUS_ERROR = "error"
    STATUS_CHOICES = [
        (STATUS_DISABLED, "Disabled"),
        (STATUS_PENDING, "Pending"),
        (STATUS_ACTIVE, "Active"),
        (STATUS_ERROR, "Error"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Required tenant binding — NO default tenant (fail-closed, T-5).
    tenant = models.ForeignKey(
        "aaas.Tenant",
        on_delete=models.CASCADE,
        related_name="bridge_channels",
        db_index=True,
        help_text="Owning tenant; required — no default tenant",
    )

    capsule = models.ForeignKey(
        "core.Capsule",
        on_delete=models.PROTECT,
        related_name="bridge_channels",
        null=True,
        blank=True,
        help_text="Capsule that answers on this channel; unbound = fail-closed dispatch",
    )

    kind = models.CharField(
        max_length=20,
        choices=KIND_CHOICES,
        db_index=True,
        help_text="Channel network: whatsapp/telegram/email/slack/web",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DISABLED,
        db_index=True,
    )

    name = models.CharField(max_length=255, blank=True, default="")
    config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Channel config (allowlists, group mode, poll interval, …)",
    )
    credentials_ref = models.CharField(
        max_length=512,
        blank=True,
        default="",
        help_text="Vault/secrets-store reference for channel credentials — never raw secrets",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta class implementation."""

        db_table = "bridge_channels"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "kind"]),
            models.Index(fields=["status"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "kind", "name"],
                condition=~models.Q(name=""),
                name="bridge_channel_unique_name_per_tenant_kind",
            ),
        ]

    def __str__(self) -> str:
        """Return string representation."""

        return f"Channel({self.kind}:{self.id}:{self.status})"


class BridgeSession(models.Model):
    """External conversation/session state on a channel.

    Fields (normative §6.3): channel FK, external_user/chat id, state,
    context JSON.
    """

    STATE_PENDING = "pending"
    STATE_ACTIVE = "active"
    STATE_PAUSED = "paused"
    STATE_CHOICES = [
        (STATE_PENDING, "Pending"),
        (STATE_ACTIVE, "Active"),
        (STATE_PAUSED, "Paused"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey(
        Channel,
        on_delete=models.CASCADE,
        related_name="sessions",
        db_index=True,
    )
    external_user_id = models.CharField(
        max_length=255,
        db_index=True,
        help_text="External user identifier (WA JID, TG user id, email address)",
    )
    external_chat_id = models.CharField(
        max_length=255,
        db_index=True,
        blank=True,
        default="",
        help_text="External chat/group/thread identifier when distinct from user",
    )
    state = models.CharField(
        max_length=20,
        choices=STATE_CHOICES,
        default=STATE_PENDING,
        db_index=True,
    )
    context = models.JSONField(
        default=dict,
        blank=True,
        help_text="Session context (thread markers, group metadata, slash state)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta class implementation."""

        db_table = "bridge_sessions"
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["channel", "external_user_id", "external_chat_id"]),
        ]

    def __str__(self) -> str:
        """Return string representation."""

        return f"BridgeSession({self.channel_id}:{self.external_user_id}:{self.state})"


class InboundMessage(models.Model):
    """Message received from the external messaging network.

    Fields (normative §6.3): channel, session, external_id, direction, payload,
    attachments, received_at, processed_at.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey(
        Channel,
        on_delete=models.CASCADE,
        related_name="inbound_messages",
        db_index=True,
    )
    session = models.ForeignKey(
        BridgeSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inbound_messages",
    )
    external_id = models.CharField(
        max_length=255,
        db_index=True,
        blank=True,
        default="",
        help_text="Message id on the external network (for dedupe)",
    )
    direction = models.CharField(
        max_length=20,
        default="inbound",
        help_text="Message direction marker (inbound)",
    )
    payload = models.JSONField(
        default=dict,
        blank=True,
        help_text="Normalized inbound payload (text, sender, chat, raw ref)",
    )
    attachments = models.JSONField(
        default=list,
        blank=True,
        help_text="Attachment descriptors (media type, vault/storage ref)",
    )
    received_at = models.DateTimeField(auto_now_add=True, db_index=True)
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Set when dispatched to the agent; null = unprocessed",
    )

    class Meta:
        """Meta class implementation."""

        db_table = "bridge_inbound_messages"
        ordering = ["-received_at"]
        indexes = [
            models.Index(fields=["channel", "external_id"]),
        ]

    def __str__(self) -> str:
        """Return string representation."""

        return f"InboundMessage({self.channel_id}:{self.external_id or self.id})"


class OutboundMessage(models.Model):
    """Message queued to send back to the external network.

    Fields (normative §6.3): channel, session, payload, status, attempts,
    last_error, idempotency_key.
    """

    STATUS_QUEUED = "queued"
    STATUS_SENT = "sent"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_QUEUED, "Queued"),
        (STATUS_SENT, "Sent"),
        (STATUS_FAILED, "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey(
        Channel,
        on_delete=models.CASCADE,
        related_name="outbound_messages",
        db_index=True,
    )
    session = models.ForeignKey(
        BridgeSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="outbound_messages",
    )
    payload = models.JSONField(
        default=dict,
        blank=True,
        help_text="Outbound payload (text/markdown, reply_to, media refs)",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_QUEUED,
        db_index=True,
    )
    attempts = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True, default="")
    idempotency_key = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        help_text="Idempotency key to prevent double-send",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Meta class implementation."""

        db_table = "bridge_outbound_messages"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["channel", "idempotency_key"],
                condition=~models.Q(idempotency_key=None) & ~models.Q(idempotency_key=""),
                name="bridge_outbound_idempotency_unique",
            ),
        ]

    def __str__(self) -> str:
        """Return string representation."""

        return f"OutboundMessage({self.channel_id}:{self.status}:{self.id})"
