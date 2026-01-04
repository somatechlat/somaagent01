"""Process message use case.

This use case orchestrates the complete message processing pipeline:
1. Validate and analyze incoming message
2. Check policy enforcement
3. Store user message to memory
4. Build context for LLM
5. Generate response
6. Store assistant response to memory
7. Publish response event

All dependencies are injected via constructor following Clean Architecture.
"""

from __future__ import annotations

import json
import logging
import os
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from services.common.job_planner import JobPlanner, PlanValidationError

LOGGER = logging.getLogger(__name__)


# Use Any for protocol types to avoid strict type checking issues with real implementations
SessionRepositoryProtocol = Any
PolicyEnforcerProtocol = Any
MemoryClientProtocol = Any
PublisherProtocol = Any
ContextBuilderProtocol = Any
ResponseGeneratorProtocol = Any


@dataclass
class ProcessMessageInput:
    """Input data for process message use case."""

    event: Dict[str, Any]
    session_id: str
    tenant: str
    persona_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessMessageOutput:
    """Output data from process message use case."""

    success: bool
    response_text: str = ""
    response_event: Dict[str, Any] = field(default_factory=dict)
    usage: Dict[str, int] = field(default_factory=dict)
    path: str = "unknown"
    confidence: Optional[float] = None
    error: Optional[str] = None


@dataclass
class AnalysisResult:
    """Message analysis result."""

    intent: str
    sentiment: str
    tags: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {"intent": self.intent, "sentiment": self.sentiment, "tags": self.tags}


class MessageAnalyzer:
    """Analyze message intent, sentiment, and tags."""

    def analyze(self, message: str) -> AnalysisResult:
        text = message.strip()
        lower = text.lower()

        # Intent detection
        if not text:
            intent = "empty"
        elif lower.startswith(("how", "what", "why", "when", "where", "who")) or text.endswith("?"):
            intent = "question"
        elif any(kw in lower for kw in ["create", "build", "implement", "write"]):
            intent = "action_request"
        elif any(kw in lower for kw in ["fix", "bug", "issue", "error"]):
            intent = "problem_report"
        else:
            intent = "statement"

        # Tag detection
        tags: List[str] = []
        if any(w in lower for w in ["code", "python", "function", "class"]):
            tags.append("code")
        if any(w in lower for w in ["deploy", "docker", "kubernetes", "infra"]):
            tags.append("infrastructure")
        if any(w in lower for w in ["test", "validate", "qa"]):
            tags.append("testing")

        # Sentiment detection
        negatives = {"fail", "broken", "crash", "error", "issue"}
        positives = {"great", "thanks", "awesome", "good"}
        sentiment = "neutral"
        if any(w in lower for w in negatives):
            sentiment = "negative"
        elif any(w in lower for w in positives):
            sentiment = "positive"

        return AnalysisResult(intent=intent, sentiment=sentiment, tags=tags)


