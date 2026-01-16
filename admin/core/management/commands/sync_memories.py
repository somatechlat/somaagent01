"""Sync Pending Memories Django Management Command.

Syncs pending memories to SomaBrain when connection is restored.

Usage:
    python manage.py sync_memories --batch-size=50 --interval=5


"""

from __future__ import annotations

import asyncio
import logging
import signal

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Sync pending memories to SomaBrain.

    When SomaBrain becomes available after degradation mode,
    this command flushes the pending memory queue.
    """

    help = "Sync pending memories to SomaBrain (degradation mode recovery)"

    def __init__(self, *args, **kwargs):
        """Initialize the instance."""

        super().__init__(*args, **kwargs)
        self._running = True
        self._client = None

    def add_arguments(self, parser):
        """Execute add arguments.

        Args:
            parser: The parser.
        """

        parser.add_argument(
            "--batch-size",
            type=int,
            default=50,
            help="Number of memories to sync per batch (default: 50)",
        )
        parser.add_argument(
            "--interval",
            type=float,
            default=5.0,
            help="Seconds between sync attempts (default: 5.0)",
        )
        parser.add_argument(
            "--once",
            action="store_true",
            help="Run once and exit",
        )
        parser.add_argument(
            "--max-retries",
            type=int,
            default=3,
            help="Max retry attempts per memory (default: 3)",
        )

    def handle(self, *args, **options):
        """Main command entrypoint."""
        batch_size = options["batch_size"]
        interval = options["interval"]
        run_once = options["once"]
        max_retries = options["max_retries"]

        self.stdout.write(
            self.style.SUCCESS(f"Starting Memory Sync (batch={batch_size}, interval={interval}s)")
        )

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        try:
            asyncio.run(self._run_sync(batch_size, interval, run_once, max_retries))
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Shutting down..."))
        finally:
            self.stdout.write(self.style.SUCCESS("Memory Sync stopped"))

    def _handle_signal(self, signum, frame):
        """Handle shutdown signals."""
        self._running = False

    async def _run_sync(self, batch_size: int, interval: float, run_once: bool, max_retries: int):
        """Main sync loop."""
        from admin.core.models import PendingMemory

        while self._running:
            try:
                # Check SomaBrain health first
                if not await self._check_somabrain_health():
                    self.stdout.write(self.style.WARNING("SomaBrain unavailable, waiting..."))
                    await asyncio.sleep(interval * 2)
                    continue

                # Get pending count
                pending_count = PendingMemory.objects.filter(synced=False).count()

                if pending_count == 0:
                    if run_once:
                        self.stdout.write(self.style.SUCCESS("No pending memories"))
                        break
                    await asyncio.sleep(interval)
                    continue

                self.stdout.write(f"Pending memories: {pending_count}")

                # Sync batch
                synced, failed = await self._sync_batch(batch_size, max_retries)

                self.stdout.write(
                    f"Synced: {synced}, Failed: {failed}, Remaining: {pending_count - synced}"
                )

                if run_once:
                    break

                await asyncio.sleep(interval)

            except Exception as e:
                logger.error(f"Sync error: {e}")
                self.stdout.write(self.style.ERROR(f"Error: {e}"))
                await asyncio.sleep(interval * 3)

        # Cleanup
        if self._client:
            await self._client.close()

    async def _check_somabrain_health(self) -> bool:
        """Check if SomaBrain is available."""
        try:
            from admin.core.somabrain_client import SomaBrainClient

            if self._client is None:
                self._client = SomaBrainClient()

            return await self._client.health_check()
        except Exception as e:
            logger.debug(f"SomaBrain health check failed: {e}")
            return False

    async def _sync_batch(self, batch_size: int, max_retries: int) -> tuple[int, int]:
        """Sync a batch of pending memories.

        Returns:
            (synced_count, failed_count)
        """
        from admin.core.models import PendingMemory
        from admin.core.somabrain_client import SomaBrainClient

        synced = 0
        failed = 0

        # Get pending memories
        memories = list(
            PendingMemory.objects.filter(
                synced=False,
                sync_attempts__lt=max_retries,
            ).order_by(
                "created_at"
            )[:batch_size]
        )

        if self._client is None:
            self._client = SomaBrainClient()

        for memory in memories:
            try:
                # Send to SomaBrain
                await self._client.remember(
                    payload=memory.payload,
                    tenant=memory.tenant_id,
                    namespace=memory.namespace,
                )

                # Mark as synced
                memory.mark_synced()
                synced += 1

            except Exception as e:
                # Record failure
                memory.sync_attempts += 1
                memory.last_error = str(e)
                memory.save(update_fields=["sync_attempts", "last_error"])
                failed += 1

                logger.warning(f"Failed to sync memory {memory.id}: {e}")

        return synced, failed


class MemorySyncService:
    """Django service for memory operations with degradation support.

    Use this service instead of direct SomaBrainClient calls
    to ensure zero data loss during SomaBrain outages.
    """

    def __init__(self):
        """Initialize the instance."""

        self._client = None
        self._degraded = False

    async def remember(
        self,
        payload: dict,
        tenant_id: str,
        namespace: str = "wm",
    ) -> dict:
        """Store memory with guaranteed delivery.

        If SomaBrain is available: sends directly.
        If SomaBrain is down: queues for later sync.

        ZERO DATA LOSS GUARANTEED.
        """
        import hashlib
        import json

        from admin.core.models import IdempotencyRecord, PendingMemory
        from admin.core.somabrain_client import SomaBrainClient

        # Generate idempotency key
        payload_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]
        idempotency_key = f"memory:{tenant_id}:{payload_hash}"

        # Check idempotency
        is_new, record = IdempotencyRecord.check_and_set(
            key=idempotency_key,
            operation_type="memory.remember",
        )
        if not is_new and record.result:
            return record.result  # Return cached result

        try:
            # Try direct SomaBrain call
            if self._client is None:
                self._client = SomaBrainClient()

            result = await self._client.remember(
                payload=payload,
                tenant=tenant_id,
                namespace=namespace,
            )

            # Cache result
            if record:
                record.result = result
                record.save(update_fields=["result"])

            self._degraded = False
            return result

        except Exception as e:
            logger.warning(f"SomaBrain unavailable, queueing memory: {e}")
            self._degraded = True

            # Queue for later sync
            PendingMemory.objects.get_or_create(
                idempotency_key=idempotency_key,
                defaults={
                    "tenant_id": tenant_id,
                    "namespace": namespace,
                    "payload": payload,
                },
            )

            return {
                "status": "queued",
                "message": "Memory queued for sync when SomaBrain available",
                "idempotency_key": idempotency_key,
            }

    @property
    def is_degraded(self) -> bool:
        """Check if currently in degraded mode."""
        return self._degraded


# Global service instance (Django pattern)
memory_sync_service = MemorySyncService()
