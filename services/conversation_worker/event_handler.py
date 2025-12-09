"""Event handling for conversation worker.

This module contains the core event processing logic extracted from the
ConversationWorker class to reduce main.py file size.
"""
from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Dict, Optional, TYPE_CHECKING

from jsonschema import ValidationError
from prometheus_client import Counter, Histogram

from observability.metrics import thinking_policy_seconds, tokens_received_total
from python.helpers.tokens import count_tokens
from services.common.schema_validator import validate as validate_schema, validate_event

if TYPE_CHECKING:
    from services.conversation_worker.main import ConversationWorker

LOGGER = logging.getLogger(__name__)

# Metrics
EVENT_PROCESSING_COUNTER = Counter(
    "conversation_worker_events_total",
    "Total conversation events processed",
    labelnames=("result",),
)
EVENT_LATENCY = Histogram(
    "conversation_worker_event_seconds",
    "Event processing latency",
    labelnames=("path",),
)


class EventHandler:
    """Handle conversation events for the worker."""
    
    def __init__(self, worker: "ConversationWorker"):
        """Initialize event handler.
        
        Args:
            worker: The parent ConversationWorker instance
        """
        self.worker = worker
    
    async def handle_event(self, event: Dict[str, Any]) -> None:
        """Process a single conversation event.
        
        Args:
            event: The event payload to process
        """
        start_time = time.perf_counter()
        path = "unknown"
        result_label = "success"
        
        def record_metrics(result: str, path_label: Optional[str] = None) -> None:
            label = path_label or path
            duration = time.perf_counter() - start_time
            EVENT_PROCESSING_COUNTER.labels(result).inc()
            EVENT_LATENCY.labels(label).observe(duration)
        
        session_id = event.get("session_id")
        
        # Validate schema
        try:
            validate_schema(event, "conversation_event")
        except Exception as exc:
            LOGGER.error("conversation_event schema invalid", extra={"error": str(exc)})
            record_metrics("schema_error")
            return
        
        # Extract tenant
        try:
            tenant = (event.get("metadata") or {}).get("tenant", "default")
        except Exception:
            tenant = "default"
        
        if not session_id:
            LOGGER.warning("Received event without session_id", extra={"event": event})
            record_metrics("missing_session")
            return
        
        try:
            validate_event(event, "conversation_event")
        except ValidationError as exc:
            LOGGER.error(
                "Invalid conversation event",
                extra={"error": exc.message, "event": event},
            )
            record_metrics("validation_error")
            return
        
        # Log event receipt
        event_id = event.get("event_id") or str(uuid.uuid4())
        preview = (event.get("message") or "")[:200]
        LOGGER.info(
            "Received inbound event",
            extra={
                "event_id": event_id,
                "session_id": session_id,
                "tenant": tenant,
                "preview": preview,
            },
        )
        
        # Process message
        try:
            await self._process_message(event, session_id, tenant, record_metrics)
            record_metrics("success", path)
        except Exception as e:
            LOGGER.error(f"Event processing failed: {e}", exc_info=True)
            record_metrics("error", path)
    
    async def _process_message(
        self,
        event: Dict[str, Any],
        session_id: str,
        tenant: str,
        record_metrics: Any,
    ) -> None:
        """Process the message content of an event.
        
        Args:
            event: The event payload
            session_id: Session identifier
            tenant: Tenant identifier
            record_metrics: Metrics recording function
        """
        raw_message = event.get("message", "")
        
        # Count tokens
        if isinstance(raw_message, str) and raw_message:
            try:
                tokens_received_total.inc(count_tokens(raw_message))
            except Exception:
                LOGGER.debug("Token counting failed for inbound message", exc_info=True)
        
        # Analyze message
        analysis = self.worker.preprocessor.analyze(
            raw_message if isinstance(raw_message, str) else str(raw_message)
        )
        analysis_dict = analysis.to_dict()
        
        # Enrich metadata
        enriched_metadata = dict(event.get("metadata", {}))
        enriched_metadata["analysis"] = analysis_dict
        event["metadata"] = enriched_metadata
        
        persona_id = event.get("persona_id")
        
        # Check policy
        with thinking_policy_seconds.labels(policy="conversation").time():
            allowed = await self.worker.policy_enforcer.check_message_policy(
                tenant=tenant,
                persona_id=persona_id,
                message=event.get("message", ""),
                metadata=enriched_metadata,
            )
        
        if not allowed:
            await self._handle_policy_denial(event, session_id, persona_id, analysis_dict)
            return
        
        # Continue with normal processing - delegate back to worker
        # The worker has all the state needed for response generation
        await self.worker._process_allowed_message(event, session_id, tenant, enriched_metadata)
    
    async def _handle_policy_denial(
        self,
        event: Dict[str, Any],
        session_id: str,
        persona_id: Optional[str],
        analysis_dict: Dict[str, Any],
    ) -> None:
        """Handle a policy-denied message.
        
        Args:
            event: The original event
            session_id: Session identifier
            persona_id: Persona identifier
            analysis_dict: Message analysis results
        """
        policy_record = {
            "type": "policy_denied",
            "event_id": str(uuid.uuid4()),
            "session_id": session_id,
            "persona_id": persona_id,
            "message": event.get("message", ""),
            "metadata": {
                "source": "policy",
                "analysis": analysis_dict,
                "policy": {
                    "action": "conversation.send",
                    "status": "denied",
                },
            },
        }
        await self.worker.store.append_event(session_id, policy_record)
        
        denial_response = {
            "event_id": str(uuid.uuid4()),
            "session_id": session_id,
            "persona_id": persona_id,
            "role": "assistant",
            "message": "Message blocked by policy. Please contact your administrator if you believe this is an error.",
            "metadata": {
                "source": "policy",
                "analysis": analysis_dict,
                "policy": {
                    "action": "conversation.send",
                    "status": "denied",
                },
            },
        }
        
        await self.worker.publisher.publish(
            topic=self.worker.settings["outbound"],
            payload=denial_response,
        )
