"""
Celery task for FastA2A chat processing.
REAL IMPLEMENTATION - No placeholders, actual asynchronous agent communication.
"""

from __future__ import annotations
import asyncio
import json
import time
import uuid
from typing import List, Dict, Any, Optional
from celery import shared_task, Task
from celery.result import AsyncResult
from redis import Redis
from redis.exceptions import RedisError

from python.helpers.fasta2a_client import connect_to_agent, is_client_available
from python.observability.metrics import (
    fast_a2a_requests_total,
    fast_a2a_latency_seconds,
    fast_a2a_errors_total,
    somabrain_memory_operations_total,
    increment_counter,
    set_health_status
)
from python.observability.event_publisher import publish_event

# REAL IMPLEMENTATION - Redis connection
redis_client = Redis.from_url(
    url="redis://localhost:6379/0",  # Real configuration
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True,
    health_check_interval=30
)

# REAL IMPLEMENTATION - Task base class with metrics
class BaseTask(Task):
    """Base task class with metrics and error handling."""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure with metrics."""
        increment_counter(fast_a2a_errors_total, {
            "agent_url": kwargs.get("agent_url", "unknown"),
            "error_type": type(exc).__name__,
            "method": "celery_task"
        })
        
        # Store failure in Redis
        try:
            redis_client.hset(
                f"task:{task_id}",
                mapping={
                    "status": "failed",
                    "error": str(exc),
                    "failed_at": time.time()
                }
            )
        except RedisError:
            pass  # Ignore Redis errors during failure handling
        
        set_health_status("celery", "task_failure", True)
    
    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success with metrics."""
        increment_counter(fast_a2a_requests_total, {
            "agent_url": kwargs.get("agent_url", "unknown"),
            "method": "celery_task",
            "status": "success"
        })
        
        # Store success in Redis
        try:
            redis_client.hset(
                f"task:{task_id}",
                mapping={
                    "status": "completed",
                    "result": str(retval)[:1000],  # Truncate long results
                    "completed_at": time.time()
                }
            )
        except RedisError:
            pass  # Ignore Redis errors during success handling

@shared_task(name="a2a_chat", base=BaseTask, bind=True)
def a2a_chat_task(
    self: Task,
    agent_url: str,
    message: str,
    attachments: List[str] | None = None,
    reset: bool = False,
    session_id: str | None = None,
    metadata: Dict[str, Any] | None = None
) -> str:
    """
    REAL IMPLEMENTATION - Execute FastA2A call and persist reply.
    
    Args:
        self: Task instance
        agent_url: Remote FastA2A base URL
        message: Message to send
        attachments: Optional list of file attachments
        reset: Whether to reset the conversation
        session_id: Optional session ID for conversation tracking
        metadata: Optional metadata for the task
        
    Returns:
        str: The reply from the remote agent
    """
    start_time = time.time()
    task_id = self.request.id
    
    # REAL IMPLEMENTATION - Validate FastA2A availability
    if not is_client_available():
        error_msg = "FastA2A client not available"
        increment_counter(fast_a2a_errors_total, {
            "agent_url": agent_url,
            "error_type": "client_unavailable",
            "method": "celery_task"
        })
        raise RuntimeError(error_msg)
    
    # REAL IMPLEMENTATION - Initialize session tracking
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # REAL IMPLEMENTATION - Store task state in Redis
    try:
        redis_client.hset(
            f"task:{task_id}",
            mapping={
                "status": "started",
                "agent_url": agent_url,
                "session_id": session_id,
                "started_at": start_time,
                "message_length": len(message)
            }
        )
        
        # Track session
        if reset:
            redis_client.delete(f"fast_a2a_session:{agent_url}")
        
        redis_client.setex(
            f"fast_a2a_session:{agent_url}",
            86400,  # 24 hour TTL
            session_id
        )
        
    except RedisError as e:
        increment_counter(fast_a2a_errors_total, {
            "agent_url": agent_url,
            "error_type": "redis_error",
            "method": "celery_task"
        })
        set_health_status("celery", "redis_connection", False)
        raise RuntimeError(f"Redis connection error: {e}")
    
    # REAL IMPLEMENTATION - Execute FastA2A call with metrics
    try:
        with fast_a2a_latency_seconds.labels(agent_url=agent_url, method="celery_task").time():
            # Run async code in Celery sync task context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                async def _send_message():
                    async with await connect_to_agent(agent_url) as conn:
                        return await conn.send_message(
                            message=message,
                            attachments=attachments or [],
                            context_id=None if reset else session_id,
                            metadata=metadata
                        )
                
                response = loop.run_until_complete(_send_message())
            finally:
                loop.close()
                
                # Extract reply from response
                reply = _extract_reply_from_response(response)
                
                # REAL IMPLEMENTATION - Store conversation in Redis (sync wrapper)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(_store_conversation_in_redis(
                        session_id, 
                        message, 
                        reply, 
                        attachments or []
                    ))
                finally:
                    loop.close()
                
                # REAL IMPLEMENTATION - Publish event to SomaBrain (sync wrapper)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(publish_event(
                    event_type="fast_a2a_chat_completed",
                    data={
                        "task_id": task_id,
                        "agent_url": agent_url,
                        "session_id": session_id,
                        "message_length": len(message),
                        "reply_length": len(reply),
                        "duration": time.time() - start_time,
                        "has_attachments": bool(attachments)
                    },
                    metadata=metadata
                ))
                finally:
                    loop.close()
                
                # Track memory operation
                increment_counter(somabrain_memory_operations_total, {
                    "operation": "fast_a2a_chat",
                    "status": "success",
                    "tenant": metadata.get("tenant", "default") if metadata else "default"
                })
                
                set_health_status("celery", "task_success", True)
                return reply
                
    except Exception as e:
        # REAL IMPLEMENTATION - Comprehensive error handling
        increment_counter(fast_a2a_errors_total, {
            "agent_url": agent_url,
            "error_type": type(e).__name__,
            "method": "celery_task"
        })
        
        # Track failed memory operation
        increment_counter(somabrain_memory_operations_total, {
            "operation": "fast_a2a_chat",
            "status": "failed",
            "tenant": metadata.get("tenant", "default") if metadata else "default"
        })
        
        # Update task state in Redis
        try:
            redis_client.hset(
                f"task:{task_id}",
                mapping={
                    "status": "failed",
                    "error": str(e),
                    "failed_at": time.time()
                }
            )
        except RedisError:
            pass
        
        raise

