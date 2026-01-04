"""Outbox Publisher Django Management Command.

Run the transactional outbox publisher as a Django worker.

Usage:
    python manage.py publish_outbox --batch-size=100 --interval=1


"""

from __future__ import annotations

import asyncio
import logging
import signal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Publish pending outbox messages to Kafka.

    Django Management Command pattern for background workers.
    """

    help = "Publish pending outbox messages to Kafka with exactly-once semantics"

    def __init__(self, *args, **kwargs):
        """Initialize the instance."""

        super().__init__(*args, **kwargs)
        self._running = True
        self._producer = None

    def add_arguments(self, parser):
        """Execute add arguments.

            Args:
                parser: The parser.
            """

        parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
            help="Number of messages to process per batch (default: 100)",
        )
        parser.add_argument(
            "--interval",
            type=float,
            default=1.0,
            help="Seconds between polling (default: 1.0)",
        )
        parser.add_argument(
            "--once",
            action="store_true",
            help="Run once and exit (useful for cron)",
        )

    def handle(self, *args, **options):
        """Main command entrypoint."""
        batch_size = options["batch_size"]
        interval = options["interval"]
        run_once = options["once"]

        self.stdout.write(
            self.style.SUCCESS(
                f"Starting Outbox Publisher (batch={batch_size}, interval={interval}s)"
            )
        )

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        try:
            asyncio.run(self._run_publisher(batch_size, interval, run_once))
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Shutting down..."))
        finally:
            self.stdout.write(self.style.SUCCESS("Outbox Publisher stopped"))

    def _handle_signal(self, signum, frame):
        """Handle shutdown signals."""
        self._running = False
        self.stdout.write(self.style.WARNING(f"Received signal {signum}, shutting down..."))

    async def _run_publisher(self, batch_size: int, interval: float, run_once: bool):
        """Main publisher loop."""
        from admin.core.models import OutboxMessage

        # Initialize Kafka producer
        await self._init_producer()

        while self._running:
            try:
                published, failed = await self._publish_batch(batch_size)

                if published > 0 or failed > 0:
                    self.stdout.write(
                        f"Published: {published}, Failed: {failed}, "
                        f"Pending: {OutboxMessage.objects.filter(status=OutboxMessage.Status.PENDING).count()}"
                    )

                if run_once:
                    break

                await asyncio.sleep(interval)

            except Exception as e:
                logger.error(f"Publisher error: {e}")
                self.stdout.write(self.style.ERROR(f"Error: {e}"))
                await asyncio.sleep(interval * 5)  # Back off on errors

        # Cleanup
        await self._close_producer()

    async def _init_producer(self):
        """Initialize Kafka producer with exactly-once semantics."""
        try:
            import os

            from aiokafka import AIOKafkaProducer
            from django.conf import settings

            bootstrap_servers = getattr(
                settings,
                "KAFKA_BOOTSTRAP_SERVERS",
                os.environ.get("SA01_KAFKA_BOOTSTRAP_SERVERS", "localhost:20092"),
            )

            self._producer = AIOKafkaProducer(
                bootstrap_servers=bootstrap_servers,
                enable_idempotence=True,  # EXACTLY-ONCE
                acks="all",
                retries=5,
                max_in_flight_requests_per_connection=1,
            )
            await self._producer.start()
            self.stdout.write(self.style.SUCCESS(f"Connected to Kafka: {bootstrap_servers}"))
        except Exception as e:
            logger.warning(f"Kafka not available: {e}. Running in degraded mode.")
            self._producer = None

    async def _close_producer(self):
        """Close Kafka producer."""
        if self._producer:
            await self._producer.stop()
            self._producer = None

    @transaction.atomic
    async def _publish_batch(self, batch_size: int) -> tuple[int, int]:
        """Publish a batch of pending messages.

        Uses SELECT FOR UPDATE SKIP LOCKED for concurrent-safe processing.

        Returns:
            (published_count, failed_count)
        """
        from admin.core.models import OutboxMessage

        published = 0
        failed = 0

        # Get pending messages with row-level lock
        messages = list(
            OutboxMessage.objects.select_for_update(skip_locked=True)
            .filter(
                status__in=[OutboxMessage.Status.PENDING, OutboxMessage.Status.FAILED],
            )
            .filter(
                # Only get messages ready for retry
                models.Q(next_retry_at__isnull=True)
                | models.Q(next_retry_at__lte=timezone.now())
            )
            .order_by("created_at")[:batch_size]
        )

        for message in messages:
            try:
                await self._publish_message(message)
                message.mark_published()
                published += 1
            except Exception as e:
                error_str = str(e)
                message.mark_failed(error_str)
                failed += 1

                # Move to DLQ if max attempts reached
                if message.status == OutboxMessage.Status.DEAD:
                    await self._move_to_dlq(message, error_str)

        return published, failed

    async def _publish_message(self, message):
        """Publish a single message to Kafka."""
        import json

        if self._producer is None:
            raise RuntimeError("Kafka producer not available")

        # Prepare message
        key = message.partition_key.encode() if message.partition_key else None
        value = json.dumps(message.payload).encode()
        headers = [(k, v.encode() if isinstance(v, str) else v) for k, v in message.headers.items()]

        # Add idempotency key to headers
        headers.append(("idempotency_key", message.idempotency_key.encode()))

        # Send to Kafka
        await self._producer.send_and_wait(
            topic=message.topic,
            key=key,
            value=value,
            headers=headers,
        )

    async def _move_to_dlq(self, message, error: str):
        """Move failed message to Dead Letter Queue."""
        from admin.core.models import DeadLetterMessage

        DeadLetterMessage.objects.create(
            original_outbox_id=message.id,
            original_topic=message.topic,
            idempotency_key=message.idempotency_key,
            payload=message.payload,
            headers=message.headers,
            error_message=error,
            error_type=type(error).__name__ if isinstance(error, Exception) else "Unknown",
            attempts=message.attempts,
            original_created_at=message.created_at,
        )

        self.stdout.write(
            self.style.ERROR(f"Moved to DLQ: {message.topic} ({message.idempotency_key})")
        )


# Import models for Q object
from django.db import models