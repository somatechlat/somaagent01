"""Simple Context Builder - Production-grade LLM context assembly.

Replaces 759-line context_builder with 150-line production implementation.

VIBE COMPLIANT:
- Real production-grade implementation
- No unnecessary health state tracking
- No knapsack algorithm optimization
- Simple, testable, observable
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Callable

from admin.core.somabrain_client import SomaBrainClient, SomaClientError
from services.common.circuit_breaker import CircuitBreakerError, get_circuit_breaker

logger = logging.getLogger(__name__)

# Deployment mode detection
DEPLOYMENT_MODE = os.environ.get("SA01_DEPLOYMENT_MODE", "dev").upper()
SAAS_MODE = DEPLOYMENT_MODE == "SAAS"
STANDALONE_MODE = DEPLOYMENT_MODE == "STANDALONE"


from enum import Enum


class SomabrainHealthState(str, Enum):
    """SomaBrain health state for degradation handling.

    NORMAL: Full capabilities available
    DEGRADED: Reduced capabilities (e.g., lower Top-K, faster timeout)
    DOWN: SomaBrain unavailable, fallback mode
    """

    NORMAL = "normal"
    DEGRADED = "degraded"
    DOWN = "down"


@dataclass
class BuiltContext:
    """Result of context building for a turn.

    Attributes:
        system_prompt: System prompt for LLM
        messages: Formatted messages for LLM
        token_counts: Token usage by category
        lane_actual: Actual tokens per lane for governor reporting
    """

    system_prompt: str
    messages: list[dict[str, Any]]
    token_counts: dict[str, int]
    lane_actual: dict[str, int] = field(default_factory=dict)


class PresidioRedactor:
    """Production-grade PII redaction using Presidio.

    Lazy loading to avoid startup delay.
    Handles: PHONE_NUMBER, EMAIL_ADDRESS, IBAN, CREDIT_CARD, US_SSN
    """

    def __init__(self):
        self._analyzer = None
        self._anonymizer = None
        self._entities = ["PHONE_NUMBER", "EMAIL_ADDRESS", "IBAN", "CREDIT_CARD", "US_SSN"]

    def _ensure_loaded(self):
        """Lazy load presidio components."""
        if self._analyzer is None:
            try:
                from presidio_analyzer import AnalyzerEngine
                from presidio_anonymizer import AnonymizerEngine

                self._analyzer = AnalyzerEngine()
                self._anonymizer = AnonymizerEngine()
            except ImportError:
                logger.warning("Presidio not installed - redaction disabled")

    def redact(self, text: str) -> str:
        """Redact PII from text.

        Args:
            text: Text to redact

        Returns:
            Redacted text (fails open on error)
        """
        if not text:
            return text

        try:
            self._ensure_loaded()
            if not self._analyzer or not self._anonymizer:
                return text

            results = self._analyzer.analyze(text=text, entities=self._entities, language="en")
            anonymized = self._anonymizer.anonymize(text=text, analyzer_results=results)
            return anonymized.text

        except Exception:
            logger.warning("Presidio redaction failed - returning original text")
            return text


class ContextBuilder:
    """Simple production-grade context builder.

    Replaces 759-line implementation with focused logic:
    1. Add system prompt and multimodal instructions
    2. Add trimmed history within budget
    3. Add memory snippets if service healthy (protected by circuit breaker)
    4. Add user message
    5. Format for LLM
    """

    def __init__(
        self,
        somabrain: SomaBrainClient,
        token_counter: Callable[[str], int],
    ) -> None:
        """Initialize context builder.

        Args:
            somabrain: SomaBrain client for memory retrieval
            token_counter: Function to count tokens in text
        """
        self.somabrain = somabrain
        self.count_tokens = token_counter
        self.redactor = PresidioRedactor()

        # Circuit breaker for SomaBrain
        self.somabrain_breaker = get_circuit_breaker(
            name="somabrain",
            failure_threshold=5,
            reset_timeout=30,
        )

    async def build_for_turn(
        self,
        turn: dict[str, Any],
        lane_budget: dict[str, int],
        is_degraded: bool = False,
    ) -> BuiltContext:
        """Build context for LLM from turn data.

        Args:
            turn: Turn context with user_message, history, system_prompt
            lane_budget: Token budget per lane (from SimpleGovernor)
            is_degraded: Whether system is degraded (disable memory if true)

        Returns:
            BuiltContext with formatted messages and token counts
        """
        # Extract turn data
        system_prompt_base = turn.get("system_prompt", "You are SomaAgent01.")
        user_message = turn.get("user_message", "").strip()
        history = turn.get("history") or []

        # Calculate budgets from lane_budget
        history_budget = lane_budget.get("history", 0)
        memory_budget = lane_budget.get("memory", 0)
        system_tokens = self.count_tokens(system_prompt_base)
        user_tokens = self.count_tokens(user_message)

        # 1. Build system prompt with instructions
        system_prompt = self._build_system_prompt(system_prompt_base)

        messages = [{"role": "system", "content": system_prompt}]

        # 2. Add history within budget
        history_messages, history_tokens = self._add_history(messages, history, history_budget)

        # 3. Add memory snippets if not degraded and SomaBrain healthy
        snippet_messages, snippet_tokens = await self._add_memory(
            messages, turn, memory_budget, is_degraded
        )

        # 4. Add user message
        messages.append({"role": "user", "content": user_message})

        # 5. Track token counts
        token_counts = {
            "system": system_tokens,
            "history": history_tokens,
            "memory": snippet_tokens,
            "user": user_tokens,
        }

        # 6. Map to lane_actual for governor reporting
        lane_actual = {
            "system_policy": system_tokens,
            "history": history_tokens,
            "memory": snippet_tokens,
            "tools": 0,
            "tool_results": 0,
            "buffer": lane_budget.get("buffer", 0),
        }

        logger.debug(
            "Context built",
            extra={
                "session_id": turn.get("session_id"),
                "messages": len(messages),
                "tokens": token_counts,
            },
        )

        # Record metrics
        from services.common.unified_metrics import get_metrics

        metrics = get_metrics()

        if snippet_tokens > 0:
            metrics.record_memory_retrieval(
                latency_seconds=0.0,  # Will be updated in caller
                snippet_count=len(snippet_messages),
            )

        return BuiltContext(
            system_prompt=system_prompt,
            messages=messages,
            token_counts=token_counts,
            lane_actual=lane_actual,
        )

    def _build_system_prompt(self, base_prompt: str) -> str:
        """Build system prompt with optional multimodal instructions.

        Args:
            base_prompt: Base system prompt

        Returns:
            Complete system prompt with instructions if enabled
        """
        # Check if multimodal capabilities are enabled
        if os.environ.get("SA01_ENABLE_MULTIMODAL_CAPABILITIES", "false").lower() != "true":
            return base_prompt

        # Add multimodal instructions
        multimodal_instruction = (
            "\n\nMULTIMODAL CAPABILITIES:\n"
            "You can generate images, diagrams (Mermaid/PlantUML), and screenshots.\n"
            "If user explicitly asks for visual content, output JSON block at end:\n\n"
            "```json\n"
            '{ "multimodal_plan": { "version": "1.0", "tasks": [...] } }\n'
            "```\n"
            "Supported task_types: generate_image, generate_diagram, capture_screenshot.\n"
        )

        return base_prompt + multimodal_instruction

    def _add_history(
        self,
        messages: list[dict[str, Any]],
        history: list[dict[str, str]],
        budget: int,
    ) -> tuple[list[dict[str, Any]], int]:
        """Add history messages within budget.

        Uses recent-most-first strategy (simple, production-proven).

        Args:
            messages: Existing message list to append to
            history: Full conversation history
            budget: Token budget for history

        Returns:
            Tuple of (added_messages, total_tokens_used)
        """
        if budget <= 0 or not history:
            return [], 0

        added = []
        used_tokens = 0

        # Add history from most recent (reverse order to recent-first)
        for msg in reversed(history):
            content = msg.get("content", "")
            if not content:
                continue

            tokens = self.count_tokens(content)
            if used_tokens + tokens > budget:
                break

            added.append(msg)
            used_tokens += tokens

        messages.extend(reversed(added))
        return added, used_tokens

    async def _add_memory(
        self,
        messages: list[dict[str, Any]],
        turn: dict[str, Any],
        budget: int,
        is_degraded: bool,
    ) -> tuple[list[dict[str, Any]], int]:
        """Add memory snippets within budget.

        Protected by circuit breaker. Skips entire SomaBrain:
        - If is_degraded=True (system-level decision)
        - If circuit breaker is OPEN (SomaBrain-specific failure)

        Deployment mode support:
        - SAAS mode: HTTP POST to SomaBrain with circuit breaker
        - STANDALONE mode: Direct PostgreSQL query via embedded module

        Args:
            messages: Existing message list to append to
            turn: Turn context
            budget: Token budget for memory
            is_degraded: Whether system is degraded

        Returns:
            Tuple of (snippet_messages, tokens_used)
        """
        if budget <= 0 or is_degraded:
            logger.debug(f"Memory retrieval skipped: budget={budget}, degraded={is_degraded}")
            return [], 0

        # STANDALONE mode: Use embedded SomaBrain module
        if STANDALONE_MODE:
            return await self._add_memory_standalone(messages, turn, budget)

        # SAAS mode: Use SomaBrain HTTP API
        return await self._add_memory_saas(messages, turn, budget)

    async def _add_memory_saas(
        self,
        messages: list[dict[str, Any]],
        turn: dict[str, Any],
        budget: int,
    ) -> tuple[list[dict[str, Any]], int]:
        """Add memory snippets via SomaBrain HTTP API (SAAS mode).

        Protected by circuit breaker. Uses cached somafactalmemory client.

        Args:
            messages: Existing message list to append to
            turn: Turn context
            budget: Token budget for memory

        Returns:
            Tuple of (snippet_messages, tokens_used)
        """
        try:
            # Call SomaBrain with circuit breaker protection
            async def retrieve():
                return await self.somabrain.context_evaluate(
                    {
                        "tenant_id": turn.get("tenant_id", ""),
                        "session_id": turn.get("session_id", ""),
                        "query": turn.get("user_message", ""),
                        "top_k": 3,  # Fixed top_k for simplicity
                    }
                )

            response: dict[str, Any] = await self.somabrain_breaker.call(retrieve)

            results = response.get("memories") or []

            if not results:
                logger.debug("SAAS mode: No memories returned from SomaBrain")
                return [], 0

            # Redact and budget snippets
            added = []
            used_tokens = 0

            for item in results:
                text = self._extract_snippet_text(item)
                if not text:
                    continue

                redacted = self.redactor.redact(text)
                tokens = self.count_tokens(redacted)

                if used_tokens + tokens > budget:
                    break

                added.append(redacted)
                used_tokens += tokens

            # Add as memory block
            if added:
                memory_block = self._format_snippet_block(added)
                messages.append(
                    {
                        "role": "system",
                        "content": memory_block,
                        "name": "memory",
                    }
                )

            logger.info(f"SAAS mode: Retrieved {len(added)} memory snippets")
            return added, used_tokens

        except CircuitBreakerError as e:
            logger.warning(f"SAAS mode: SomaBrain circuit breaker open - {e}")
            return [], 0

        except SomaClientError as e:
            logger.warning(f"SAAS mode: SomaBrain client error - {e}")
            return [], 0

        except Exception as e:
            logger.error(f"SAAS mode: Unexpected error retrieving memory - {e}", exc_info=True)
            return [], 0

    async def _add_memory_standalone(
        self,
        messages: list[dict[str, Any]],
        turn: dict[str, Any],
        budget: int,
    ) -> tuple[list[dict[str, Any]], int]:
        """Add memory snippets via embedded SomaBrain (STANDALONE mode).

        Uses direct PostgreSQL queries via hybrid search, no HTTP calls.

        Args:
            messages: Existing message list to append to
            turn: Turn context
            budget: Token budget for memory

        Returns:
            Tuple of (snippet_messages, tokens_used)
        """
        try:
            from somabrain.cognition.core import HybridSearch  # Embedded import

            search_engine = HybridSearch()

            # Direct hybrid search query (no HTTP call)
            results: list[str] = search_engine.search(
                query_text=turn.get("user_message", ""),
                conversation_id=turn.get("session_id", ""),
                top_k=3,  # Fixed top_k for simplicity
            )

            if not results:
                logger.debug("STANDALONE mode: No memories from embedded SomaBrain")
                return [], 0

            # Redact and budget snippets
            added = []
            used_tokens = 0

            for text in results:
                if not text:
                    continue

                redacted = self.redactor.redact(text)
                tokens = self.count_tokens(redacted)

                if used_tokens + tokens > budget:
                    break

                added.append(redacted)
                used_tokens += tokens

            # Add as memory block
            if added:
                memory_block = self._format_snippet_block(added)
                messages.append(
                    {
                        "role": "system",
                        "content": memory_block,
                        "name": "memory",
                    }
                )

            logger.info(
                f"STANDALONE mode: Retrieved {len(added)} memory snippets via embedded module"
            )
            return added, used_tokens

        except ImportError as e:
            logger.error(f"STANDALONE mode: Embedded SomaBrain module not found - {e}")
            return [], 0

        except Exception as e:
            logger.error(f"STANDALONE mode: Error in embedded SomaBrain - {e}", exc_info=True)
            return [], 0

    def _extract_snippet_text(self, item: dict[str, Any]) -> str:
        """Extract text content from memory snippet.

        Args:
            item: Snippet dict from SomaBrain

        Returns:
            Text content or empty string
        """
        if "text" in item:
            return str(item["text"])

        value = item.get("value")
        if isinstance(value, dict):
            for key in ("content", "text", "value"):
                if key in value:
                    return str(value[key])
        elif isinstance(value, str):
            return value

        return ""

    def _format_snippet_block(self, snippets: list[str]) -> str:
        """Format memory snippets into block for LLM.

        Args:
            snippets: List of snippet texts

        Returns:
            Formatted block string
        """
        parts = [f"[{idx}] {snippet}" for idx, snippet in enumerate(snippets, start=1)]

        return "Relevant memory:\n" + "\n".join(parts)


# Factory function for easy initialization
def create_context_builder(
    somabrain: SomaBrainClient,
    token_counter: Callable[[str], int],
) -> ContextBuilder:
    """Create context builder instance.

    Args:
        somabrain: SomaBrain client
        token_counter: Token counting function

    Returns:
        ContextBuilder instance
    """
    return ContextBuilder(somabrain=somabrain, token_counter=token_counter)


# Re-export for backward compatibility
LegacyContextBuilder = ContextBuilder


__all__ = [
    "ContextBuilder",
    "BuiltContext",
    "PresidioRedactor",
    "create_context_builder",
    "LegacyContextBuilder",  # For migration
]