class ProcessMessageUseCase:
    """Use case for processing conversation messages.

    This use case orchestrates the complete message processing pipeline
    with all dependencies injected via constructor.
    """

    def __init__(
        self,
        session_repo: SessionRepositoryProtocol,
        policy_enforcer: PolicyEnforcerProtocol,
        memory_client: MemoryClientProtocol,
        publisher: PublisherProtocol,
        context_builder: ContextBuilderProtocol,
        response_generator: ResponseGeneratorProtocol,
        outbound_topic: str,
        analyzer: Optional[MessageAnalyzer] = None,
    ):
        self._session_repo = session_repo
        self._policy_enforcer = policy_enforcer
        self._memory_client = memory_client
        self._publisher = publisher
        self._context_builder = context_builder
        self._response_generator = response_generator
        self._outbound_topic = outbound_topic
        self._analyzer = analyzer or MessageAnalyzer()

    async def execute(self, input_data: ProcessMessageInput) -> ProcessMessageOutput:
        """Execute the message processing pipeline."""
        event = input_data.event
        session_id = input_data.session_id
        tenant = input_data.tenant
        persona_id = input_data.persona_id

        # Step 1: Analyze message
        raw_message = event.get("message", "")
        analysis = self._analyzer.analyze(
            raw_message if isinstance(raw_message, str) else str(raw_message)
        )
        analysis_dict = analysis.to_dict()

        # Enrich metadata with analysis
        enriched_metadata = dict(event.get("metadata", {}))
        enriched_metadata["analysis"] = analysis_dict
        event["metadata"] = enriched_metadata

        # Step 2: Check policy
        allowed = await self._policy_enforcer.check_message_policy(
            tenant=tenant,
            persona_id=persona_id,
            message=event.get("message", ""),
            metadata=enriched_metadata,
        )

        if not allowed:
            return await self._handle_policy_denial(event, session_id, persona_id, analysis_dict)

        # Step 3: Store user message
        try:
            await self._session_repo.append_event(session_id, {"type": "user", **event})
        except Exception as e:
            if "UniqueViolation" not in str(type(e).__name__):
                LOGGER.warning(f"Failed to store user event: {e}")

        # Step 4: Store to memory (best effort)
        await self._store_user_memory(event, session_id, tenant, enriched_metadata)

        # Step 5: Build context and generate response
        try:
            response_text, usage, path, confidence = await self._generate_response(
                event, session_id, persona_id, tenant, enriched_metadata, analysis_dict
            )

            if os.environ.get("SA01_ENABLE_MULTIMODAL_CAPABILITIES", "false").lower() == "true":
                response_text = await self._handle_multimodal_plan(
                    response_text, session_id, tenant
                )
        except Exception as e:
            LOGGER.exception("Response generation failed")
            return ProcessMessageOutput(
                success=False,
                error=str(e),
                path="error",
            )

        # Step 6: Build and publish response event
        response_event = self._build_response_event(
            session_id,
            persona_id,
            response_text,
            usage,
            enriched_metadata,
            analysis_dict,
            confidence,
        )

        # Step 7: Store assistant response
        await self._session_repo.append_event(session_id, {"type": "assistant", **response_event})

        # Step 8: Publish response
        await self._publisher.publish(
            self._outbound_topic,
            response_event,
            dedupe_key=response_event.get("event_id"),
            session_id=session_id,
            tenant=tenant,
        )

        # Step 9: Store assistant to memory (best effort)
        await self._store_assistant_memory(
            response_text, session_id, persona_id, tenant, response_event.get("metadata", {})
        )

        return ProcessMessageOutput(
            success=True,
            response_text=response_text,
            response_event=response_event,
            usage=usage,
            path=path,
            confidence=confidence,
        )

    async def _handle_policy_denial(
        self,
        event: Dict[str, Any],
        session_id: str,
        persona_id: Optional[str],
        analysis_dict: Dict[str, Any],
    ) -> ProcessMessageOutput:
        """Handle policy-denied message."""
        policy_record = {
            "type": "policy_denied",
            "event_id": str(uuid.uuid4()),
            "session_id": session_id,
            "persona_id": persona_id,
            "message": event.get("message", ""),
            "metadata": {
                "source": "policy",
                "analysis": analysis_dict,
                "policy": {"action": "conversation.send", "status": "denied"},
            },
        }
        await self._session_repo.append_event(session_id, policy_record)

        denial_response = {
            "event_id": str(uuid.uuid4()),
            "session_id": session_id,
            "persona_id": persona_id,
            "role": "assistant",
            "message": "Message blocked by policy. Please contact your administrator if you believe this is an error.",
            "metadata": {
                "source": "policy",
                "analysis": analysis_dict,
                "policy": {"action": "conversation.send", "status": "denied"},
            },
        }

        await self._publisher.publish(
            self._outbound_topic,
            denial_response,
            dedupe_key=denial_response.get("event_id"),
            session_id=session_id,
        )

        return ProcessMessageOutput(
            success=False,
            response_text=denial_response["message"],
            response_event=denial_response,
            path="policy",
            error="Policy denied",
        )

    async def _store_user_memory(
        self,
        event: Dict[str, Any],
        session_id: str,
        tenant: str,
        metadata: Dict[str, Any],
    ) -> None:
        """Store user message to memory (best effort)."""
        try:
            from services.common.idempotency import generate_for_memory_payload

            payload = {
                "id": event.get("event_id") or str(uuid.uuid4()),
                "type": "conversation_event",
                "role": "user",
                "content": event.get("message", ""),
                "attachments": event.get("attachments", []) or [],
                "session_id": session_id,
                "persona_id": event.get("persona_id"),
                "metadata": metadata,
            }
            payload["idempotency_key"] = generate_for_memory_payload(payload)
            await self._memory_client.remember(payload)
        except Exception:
            LOGGER.debug("Failed to store user memory", exc_info=True)

    async def _store_assistant_memory(
        self,
        response_text: str,
        session_id: str,
        persona_id: Optional[str],
        tenant: str,
        metadata: Dict[str, Any],
    ) -> None:
        """Store assistant response to memory (best effort)."""
        try:
            from services.common.idempotency import generate_for_memory_payload

            payload = {
                "id": str(uuid.uuid4()),
                "type": "conversation_event",
                "role": "assistant",
                "content": response_text,
                "attachments": [],
                "session_id": session_id,
                "persona_id": persona_id,
                "metadata": metadata,
            }
            payload["idempotency_key"] = generate_for_memory_payload(payload)
            await self._memory_client.remember(payload)
        except Exception:
            LOGGER.debug("Failed to store assistant memory", exc_info=True)

    async def _generate_response(
        self,
        event: Dict[str, Any],
        session_id: str,
        persona_id: Optional[str],
        tenant: str,
        metadata: Dict[str, Any],
        analysis_dict: Dict[str, Any],
    ) -> tuple[str, Dict[str, int], str, Optional[float]]:
        """Generate LLM response."""
        # Get history
        history = await self._session_repo.list_events(session_id, limit=20)
        history_messages = self._history_to_messages(history)

        # Build context
        turn_envelope = {
            "tenant_id": tenant,
            "session_id": session_id,
            "system_prompt": self._build_system_prompt(analysis_dict),
            "user_message": event.get("message", ""),
            "history": history_messages,
        }

        built_context = await self._context_builder.build_for_turn(
            turn_envelope, max_prompt_tokens=4096
        )

        # Convert to ChatMessage format
        messages = [
            {"role": msg.get("role", "user"), "content": str(msg.get("content", ""))}
            for msg in built_context.messages
        ]

        # Generate response using GenerateResponseUseCase
        from src.core.application.use_cases.conversation.generate_response import (
            GenerateResponseInput,
        )

        gen_input = GenerateResponseInput(
            session_id=session_id,
            persona_id=persona_id,
            messages=messages,
            tenant=tenant,
            analysis_metadata=analysis_dict,
            base_metadata=metadata,
        )
        result = await self._response_generator.execute(gen_input)

        return result.text, result.usage, "llm", result.confidence

    def _history_to_messages(self, events: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Convert history events to message format."""
        messages: List[Dict[str, str]] = []
        for entry in events:
            if not isinstance(entry, dict):
                continue
            role = entry.get("type")
            if role == "user":
                content = entry.get("message") or ""
                if content:
                    messages.append({"role": "user", "content": str(content)})
            elif role == "assistant":
                content = entry.get("message") or ""
                if content:
                    messages.append({"role": "assistant", "content": str(content)})
        return messages

    def _build_system_prompt(self, analysis_dict: Dict[str, Any]) -> str:
        """Build system prompt from analysis."""
        tags = ", ".join(analysis_dict.get("tags", [])) or "none"
        return (
            "The following classification is for internal guidance only. "
            "Do not repeat or mention it in your reply. "
            f"Classification: intent={analysis_dict.get('intent', 'general')}; "
            f"sentiment={analysis_dict.get('sentiment', 'neutral')}; tags={tags}."
        )

    def _build_response_event(
        self,
        session_id: str,
        persona_id: Optional[str],
        response_text: str,
        usage: Dict[str, int],
        metadata: Dict[str, Any],
        analysis_dict: Dict[str, Any],
        confidence: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Build response event for publishing."""
        response_metadata = dict(metadata)
        response_metadata["source"] = "llm"
        response_metadata["status"] = "completed"
        response_metadata["analysis"] = analysis_dict
        response_metadata["usage"] = usage
        if confidence is not None:
            response_metadata["confidence"] = confidence

        return {
            "event_id": str(uuid.uuid4()),
            "session_id": session_id,
            "persona_id": persona_id,
            "role": "assistant",
            "message": response_text,
            "metadata": response_metadata,
            "version": "sa01-v1",
            "type": "assistant.final",
        }

    async def _handle_multimodal_plan(
        self,
        response_text: str,
        session_id: str,
        tenant: str,
    ) -> str:
        """Extract and execute multimodal plan if present."""
        # Regex to find JSON block at end of message
        # We look for ```json { ... } ``` or just { ... } at the end
        pattern = r"```json\s*(\{.*?\})\s*```\s*$"
        match = re.search(pattern, response_text, re.DOTALL)

        if not match:
            # Try matching raw JSON at end if no blocks
            pattern_raw = r"(\{.*?\})\s*$"
            match = re.search(pattern_raw, response_text, re.DOTALL)

        if not match:
            return response_text

        json_str = match.group(1)
        try:
            data = json.loads(json_str)
            if "multimodal_plan" not in data:
                return response_text

            plan_data = data["multimodal_plan"]

            # Clean response text (remove the JSON block)
            clean_text = response_text.replace(match.group(0), "").strip()

            # Validate/Compile Plan
            planner = JobPlanner()
            request_id = plan_data.get("request_id") or data.get("request_id")
            job_plan = planner.compile(
                tenant_id=tenant,
                session_id=session_id,
                dsl=plan_data,
                request_id=request_id,
            )
            await planner.create(job_plan)
            LOGGER.info("Created multimodal plan %s for session %s", job_plan.id, session_id)
            return clean_text

        except json.JSONDecodeError:
            LOGGER.warning("Failed to decode extracted JSON plan")
            return response_text
        except PlanValidationError as e:
            LOGGER.warning("Invalid multimodal plan: %s", e.errors)
            return response_text
        except Exception as e:
            LOGGER.warning(f"Failed to process multimodal plan: {e}")
            return response_text
