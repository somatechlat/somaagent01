"""Somabrain-aware context builder for SomaAgent01."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from time import perf_counter
from typing import Any, Callable, Dict, List, Optional, Protocol

from observability.metrics import ContextBuilderMetrics
from python.integrations.somabrain_client import SomaBrainClient, SomaClientError

import hashlib
import json

LOGGER = logging.getLogger(__name__)


class SomabrainHealthState(str, Enum):
    NORMAL = "normal"
    DEGRADED = "degraded"
    DOWN = "down"


class CacheClientProtocol(Protocol):  # pragma: no cover - interface definition
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        ...

    async def set(self, key: str, value: Dict[str, Any], ttl: int) -> None:
        ...



class RedactorProtocol(Protocol):  # pragma: no cover - interface definition
    def redact(self, text: str) -> str:
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
        cache_client: Optional[CacheClientProtocol] = None,
    ) -> None:
        self.somabrain = somabrain
        self.metrics = metrics
        self.count_tokens = token_counter
        self.redactor = redactor or _NoopRedactor()
        self.health_provider = health_provider or (lambda: SomabrainHealthState.NORMAL)
        self.on_degraded = on_degraded or (lambda _duration: None)
        self.cache_client = cache_client

    async def build_for_turn(
        self,
        turn: Dict[str, Any],
        *,
        max_prompt_tokens: int = 4000,
        active_profile: Optional[Dict[str, Any]] = None,
    ) -> BuiltContext:
        """Build the complete context for a conversation turn.
        
        Args:
            turn: The conversation turn data.
            max_prompt_tokens: Maximum tokens allowed for the prompt.
            active_profile: Optional active profile configuration (from ProfileStore).
        """
        start_time = perf_counter()
        session_id = turn.get("session_id", "unknown")
        
        # Get current SomaBrain health state from the injected health provider
        state = self._current_health()
        
        # 1. Retrieve behavior rules (Pass 1)
        behavior_rules = await self._retrieve_behavior_rules(turn, state)
        
        # 2. Retrieve contextual memories (Pass 2)
        snippets = await self._retrieve_context(turn)
        
        # 3. Construct system messages
        system_messages = []
        
        # 3a. Behavior Rules (Highest Priority)
        if behavior_rules:
            rule_text = "\n".join([f"- {r['text']}" for r in behavior_rules])
            system_messages.append({
                "role": "system",
                "content": f"## Session Behavioral Rules\n{rule_text}",
                "name": "behavior"
            })
            
        # 3b. Active Profile Modifier (High Priority)
        if active_profile and active_profile.get("system_prompt_modifier"):
            system_messages.append({
                "role": "system",
                "content": f"## Active Mode: {active_profile.get('name')}\n{active_profile['system_prompt_modifier']}",
                "name": "profile_mode"
            })
            
        # 3c. Base System Prompt / Persona
        if turn.get("system_prompt"):
            system_messages.append({
                "role": "system",
                "content": turn["system_prompt"],
                "name": "persona"
            })
            
        # 3d. Memory Block
        if snippets:
            memory_text = "\n".join([f"- {s['text']}" for s in snippets])
            system_messages.append({
                "role": "system",
                "content": f"## Relevant Memories\n{memory_text}",
                "name": "memory"
            })

        # 4. Construct history (trimmed)
        # Calculate remaining budget for history
        current_tokens = sum(self.count_tokens(m["content"]) for m in system_messages)
        history_budget = max(0, max_prompt_tokens - current_tokens - 500) # Reserve 500 for safety
        
        history_messages = self._trim_history(turn.get("history", []), history_budget)
        
        # 5. Assemble final messages
        final_messages = system_messages + history_messages
        
        # Add user message if not already in history (it usually isn't for the current turn)
        if turn.get("user_message"):
             final_messages.append({"role": "user", "content": turn["user_message"]})

        duration = perf_counter() - start_time
        self.metrics.time_total.observe(duration)
        
        return BuiltContext(
            system_prompt="",  # System messages are included in 'messages' list
            messages=final_messages,
            token_counts={
                "total": sum(self.count_tokens(m["content"]) for m in final_messages),
                "system": sum(self.count_tokens(m["content"]) for m in system_messages),
            },
            debug={
                "retrieval_count": len(snippets),
                "behavior_rule_count": len(behavior_rules),
                "profile_active": bool(active_profile),
                "constitution_checksum": turn.get("_cognitive_data", {}).get("constitution_checksum"),
            }
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
        top_k = self.DEFAULT_TOP_K if state == SomabrainHealthState.NORMAL else self.DEGRADED_TOP_K
        payload = {
            "tenant_id": turn.get("tenant_id"),
            "session_id": turn.get("session_id"),
            "query": turn.get("user_message", ""),
            "top_k": top_k,
        }
        try:
            with self.metrics.time_retrieval(state=state.value):
                resp = await self.somabrain.context_evaluate(payload)
        except SomaClientError as exc:
            LOGGER.info("Somabrain context_evaluate failed", exc_info=True, extra={"state": state.value})
            if state == SomabrainHealthState.NORMAL:
                self.on_degraded(self.DEGRADED_WINDOW_SECONDS)
            LOGGER.debug("SomaBrain error detail", extra={"error": str(exc)})
            return await self._retrieve_from_cache(turn, "context")
        except Exception:
            LOGGER.exception("Unexpected Somabrain failure during context evaluation")
            self.on_degraded(self.DEGRADED_WINDOW_SECONDS)
            return await self._retrieve_from_cache(turn, "context")
        
        # Extract all cognitive data from response
        results = resp.get("candidates") or resp.get("results") or resp.get("memories") or []
        
        # Store cognitive metadata for observability (NEW)
        cognitive_data = {
            "retrieval_weights": resp.get("weights", []),
            "residual_vector": resp.get("residual_vector", []),
            "working_memory": resp.get("working_memory", []),
            "constitution_checksum": resp.get("constitution_checksum"),
        }
        turn["_cognitive_data"] = cognitive_data
        
        LOGGER.debug(
            "context_evaluate response",
            extra={"result_count": len(results), "has_weights": bool(resp.get("weights")), "has_constitution": bool(resp.get("constitution_checksum"))}
        )
        
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
            
        # Cache successful result
        if self.cache_client and snippets:
            await self._write_to_cache(turn, "context", snippets, cognitive_data)
            
        return snippets

    async def _retrieve_behavior_rules(
        self,
        turn: Dict[str, Any],
        state: SomabrainHealthState,
    ) -> List[Dict[str, Any]]:
        """Retrieve active behavior rules for the session (Pass 1)."""
        if state != SomabrainHealthState.NORMAL:
            return []
            
        try:
            # Use recall with tags filtering as context_evaluate doesn't support it yet
            resp = await self.somabrain.recall(
                query="behavioral rules",
                top_k=3,
                tags=["behavior_rule"],
                tenant=turn.get("tenant_id"),
                session_id=turn.get("session_id"),
            )
            
            rules = []
            candidates = resp.get("candidates") or resp.get("results") or []
            for item in candidates:
                text = self._extract_text(item)
                if text:
                    rules.append({"text": text, "score": item.get("score", 1.0)})
            
            # Cache successful rules
            if self.cache_client and rules:
                await self._write_to_cache(turn, "behavior", rules)
                
            return rules
            
        except Exception:
            LOGGER.warning("Failed to retrieve behavior rules", exc_info=True)
            return await self._retrieve_from_cache(turn, "behavior")

    async def _retrieve_from_cache(self, turn: Dict[str, Any], kind: str) -> List[Dict[str, Any]]:
        """Try to fetch snippets/rules from cache."""
        if not self.cache_client:
            return []
        
        key = self._cache_key(turn, kind)
        try:
            cached = await self.cache_client.get(key)
            if cached and isinstance(cached, dict):
                # If it's context, restore cognitive data too
                if kind == "context" and "cognitive_data" in cached:
                    turn["_cognitive_data"] = cached["cognitive_data"]
                return cached.get("items", [])
        except Exception:
            LOGGER.debug(f"Cache read failed for {kind}", exc_info=True)
        return []

    async def _write_to_cache(
        self, 
        turn: Dict[str, Any], 
        kind: str, 
        items: List[Dict[str, Any]],
        cognitive_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Write items to cache."""
        if not self.cache_client:
            return
            
        key = self._cache_key(turn, kind)
        payload = {"items": items}
        if cognitive_data:
            payload["cognitive_data"] = cognitive_data
            
        try:
            # TTL: 1 hour for context, 24 hours for behavior (rules change less often)
            ttl = 3600 if kind == "context" else 86400
            await self.cache_client.set(key, payload, ttl)
        except Exception:
            LOGGER.debug(f"Cache write failed for {kind}", exc_info=True)

    def _cache_key(self, turn: Dict[str, Any], kind: str) -> str:
        """Stable cache key based on session and message hash."""
        session_id = turn.get("session_id", "unknown")
        # For behavior, we cache per session (rules shouldn't change mid-turn based on query)
        if kind == "behavior":
            return f"ctx:behavior:{session_id}"
            
        # For context, we cache based on the specific query
        msg = turn.get("user_message", "")
        msg_hash = hashlib.sha256(msg.encode("utf-8")).hexdigest()[:16]
        return f"ctx:{kind}:{session_id}:{msg_hash}"

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
        if not snippets:
            return []
        with self.metrics.time_ranking():
            ranked = sorted(snippets, key=lambda s: self._safe_float(s.get("score")), reverse=True)
            limit = self.DEFAULT_TOP_K if state == SomabrainHealthState.NORMAL else self.DEGRADED_TOP_K
            return ranked[:limit]

    def _apply_salience(self, snippets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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

        return trimmed

    def _trim_history(
        self,
        history: List[Dict[str, str]],
        allowed_tokens: int,
    ) -> List[Dict[str, str]]:
        """Intelligently trim history: Keep first 2 (anchor) + last N (recency)."""
        if allowed_tokens <= 0 or not history:
            return []
            
        # If history is short, just return what fits
        total_tokens = sum(self.count_tokens(m.get("content", "")) for m in history)
        if total_tokens <= allowed_tokens:
            return history

        # Strategy: Keep first 2 (anchor), then fill from end (recency)
        anchor = history[:2]
        recent = history[2:]
        
        anchor_tokens = sum(self.count_tokens(m.get("content", "")) for m in anchor)
        remaining_budget = allowed_tokens - anchor_tokens
        
        if remaining_budget <= 0:
            # Budget too tight, fallback to just recency from end
            return self._trim_history_simple(history, allowed_tokens)

        trimmed_recent: List[Dict[str, str]] = []
        for entry in reversed(recent):
            tokens = self.count_tokens(entry.get("content", ""))
            if tokens > remaining_budget:
                continue
            trimmed_recent.append(entry)
            remaining_budget -= tokens
            if remaining_budget <= 0:
                break
        
        trimmed_recent.reverse()
        return anchor + trimmed_recent

    def _trim_history_simple(
        self,
        history: List[Dict[str, str]],
        allowed_tokens: int,
    ) -> List[Dict[str, str]]:
        """Simple trimming from the end (fallback)."""
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
