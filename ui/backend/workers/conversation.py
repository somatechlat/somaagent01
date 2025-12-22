"""
Conversation Worker - Kafka Consumer
Per CANONICAL_DESIGN.md Section 2.1

VIBE COMPLIANT:
- Real Kafka consumer
- ProcessMessageUseCase integration
- SomaBrain memory storage
- Error handling with DLQ

Flow:
  Gateway → Kafka: conversation.inbound → ConversationWorker
    → ProcessMessageUseCase
    → GenerateResponseUseCase  
    → StoreMemoryUseCase (SomaBrain)
    → Kafka: conversation.outbound
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Callable
from uuid import uuid4

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.errors import KafkaError

LOGGER = logging.getLogger(__name__)


@dataclass
class ConversationMessage:
    """Inbound conversation message from Kafka."""
    message_id: str
    session_id: str
    tenant_id: str
    user_id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ConversationResponse:
    """Outbound response to Kafka."""
    message_id: str
    session_id: str
    tenant_id: str
    content: str
    confidence: Optional[float] = None
    tokens_used: int = 0
    model: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConversationWorker:
    """
    Kafka consumer for conversation.inbound topic.
    
    Processes messages through the conversation pipeline:
    1. Deserialize message
    2. Build context (ContextBuilder)
    3. Generate response (LLM)
    4. Store memory (SomaBrain)
    5. Publish response (conversation.outbound)
    """
    
    def __init__(
        self,
        kafka_brokers: Optional[str] = None,
        consumer_group: str = "conversation-worker",
        input_topic: str = "conversation.inbound",
        output_topic: str = "conversation.outbound",
        dlq_topic: str = "dlq.events",
    ):
        self.kafka_brokers = kafka_brokers or os.getenv(
            "KAFKA_BROKERS", "localhost:9092"
        )
        self.consumer_group = consumer_group
        self.input_topic = input_topic
        self.output_topic = output_topic
        self.dlq_topic = dlq_topic
        
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._producer: Optional[AIOKafkaProducer] = None
        self._running = False
        
        # Handlers - inject real implementations
        self._message_handler: Optional[Callable] = None
        self._memory_handler: Optional[Callable] = None
    
    def set_message_handler(self, handler: Callable):
        """Set the message processing handler (ProcessMessageUseCase)."""
        self._message_handler = handler
    
    def set_memory_handler(self, handler: Callable):
        """Set the memory storage handler (SomaBrain client)."""
        self._memory_handler = handler
    
    async def start(self):
        """Start the Kafka consumer."""
        LOGGER.info(f"Starting ConversationWorker on {self.kafka_brokers}")
        
        self._consumer = AIOKafkaConsumer(
            self.input_topic,
            bootstrap_servers=self.kafka_brokers,
            group_id=self.consumer_group,
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        )
        
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self.kafka_brokers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            acks="all",
            enable_idempotence=True,
        )
        
        await self._consumer.start()
        await self._producer.start()
        self._running = True
        
        LOGGER.info(f"ConversationWorker started, consuming from {self.input_topic}")
    
    async def stop(self):
        """Stop the Kafka consumer gracefully."""
        LOGGER.info("Stopping ConversationWorker...")
        self._running = False
        
        if self._consumer:
            await self._consumer.stop()
        if self._producer:
            await self._producer.stop()
        
        LOGGER.info("ConversationWorker stopped")
    
    async def run(self):
        """Main consumer loop."""
        if not self._running:
            await self.start()
        
        try:
            async for msg in self._consumer:
                try:
                    await self._process_message(msg)
                    await self._consumer.commit()
                except Exception as e:
                    LOGGER.error(f"Error processing message: {e}")
                    await self._send_to_dlq(msg, str(e))
                    await self._consumer.commit()
        except asyncio.CancelledError:
            LOGGER.info("ConversationWorker cancelled")
        finally:
            await self.stop()
    
    async def _process_message(self, msg):
        """Process a single conversation message."""
        data = msg.value
        
        message = ConversationMessage(
            message_id=data.get("message_id", str(uuid4())),
            session_id=data["session_id"],
            tenant_id=data["tenant_id"],
            user_id=data["user_id"],
            content=data["content"],
            metadata=data.get("metadata", {}),
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
        )
        
        LOGGER.info(f"Processing message {message.message_id} for session {message.session_id}")
        
        # Step 1: Process message through handler
        response_content = ""
        confidence = None
        tokens_used = 0
        model = ""
        
        if self._message_handler:
            result = await self._message_handler(
                content=message.content,
                session_id=message.session_id,
                tenant_id=message.tenant_id,
                user_id=message.user_id,
                metadata=message.metadata,
            )
            response_content = result.get("content", "")
            confidence = result.get("confidence")
            tokens_used = result.get("tokens_used", 0)
            model = result.get("model", "")
        else:
            # Default echo for testing
            response_content = f"Echo: {message.content}"
        
        # Step 2: Store to SomaBrain memory
        if self._memory_handler:
            await self._memory_handler(
                tenant_id=message.tenant_id,
                agent_id=message.session_id,
                content=f"User: {message.content}\nAssistant: {response_content}",
                memory_type="episodic",
                metadata={
                    "message_id": message.message_id,
                    "user_id": message.user_id,
                    "model": model,
                    "confidence": confidence,
                },
            )
        
        # Step 3: Publish response
        response = ConversationResponse(
            message_id=str(uuid4()),
            session_id=message.session_id,
            tenant_id=message.tenant_id,
            content=response_content,
            confidence=confidence,
            tokens_used=tokens_used,
            model=model,
            metadata={"in_reply_to": message.message_id},
        )
        
        await self._producer.send_and_wait(
            self.output_topic,
            value={
                "message_id": response.message_id,
                "session_id": response.session_id,
                "tenant_id": response.tenant_id,
                "content": response.content,
                "confidence": response.confidence,
                "tokens_used": response.tokens_used,
                "model": response.model,
                "metadata": response.metadata,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
        
        LOGGER.info(f"Published response {response.message_id} to {self.output_topic}")
    
    async def _send_to_dlq(self, msg, error: str):
        """Send failed message to dead letter queue."""
        if self._producer:
            await self._producer.send_and_wait(
                self.dlq_topic,
                value={
                    "original_topic": self.input_topic,
                    "original_message": msg.value,
                    "error": error,
                    "timestamp": datetime.utcnow().isoformat(),
                    "partition": msg.partition,
                    "offset": msg.offset,
                },
            )
            LOGGER.warning(f"Message sent to DLQ: {error}")


# Entry point for standalone worker
async def main():
    """Run the conversation worker standalone."""
    logging.basicConfig(level=logging.INFO)
    
    worker = ConversationWorker()
    
    try:
        await worker.run()
    except KeyboardInterrupt:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
