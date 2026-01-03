"""Django Management Command: run_sync_worker.

VIBE COMPLIANT - Django pattern for background tasks.
Syncs SensorOutbox to SomaBrain with ZDL guarantees.

Usage:
    python manage.py run_sync_worker
    python manage.py run_sync_worker --interval=10 --batch-size=100
"""

import asyncio
import logging

from django.core.management.base import BaseCommand

from admin.core.sensors.sync_worker import sync_worker_loop

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Run the SensorOutbox sync worker."""

    help = "Run the sensor outbox sync worker (SomaBrain integration)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--interval",
            type=int,
            default=5,
            help="Polling interval in seconds (default: 5)",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=50,
            help="Batch size for each sync (default: 50)",
        )

    def handle(self, *args, **options):
        interval = options["interval"]
        batch_size = options["batch_size"]

        self.stdout.write(
            self.style.SUCCESS(
                f"Starting sync worker (interval={interval}s, batch_size={batch_size})"
            )
        )

        try:
            asyncio.run(
                sync_worker_loop(
                    interval_seconds=interval,
                    batch_size=batch_size,
                )
            )
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Sync worker stopped"))
