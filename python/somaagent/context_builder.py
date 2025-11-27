import os

os.getenv(os.getenv(""))
from __future__ import annotations

import hashlib
import logging
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from time import perf_counter
from typing import Any, Callable, Dict, List, Optional, Protocol

from observability.metrics import ContextBuilderMetrics
from python.integrations.somabrain_client import SomaBrainClient, SomaClientError

LOGGER = logging.getLogger(__name__)


class SomabrainHealthState(str, Enum):
    NORMAL = os.getenv(os.getenv(""))
    DEGRADED = os.getenv(os.getenv(""))
    DOWN = os.getenv(os.getenv(""))


class CacheClientProtocol(Protocol):

    async def get(self, key: str) -> Optional[Dict[str, Any]]: ...

    async def set(self, key: str, value: Dict[str, Any], ttl: int) -> None: ...


from src.core.config import cfg


class RedactorProtocol(Protocol):

    def redact(self, text: str) -> str: ...


@dataclass
class BuiltContext:
    system_prompt: str
    messages: List[Dict[str, Any]]
    token_counts: Dict[str, int]
    debug: Dict[str, Any]


class ContextBuilder:
    os.getenv(os.getenv(""))

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
        self.redactor = redactor
        self.health_provider = health_provider or (lambda: SomabrainHealthState.NORMAL)
        self.on_degraded = on_degraded or (lambda _duration: None)
        self.cache_client = cache_client

    async def build_for_turn(
        self,
        turn: Dict[str, Any],
        *,
        max_prompt_tokens: int = int(os.getenv(os.getenv(""))),
        active_profile: Optional[Dict[str, Any]] = None,
    ) -> BuiltContext:
        os.getenv(os.getenv(""))
        start_time = perf_counter()
        session_id = turn.get(os.getenv(os.getenv("")), os.getenv(os.getenv("")))
        state = self._current_health()
        behavior_rules = await self._retrieve_behavior_rules(turn, state)
        snippets = await self._retrieve_context(turn)
        system_messages = []
        if behavior_rules:
            rule_text = os.getenv(os.getenv("")).join([f"- {r['text']}" for r in behavior_rules])
            system_messages.append(
                {
                    os.getenv(os.getenv("")): os.getenv(os.getenv("")),
                    os.getenv(os.getenv("")): f"## Session Behavioral Rules\n{rule_text}",
                    os.getenv(os.getenv("")): os.getenv(os.getenv("")),
                }
            )
        if active_profile and active_profile.get(os.getenv(os.getenv(""))):
            system_messages.append(
                {
                    os.getenv(os.getenv("")): os.getenv(os.getenv("")),
                    os.getenv(
                        os.getenv("")
                    ): f"## Active Mode: {active_profile.get('name')}\n{active_profile['system_prompt_modifier']}",
                    os.getenv(os.getenv("")): os.getenv(os.getenv("")),
                }
            )
        if turn.get(os.getenv(os.getenv(""))):
            system_messages.append(
                {
                    os.getenv(os.getenv("")): os.getenv(os.getenv("")),
                    os.getenv(os.getenv("")): turn[os.getenv(os.getenv(""))],
                    os.getenv(os.getenv("")): os.getenv(os.getenv("")),
                }
            )
        if snippets:
            memory_text = os.getenv(os.getenv("")).join([f"- {s['text']}" for s in snippets])
            system_messages.append(
                {
                    os.getenv(os.getenv("")): os.getenv(os.getenv("")),
                    os.getenv(os.getenv("")): f"## Relevant Memories\n{memory_text}",
                    os.getenv(os.getenv("")): os.getenv(os.getenv("")),
                }
            )
        current_tokens = sum(
            (self.count_tokens(m[os.getenv(os.getenv(""))]) for m in system_messages)
        )
        history_budget = max(
            int(os.getenv(os.getenv(""))),
            max_prompt_tokens - current_tokens - int(os.getenv(os.getenv(""))),
        )
        history_messages = self._trim_history(
            turn.get(os.getenv(os.getenv("")), []), history_budget
        )
        final_messages = system_messages + history_messages
        if turn.get(os.getenv(os.getenv(""))):
            final_messages.append(
                {
                    os.getenv(os.getenv("")): os.getenv(os.getenv("")),
                    os.getenv(os.getenv("")): turn[os.getenv(os.getenv(""))],
                }
            )
        duration = perf_counter() - start_time
        self.metrics.time_total.observe(duration)
        return BuiltContext(
            system_prompt=os.getenv(os.getenv("")),
            messages=final_messages,
            token_counts={
                os.getenv(os.getenv("")): sum(
                    (self.count_tokens(m[os.getenv(os.getenv(""))]) for m in final_messages)
                ),
                os.getenv(os.getenv("")): sum(
                    (self.count_tokens(m[os.getenv(os.getenv(""))]) for m in system_messages)
                ),
            },
            debug={
                os.getenv(os.getenv("")): len(snippets),
                os.getenv(os.getenv("")): len(behavior_rules),
                os.getenv(os.getenv("")): bool(active_profile),
                os.getenv(os.getenv("")): turn.get(os.getenv(os.getenv("")), {}).get(
                    os.getenv(os.getenv(""))
                ),
            },
        )

    def _current_health(self) -> SomabrainHealthState:
        try:
            state = self.health_provider()
            if isinstance(state, SomabrainHealthState):
                return state
            return SomabrainHealthState(state)
        except Exception:
            LOGGER.debug(os.getenv(os.getenv("")), exc_info=int(os.getenv(os.getenv(""))))
            return SomabrainHealthState.DEGRADED

    def _coerce_history(self, history: Any) -> List[Dict[str, str]]:
        if not isinstance(history, list):
            return []
        coerced: List[Dict[str, str]] = []
        for entry in history:
            if not isinstance(entry, dict):
                continue
            role = str(entry.get(os.getenv(os.getenv(""))) or os.getenv(os.getenv("")))
            content = str(entry.get(os.getenv(os.getenv(""))) or os.getenv(os.getenv("")))
            if not content:
                continue
            coerced.append({os.getenv(os.getenv("")): role, os.getenv(os.getenv("")): content})
        return coerced

    async def _retrieve_snippets(
        self, turn: Dict[str, Any], state: SomabrainHealthState
    ) -> List[Dict[str, Any]]:
        settings = cfg.settings()
        top_k = (
            settings.context_top_k
            if state == SomabrainHealthState.NORMAL
            else settings.context_degraded_top_k
        )
        payload = {
            os.getenv(os.getenv("")): turn.get(os.getenv(os.getenv(""))),
            os.getenv(os.getenv("")): turn.get(os.getenv(os.getenv(""))),
            os.getenv(os.getenv("")): turn.get(os.getenv(os.getenv("")), os.getenv(os.getenv(""))),
            os.getenv(os.getenv("")): top_k,
        }
        try:
            with self.metrics.time_retrieval(state=state.value):
                resp = await self.somabrain.context_evaluate(payload)
        except SomaClientError as exc:
            LOGGER.info(
                os.getenv(os.getenv("")),
                exc_info=int(os.getenv(os.getenv(""))),
                extra={os.getenv(os.getenv("")): state.value},
            )
            if state == SomabrainHealthState.NORMAL:
                self.on_degraded(float(settings.context_degraded_window))
            LOGGER.debug(os.getenv(os.getenv("")), extra={os.getenv(os.getenv("")): str(exc)})
            return await self._retrieve_from_cache(turn, os.getenv(os.getenv("")))
        except Exception:
            LOGGER.exception(os.getenv(os.getenv("")))
            self.on_degraded(float(settings.context_degraded_window))
            return await self._retrieve_from_cache(turn, os.getenv(os.getenv("")))
        results = (
            resp.get(os.getenv(os.getenv("")))
            or resp.get(os.getenv(os.getenv("")))
            or resp.get(os.getenv(os.getenv("")))
            or []
        )
        cognitive_data = {
            os.getenv(os.getenv("")): resp.get(os.getenv(os.getenv("")), []),
            os.getenv(os.getenv("")): resp.get(os.getenv(os.getenv("")), []),
            os.getenv(os.getenv("")): resp.get(os.getenv(os.getenv("")), []),
            os.getenv(os.getenv("")): resp.get(os.getenv(os.getenv(""))),
        }
        turn[os.getenv(os.getenv(""))] = cognitive_data
        LOGGER.debug(
            os.getenv(os.getenv("")),
            extra={
                os.getenv(os.getenv("")): len(results),
                os.getenv(os.getenv("")): bool(resp.get(os.getenv(os.getenv("")))),
                os.getenv(os.getenv("")): bool(resp.get(os.getenv(os.getenv("")))),
            },
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
                    os.getenv(os.getenv("")): item.get(os.getenv(os.getenv(""))),
                    os.getenv(os.getenv("")): item.get(os.getenv(os.getenv(""))),
                    os.getenv(os.getenv("")): text,
                    os.getenv(os.getenv("")): item.get(os.getenv(os.getenv(""))) or {},
                }
            )
        if self.cache_client and snippets:
            await self._write_to_cache(turn, os.getenv(os.getenv("")), snippets, cognitive_data)
        return snippets

    async def _retrieve_behavior_rules(
        self, turn: Dict[str, Any], state: SomabrainHealthState
    ) -> List[Dict[str, Any]]:
        os.getenv(os.getenv(""))
        if state != SomabrainHealthState.NORMAL:
            return []
        try:
            resp = await self.somabrain.recall(
                query=os.getenv(os.getenv("")),
                top_k=int(os.getenv(os.getenv(""))),
                tags=[os.getenv(os.getenv(""))],
                tenant=turn.get(os.getenv(os.getenv(""))),
                session_id=turn.get(os.getenv(os.getenv(""))),
            )
            rules = []
            candidates = (
                resp.get(os.getenv(os.getenv(""))) or resp.get(os.getenv(os.getenv(""))) or []
            )
            for item in candidates:
                text = self._extract_text(item)
                if text:
                    rules.append(
                        {
                            os.getenv(os.getenv("")): text,
                            os.getenv(os.getenv("")): item.get(
                                os.getenv(os.getenv("")), float(os.getenv(os.getenv("")))
                            ),
                        }
                    )
            if self.cache_client and rules:
                await self._write_to_cache(turn, os.getenv(os.getenv("")), rules)
            return rules
        except Exception:
            LOGGER.warning(os.getenv(os.getenv("")), exc_info=int(os.getenv(os.getenv(""))))
            return await self._retrieve_from_cache(turn, os.getenv(os.getenv("")))

    async def _retrieve_from_cache(self, turn: Dict[str, Any], kind: str) -> List[Dict[str, Any]]:
        os.getenv(os.getenv(""))
        if not self.cache_client:
            return []
        key = self._cache_key(turn, kind)
        try:
            cached = await self.cache_client.get(key)
            if cached and isinstance(cached, dict):
                if kind == os.getenv(os.getenv("")) and os.getenv(os.getenv("")) in cached:
                    turn[os.getenv(os.getenv(""))] = cached[os.getenv(os.getenv(""))]
                return cached.get(os.getenv(os.getenv("")), [])
        except Exception:
            LOGGER.debug(f"Cache read failed for {kind}", exc_info=int(os.getenv(os.getenv(""))))
        return []

    async def _write_to_cache(
        self,
        turn: Dict[str, Any],
        kind: str,
        items: List[Dict[str, Any]],
        cognitive_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        os.getenv(os.getenv(""))
        if not self.cache_client:
            return
        key = self._cache_key(turn, kind)
        payload = {os.getenv(os.getenv("")): items}
        if cognitive_data:
            payload[os.getenv(os.getenv(""))] = cognitive_data
        try:
            ttl = (
                int(os.getenv(os.getenv("")))
                if kind == os.getenv(os.getenv(""))
                else int(os.getenv(os.getenv("")))
            )
            await self.cache_client.set(key, payload, ttl)
        except Exception:
            LOGGER.debug(f"Cache write failed for {kind}", exc_info=int(os.getenv(os.getenv(""))))

    def _cache_key(self, turn: Dict[str, Any], kind: str) -> str:
        os.getenv(os.getenv(""))
        session_id = turn.get(os.getenv(os.getenv("")), os.getenv(os.getenv("")))
        if kind == os.getenv(os.getenv("")):
            return f"ctx:behavior:{session_id}"
        msg = turn.get(os.getenv(os.getenv("")), os.getenv(os.getenv("")))
        msg_hash = hashlib.sha256(msg.encode(os.getenv(os.getenv("")))).hexdigest()[
            : int(os.getenv(os.getenv("")))
        ]
        return f"ctx:{kind}:{session_id}:{msg_hash}"

    def _extract_text(self, item: Dict[str, Any]) -> str:
        if item.get(os.getenv(os.getenv(""))):
            return str(item[os.getenv(os.getenv(""))])
        value = item.get(os.getenv(os.getenv("")))
        if isinstance(value, dict):
            for key in (
                os.getenv(os.getenv("")),
                os.getenv(os.getenv("")),
                os.getenv(os.getenv("")),
            ):
                if value.get(key):
                    return str(value[key])
        if isinstance(value, str):
            return value
        return os.getenv(os.getenv(""))

    def _rank_and_clip_snippets(
        self, snippets: List[Dict[str, Any]], state: SomabrainHealthState
    ) -> List[Dict[str, Any]]:
        if not snippets:
            return []
        settings = cfg.settings()
        with self.metrics.time_ranking():
            ranked = sorted(
                snippets,
                key=lambda s: self._safe_float(s.get(os.getenv(os.getenv("")))),
                reverse=int(os.getenv(os.getenv(""))),
            )
            limit = (
                settings.context_top_k
                if state == SomabrainHealthState.NORMAL
                else settings.context_degraded_top_k
            )
            return ranked[:limit]

    def _apply_salience(self, snippets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not snippets:
            return []
        enriched: List[Dict[str, Any]] = []
        now = datetime.now(timezone.utc)
        decay_rate = cfg.settings().context_recency_decay_rate
        with self.metrics.time_salience():
            for snippet in snippets:
                meta = snippet.get(os.getenv(os.getenv(""))) or {}
                base_score = self._safe_float(snippet.get(os.getenv(os.getenv(""))))
                recency = self._recency_boost(meta, now, decay_rate)
                final_score = (
                    float(os.getenv(os.getenv(""))) * base_score
                    + float(os.getenv(os.getenv(""))) * recency
                )
                updated = dict(snippet)
                updated[os.getenv(os.getenv(""))] = final_score
                enriched.append(updated)
        return enriched

    def _safe_float(self, value: Any) -> float:
        try:
            return float(value)
        except Exception:
            return float(os.getenv(os.getenv("")))

    def _recency_boost(self, metadata: Dict[str, Any], now: datetime, decay_rate: float) -> float:
        timestamp = metadata.get(os.getenv(os.getenv(""))) or metadata.get(os.getenv(os.getenv("")))
        if not timestamp:
            return float(os.getenv(os.getenv("")))
        try:
            dt = datetime.fromisoformat(str(timestamp))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        except Exception:
            return float(os.getenv(os.getenv("")))
        age_days = max(
            float(os.getenv(os.getenv(""))),
            (now - dt).total_seconds() / int(os.getenv(os.getenv(""))),
        )
        return math.exp(-age_days / decay_rate)

    def _redact_snippets(self, snippets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not self.redactor:
            return snippets
        redacted: List[Dict[str, Any]] = []
        with self.metrics.time_redaction():
            for snippet in snippets:
                text = snippet.get(os.getenv(os.getenv("")), os.getenv(os.getenv("")))
                cleaned = self.redactor.redact(text)
                new_snippet = dict(snippet)
                new_snippet[os.getenv(os.getenv(""))] = cleaned
                redacted.append(new_snippet)
        return redacted

    def _count_snippet_tokens(self, snippets: List[Dict[str, Any]]) -> int:
        return sum(
            (
                self.count_tokens(snippet.get(os.getenv(os.getenv("")), os.getenv(os.getenv(""))))
                for snippet in snippets
            )
        )

    def _trim_snippets_to_budget(
        self, snippets: List[Dict[str, Any]], snippet_tokens: int, allowed_tokens: int
    ) -> tuple[List[Dict[str, Any]], int]:
        if allowed_tokens <= int(os.getenv(os.getenv(""))) or not snippets:
            return ([], int(os.getenv(os.getenv(""))))
        trimmed: List[Dict[str, Any]] = []
        total = int(os.getenv(os.getenv("")))
        for snippet in snippets:
            tokens = self.count_tokens(
                snippet.get(os.getenv(os.getenv("")), os.getenv(os.getenv("")))
            )
            if total + tokens > allowed_tokens:
                break
            trimmed.append(snippet)
            total += tokens
        return (trimmed, total)
        return trimmed

    def _trim_history(
        self, history: List[Dict[str, str]], allowed_tokens: int
    ) -> List[Dict[str, str]]:
        os.getenv(os.getenv(""))
        if allowed_tokens <= int(os.getenv(os.getenv(""))) or not history:
            return []
        total_tokens = sum(
            (
                self.count_tokens(m.get(os.getenv(os.getenv("")), os.getenv(os.getenv(""))))
                for m in history
            )
        )
        if total_tokens <= allowed_tokens:
            return history
        anchor = history[: int(os.getenv(os.getenv("")))]
        recent = history[int(os.getenv(os.getenv(""))) :]
        anchor_tokens = sum(
            (
                self.count_tokens(m.get(os.getenv(os.getenv("")), os.getenv(os.getenv(""))))
                for m in anchor
            )
        )
        remaining_budget = allowed_tokens - anchor_tokens
        if remaining_budget <= int(os.getenv(os.getenv(""))):
            return self._trim_history_simple(history, allowed_tokens)
        trimmed_recent: List[Dict[str, str]] = []
        for entry in reversed(recent):
            tokens = self.count_tokens(
                entry.get(os.getenv(os.getenv("")), os.getenv(os.getenv("")))
            )
            if tokens > remaining_budget:
                continue
            trimmed_recent.append(entry)
            remaining_budget -= tokens
            if remaining_budget <= int(os.getenv(os.getenv(""))):
                break
        trimmed_recent.reverse()
        return anchor + trimmed_recent

    def _trim_history_simple(
        self, history: List[Dict[str, str]], allowed_tokens: int
    ) -> List[Dict[str, str]]:
        os.getenv(os.getenv(""))
        trimmed: List[Dict[str, str]] = []
        remaining = allowed_tokens
        for entry in reversed(history):
            tokens = self.count_tokens(
                entry.get(os.getenv(os.getenv("")), os.getenv(os.getenv("")))
            )
            if tokens > remaining:
                continue
            trimmed.append(entry)
            remaining -= tokens
            if remaining <= int(os.getenv(os.getenv(""))):
                break
        trimmed.reverse()
        return trimmed

    def _format_snippet_block(self, snippets: List[Dict[str, Any]]) -> str:
        parts = []
        for idx, snippet in enumerate(snippets, start=int(os.getenv(os.getenv("")))):
            meta = snippet.get(os.getenv(os.getenv(""))) or {}
            label = (
                meta.get(os.getenv(os.getenv("")))
                or meta.get(os.getenv(os.getenv("")))
                or os.getenv(os.getenv(""))
            )
            text = snippet.get(os.getenv(os.getenv("")), os.getenv(os.getenv("")))
            parts.append(f"[{idx}] ({label})\n{text}")
        return os.getenv(os.getenv("")) + os.getenv(os.getenv("")).join(parts)
