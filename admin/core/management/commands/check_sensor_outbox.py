"""Management command to check sensor outbox health and scaling status.

Reports pending event counts and recommends scale-up when thresholds are exceeded.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand

from admin.core.sensors.outbox import SensorOutbox


class Command(BaseCommand):
    """Check sensor outbox health status."""

    help = "Report sensor outbox pending counts and health status"

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "--target-service",
            type=str,
            default="somabrain",
            help="Target service to check (default: somabrain)",
        )
        parser.add_argument(
            "--threshold",
            type=int,
            default=1000,
            help="Pending count threshold for scale-up warning (default: 1000)",
        )

    def handle(self, *args, **options):
        """Execute the command."""
        from django.db import DatabaseError

        target_service = options["target_service"]
        threshold = options["threshold"]

        try:
            total_pending = SensorOutbox.objects.filter(
                synced=False,
                dead_letter=False,
            ).count()

            service_pending = SensorOutbox.get_pending_count(target_service)
            dead_letter_count = SensorOutbox.get_dead_letter_count()
            health = SensorOutbox.check_scaling_threshold(target_service, threshold)
        except DatabaseError as exc:
            self.stdout.write(self.style.ERROR(f"Database unavailable: {exc}"))
            return

        self.stdout.write("=" * 50)
        self.stdout.write("Sensor Outbox Health Report")
        self.stdout.write("=" * 50)
        self.stdout.write(f"Target service:       {target_service}")
        self.stdout.write(f"Total pending:        {total_pending}")
        self.stdout.write(f"Service pending:      {service_pending}")
        self.stdout.write(f"Dead letter count:    {dead_letter_count}")
        self.stdout.write(f"Scale-up threshold:   {threshold}")
        self.stdout.write(f"Recommend scale-up:   {health['recommend_scale_up']}")
        self.stdout.write("=" * 50)

        if health["recommend_scale_up"]:
            self.stdout.write(
                self.style.WARNING(
                    f"WARNING: Pending outbox count ({service_pending}) exceeds threshold "
                    f"({threshold}). Scale up outbox workers to prevent backlog."
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS("Outbox health: OK"))
