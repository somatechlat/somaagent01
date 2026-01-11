"""Somabrain-aware context builder for SomaAgent01.

Integrates with AgentIQ Governor for lane-based token budgeting.
"""

from __future__ import annotations

import asyncio
import logging
import math
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Protocol, TYPE_CHECKING

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from admin.core.observability.metrics import ContextBuilderMetrics
from admin.core.somabrain_client import SomaBrainClient, SomaClientError
from services.common import degradation_monitor
from services.common.resilience import AsyncCircuitBreaker, CircuitBreakerError

if TYPE_CHECKING:
    from admin.agents.services.agentiq_governor import LanePlan

LOGGER = logging.getLogger(__name__)

# Circuit Breaker for SomaBrain
SOMABRAIN_BREAKER = AsyncCircuitBreaker(name="somabrain_breaker", fail_max=5, reset_timeout=30)


class SomabrainHealthState(str, Enum):
    """Somabrainhealthstate class implementation."""

    NORMAL = "normal"
    DEGRADED = "degraded"
    DOWN = "down"


class RedactorProtocol(Protocol):  # pragma: no cover - interface definition
    """Protocol for text redaction services."""

    def redact(self, text: str) -> str:
        """Redact sensitive data from text.

        Args:
            text: The text to redact.

        Returns:
            Redacted text.
        """
        ...


class RealPresidioRedactor:
    """Production-grade sensitive data redaction using Presidio.


    - Real implementation (no mocks) using presidio-analyzer/anonymizer
    - Lazy loading to reduce startup time
    - Handles PII entities: PHONE_NUMBER, EMAIL_ADDRESS, IBAN, CREDIT_CARD
    """

    def __init__(self):
        """Initialize the instance."""

        self._analyzer = None
        self._anonymizer = None
        self._entities = ["PHONE_NUMBER", "EMAIL_ADDRESS", "IBAN", "CREDIT_CARD", "US_SSN"]

    def _ensure_loaded(self):
        """Execute ensure loaded."""

        if self._analyzer is None:
            try:
                from presidio_analyzer import AnalyzerEngine
                from presidio_anonymizer import AnonymizerEngine

                self._analyzer = AnalyzerEngine()
                self._anonymizer = AnonymizerEngine()
            except ImportError as e:
                LOGGER.error(
                    "Presidio dependencies missing. Redaction disabled. Install requirements.",
                    exc_info=True,
                )
                raise e

    def redact(self, text: str) -> str:
        """Execute redact.

        Args:
            text: The text.
        """

        if not text:
            return ""

        try:
            self._ensure_loaded()
            if not self._analyzer or not self._anonymizer:
                return text

            results = self._analyzer.analyze(text=text, entities=self._entities, language="en")
            anonymized = self._anonymizer.anonymize(text=text, analyzer_results=results)
            return anonymized.text
        except Exception:
            LOGGER.warning("Presidio redaction failed. Returning original text.", exc_info=True)
            return text  # Fail open (return text) to avoid breaking conversation, but log error.


@dataclass
class BuiltContext:
    """Result of context building for a turn.

    Attributes:
        system_prompt: The system prompt for the LLM
        messages: List of formatted messages for the LLM
        token_counts: Token counts by category (system, history, snippets, user)
        debug: Debug information about the build process
        lane_actual: Actual token usage per lane (for AgentIQ Governor)
    """

    system_prompt: str
    messages: List[Dict[str, Any]]
    token_counts: Dict[str, int]
    debug: Dict[str, Any]
    lane_actual: Dict[str, int] = field(default_factory=dict)


