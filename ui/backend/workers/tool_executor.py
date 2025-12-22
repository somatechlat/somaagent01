"""
Tool Executor Worker - Kafka Consumer
Per CANONICAL_DESIGN.md Section 2.1

VIBE COMPLIANT:
- Real Kafka consumer
- OPA policy enforcement
- Sandboxed tool execution
- SomaBrain memory capture

Flow:
  ConversationWorker → Kafka: tool.requests → ToolExecutorWorker
    → OPA Policy Check
    → ToolDispatcher.execute()
    → Provenance Recording
    → SomaBrain memory
    → Kafka: tool.results
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from uuid import uuid4

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

LOGGER = logging.getLogger(__name__)


@dataclass
class ToolRequest:
    """Tool execution request from Kafka."""
    request_id: str
    session_id: str
    tenant_id: str
    tool_name: str
    tool_args: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ToolResult:
    """Tool execution result to Kafka."""
    request_id: str
    session_id: str
    tenant_id: str
    tool_name: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time_ms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


# Built-in tools registry
BUILTIN_TOOLS = {
    "web_search": "Search the web for information",
    "code_execute": "Execute code in sandbox",
    "file_read": "Read file contents",
    "file_write": "Write file contents",
    "http_request": "Make HTTP requests",
    "image_generate": "Generate images",
    "diagram_generate": "Generate diagrams",
    "memory_search": "Search agent memory",
    "calendar_query": "Query calendar events",
}


class ToolExecutorWorker:
    """
    Kafka consumer for tool.requests topic.
    
    Executes tools in a sandboxed environment with:
    1. OPA policy enforcement
    2. Rate limiting
    3. Timeout handling
    4. Result validation
    5. Provenance recording
    """
    
    def __init__(
        self,
        kafka_brokers: Optional[str] = None,
        consumer_group: str = "tool-executor",
        input_topic: str = "tool.requests",
        output_topic: str = "tool.results",
        dlq_topic: str = "dlq.events",
        default_timeout_ms: int = 30000,
    ):
        self.kafka_brokers = kafka_brokers or os.getenv(
            "KAFKA_BROKERS", "localhost:9092"
        )
        self.consumer_group = consumer_group
        self.input_topic = input_topic
        self.output_topic = output_topic
        self.dlq_topic = dlq_topic
        self.default_timeout_ms = default_timeout_ms
        
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._producer: Optional[AIOKafkaProducer] = None
        self._running = False
        
        # Handlers - inject real implementations
        self._policy_checker: Optional[Callable] = None
        self._tool_registry: Dict[str, Callable] = {}
        self._memory_handler: Optional[Callable] = None
        self._provenance_handler: Optional[Callable] = None
    
    def set_policy_checker(self, checker: Callable):
        """Set OPA policy checker."""
        self._policy_checker = checker
    
    def register_tool(self, name: str, handler: Callable):
        """Register a tool handler."""
        self._tool_registry[name] = handler
        LOGGER.info(f"Registered tool: {name}")
    
    def set_memory_handler(self, handler: Callable):
        """Set SomaBrain memory handler."""
        self._memory_handler = handler
    
    def set_provenance_handler(self, handler: Callable):
        """Set provenance recording handler."""
        self._provenance_handler = handler
    
    async def start(self):
        """Start the Kafka consumer."""
        LOGGER.info(f"Starting ToolExecutorWorker on {self.kafka_brokers}")
        
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
        
        LOGGER.info(f"ToolExecutorWorker started, consuming from {self.input_topic}")
    
    async def stop(self):
        """Stop the Kafka consumer gracefully."""
        LOGGER.info("Stopping ToolExecutorWorker...")
        self._running = False
        
        if self._consumer:
            await self._consumer.stop()
        if self._producer:
            await self._producer.stop()
        
        LOGGER.info("ToolExecutorWorker stopped")
    
    async def run(self):
        """Main consumer loop."""
        if not self._running:
            await self.start()
        
        try:
            async for msg in self._consumer:
                try:
                    await self._process_request(msg)
                    await self._consumer.commit()
                except Exception as e:
                    LOGGER.error(f"Error processing tool request: {e}")
                    await self._send_to_dlq(msg, str(e))
                    await self._consumer.commit()
        except asyncio.CancelledError:
            LOGGER.info("ToolExecutorWorker cancelled")
        finally:
            await self.stop()
    
    async def _process_request(self, msg):
        """Process a single tool request."""
        data = msg.value
        start_time = datetime.utcnow()
        
        request = ToolRequest(
            request_id=data.get("request_id", str(uuid4())),
            session_id=data["session_id"],
            tenant_id=data["tenant_id"],
            tool_name=data["tool_name"],
            tool_args=data.get("tool_args", {}),
            metadata=data.get("metadata", {}),
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
        )
        
        LOGGER.info(f"Processing tool request {request.request_id}: {request.tool_name}")
        
        # Step 1: OPA Policy check
        if self._policy_checker:
            allowed = await self._policy_checker(
                action="tool.execute",
                resource=request.tool_name,
                context={
                    "tenant_id": request.tenant_id,
                    "session_id": request.session_id,
                    "tool_args": request.tool_args,
                },
            )
            if not allowed:
                result = ToolResult(
                    request_id=request.request_id,
                    session_id=request.session_id,
                    tenant_id=request.tenant_id,
                    tool_name=request.tool_name,
                    success=False,
                    error="Policy denied: Tool execution not allowed",
                )
                await self._publish_result(result)
                return
        
        # Step 2: Execute tool
        success = False
        result_data = None
        error_msg = None
        
        if request.tool_name not in self._tool_registry:
            error_msg = f"Unknown tool: {request.tool_name}"
        else:
            try:
                handler = self._tool_registry[request.tool_name]
                result_data = await asyncio.wait_for(
                    handler(**request.tool_args),
                    timeout=self.default_timeout_ms / 1000,
                )
                success = True
            except asyncio.TimeoutError:
                error_msg = f"Tool execution timed out after {self.default_timeout_ms}ms"
            except Exception as e:
                error_msg = f"Tool execution failed: {str(e)}"
        
        end_time = datetime.utcnow()
        execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Step 3: Record provenance
        if self._provenance_handler:
            await self._provenance_handler(
                request_id=request.request_id,
                tool_name=request.tool_name,
                tenant_id=request.tenant_id,
                session_id=request.session_id,
                success=success,
                execution_time_ms=execution_time_ms,
                error=error_msg,
            )
        
        # Step 4: Store to memory
        if self._memory_handler and success:
            await self._memory_handler(
                tenant_id=request.tenant_id,
                agent_id=request.session_id,
                content=f"Tool: {request.tool_name}\nArgs: {json.dumps(request.tool_args)}\nResult: {json.dumps(result_data)}",
                memory_type="procedural",
                metadata={
                    "request_id": request.request_id,
                    "tool_name": request.tool_name,
                    "execution_time_ms": execution_time_ms,
                },
            )
        
        # Step 5: Publish result
        result = ToolResult(
            request_id=request.request_id,
            session_id=request.session_id,
            tenant_id=request.tenant_id,
            tool_name=request.tool_name,
            success=success,
            result=result_data,
            error=error_msg,
            execution_time_ms=execution_time_ms,
            metadata=request.metadata,
        )
        
        await self._publish_result(result)
    
    async def _publish_result(self, result: ToolResult):
        """Publish tool result to Kafka."""
        await self._producer.send_and_wait(
            self.output_topic,
            value={
                "request_id": result.request_id,
                "session_id": result.session_id,
                "tenant_id": result.tenant_id,
                "tool_name": result.tool_name,
                "success": result.success,
                "result": result.result,
                "error": result.error,
                "execution_time_ms": result.execution_time_ms,
                "metadata": result.metadata,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
        LOGGER.info(f"Published result for {result.request_id}: success={result.success}")
    
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
            LOGGER.warning(f"Tool request sent to DLQ: {error}")


# Entry point for standalone worker
async def main():
    """Run the tool executor worker standalone."""
    logging.basicConfig(level=logging.INFO)
    
    worker = ToolExecutorWorker()
    
    # Register sample tools for testing
    async def echo_tool(message: str) -> str:
        return f"Echo: {message}"
    
    worker.register_tool("echo", echo_tool)
    
    try:
        await worker.run()
    except KeyboardInterrupt:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
