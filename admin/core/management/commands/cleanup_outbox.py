"""Cleanup old outbox and dead-letter messages.

Removes published OutboxMessage records older than 30 days
and resolved DeadLetterMessage records older than 7 days.

Usage:
    python manage.py cleanup_outbox --dry-run
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from admin.core.models.zdl import DeadLetterMessage, OutboxMessage

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Cleanup old outbox and dead-letter messages."""

    help = "Cleanup published outbox messages and resolved dead-letter messages"

    def add_arguments(self, parser: Any) -> None:
        """Add command arguments."""
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Log what would be deleted without modifying",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Process cleanup."""
        dry_run = options["dry_run"]

        cutoff_outbox = timezone.now() - timedelta(days=30)
        cutoff_dlq = timezone.now() - timedelta(days=7)

        outbox_qs = OutboxMessage.objects.filter(
            status=OutboxMessage.Status.PUBLISHED,
            published_at__lt=cutoff_outbox,
        )
        dlq_qs = DeadLetterMessage.objects.filter(
            resolved=True,
            resolved_at__lt=cutoff_dlq,
        )

        outbox_count = outbox_qs.count()
        dlq_count = dlq_qs.count()

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[DRY-RUN] Would delete {outbox_count} published outbox messages "
                    f"older than 30 days and {dlq_count} resolved dead-letter messages "
                    f"older than 7 days"
                )
            )
            return

        if not outbox_count and not dlq_count:
            self.stdout.write(self.style.SUCCESS("Nothing to clean up"))
            return

        with transaction.atomic():
            outbox_deleted, _ = outbox_qs.delete()
            dlq_deleted, _ = dlq_qs.delete()

        logger.info(
            "Outbox cleanup complete: %s outbox messages, %s dead-letter messages deleted",
            outbox_deleted,
            dlq_deleted,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted {outbox_deleted} published outbox messages and "
                f"{dlq_deleted} resolved dead-letter messages"
            )
        )