class ContextBuilder:
    """High-level context builder that tracks Somabrain health + metrics."""

    DEFAULT_TOP_K = 8
    DEGRADED_TOP_K = 3
    DEGRADED_WINDOW_SECONDS = 15

    def __init__(
        self,
        *,
        somabrain: SomaBrainClient,
        metrics: ContextBuilderMetrics,
        token_counter: Callable[[str], int],
        redactor: Optional[RedactorProtocol] = None,
        health_provider: Optional[Callable[[], SomabrainHealthState]] = None,
        on_degraded: Optional[Callable[[float], None]] = None,
        use_optimal_budget: bool = False,
    ) -> None:
        """Initialize the instance."""

        self.somabrain = somabrain
        self.metrics = metrics
        self.count_tokens = token_counter
        self.redactor = redactor or RealPresidioRedactor()
        self.health_provider = health_provider or (lambda: SomabrainHealthState.NORMAL)
        self.on_degraded = on_degraded or self._default_on_degraded
        self.use_optimal_budget = use_optimal_budget

    @staticmethod
    def _default_on_degraded(duration: float) -> None:
        """Record Somabrain degradation in the system monitor."""
        if not degradation_monitor.is_monitoring():
            LOGGER.warning("Somabrain degraded for %.1fs (monitor disabled)", duration)
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            LOGGER.warning("Somabrain degraded for %.1fs (no running loop)", duration)
            return
        err = RuntimeError(f"Somabrain degraded for {duration:.1f}s")
        loop.create_task(degradation_monitor.record_component_failure("somabrain", err))

    async def build_for_turn(
        self,
        turn: Dict[str, Any],
        *,
        max_prompt_tokens: int,
        lane_plan: Optional["LanePlan"] = None,
    ) -> BuiltContext:
        """Build context for a conversation turn.

        Args:
            turn: Turn context with user_message, history, system_prompt, etc.
            max_prompt_tokens: Overall token budget (used if lane_plan is None)
            lane_plan: Optional AgentIQ lane plan for per-lane budgeting

        Returns:
            BuiltContext with assembled messages and token usage
        """
        with self.metrics.time_total():
            state = self._current_health()
            reason = state.value
            system_prompt = (turn.get("system_prompt") or "You are SomaAgent01.").strip()
            user_message = (turn.get("user_message") or "").strip()
            history = self._coerce_history(turn.get("history"))

            snippets: List[Dict[str, Any]] = []
            snippet_tokens = 0

            if state != SomabrainHealthState.DOWN:
                raw_snippets = await self._retrieve_snippets(turn, state)
                scored_snippets = self._apply_salience(raw_snippets)
                self.metrics.inc_snippets(stage="salient", count=len(scored_snippets))

                ranked_snippets = self._rank_and_clip_snippets(scored_snippets, state)
                self.metrics.inc_snippets(stage="ranked", count=len(ranked_snippets))

                snippets = self._redact_snippets(ranked_snippets)
                self.metrics.inc_snippets(stage="redacted", count=len(snippets))

                snippet_tokens = self._count_snippet_tokens(snippets)
                self.metrics.inc_snippets(stage="final", count=len(snippets))
            else:
                LOGGER.debug(
                    "Somabrain DOWN – skipping retrieval", extra={"session": turn.get("session_id")}
                )

            # Multimodal Instructions Injection
            mm_instruction = self._build_multimodal_instructions()
            if mm_instruction:
                system_prompt += mm_instruction

            with self.metrics.time_tokenisation():
                system_tokens = self.count_tokens(system_prompt)
                user_tokens = self.count_tokens(user_message)

            budget_for_history = max_prompt_tokens - (system_tokens + user_tokens + snippet_tokens)
            if budget_for_history < 0:
                available_for_snippets = max_prompt_tokens - (system_tokens + user_tokens)
                if self.use_optimal_budget:
                    snippets, snippet_tokens = self._trim_snippets_optimal(
                        snippets, available_for_snippets
                    )
                    self.metrics.inc_snippets(stage="budgeted_optimal", count=len(snippets))
                else:
                    snippets, snippet_tokens = self._trim_snippets_to_budget(
                        snippets,
                        snippet_tokens,
                        available_for_snippets,
                    )
                    self.metrics.inc_snippets(stage="budgeted_greedy", count=len(snippets))
                budget_for_history = max(
                    0, max_prompt_tokens - (system_tokens + user_tokens + snippet_tokens)
                )

            trimmed_history = self._trim_history(history, budget_for_history)
            history_tokens = sum(
                self.count_tokens(msg.get("content", "")) for msg in trimmed_history
            )

            if len(history) > len(trimmed_history):
                await self._store_summary(
                    turn=turn,
                    original_history=history,
                    trimmed_history=trimmed_history,
                )

            self.metrics.record_tokens(
                before_budget=sum(self.count_tokens(m.get("content", "")) for m in history),
                after_budget=history_tokens,
                after_redaction=(
                    self.count_tokens("\n".join(s["text"] for s in snippets))
                    if snippets
                    else history_tokens
                ),
                prompt_tokens=system_tokens + user_tokens + snippet_tokens + history_tokens,
            )
            self.metrics.inc_prompt()

            with self.metrics.time_prompt():
                messages: List[Dict[str, Any]] = []
                messages.append({"role": "system", "content": system_prompt})
                messages.extend(trimmed_history)
                if snippets:
                    snippet_block = self._format_snippet_block(snippets)
                    messages.append({"role": "system", "content": snippet_block, "name": "memory"})
                messages.append({"role": "user", "content": user_message})

            debug = {
                "somabrain_state": state.value,
                "somabrain_reason": reason,
                "snippet_ids": [snippet.get("id") for snippet in snippets],
                "snippet_count": len(snippets),
                "session_id": turn.get("session_id"),
                "tenant_id": turn.get("tenant_id"),
            }

            return BuiltContext(
                system_prompt=system_prompt,
                messages=messages,
                token_counts={
                    "system": system_tokens,
                    "history": history_tokens,
                    "snippets": snippet_tokens,
                    "user": user_tokens,
                },
                debug=debug,
                # Map token counts to AgentIQ lanes for Governor reporting
                lane_actual={
                    "system_policy": system_tokens,
                    "history": history_tokens,
                    "memory": snippet_tokens,
                    "tools": 0,  # Tools are added by caller after context build
                    "tool_results": 0,  # Tool results are added by caller
                    "buffer": lane_plan.buffer if lane_plan else 200,
                },
            )

    def _current_health(self) -> SomabrainHealthState:
        """Execute current health."""

        try:
            state = self.health_provider()
            if isinstance(state, SomabrainHealthState):
                return state
            return SomabrainHealthState(state)  # type: ignore[arg-type]
        except Exception:
            LOGGER.debug("Health provider failed; defaulting to degraded", exc_info=True)
            return SomabrainHealthState.DEGRADED

    def _coerce_history(self, history: Any) -> List[Dict[str, str]]:
        """Execute coerce history.

        Args:
            history: The history.
        """

        if not isinstance(history, list):
            return []
        coerced: List[Dict[str, str]] = []
        for entry in history:
            if not isinstance(entry, dict):
                continue
            role = str(entry.get("role") or "user")
            content = str(entry.get("content") or "")
            if not content:
                continue
            coerced.append({"role": role, "content": content})
        return coerced

    async def _retrieve_snippets(
        self,
        turn: Dict[str, Any],
        state: SomabrainHealthState,
    ) -> List[Dict[str, Any]]:
        """Execute retrieve snippets.

        Args:
            turn: The turn.
            state: The state.
        """

        top_k = self.DEFAULT_TOP_K if state == SomabrainHealthState.NORMAL else self.DEGRADED_TOP_K
        payload = {
            "tenant_id": turn.get("tenant_id"),
            "session_id": turn.get("session_id"),
            "query": turn.get("user_message", ""),
            "top_k": top_k,
        }
        try:
            with self.metrics.time_retrieval(state=state.value):
                # We use specific exception catching to avoid retrying on 4xx if possible,
                # but SomaClientError might be generic.
                @retry(
                    stop=stop_after_attempt(3),
                    wait=wait_exponential(multiplier=1, min=1, max=10),
                    retry=retry_if_exception_type((SomaClientError, TimeoutError)),
                    reraise=True,
                )
                async def _reliable_evaluate(p):
                    """Execute reliable evaluate.

                    Args:
                        p: The p.
                    """

                    return await SOMABRAIN_BREAKER.call(self.somabrain.context_evaluate, p)

                resp = await _reliable_evaluate(payload)
                self.metrics.inc_snippets(stage="retrieved", count=len(resp.get("candidates", [])))

        except CircuitBreakerError:
            LOGGER.warning("Somabrain circuit open. Skipping context retrieval.")
            self.on_degraded(self.DEGRADED_WINDOW_SECONDS)
            return []
        except SomaClientError as exc:
            LOGGER.info(
                "Somabrain context_evaluate failed after retries",
                exc_info=True,
                extra={"state": state.value},
            )
            if state == SomabrainHealthState.NORMAL:
                self.on_degraded(self.DEGRADED_WINDOW_SECONDS)
            LOGGER.debug("SomaBrain error detail", extra={"error": str(exc)})
            return []
        except Exception:
            LOGGER.exception("Unexpected Somabrain failure during context evaluation")
            self.on_degraded(self.DEGRADED_WINDOW_SECONDS)
            return []
        results = resp.get("candidates") or resp.get("results") or []
        snippets: List[Dict[str, Any]] = []
        for item in results:
            if not isinstance(item, dict):
                continue
            text = self._extract_text(item)
            if not text:
                continue
            snippets.append(
                {
                    "id": item.get("id"),
                    "score": item.get("score"),
                    "text": text,
                    "metadata": item.get("metadata") or {},
                }
            )
        return snippets

    def _extract_text(self, item: Dict[str, Any]) -> str:
        """Execute extract text.

        Args:
            item: The item.
        """

        if item.get("text"):
            return str(item["text"])
        value = item.get("value")
        if isinstance(value, dict):
            for key in ("content", "text", "value"):
                if value.get(key):
                    return str(value[key])
        if isinstance(value, str):
            return value
        return ""

    def _rank_and_clip_snippets(
        self, snippets: List[Dict[str, Any]], state: SomabrainHealthState
    ) -> List[Dict[str, Any]]:
        """Execute rank and clip snippets.

        Args:
            snippets: The snippets.
            state: The state.
        """

        if not snippets:
            return []
        with self.metrics.time_ranking():
            ranked = sorted(snippets, key=lambda s: self._safe_float(s.get("score")), reverse=True)
            limit = (
                self.DEFAULT_TOP_K if state == SomabrainHealthState.NORMAL else self.DEGRADED_TOP_K
            )
            return ranked[:limit]

    def _apply_salience(self, snippets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute apply salience.

        Args:
            snippets: The snippets.
        """

        if not snippets:
            return []
        enriched: List[Dict[str, Any]] = []
        now = datetime.now(timezone.utc)
        with self.metrics.time_salience():
            for snippet in snippets:
                meta = snippet.get("metadata") or {}
                base_score = self._safe_float(snippet.get("score"))
                recency = self._recency_boost(meta, now)
                final_score = 0.7 * base_score + 0.3 * recency
                updated = dict(snippet)
                updated["score"] = final_score
                enriched.append(updated)
        return enriched

    def _safe_float(self, value: Any) -> float:
        """Execute safe float.

        Args:
            value: The value.
        """

        try:
            return float(value)
        except Exception:
            return 0.0

    def _recency_boost(self, metadata: Dict[str, Any], now: datetime) -> float:
        """Execute recency boost.

        Args:
            metadata: The metadata.
            now: The now.
        """

        timestamp = metadata.get("timestamp") or metadata.get("created_at")
        if not timestamp:
            return 0.5
        try:
            dt = datetime.fromisoformat(str(timestamp))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        except Exception:
            return 0.5
        age_days = max(0.0, (now - dt).total_seconds() / 86400)
        return math.exp(-age_days / 30.0)

    def _redact_snippets(self, snippets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute redact snippets.

        Args:
            snippets: The snippets.
        """

        redacted: List[Dict[str, Any]] = []
        with self.metrics.time_redaction():
            for snippet in snippets:
                text = snippet.get("text", "")
                cleaned = self.redactor.redact(text)
                new_snippet = dict(snippet)
                new_snippet["text"] = cleaned
                redacted.append(new_snippet)
        return redacted

    def _count_snippet_tokens(self, snippets: List[Dict[str, Any]]) -> int:
        """Execute count snippet tokens.

        Args:
            snippets: The snippets.
        """

        return sum(self.count_tokens(snippet.get("text", "")) for snippet in snippets)

    def _trim_snippets_to_budget(
        self,
        snippets: List[Dict[str, Any]],
        snippet_tokens: int,
        allowed_tokens: int,
    ) -> tuple[List[Dict[str, Any]], int]:
        """Execute trim snippets to budget.

        Args:
            snippets: The snippets.
            snippet_tokens: The snippet_tokens.
            allowed_tokens: The allowed_tokens.
        """

        if allowed_tokens <= 0 or not snippets:
            return [], 0
        trimmed: List[Dict[str, Any]] = []
        total = 0
        for snippet in snippets:
            tokens = self.count_tokens(snippet.get("text", ""))
            if total + tokens > allowed_tokens:
                break
            trimmed.append(snippet)
            total += tokens
        return trimmed, total

    def _trim_snippets_optimal(
        self,
        snippets: List[Dict[str, Any]],
        allowed_tokens: int,
    ) -> tuple[List[Dict[str, Any]], int]:
        """Knapsack-style selection to maximize score within token budget."""
        if allowed_tokens <= 0 or not snippets:
            return [], 0

        # Get token cost for each snippet
        items = []
        for s in snippets:
            cost = self.count_tokens(s.get("text", ""))
            score = self._safe_float(s.get("score"))
            # Skip items that alone exceed budget (optional optimization)
            if cost <= allowed_tokens:
                items.append((cost, score, s))

        n = len(items)
        if n == 0:
            return [], 0

        # DP Table: dp[i][w] = max score using first i items with weight limit w
        # Optimised space: 1D array dp[w] stores max score for capacity w
        dp = [0.0] * (allowed_tokens + 1)
        # To reconstruct solution, we keep track of which items led to the max score
        # keep[i][w] = True if item i was included for capacity w
        # Since we need full reconstruction and N/W are relatively small (context window),
        # 2D table for reconstruction is safer or dict based approach.
        # Given allowed_tokens can be 8k+, O(N*W) might be slow if W is token count?
        # Typically snippet budget is ~1-2k. 2000 * 10 = 20k operations. Fast.

        # Using 2D for reconstruction simplicity
        # dp[i][w]
        dp_table = [[0.0 for _ in range(allowed_tokens + 1)] for _ in range(n + 1)]

        for i in range(1, n + 1):
            w_i, v_i, _ = items[i - 1]
            for w in range(allowed_tokens + 1):
                if w_i <= w:
                    dp_table[i][w] = max(dp_table[i - 1][w], dp_table[i - 1][w - w_i] + v_i)
                else:
                    dp_table[i][w] = dp_table[i - 1][w]

        # Reconstruct
        selected = []
        total_tokens = 0
        w = allowed_tokens
        for i in range(n, 0, -1):
            if dp_table[i][w] != dp_table[i - 1][w]:
                # Item was selected
                cost, _, snippet = items[i - 1]
                selected.append(snippet)
                total_tokens += cost
                w -= cost

        selected.reverse()  # Restore original relative order? No, Knapsack doesn't preserve order.
        # We might want to re-sort by score or original index if order matters for context linearisation.
        # For now, we return as is (reverse selection order).

        return selected, total_tokens

    def _trim_history(
        self,
        history: List[Dict[str, str]],
        allowed_tokens: int,
    ) -> List[Dict[str, str]]:
        """Execute trim history.

        Args:
            history: The history.
            allowed_tokens: The allowed_tokens.
        """

        if allowed_tokens <= 0 or not history:
            return []
        trimmed: List[Dict[str, str]] = []
        remaining = allowed_tokens
        for entry in reversed(history):
            tokens = self.count_tokens(entry.get("content", ""))
            if tokens > remaining:
                continue
            trimmed.append(entry)
            remaining -= tokens
            if remaining <= 0:
                break
        trimmed.reverse()
        return trimmed

    def _format_snippet_block(self, snippets: List[Dict[str, Any]]) -> str:
        """Execute format snippet block.

        Args:
            snippets: The snippets.
        """

        parts = []
        for idx, snippet in enumerate(snippets, start=1):
            meta = snippet.get("metadata") or {}
            label = meta.get("source") or meta.get("type") or "memory"
            text = snippet.get("text", "")
            parts.append(f"[{idx}] ({label})\n{text}")
        return "Relevant memory:\n" + "\n\n".join(parts)

    async def _store_summary(
        self,
        *,
        turn: Dict[str, Any],
        original_history: List[Dict[str, Any]],
        trimmed_history: List[Dict[str, Any]],
    ) -> None:
        """Create and store an extractive session summary in SomaBrain."""
        try:
            summary_text = self._build_summary(original_history, trimmed_history)
            if not summary_text:
                return
            payload = {
                "tenant_id": turn.get("tenant_id"),
                "memories": [
                    {
                        "type": "session_summary",
                        "text": summary_text,
                        "session_id": turn.get("session_id"),
                        "persona_id": turn.get("persona_id"),
                        "tags": ["session_summary", "auto", "context_builder"],
                        "metadata": {
                            "trimmed_from": len(original_history),
                            "trimmed_to": len(trimmed_history),
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        },
                    }
                ],
            }
            await self.somabrain.remember_batch(payload)
            self.metrics.inc_snippets(stage="summary", count=1)
        except SomaClientError:
            LOGGER.info("Failed to store session summary (SomaBrain error)", exc_info=True)
        except Exception:
            LOGGER.exception("Unexpected failure while storing session summary")

    def _build_summary(
        self,
        original_history: List[Dict[str, Any]],
        trimmed_history: List[Dict[str, Any]],
    ) -> str:
        """Extractive summary built from pruned messages, capped to 1024 chars."""
        removed_count = len(original_history) - len(trimmed_history)
        if removed_count <= 0:
            return ""
        removed = original_history[:removed_count]
        parts: List[str] = []
        for msg in removed:
            role = msg.get("role", "user")
            content = (msg.get("content") or "").strip()
            if not content:
                continue
            parts.append(f"{role}: {content}")
            if len(" | ".join(parts)) > 1024:
                break
        return " | ".join(parts)[:1024]

    def _build_multimodal_instructions(self) -> str:
        """Build system prompt instructions for multimodal capabilities."""
        if os.environ.get("SA01_ENABLE_MULTIMODAL_CAPABILITIES", "false").lower() != "true":
            return ""

        return (
            "\n\nMULTIMODAL CAPABILITIES:\n"
            "You have access to tools that can generate images, diagrams (Mermaid/PlantUML), "
            "and capture screenshots. If the user explicitly asks for these, or if "
            "visual aids would significantly enhance the response, you MUST output a JSON "
            "block at the END of your response (after all text) in the following format:\n\n"
            "```json\n"
            "{\n"
            '  "multimodal_plan": {\n'
            '    "version": "1.0",\n'
            '    "tasks": [\n'
            "      {\n"
            '        "task_id": "step_00",\n'
            '        "step_type": "generate_image",\n'
            '        "modality": "image",\n'
            '        "depends_on": [],\n'
            '        "params": {\n'
            '          "prompt": "Detailed description of the image to generate",\n'
            '          "format": "png",\n'
            '          "dimensions": {"width": 1920, "height": 1080}\n'
            "        },\n"
            '        "constraints": {"max_cost_cents": 50},\n'
            '        "quality_gate": {"enabled": true, "min_score": 0.7, "max_reworks": 2}\n'
            "      }\n"
            "    ],\n"
            '    "budget": {"max_cost_cents": 500}\n'
            "  }\n"
            "}\n"
            "```\n\n"
            "Supported step_types: generate_image, generate_diagram, capture_screenshot.\n"
            "Do NOT ask for confirmation. Just output the JSON block to trigger execution."
        )
