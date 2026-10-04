"""Drain the outbox into Kafka.

``admin.core.signals`` writes ``OutboxMessage`` rows on every conversation,
memory and tool event. Nothing published them: the row was a durable record
that never left Postgres, so the Kafka consumers downstream (conversation
worker, tool executor, memory replicator) never saw live traffic.

This command is the missing half of the transactional outbox. It is safe to
run alongside the app and safe to run twice: a row is marked published only
after the broker accepted it, and the dedupe key is stable per row.
"""

from __future__ import annotations

import asyncio

from django.core.management.base import BaseCommand

from admin.core.models.zdl import OutboxMessage


class Command(BaseCommand):
    help = "Publish pending OutboxMessage rows to Kafka and mark them published."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--batch",
            type=int,
            default=100,
            help="Maximum rows to publish in one run.",
        )
        parser.add_argument(
            "--once",
            action="store_true",
            help="Drain the current backlog and exit (default: also exit).",
        )

    def handle(self, *args, **options) -> None:
        batch = int(options["batch"])
        published, failed = asyncio.run(self._drain(batch))
        self.stdout.write(
            self.style.SUCCESS(f"outbox: published={published} failed={failed}")
        )
        if failed:
            raise SystemExit(1)

    async def _drain(self, batch: int) -> tuple[int, int]:
        from django.db.models import Q
        from django.utils import timezone

        from services.common.event_bus import KafkaEventBus

        now = timezone.now()
        pending = list(
            OutboxMessage.objects.filter(
                status__in=[OutboxMessage.Status.PENDING, OutboxMessage.Status.FAILED],
            )
            .filter(Q(next_retry_at__isnull=True) | Q(next_retry_at__lte=now))
            .order_by("created_at")[:batch]
        )
        if not pending:
            return 0, 0

        bus = KafkaEventBus()
        published = 0
        failed = 0
        for row in pending:
            headers = dict(row.headers or {})
            if row.idempotency_key:
                headers.setdefault("idempotency_key", row.idempotency_key)
            try:
                # KafkaEventBus.publish(topic, payload, headers=...) — the real
                # signature. Dedupe is carried in headers, not a phantom kwarg.
                await bus.publish(row.topic, row.payload, headers=headers)
            except Exception as exc:
                failed += 1
                row.mark_failed(str(exc))
                self.stderr.write(
                    self.style.WARNING(f"outbox {row.pk} -> {row.topic}: {exc}")
                )
                continue
            row.mark_published()
            published += 1
        return published, failed
