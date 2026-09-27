"""Sync pending memories through the MemoryGateway seam.

Processes PendingMemory records that were queued for FAILED store acks only
(ok=False / timed out) and retries the store named in ``payload.retry_store``.

Retry policy (PLAN-TRIAD-SEAMLESS §1 rule 4):
- Only stores whose ack failed are retried; a successful ack is never re-written.
- The retry re-issues ``remember_text()`` with the original ``ts``, which
  reproduces the same seam coord + SomaBrain key material, so both stores upsert
  one row (no duplicate memories).
- The row is marked synced only when the TARGET store's ack is ok.

Usage:
    python manage.py sync_memories --batch-size 100
"""

import logging
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from admin.core.models import PendingMemory
from services.common.circuit_breaker import get_circuit_breaker

logger = logging.getLogger(__name__)

# Legacy rows (pre-seam) targeted SomaBrain when no retry_store was recorded.
_LEGACY_TARGET_STORE = "somabrain"


class Command(BaseCommand):
    """Sync pending memories to the failed store via MemoryGateway."""

    help = "Sync PendingMemory queue (failed acks only) via MemoryGateway"

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
        """Retry ONE failed store through the MemoryGateway seam."""
        import asyncio

        if dry_run:
            self.stdout.write(f"  [DRY-RUN] Would sync {mem.idempotency_key}")
            return

        # Imported lazily: the orchestrator owns the seam policy
        # (_require_memory_gateway: explicit-disable skip, else fail-closed).
        from admin.core.chat_orchestrator import _require_memory_gateway

        payload = mem.payload or {}
        target_store = str(payload.get("retry_store") or _LEGACY_TARGET_STORE)
        text = str(payload.get("text") or payload.get("content") or "")
        kind = str(payload.get("kind") or "episodic")
        # Original ts reproduces the same coord + key material on retry.
        ts = payload.get("ts") or None
        if not text:
            raise ValueError(f"PendingMemory {mem.idempotency_key} has no text")

        async def _push() -> list[Any]:
            gateway = _require_memory_gateway()
            if gateway is None:
                raise RuntimeError(
                    "Memory is explicitly disabled by deployment mode but a "
                    "PendingMemory retry is outstanding — refusing to drop it"
                )
            return await gateway.remember_text(
                text,
                tenant_id=mem.tenant_id,
                kind=kind,
                ts=ts,
                session_id=payload.get("session_id"),
                salience=float(payload.get("salience", 0.5) or 0.5),
                source=str(payload.get("source") or "agent-chat"),
            )

        acks = asyncio.run(_push())
        ack_by_store = {ack.store: ack for ack in acks}
        ack = ack_by_store.get(target_store)
        if ack is None:
            raise RuntimeError(f"no ack returned for target store {target_store}")
        if not ack.ok:
            raise RuntimeError(f"{target_store} ack failed: {ack.error}")

        with transaction.atomic():
            mem.mark_synced()

        self.stdout.write(f"  Synced {mem.idempotency_key} -> {target_store}")
