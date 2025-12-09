"""Response generation and handling for conversation worker.

This module extracts response generation logic from the ConversationWorker
to reduce main.py file size.
"""
from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from prometheus_client import Counter

if TYPE_CHECKING:
    from services.conversation_worker.main import ConversationWorker

LOGGER = logging.getLogger(__name__)

# Metrics
RESPONSE_GENERATION_COUNTER = Counter(
    "conversation_worker_responses_total",
    "Total responses generated",
    labelnames=("type", "result"),
)


class ResponseHandler:
    """Handle response generation for conversation worker."""
    
    def __init__(self, worker: "ConversationWorker"):
        """Initialize response handler.
        
        Args:
            worker: The parent ConversationWorker instance
        """
        self.worker = worker
    
    async def generate_response(
        self,
        session_id: str,
        persona_id: Optional[str],
        tenant: str,
        messages: List[Dict[str, str]],
        context: Dict[str, Any],
        model_profile: Dict[str, Any],
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate a response using the configured LLM.
        
        Args:
            session_id: Session identifier
            persona_id: Persona identifier
            tenant: Tenant identifier
            messages: Conversation messages
            context: Built context from context_builder
            model_profile: Model configuration
            metadata: Request metadata
            
        Returns:
            Response dict with text, usage, and metadata
        """
        start_time = time.perf_counter()
        
        try:
            # Check if tools are enabled
            tools_enabled = model_profile.get("tools_enabled", False)
            
            if tools_enabled:
                response_text, usage = await self._generate_with_tools(
                    session_id=session_id,
                    persona_id=persona_id,
                    tenant=tenant,
                    messages=messages,
                    context=context,
                    model_profile=model_profile,
                    metadata=metadata,
                )
            else:
                response_text, usage = await self._generate_simple(
                    messages=messages,
                    model_profile=model_profile,
                    metadata=metadata,
                )
            
            elapsed = time.perf_counter() - start_time
            RESPONSE_GENERATION_COUNTER.labels(
                type="tools" if tools_enabled else "simple",
                result="success"
            ).inc()
            
            return {
                "text": response_text,
                "usage": usage,
                "elapsed": elapsed,
                "model": model_profile.get("model"),
            }
            
        except Exception as e:
            LOGGER.error(f"Response generation failed: {e}", exc_info=True)
            RESPONSE_GENERATION_COUNTER.labels(type="unknown", result="error").inc()
            raise
    
    async def _generate_simple(
        self,
        messages: List[Dict[str, str]],
        model_profile: Dict[str, Any],
        metadata: Dict[str, Any],
    ) -> tuple[str, Dict[str, int]]:
        """Generate a simple response without tools.
        
        Args:
            messages: Conversation messages
            model_profile: Model configuration
            metadata: Request metadata
            
        Returns:
            Tuple of (response_text, usage_dict)
        """
        # Delegate to worker's existing method
        return await self.worker._generate_response(
            messages=messages,
            model=model_profile.get("model"),
            temperature=model_profile.get("temperature", 0.7),
            max_tokens=model_profile.get("max_tokens", 2048),
            metadata=metadata,
        )
    
    async def _generate_with_tools(
        self,
        session_id: str,
        persona_id: Optional[str],
        tenant: str,
        messages: List[Dict[str, str]],
        context: Dict[str, Any],
        model_profile: Dict[str, Any],
        metadata: Dict[str, Any],
    ) -> tuple[str, Dict[str, int]]:
        """Generate a response with tool calling support.
        
        Args:
            session_id: Session identifier
            persona_id: Persona identifier
            tenant: Tenant identifier
            messages: Conversation messages
            context: Built context
            model_profile: Model configuration
            metadata: Request metadata
            
        Returns:
            Tuple of (response_text, usage_dict)
        """
        # Delegate to worker's existing tool-enabled generation
        return await self.worker._generate_with_tools(
            session_id=session_id,
            persona_id=persona_id,
            tenant=tenant,
            messages=messages,
            context=context,
            model=model_profile.get("model"),
            temperature=model_profile.get("temperature", 0.7),
            max_tokens=model_profile.get("max_tokens", 2048),
            tools=self.worker._tools_openai_schema(),
            metadata=metadata,
        )
    
    def build_response_event(
        self,
        session_id: str,
        persona_id: Optional[str],
        response_text: str,
        usage: Dict[str, int],
        metadata: Dict[str, Any],
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build a response event for publishing.
        
        Args:
            session_id: Session identifier
            persona_id: Persona identifier
            response_text: Generated response text
            usage: Token usage stats
            metadata: Additional metadata
            model: Model used for generation
            
        Returns:
            Response event dict
        """
        event_id = str(uuid.uuid4())
        
        response_metadata = dict(metadata)
        response_metadata["source"] = "conversation_worker"
        response_metadata["model"] = model
        response_metadata["usage"] = usage
        
        return {
            "event_id": event_id,
            "session_id": session_id,
            "persona_id": persona_id,
            "role": "assistant",
            "message": response_text,
            "metadata": response_metadata,
        }
    
    async def publish_response(
        self,
        response_event: Dict[str, Any],
        tenant: str,
    ) -> None:
        """Publish a response event to the outbound topic.
        
        Args:
            response_event: The response event to publish
            tenant: Tenant identifier
        """
        await self.worker.publisher.publish(
            self.worker.settings["outbound"],
            response_event,
            dedupe_key=response_event.get("event_id"),
            session_id=response_event.get("session_id"),
            tenant=tenant,
        )
