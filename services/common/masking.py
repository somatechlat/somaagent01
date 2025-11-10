"""Lightweight content masking for messages and errors.

Rules are loaded from either the env var `SA01_MASK_RULES` (JSON array)
or a file path in `SA01_MASK_RULES_FILE`. Each rule must have:

- id: stable identifier string
- pattern: regular expression string
- replacement: replacement string (e.g., "[REDACTED]")

Default rules cover common API keys and simple secrets. Masking is
idempotent and only applies to string fields.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, List, Tuple

from services.common import runtime_config as cfg

try:  # Metrics are optional in some test contexts
    from prometheus_client import Counter
except Exception:  # pragma: no cover
    Counter = None  # type: ignore


_DEFAULT_RULES = [
    {
        "id": "openai_api_key",
        "pattern": r"(?i)\bsk-[A-Za-z0-9]{16,}\b",
        "replacement": "[REDACTED_KEY]",
    },
    {
        "id": "bearer_token",
        "pattern": r"(?i)\bBearer\s+[A-Za-z0-9._-]{16,}\b",
        "replacement": "Bearer [REDACTED]",
    },
    {
        "id": "password_equal",
        "pattern": r"(?i)(password|secret|token)\s*[:=]\s*[^\s]{6,}",
        "replacement": "\\1=[REDACTED]",
    },
]


@dataclass(frozen=True)
class MaskRule:
    id: str
    pattern: re.Pattern
    replacement: str


_RULES: List[MaskRule] | None = None

# Prometheus counters (guarded for duplicate registration in reload scenarios)
_MASK_RULE_HITS: Any = None  # type: ignore
_MASK_EVENTS_TOTAL: Any = None  # type: ignore


def _init_metrics() -> None:
    global _MASK_RULE_HITS, _MASK_EVENTS_TOTAL
    if Counter is None:
        return
    if _MASK_RULE_HITS is None:
        try:
            _MASK_RULE_HITS = Counter(
                "mask_rule_hits_total",
                "Total matches per masking rule (individual rule applications)",
                labelnames=("rule",),
            )
        except ValueError:  # already registered
            pass
    if _MASK_EVENTS_TOTAL is None:
        try:
            _MASK_EVENTS_TOTAL = Counter(
                "mask_events_total",
                "Events (messages/errors) that had at least one masking rule applied",
                labelnames=("rule_count",),
            )
        except ValueError:
            pass


def _load_rules_from_env() -> List[MaskRule]:
    raw = cfg.env("SA01_MASK_RULES")
    path = cfg.env("SA01_MASK_RULES_FILE")
    rules: list[dict[str, str]] = []
    if path:
        try:
            with open(path, "r", encoding="utf-8") as f:
                rules = json.load(f) or []
        except Exception:
            rules = []
    elif raw:
        try:
            rules = json.loads(raw) or []
        except Exception:
            rules = []

    if not rules:
        rules = _DEFAULT_RULES

    out: List[MaskRule] = []
    for r in rules:
        try:
            rid = str(r.get("id") or "rule")
            pat = re.compile(str(r.get("pattern") or ""))
            rep = str(r.get("replacement") or "[REDACTED]")
            out.append(MaskRule(rid, pat, rep))
        except Exception:
            continue
    return out


def _rules() -> List[MaskRule]:
    global _RULES
    if _RULES is None:
        _RULES = _load_rules_from_env()
        _init_metrics()
    return _RULES


def mask_text(text: str) -> Tuple[str, List[str]]:
    """Return masked text and list of rule ids that matched."""
    if not isinstance(text, str) or not text:
        return text, []  # type: ignore[return-value]
    hits: list[str] = []
    out = text
    for r in _rules():
        if r.pattern.search(out):
            hits.append(r.id)
            out = r.pattern.sub(r.replacement, out)
            try:
                if _MASK_RULE_HITS is not None:
                    _MASK_RULE_HITS.labels(r.id).inc()
            except Exception:
                pass
    return out, hits


def mask_event_payload(payload: dict[str, Any]) -> Tuple[dict[str, Any], List[str]]:
    """Mask common fields in an event payload copy: message and metadata.error."""
    if not isinstance(payload, dict):
        return payload, []  # type: ignore[return-value]
    changed = False
    hits: list[str] = []
    new = dict(payload)
    # message
    msg = new.get("message")
    if isinstance(msg, str) and msg:
        masked, h = mask_text(msg)
        if h:
            new["message"] = masked
            hits.extend(h)
            changed = True
    # metadata.error
    md = new.get("metadata")
    if isinstance(md, dict):
        err = md.get("error")
        if isinstance(err, str) and err:
            masked, h = mask_text(err)
            if h:
                mdc = dict(md)
                mdc["error"] = masked
                new["metadata"] = mdc
                hits.extend(h)
                changed = True
    if changed and hits:
        try:
            if _MASK_EVENTS_TOTAL is not None:
                _MASK_EVENTS_TOTAL.labels(str(len(set(hits)))).inc()
        except Exception:
            pass
    return (new if changed else payload), hits
