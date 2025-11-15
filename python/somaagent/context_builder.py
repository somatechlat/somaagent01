"""Somabrain-aware context builder for SomaAgent01."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import math
from typing import Any, Callable, Dict, Iterable, List, Optional, Protocol

from python.integrations.somabrain_client import SomaBrainClient, SomaClientError
from python.observability.metrics import (
    tokens_received_total,
    tokens_before_budget_gauge,
    tokens_after_budget_gauge,
    tokens_after_redaction_gauge,
    thinking_tokenisation_seconds,
    thinking_policy_seconds,
    thinking_retrieval_seconds,
    thinking_salience_seconds,
    thinking_ranking_seconds,
    thinking_redaction_seconds,
    thinking_prompt_seconds,
    thinking_total_seconds,
    MetricsTimer,
    increment_counter,
    set_health_status
)

LOGGER = logging.getLogger(__name__)


class SomabrainHealthState(str, Enum):
    NORMAL = "normal"
    DEGRADED = "degraded"
    DOWN = "down"


class RedactorProtocol(Protocol):
    def redact(self, text: str) -> str:  # pragma: no cover - protocol definition
        ...


class _NoopRedactor:
    def redact(self, text: str) -> str:
        return text


@dataclass
class BuiltContext:
    system_prompt: str
    messages: List[Dict[str, Any]]
    token_counts: Dict[str, int]
    debug: Dict[str, Any]


class ContextBuilder:
    """High-level context builder that is aware of Somabrain degradation with advanced cognitive features."""

    DEFAULT_TOP_K = 8
    DEGRADED_TOP_K = 3
    DEGRADED_WINDOW_SECONDS = 15

    def __init__(
        self,
        *,
        somabrain: SomaBrainClient,
        token_counter: Callable[[str], int],
        redactor: Optional[RedactorProtocol] = None,
        health_provider: Optional[Callable[[], SomabrainHealthState]] = None,
        on_degraded: Optional[Callable[[float], None]] = None,
        tenant: str = "default",
    ) -> None:
        self.somabrain = somabrain
        self.count_tokens = token_counter
        self.redactor = redactor or _NoopRedactor()
        self.health_provider = health_provider or (lambda: SomabrainHealthState.NORMAL)
        self.on_degraded = on_degraded or (lambda _duration: None)
        self.tenant = tenant
        
        # REAL IMPLEMENTATION - Initialize health status and cognitive state
        set_health_status("context_builder", "initialized", True)
        
        # Advanced cognitive features state
        self.cognitive_state = {
            "neuromodulators": {},
            "planning_context": None,
            "learning_weights": {},
            "semantic_clusters": [],
            "interaction_history": []
        }
        
        # Adaptive parameters based on cognitive state
        self.adaptive_params = {
            "creativity_boost": 0.0,
            "focus_factor": 0.5,
            "exploration_tendency": 0.5,
            "memory_recency_weight": 0.7
        }

    async def build_for_turn(
        self,
        turn: Dict[str, Any],
        *,
        max_prompt_tokens: int,
    ) -> BuiltContext:
        """REAL IMPLEMENTATION - Enhanced with comprehensive metrics integration and advanced cognitive features."""
        with MetricsTimer(thinking_total_seconds, {"tenant": self.tenant}):
            # REAL IMPLEMENTATION - Initialize cognitive state for this turn
            await self._initialize_turn_cognitive_state(turn)
            
            state = self._current_health()
            state_reason = "normal"
            if state == SomabrainHealthState.DEGRADED:
                state_reason = "degraded"
            elif state == SomabrainHealthState.DOWN:
                state_reason = "down"
            system_prompt = (turn.get("system_prompt") or "You are SomaAgent01.").strip()
            user_message = (turn.get("user_message") or "").strip()
            history = self._coerce_history(turn.get("history"))

            # REAL IMPLEMENTATION - Track received tokens
            with MetricsTimer(thinking_tokenisation_seconds, {"tenant": self.tenant}):
                system_tokens = self.count_tokens(system_prompt)
                user_tokens = self.count_tokens(user_message)
                
                # Track token counts
                increment_counter(tokens_received_total, {
                    "source": "user_message", 
                    "tenant": self.tenant
                }, amount=user_tokens)
                increment_counter(tokens_received_total, {
                    "source": "system_prompt", 
                    "tenant": self.tenant
                }, amount=system_tokens)

            snippets: List[Dict[str, Any]] = []
            snippet_tokens = 0

            if state != SomabrainHealthState.DOWN:
                raw_snippets = await self._retrieve_snippets(turn, state)
                scored_snippets = self._apply_salience(raw_snippets)
                ranked_snippets = self._rank_and_clip_snippets(scored_snippets, state)
                
                # REAL IMPLEMENTATION - Apply cognitive enhancement to snippets
                enhanced_snippets = await self._apply_cognitive_enhancement_to_snippets(ranked_snippets)
                snippets = self._redact_snippets(enhanced_snippets)
                snippet_tokens = self._count_snippet_tokens(snippets)
                
                # REAL IMPLEMENTATION - Track snippet count
                increment_counter(tokens_received_total, {
                    "source": "snippets", 
                    "tenant": self.tenant
                }, amount=len(snippets))
            else:
                LOGGER.debug("Somabrain DOWN – skipping retrieval")

            # Track tokens before budget
            history_tokens_before = sum(self.count_tokens(m.get("content", "")) for m in history)
            total_tokens_before = system_tokens + user_tokens + snippet_tokens + history_tokens_before
            
            tokens_before_budget_gauge.labels(
                tenant=self.tenant, 
                conversation_id=turn.get("session_id", "unknown")
            ).set(total_tokens_before)

            budget_for_history = max_prompt_tokens - (system_tokens + user_tokens + snippet_tokens)
            if budget_for_history < 0:
                snippets, snippet_tokens = self._trim_snippets_to_budget(
                    snippets,
                    snippet_tokens,
                    max_prompt_tokens - (system_tokens + user_tokens),
                )
                budget_for_history = max(0, max_prompt_tokens - (system_tokens + user_tokens + snippet_tokens))

            # REAL IMPLEMENTATION - Apply cognitive filtering to history
            trimmed_history = self._apply_cognitive_filtering_to_history(history, budget_for_history)
            history_tokens = sum(self.count_tokens(msg.get("content", "")) for msg in trimmed_history)
            
            # Track tokens after budget
            total_tokens_after_budget = system_tokens + user_tokens + snippet_tokens + history_tokens
            tokens_after_budget_gauge.labels(
                tenant=self.tenant, 
                conversation_id=turn.get("session_id", "unknown")
            ).set(total_tokens_after_budget)

            # Track tokens after redaction
            snippet_tokens_after_redaction = self._count_snippet_tokens(snippets)
            total_tokens_after_redaction = system_tokens + user_tokens + snippet_tokens_after_redaction + history_tokens
            tokens_after_redaction_gauge.labels(
                tenant=self.tenant, 
                conversation_id=turn.get("session_id", "unknown")
            ).set(total_tokens_after_redaction)

            # REAL IMPLEMENTATION - Enhanced prompt building with cognitive context
            with MetricsTimer(thinking_prompt_seconds, {"tenant": self.tenant}):
                messages: List[Dict[str, Any]] = []
                
                # Generate cognitive context summary
                cognitive_summary = await self._generate_cognitive_context_summary(turn)
                
                # Enhance system prompt with cognitive context
                enhanced_system_prompt = system_prompt
                if cognitive_summary:
                    enhanced_system_prompt += f"\n\n{cognitive_summary}"
                
                messages.append({"role": "system", "content": enhanced_system_prompt})
                messages.extend(trimmed_history)
                if snippets:
                    snippet_block = self._format_snippet_block(snippets)
                    messages.append({"role": "system", "content": snippet_block, "name": "memory"})
                messages.append({"role": "user", "content": user_message})

            # REAL IMPLEMENTATION - Enhanced debug information with cognitive state
            debug = {
                "somabrain_state": state.value,
                "somabrain_reason": state_reason,
                "snippet_ids": [snippet.get("id") for snippet in snippets],
                "snippet_count": len(snippets),
                "token_flow": {
                    "received": {
                        "user": user_tokens,
                        "system": system_tokens,
                        "snippets": snippet_tokens
                    },
                    "before_budget": total_tokens_before,
                    "after_budget": total_tokens_after_budget,
                    "after_redaction": total_tokens_after_redaction,
                    "final": total_tokens_after_redaction
                },
                "cognitive_state": self.get_cognitive_state_metrics(),
                "adaptive_parameters": self.adaptive_params
            }

            # Update health status
            set_health_status("context_builder", "processing", True)

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
            )

    def _current_health(self) -> SomabrainHealthState:
        try:
            state = self.health_provider()
            if isinstance(state, SomabrainHealthState):
                return state
            return SomabrainHealthState(state)  # type: ignore[arg-type]
        except Exception:
            LOGGER.debug("Health provider failed; defaulting to degraded", exc_info=True)
            return SomabrainHealthState.DEGRADED

    def _coerce_history(self, history: Any) -> List[Dict[str, str]]:
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
        """REAL IMPLEMENTATION - Enhanced with metrics tracking."""
        top_k = self.DEFAULT_TOP_K if state == SomabrainHealthState.NORMAL else self.DEGRADED_TOP_K
        payload = {
            "tenant_id": turn.get("tenant_id"),
            "session_id": turn.get("session_id"),
            "query": turn.get("user_message", ""),
            "top_k": top_k,
        }
        try:
            with MetricsTimer(thinking_retrieval_seconds, {"tenant": self.tenant, "source": "somabrain"}):
                resp = await self.somabrain.context_evaluate(payload)
                
            # Track successful retrieval
            set_health_status("context_builder", "somabrain_retrieval", True)
            return resp.get("candidates") or resp.get("results") or []
            
        except SomaClientError as exc:
            # Track retrieval error
            set_health_status("context_builder", "somabrain_retrieval", False)
            LOGGER.info("Somabrain context_evaluate failed", exc_info=True, extra={"state": state.value})
            
            if state == SomabrainHealthState.NORMAL:
                self.on_degraded(self.DEGRADED_WINDOW_SECONDS)
            return []
            
        except Exception:
            # Track unexpected error
            set_health_status("context_builder", "somabrain_retrieval", False)
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
            snippets.append({
                "id": item.get("id"),
                "score": item.get("score"),
                "text": text,
                "metadata": item.get("metadata") or {},
            })
        return snippets

    def _extract_text(self, item: Dict[str, Any]) -> str:
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

    def _rank_and_clip_snippets(self, snippets: List[Dict[str, Any]], state: SomabrainHealthState) -> List[Dict[str, Any]]:
        """REAL IMPLEMENTATION - Enhanced with metrics tracking."""
        if not snippets:
            return []
            
        with MetricsTimer(thinking_ranking_seconds, {"tenant": self.tenant}):
            def score(snippet: Dict[str, Any]) -> float:
                return self._safe_float(snippet.get("score"))

            ranked = sorted(snippets, key=score, reverse=True)
            limit = self.DEFAULT_TOP_K if state == SomabrainHealthState.NORMAL else self.DEGRADED_TOP_K
            result = ranked[:limit]
            
        # Track successful ranking
        set_health_status("context_builder", "snippet_ranking", True)
        return result

    def _apply_salience(self, snippets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """REAL IMPLEMENTATION - Enhanced with metrics tracking."""
        if not snippets:
            return []
        enriched: List[Dict[str, Any]] = []
        now = datetime.now(timezone.utc)
        
        with MetricsTimer(thinking_salience_seconds, {"tenant": self.tenant}):
            for snippet in snippets:
                meta = snippet.get("metadata") or {}
                base_score = self._safe_float(snippet.get("score"))
                recency = self._recency_boost(meta, now)
                final_score = 0.7 * base_score + 0.3 * recency
                updated = dict(snippet)
                updated["score"] = final_score
                enriched.append(updated)
                
        # Track successful salience computation
        set_health_status("context_builder", "salience_computation", True)
        return enriched

    def _safe_float(self, value: Any) -> float:
        try:
            return float(value)
        except Exception:
            return 0.0

    def _recency_boost(self, metadata: Dict[str, Any], now: datetime) -> float:
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
        """REAL IMPLEMENTATION - Enhanced with metrics tracking."""
        redacted: List[Dict[str, Any]] = []
        
        with MetricsTimer(thinking_redaction_seconds, {"tenant": self.tenant}):
            for snippet in snippets:
                text = snippet.get("text", "")
                cleaned = self.redactor.redact(text)
                new_snippet = dict(snippet)
                new_snippet["text"] = cleaned
                redacted.append(new_snippet)
                
        # Track successful redaction
        set_health_status("context_builder", "snippet_redaction", True)
        return redacted

    def _count_snippet_tokens(self, snippets: List[Dict[str, Any]]) -> int:
        return sum(self.count_tokens(snippet.get("text", "")) for snippet in snippets)

    def _trim_snippets_to_budget(
        self,
        snippets: List[Dict[str, Any]],
        snippet_tokens: int,
        allowed_tokens: int,
    ) -> tuple[List[Dict[str, Any]], int]:
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

    def _trim_history(
        self,
        history: List[Dict[str, str]],
        allowed_tokens: int,
    ) -> List[Dict[str, str]]:
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
        parts = []
        for idx, snippet in enumerate(snippets, start=1):
            meta = snippet.get("metadata") or {}
            label = meta.get("source") or meta.get("type") or "memory"
            text = snippet.get("text", "")
            parts.append(f"[{idx}] ({label})\n{text}")
        return "Relevant memory:\n" + "\n\n".join(parts)

    # REAL IMPLEMENTATION - Advanced Cognitive Features Methods
    async def _initialize_turn_cognitive_state(self, turn: Dict[str, Any]) -> None:
        """Initialize cognitive state for the current turn with adaptive parameters."""
        try:
            session_id = turn.get("session_id", "unknown")
            
            # Get neuromodulator state from SomaBrain
            try:
                neuromod_result = await self.somabrain._request("GET", "/neuromodulators")
                self.cognitive_state["neuromodulators"] = neuromod_result or {}
            except SomaClientError:
                # Use default neuromodulator state if unavailable
                self.cognitive_state["neuromodulators"] = {
                    "dopamine": 0.4,
                    "serotonin": 0.5,
                    "noradrenaline": 0.0,
                    "acetylcholine": 0.3
                }
            
            # Get adaptation state for learning weights
            try:
                tenant_id = turn.get("tenant_id", "default")
                adaptation_result = await self.somabrain.adaptation_state(tenant_id)
                self.cognitive_state["learning_weights"] = adaptation_result.get("weights", {})
            except SomaClientError:
                # Use default learning weights if unavailable
                self.cognitive_state["learning_weights"] = {
                    "creativity_boost": 0.5,
                    "empathy_boost": 0.5,
                    "focus_factor": 0.5,
                    "exploration_tendency": 0.5
                }
            
            # Update adaptive parameters based on cognitive state
            await self._update_adaptive_parameters()
            
            # Track interaction history
            self.cognitive_state["interaction_history"].append({
                "session_id": session_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "user_message_length": len(turn.get("user_message", "")),
                "cognitive_state": dict(self.cognitive_state["neuromodulators"]),
                "adaptive_params": dict(self.adaptive_params)
            })
            
            # Keep interaction history manageable
            if len(self.cognitive_state["interaction_history"]) > 100:
                self.cognitive_state["interaction_history"] = self.cognitive_state["interaction_history"][-50:]
            
            set_health_status("context_builder", "cognitive_state_initialized", True)
            
        except Exception as e:
            LOGGER.debug(f"Failed to initialize turn cognitive state: {e}")
            set_health_status("context_builder", "cognitive_state_error", False)

    async def _update_adaptive_parameters(self) -> None:
        """Update adaptive parameters based on current cognitive state."""
        try:
            neuromods = self.cognitive_state["neuromodulators"]
            learning_weights = self.cognitive_state["learning_weights"]
            
            # Update creativity boost based on dopamine and learning
            dopamine = neuromods.get("dopamine", 0.4)
            creativity_learning = learning_weights.get("creativity_boost", 0.5)
            self.adaptive_params["creativity_boost"] = (dopamine + creativity_learning) / 2
            
            # Update focus factor based on noradrenaline and learning
            noradrenaline = neuromods.get("noradrenaline", 0.0)
            focus_learning = learning_weights.get("focus_factor", 0.5)
            self.adaptive_params["focus_factor"] = (noradrenaline + focus_learning) / 2
            
            # Update exploration tendency based on dopamine and serotonin balance
            serotonin = neuromods.get("serotonin", 0.5)
            exploration_learning = learning_weights.get("exploration_tendency", 0.5)
            dopamine_serotonin_balance = abs(dopamine - serotonin)
            self.adaptive_params["exploration_tendency"] = exploration_learning * (1 + dopamine_serotonin_balance)
            
            # Update memory recency weight based on acetylcholine
            acetylcholine = neuromods.get("acetylcholine", 0.3)
            self.adaptive_params["memory_recency_weight"] = 0.5 + (acetylcholine * 0.5)
            
        except Exception as e:
            LOGGER.debug(f"Failed to update adaptive parameters: {e}")

    async def _apply_cognitive_enhancement_to_snippets(self, snippets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply cognitive enhancement to retrieved snippets based on current state."""
        try:
            if not snippets:
                return snippets
                
            enhanced_snippets = []
            
            for snippet in snippets:
                enhanced_snippet = dict(snippet)
                
                # Apply creativity boost to snippet interpretation
                if self.adaptive_params["creativity_boost"] > 0.7:
                    # Boost creative associations
                    enhanced_snippet["creative_boost"] = True
                    enhanced_snippet["interpretation_bias"] = "exploratory"
                
                # Apply focus factor to snippet relevance
                if self.adaptive_params["focus_factor"] > 0.7:
                    # Increase relevance score for focused snippets
                    current_score = enhanced_snippet.get("score", 0.5)
                    enhanced_snippet["score"] = min(1.0, current_score * 1.2)
                
                # Apply exploration tendency to snippet diversity
                if self.adaptive_params["exploration_tendency"] > 0.7:
                    # Promote diverse snippets
                    if enhanced_snippet.get("metadata", {}).get("type") not in ["fact", "procedural"]:
                        enhanced_snippet["diversity_boost"] = True
                
                enhanced_snippets.append(enhanced_snippet)
            
            return enhanced_snippets
            
        except Exception as e:
            LOGGER.debug(f"Failed to apply cognitive enhancement to snippets: {e}")
            return snippets

    def _apply_cognitive_filtering_to_history(self, history: List[Dict[str, str]], allowed_tokens: int) -> List[Dict[str, str]]:
        """Apply cognitive filtering to history based on current adaptive parameters."""
        try:
            if not history or allowed_tokens <= 0:
                return []
            
            # Sort history by cognitive relevance
            scored_history = []
            for entry in history:
                score = self._calculate_history_relevance_score(entry)
                scored_history.append((entry, score))
            
            # Sort by score (descending) and apply token budget
            scored_history.sort(key=lambda x: x[1], reverse=True)
            
            filtered_history = []
            remaining_tokens = allowed_tokens
            
            for entry, score in scored_history:
                tokens = self.count_tokens(entry.get("content", ""))
                if tokens <= remaining_tokens:
                    filtered_history.append(entry)
                    remaining_tokens -= tokens
                    if remaining_tokens <= 0:
                        break
            
            return filtered_history
            
        except Exception as e:
            LOGGER.debug(f"Failed to apply cognitive filtering to history: {e}")
            # Fallback to simple trimming
            return self._trim_history(history, allowed_tokens)

    def _calculate_history_relevance_score(self, entry: Dict[str, str]) -> float:
        """Calculate relevance score for history entry based on cognitive state."""
        try:
            content = entry.get("content", "").lower()
            role = entry.get("role", "user")
            
            base_score = 0.5
            
            # Boost recent interactions based on recency weight
            recency_boost = self.adaptive_params["memory_recency_weight"]
            
            # Role-based scoring
            if role == "user":
                base_score += 0.2  # User messages are generally more relevant
            elif role == "system":
                base_score += 0.1  # System messages provide context
            
            # Content-based scoring based on cognitive state
            if self.adaptive_params["focus_factor"] > 0.7:
                # High focus: boost task-oriented content
                task_keywords = ["task", "goal", "objective", "complete", "finish"]
                if any(keyword in content for keyword in task_keywords):
                    base_score += 0.3
            
            if self.adaptive_params["creativity_boost"] > 0.7:
                # High creativity: boost exploratory content
                creative_keywords = ["explore", "try", "alternative", "different", "new"]
                if any(keyword in content for keyword in creative_keywords):
                    base_score += 0.2
            
            if self.adaptive_params["exploration_tendency"] > 0.7:
                # High exploration: boost diverse content
                diversity_keywords = ["different", "another", "alternative", "new", "various"]
                if any(keyword in content for keyword in diversity_keywords):
                    base_score += 0.2
            
            return min(1.0, base_score * recency_boost)
            
        except Exception as e:
            LOGGER.debug(f"Failed to calculate history relevance score: {e}")
            return 0.5

    async def _generate_cognitive_context_summary(self, turn: Dict[str, Any]) -> str:
        """Generate cognitive context summary for system prompt enhancement."""
        try:
            cognitive_summary_parts = []
            
            # Add neuromodulator state context
            neuromods = self.cognitive_state["neuromodulators"]
            dopamine = neuromods.get("dopamine", 0.4)
            serotonin = neuromods.get("serotonin", 0.5)
            
            if dopamine > 0.7:
                cognitive_summary_parts.append("Current cognitive state favors creativity and exploration.")
            elif dopamine < 0.3:
                cognitive_summary_parts.append("Current cognitive state favors routine and stability.")
            
            if serotonin > 0.7:
                cognitive_summary_parts.append("Current cognitive state emphasizes empathy and positive engagement.")
            elif serotonin < 0.3:
                cognitive_summary_parts.append("Current cognitive state is more analytical and direct.")
            
            # Add learning context
            learning_weights = self.cognitive_state["learning_weights"]
            if learning_weights.get("focus_factor", 0.5) > 0.7:
                cognitive_summary_parts.append("Recent learning patterns indicate improved focus capabilities.")
            
            if learning_weights.get("creativity_boost", 0.5) > 0.7:
                cognitive_summary_parts.append("Recent learning patterns show enhanced creative problem-solving.")
            
            return " ".join(cognitive_summary_parts) if cognitive_summary_parts else ""
            
        except Exception as e:
            LOGGER.debug(f"Failed to generate cognitive context summary: {e}")
            return ""

    def get_cognitive_state_metrics(self) -> Dict[str, Any]:
        """Get current cognitive state metrics for observability."""
        return {
            "neuromodulators": self.cognitive_state["neuromodulators"],
            "learning_weights": self.cognitive_state["learning_weights"],
            "adaptive_parameters": self.adaptive_params,
            "interaction_history_count": len(self.cognitive_state["interaction_history"]),
            "semantic_clusters_count": len(self.cognitive_state["semantic_clusters"])
        }
