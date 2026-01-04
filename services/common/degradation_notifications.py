"""Centralized Degradation Notification Service.

Django + Kafka based notification system for degradation alerts.
All services report health → centralized monitor → Kafka events → notifications.


"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Awaitable

from django.db import models, transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    """Available notification channels."""

    KAFKA = "kafka"
    DATABASE = "database"
    WEBHOOK = "webhook"
    LOG = "log"


class NotificationSeverity(Enum):
    """Notification severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    RECOVERY = "recovery"


@dataclass
class DegradationEvent:
    """A degradation event to be notified."""

    component: str
    old_status: str
    new_status: str
    severity: NotificationSeverity
    message: str
    details: Dict[str, Any]
    timestamp: float


class DegradationNotificationService:
    """Centralized service for degradation notifications.

    Receives degradation events from DegradationMonitor and:
    1. Stores in Django ORM (DegradationNotification model)
    2. Publishes to Kafka topic (degradation.events)
    3. Calls registered webhook callbacks
    4. Logs to structured logger

    Usage:
        service = DegradationNotificationService()
        await service.initialize()

        # Notify degradation
        await service.notify(
            component="somabrain",
            old_status="healthy",
            new_status="unavailable",
            severity=NotificationSeverity.CRITICAL,
            message="SomaBrain connection failed",
            details={"error": "Connection refused"}
        )
    """

    KAFKA_TOPIC = "degradation.events"

    def __init__(self):
        self._producer = None
        self._initialized = False
        self._channels: List[NotificationChannel] = [
            NotificationChannel.DATABASE,
            NotificationChannel.KAFKA,
            NotificationChannel.LOG,
        ]
        self._webhook_callbacks: List[Callable[[DegradationEvent], Awaitable[None]]] = []
        self._suppression_window = timedelta(minutes=5)  # Prevent alert storms
        self._last_notifications: Dict[str, float] = {}  # component -> timestamp

    async def initialize(self):
        """Initialize the notification service."""
        if self._initialized:
            return

        # Initialize Kafka producer
        try:
            await self._init_kafka_producer()
        except Exception as e:
            logger.warning(
                f"Kafka producer not available: {e}. Notifications will use database only."
            )

        self._initialized = True
        logger.info("DegradationNotificationService initialized")

    async def _init_kafka_producer(self):
        """Initialize Kafka producer."""
        from aiokafka import AIOKafkaProducer
        from django.conf import settings
        import os

        bootstrap_servers = getattr(
            settings,
            "KAFKA_BOOTSTRAP_SERVERS",
            os.environ.get("SA01_KAFKA_BOOTSTRAP_SERVERS", "localhost:20092"),
        )

        self._producer = AIOKafkaProducer(
            bootstrap_servers=bootstrap_servers,
            enable_idempotence=True,
            acks="all",
        )
        await self._producer.start()
        logger.info(f"Kafka producer connected: {bootstrap_servers}")

    async def close(self):
        """Close the notification service."""
        if self._producer:
            await self._producer.stop()
            self._producer = None
        self._initialized = False

    def add_webhook(self, callback: Callable[[DegradationEvent], Awaitable[None]]):
        """Register a webhook callback for notifications."""
        self._webhook_callbacks.append(callback)
        if NotificationChannel.WEBHOOK not in self._channels:
            self._channels.append(NotificationChannel.WEBHOOK)

    def set_channels(self, channels: List[NotificationChannel]):
        """Configure which notification channels to use."""
        self._channels = channels

    async def notify(
        self,
        component: str,
        old_status: str,
        new_status: str,
        severity: NotificationSeverity,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Send a degradation notification.

        Args:
            component: Name of the affected component
            old_status: Previous status
            new_status: New status
            severity: Notification severity
            message: Human-readable message
            details: Additional details dict

        Returns:
            True if notification was sent, False if suppressed
        """
        import time

        # Check suppression window
        last_time = self._last_notifications.get(component, 0)
        now = time.time()

        if now - last_time < self._suppression_window.total_seconds():
            if severity != NotificationSeverity.CRITICAL:  # Always send critical
                logger.debug(f"Notification suppressed for {component} (within window)")
                return False

        # Create event
        event = DegradationEvent(
            component=component,
            old_status=old_status,
            new_status=new_status,
            severity=severity,
            message=message,
            details=details or {},
            timestamp=now,
        )

        # Update suppression tracker
        self._last_notifications[component] = now

        # Send to all configured channels
        success = True

        for channel in self._channels:
            try:
                if channel == NotificationChannel.DATABASE:
                    await self._notify_database(event)
                elif channel == NotificationChannel.KAFKA:
                    await self._notify_kafka(event)
                elif channel == NotificationChannel.WEBHOOK:
                    await self._notify_webhooks(event)
                elif channel == NotificationChannel.LOG:
                    self._notify_log(event)
            except Exception as e:
                logger.error(f"Notification failed for channel {channel.value}: {e}")
                success = False

        return success

    @transaction.atomic
    async def _notify_database(self, event: DegradationEvent):
        """Store notification in Django ORM."""
        from admin.core.models import OutboxMessage

        # Create notification record via outbox pattern for guaranteed delivery
        OutboxMessage.objects.create(
            idempotency_key=f"degradation:{event.component}:{int(event.timestamp)}",
            topic=self.KAFKA_TOPIC,
            partition_key=event.component,
            payload={
                "component": event.component,
                "old_status": event.old_status,
                "new_status": event.new_status,
                "severity": event.severity.value,
                "message": event.message,
                "details": event.details,
                "timestamp": event.timestamp,
            },
            headers={
                "event_type": "degradation",
                "severity": event.severity.value,
            },
        )

        logger.debug(f"Notification stored in database: {event.component}")

    async def _notify_kafka(self, event: DegradationEvent):
        """Publish notification to Kafka."""
        if not self._producer:
            return

        payload = json.dumps(
            {
                "component": event.component,
                "old_status": event.old_status,
                "new_status": event.new_status,
                "severity": event.severity.value,
                "message": event.message,
                "details": event.details,
                "timestamp": event.timestamp,
            }
        ).encode()

        await self._producer.send_and_wait(
            topic=self.KAFKA_TOPIC,
            key=event.component.encode(),
            value=payload,
            headers=[
                ("event_type", b"degradation"),
                ("severity", event.severity.value.encode()),
            ],
        )

        logger.debug(f"Notification sent to Kafka: {event.component}")

    async def _notify_webhooks(self, event: DegradationEvent):
        """Call registered webhook callbacks."""
        for callback in self._webhook_callbacks:
            try:
                await callback(event)
            except Exception as e:
                logger.error(f"Webhook callback failed: {e}")

    def _notify_log(self, event: DegradationEvent):
        """Log notification to structured logger."""
        log_data = {
            "event": "degradation",
            "component": event.component,
            "old_status": event.old_status,
            "new_status": event.new_status,
            "severity": event.severity.value,
            "message": event.message,
        }

        if event.severity == NotificationSeverity.CRITICAL:
            logger.critical(f"DEGRADATION: {json.dumps(log_data)}")
        elif event.severity == NotificationSeverity.WARNING:
            logger.warning(f"DEGRADATION: {json.dumps(log_data)}")
        elif event.severity == NotificationSeverity.RECOVERY:
            logger.info(f"RECOVERY: {json.dumps(log_data)}")
        else:
            logger.info(f"DEGRADATION: {json.dumps(log_data)}")

    async def get_recent_notifications(
        self,
        component: Optional[str] = None,
        severity: Optional[NotificationSeverity] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get recent notifications from database.

        Uses OutboxMessage as the source of truth.
        """
        from admin.core.models import OutboxMessage

        queryset = OutboxMessage.objects.filter(topic=self.KAFKA_TOPIC)

        if component:
            queryset = queryset.filter(partition_key=component)

        if severity:
            queryset = queryset.filter(headers__severity=severity.value)

        notifications = []
        for msg in queryset.order_by("-created_at")[:limit]:
            notifications.append(
                {
                    "id": str(msg.id),
                    "component": msg.partition_key,
                    "status": msg.status,
                    "payload": msg.payload,
                    "created_at": msg.created_at.isoformat(),
                }
            )

        return notifications


# Global singleton instance
degradation_notification_service = DegradationNotificationService()


# Integration with DegradationMonitor
async def notify_degradation_change(
    component: str,
    old_level: str,
    new_level: str,
    healthy: bool,
    error_message: Optional[str] = None,
):
    """Helper function to notify degradation changes.

    Called by DegradationMonitor when component status changes.
    """
    # Determine severity
    if new_level == "critical":
        severity = NotificationSeverity.CRITICAL
    elif new_level == "severe":
        severity = NotificationSeverity.CRITICAL
    elif new_level == "moderate":
        severity = NotificationSeverity.WARNING
    elif new_level == "minor":
        severity = NotificationSeverity.WARNING
    elif new_level == "none" and old_level != "none":
        severity = NotificationSeverity.RECOVERY
    else:
        severity = NotificationSeverity.INFO

    # Generate message
    if severity == NotificationSeverity.RECOVERY:
        message = f"{component} has recovered from {old_level} to healthy"
    else:
        message = f"{component} degraded from {old_level} to {new_level}"

    # Initialize service if needed
    if not degradation_notification_service._initialized:
        await degradation_notification_service.initialize()

    # Send notification
    await degradation_notification_service.notify(
        component=component,
        old_status=old_level,
        new_status=new_level,
        severity=severity,
        message=message,
        details={
            "healthy": healthy,
            "error": error_message,
        },
    )
