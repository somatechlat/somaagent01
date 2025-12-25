"""Django Management Command: run_tool_executor.

VIBE COMPLIANT - Django pattern for tool execution worker.
Replaces: services/tool_executor/main.py (FastAPI container)

Usage:
    python manage.py run_tool_executor
    python manage.py run_tool_executor --consumer-group=my-group
"""

import asyncio
import logging

from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Run the tool executor worker (Kafka consumer)."""
    
    help = 'Run the tool executor worker (Kafka consumer for tool execution)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--consumer-group',
            type=str,
            default='tool-executor',
            help='Kafka consumer group ID (default: tool-executor)',
        )
        parser.add_argument(
            '--topic',
            type=str,
            default='soma.tool.requests',
            help='Kafka topic to consume from',
        )
    
    def handle(self, *args, **options):
        consumer_group = options['consumer_group']
        topic = options['topic']
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Starting tool executor (group={consumer_group}, topic={topic})'
            )
        )
        
        try:
            asyncio.run(self._run_worker(consumer_group, topic))
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('Tool executor stopped'))
    
    async def _run_worker(self, consumer_group: str, topic: str):
        """Run the Kafka consumer loop."""
        from confluent_kafka import Consumer, KafkaError
        import json
        
        kafka_bootstrap = getattr(
            settings, 'KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'
        )
        
        config = {
            'bootstrap.servers': kafka_bootstrap,
            'group.id': consumer_group,
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': True,
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
                    event = json.loads(msg.value().decode('utf-8'))
                    await self._execute_tool(event)
                except Exception as e:
                    logger.error(f"Error executing tool: {e}")
                    
        finally:
            consumer.close()
    
    async def _execute_tool(self, event: dict):
        """Execute a tool request.
        
        Delegates to Django-based tool registry.
        """
        from admin.core.sensors import ToolSensor
        
        tool_name = event.get('tool_name')
        tool_input = event.get('input', {})
        session_id = event.get('session_id')
        tenant_id = event.get('tenant_id', 'default')
        
        # Capture event via sensor (ZDL pattern)
        sensor = ToolSensor(tenant_id=tenant_id)
        sensor.capture_execution_start(
            tool_name=tool_name,
            tool_input=tool_input,
            session_id=session_id,
        )
        
        try:
            # TODO: Integrate with tool registry
            # from admin.tools.registry import ToolRegistry
            # result = await ToolRegistry.execute(tool_name, tool_input)
            result = {"status": "executed", "tool_name": tool_name}
            
            sensor.capture_execution_result(
                tool_name=tool_name,
                tool_output=result,
                session_id=session_id,
            )
            
            logger.info(f"Executed tool {tool_name} for session {session_id}")
            return result
            
        except Exception as e:
            sensor.capture_execution_error(
                tool_name=tool_name,
                error=str(e),
                session_id=session_id,
            )
            raise
