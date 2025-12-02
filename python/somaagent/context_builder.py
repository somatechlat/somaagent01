"""Somabrain-aware context builder for SomaAgent01."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Protocol

from python.integrations.somabrain_client import SomaBrainClient, SomaClientError
from observability.metrics import ContextBuilderMetrics

LOGGER = logging.getLogger(__name__)


class SomabrainHealthState(str, Enum):
    NORMAL = "normal"
    DEGRADED = "degraded"
    DOWN = "down"


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
    ) -> None:
        self.somabrain = somabrain
        self.metrics = metrics
        self.count_tokens = token_counter
        self.redactor = redactor or _NoopRedactor()
        self.health_provider = health_provider or (lambda: SomabrainHealthState.NORMAL)
        self.on_degraded = on_degraded or (lambda _duration: None)

    async def build_for_turn(
        self,
        turn: Dict[str, Any],
        *,
        max_prompt_tokens: int,
    ) -> BuiltContext:
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
                ranked_snippets = self._rank_and_clip_snippets(scored_snippets, state)
                snippets = self._redact_snippets(ranked_snippets)
                snippet_tokens = self._count_snippet_tokens(snippets)
                self.metrics.inc_snippets(stage="final", count=len(snippets))
            else:
                LOGGER.debug("Somabrain DOWN – skipping retrieval", extra={"session": turn.get("session_id")})

            with self.metrics.time_tokenisation():
                system_tokens = self.count_tokens(system_prompt)
                user_tokens = self.count_tokens(user_message)

            budget_for_history = max_prompt_tokens - (system_tokens + user_tokens + snippet_tokens)
            if budget_for_history < 0:
                snippets, snippet_tokens = self._trim_snippets_to_budget(
                    snippets,
                    snippet_tokens,
                    max_prompt_tokens - (system_tokens + user_tokens),
                )
                budget_for_history = max(0, max_prompt_tokens - (system_tokens + user_tokens + snippet_tokens))

            trimmed_history = self._trim_history(history, budget_for_history)
            history_tokens = sum(self.count_tokens(msg.get("content", "")) for msg in trimmed_history)

            if len(history) > len(trimmed_history):
                await self._store_summary(
                    turn=turn,
                    original_history=history,
                    trimmed_history=trimmed_history,
                )

            self.metrics.record_tokens(
                before_budget=sum(self.count_tokens(m.get("content", "")) for m in history),
                after_budget=history_tokens,
                after_redaction=self.count_tokens("\n".join(s["text"] for s in snippets)) if snippets else history_tokens,
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
