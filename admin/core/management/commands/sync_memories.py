"""Sync pending memories to SomaBrain.

Processes PendingMemory records that were queued while SomaBrain was
unavailable and pushes them to the cognitive runtime.

Usage:
    python manage.py sync_memories --batch-size 100
"""

import logging
import time
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from admin.core.models import PendingMemory
from admin.core.somabrain_client import SomaBrainClient
from services.common.circuit_breaker import get_circuit_breaker

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Sync pending memories to SomaBrain."""

    help = "Sync PendingMemory queue to SomaBrain"

    def add_arguments(self, parser: Any) -> None:
        """Add command arguments."""
        parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
            help="Number of pending memories to process per run",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Log what would be synced without modifying",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Process pending memory queue."""
        batch_size = options["batch_size"]
        dry_run = options["dry_run"]

        # Only run if SomaBrain circuit is closed
        cb = get_circuit_breaker("somabrain")
        if cb and cb.is_open():
            self.stdout.write(
                self.style.WARNING("SomaBrain circuit is OPEN — skipping sync")
            )
            return

        pending = list(
            PendingMemory.objects.filter(synced=False)
            .order_by("created_at")
            [:batch_size]
        )

        if not pending:
            self.stdout.write(self.style.SUCCESS("No pending memories to sync"))
            return

        self.stdout.write(f"Syncing {len(pending)} pending memories...")

        synced_count = 0
        failed_count = 0

        for mem in pending:
            try:
                self._sync_one(mem, dry_run=dry_run)
                synced_count += 1
            except Exception as exc:
                failed_count += 1
                logger.error("Sync failed for %s: %s", mem.idempotency_key, exc)
                if not dry_run:
                    mem.sync_attempts += 1
                    mem.last_error = str(exc)
                    mem.save(update_fields=["sync_attempts", "last_error"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Done: {synced_count} synced, {failed_count} failed, "
                f"{len(pending) - synced_count - failed_count} skipped"
            )
        )

    def _sync_one(self, mem: PendingMemory, *, dry_run: bool = False) -> None:
        """Sync a single pending memory to SomaBrain."""
        import asyncio

        if dry_run:
            self.stdout.write(f"  [DRY-RUN] Would sync {mem.idempotency_key}")
            return

        async def _push() -> None:
            client = await SomaBrainClient.get_async()
            await client.remember(
                payload=mem.payload,
                tenant=mem.tenant_id,
                namespace=mem.namespace,
            )

        asyncio.run(_push())

        with transaction.atomic():
            mem.mark_synced()

        self.stdout.write(f"  Synced {mem.idempotency_key}")
