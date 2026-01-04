"""Django Management Command: run_conversation_worker.


Replaces: services/conversation_worker/main.py (FastAPI container)

Usage:
    python manage.py run_conversation_worker
    python manage.py run_conversation_worker --consumer-group=my-group
"""

import asyncio
import logging

from django.conf import settings
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Run the conversation worker (Kafka consumer)."""

    help = "Run the conversation worker (Kafka consumer for message processing)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--consumer-group",
            type=str,
            default="conversation-worker",
            help="Kafka consumer group ID (default: conversation-worker)",
        )
        parser.add_argument(
            "--topic",
            type=str,
            default="soma.conversation.requests",
            help="Kafka topic to consume from",
        )

    def handle(self, *args, **options):
        consumer_group = options["consumer_group"]
        topic = options["topic"]

        self.stdout.write(
            self.style.SUCCESS(
                f"Starting conversation worker (group={consumer_group}, topic={topic})"
            )
        )

        try:
            asyncio.run(self._run_worker(consumer_group, topic))
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Conversation worker stopped"))

    async def _run_worker(self, consumer_group: str, topic: str):
        """Run the Kafka consumer loop."""
        import json

        from confluent_kafka import Consumer, KafkaError

        kafka_bootstrap = getattr(settings, "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

        config = {
            "bootstrap.servers": kafka_bootstrap,
            "group.id": consumer_group,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": True,
        }

        consumer = Consumer(config)
        consumer.subscribe([topic])

        logger.info(f"Consuming from {topic} on {kafka_bootstrap}")

        try:
            while True:
                msg = consumer.poll(timeout=1.0)

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    logger.error(f"Kafka error: {msg.error()}")
                    continue

                try:
                    event = json.loads(msg.value().decode("utf-8"))
                    await self._handle_message(event)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")

        finally:
            consumer.close()

    async def _handle_message(self, event: dict):
        """Handle a conversation message.

        Delegates to Django-based use cases.
        """
        from admin.core.sensors import ConversationSensor

        session_id = event.get("session_id")
        tenant_id = event.get("tenant_id", "default")
        message = event.get("message", {})

        # Capture event via sensor (ZDL pattern)
        sensor = ConversationSensor(tenant_id=tenant_id)
        sensor.capture_message_received(
            session_id=session_id,
            message=message,
            metadata={"source": "kafka"},
        )

        logger.info(f"Processed message for session {session_id}")

        # Generate response via ChatService
        try:
            from services.common.chat_service import ChatService

            chat_service = ChatService()
            response = await chat_service.generate_response(
                conversation_id=session_id,
                message_content=message.get("content", ""),
                user_id=event.get("user_id"),
                tenant_id=tenant_id,
            )
            logger.debug(f"Response generated for session {session_id}")
        except Exception as e:
            logger.error(f"Failed to generate response for session {session_id}: {e}")
            response = None

        return {"status": "processed", "session_id": session_id, "response": response}