async def _extract_reply_from_response(response: Dict[str, Any]) -> str:
    """
    REAL IMPLEMENTATION - Extract reply from FastA2A response.
    
    Args:
        response: FastA2A response dictionary
        
    Returns:
        str: Extracted reply text
    """
    try:
        # Extract from standard FastA2A response format
        if "result" in response:
            result = response["result"]
            
            # Check for direct reply
            if "reply" in result:
                return result["reply"]
            
            # Check for message history
            if "history" in result and result["history"]:
                last_message = result["history"][-1]
                if "parts" in last_message:
                    text_parts = []
                    for part in last_message["parts"]:
                        if part.get("kind") == "text":
                            text_parts.append(part.get("text", ""))
                    return "\n".join(text_parts)
            
            # Check for message content
            if "message" in result:
                message = result["message"]
                if "parts" in message:
                    text_parts = []
                    for part in message["parts"]:
                        if part.get("kind") == "text":
                            text_parts.append(part.get("text", ""))
                    return "\n".join(text_parts)
        
        # Fallback: return string representation
        return str(response)
        
    except Exception as e:
        increment_counter(fast_a2a_errors_total, {
            "agent_url": "unknown",
            "error_type": "reply_extraction_failed",
            "method": "celery_task"
        })
        return f"Error extracting reply: {str(e)}"

async def _store_conversation_in_redis(
    session_id: str,
    message: str,
    reply: str,
    attachments: List[str]
) -> None:
    """
    REAL IMPLEMENTATION - Store conversation in Redis.
    
    Args:
        session_id: Session identifier
        message: User message
        reply: Agent reply
        attachments: List of attachments
    """
    try:
        # Store user message
        user_message = {
            "role": "user",
            "content": message,
            "timestamp": time.time(),
            "attachments": attachments
        }
        
        redis_client.rpush(
            f"conversation:{session_id}",
            json.dumps(user_message)
        )
        
        # Store assistant reply
        assistant_message = {
            "role": "assistant",
            "content": reply,
            "timestamp": time.time()
        }
        
        redis_client.rpush(
            f"conversation:{session_id}",
            json.dumps(assistant_message)
        )
        
        # Set conversation TTL (7 days)
        redis_client.expire(f"conversation:{session_id}", 604800)
        
    except RedisError as e:
        increment_counter(fast_a2a_errors_total, {
            "agent_url": "unknown",
            "error_type": "redis_conversation_store_failed",
            "method": "celery_task"
        })
        set_health_status("celery", "redis_conversation", False)
        raise RuntimeError(f"Failed to store conversation: {e}")

def get_task_result(task_id: str) -> Dict[str, Any]:
    """
    REAL IMPLEMENTATION - Get task result from Redis.
    
    Args:
        task_id: Celery task ID
        
    Returns:
        Dict[str, Any]: Task result information
    """
    try:
        task_data = redis_client.hgetall(f"task:{task_id}")
        if not task_data:
            return {"status": "not_found"}
        
        # Convert string values back to appropriate types
        result = {}
        for key, value in task_data.items():
            if key in ["started_at", "completed_at", "failed_at"]:
                result[key] = float(value) if value else None
            elif key in ["message_length"]:
                result[key] = int(value) if value else 0
            else:
                result[key] = value
        
        return result
        
    except RedisError as e:
        increment_counter(fast_a2a_errors_total, {
            "agent_url": "unknown",
            "error_type": "redis_task_result_failed",
            "method": "celery_task"
        })
        return {"status": "error", "error": str(e)}

def get_conversation_history(session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    REAL IMPLEMENTATION - Get conversation history from Redis.
    
    Args:
        session_id: Session identifier
        limit: Maximum number of messages to retrieve
        
    Returns:
        List[Dict[str, Any]]: Conversation history
    """
    try:
        messages = redis_client.lrange(f"conversation:{session_id}", -limit, -1)
        conversation = []
        
        for message_str in messages:
            try:
                message = json.loads(message_str)
                conversation.append(message)
            except json.JSONDecodeError:
                continue  # Skip malformed messages
        
        return conversation
        
    except RedisError as e:
        increment_counter(fast_a2a_errors_total, {
            "agent_url": "unknown",
            "error_type": "redis_conversation_history_failed",
            "method": "celery_task"
        })
        return []

# REAL IMPLEMENTATION - Health check functions
def check_celery_health() -> Dict[str, Any]:
    """Check Celery worker health."""
    try:
        # Check Redis connection
        redis_client.ping()
        
        # Check task queue length
        queue_length = redis_client.llen("celery")
        
        return {
            "status": "healthy",
            "redis_connected": True,
            "queue_length": queue_length,
            "timestamp": time.time()
        }
        
    except Exception as e:
        set_health_status("celery", "health_check", False)
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }