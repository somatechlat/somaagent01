"""Data models for the Context Builder pipeline.

These models are deliberately lightweight and use the standard library
``dataclasses`` module so that they have zero runtime dependencies beyond
the project's existing Python version.  All fields are typed and the
``asdict`` helper from ``dataclasses`` can be used to serialize them for
logging or Prometheus label values.

The VIBE coding rules require **real implementations** – no stubs or
placeholders – and the models must be importable from anywhere in the
codebase without side effects.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ContextRequest:
    """Input supplied by a FastAPI endpoint (or similar) to build a prompt.

    * ``tenant_id`` – the logical tenant for multi‑tenant isolation.
    * ``user_id`` – identifier of the end‑user making the request.
    * ``query`` – the raw user question or instruction.
    * ``conversation_id`` – optional identifier for a multi‑turn chat.
    * ``conversation_history`` – optional list of prior messages; each
      entry is a free‑form dict that downstream components may interpret.
    * ``tool_results`` – optional list of tool execution results that can
      be injected into the prompt.
    * ``model_max_tokens`` – maximum token budget for the LLM model.
    * ``system_prompt`` – optional system‑level instruction overriding the
      default.
    """

    tenant_id: str
    user_id: str
    query: str
    conversation_id: Optional[str] = None
    conversation_history: Optional[List[Dict[str, Any]]] = None
    tool_results: Optional[List[Dict[str, Any]]] = None
    model_max_tokens: int = 4000
    system_prompt: Optional[str] = None


@dataclass(frozen=True)
class RetrievedDoc:
    """A single document/snippet returned by Somabrain.

    The retrieval service supplies similarity, salience and recency scores –
    all normalised to the range ``0.0‒1.0``.  ``metadata`` is a catch‑all for
    any additional fields the service may return (e.g. source IDs,
    timestamps, etc.).
    """

    doc_id: str
    text: str
    similarity: float  # 0..1
    salience: float  # 0..1
    recency: float  # 0..1
    metadata: Dict[str, Any]


@dataclass(frozen=True)
class ScoredSnippet:
    """A snippet after scoring, policy evaluation and redaction.

    ``original_text`` is kept for audit logging; ``redacted_text`` is the
    version that will be inserted into the final prompt.  ``composite_score``
    is the weighted sum used for budgeting.  ``token_count`` is calculated
    with the same tokenizer that the LLM uses (tiktoken ``cl100k_base``).
    """

    doc_id: str
    original_text: str
    redacted_text: str
    composite_score: float
    token_count: int
    allowed_by_policy: bool
    metadata: Dict[str, Any]


@dataclass(frozen=True)
class ContextResult:
    """Result of the full pipeline – ready to be sent to the LLM.

    ``prompt`` is the rendered Jinja2 template.  ``snippets`` is the list of
    ``ScoredSnippet`` objects that were actually used.  ``token_count`` is the
    total token usage of the final prompt.  ``used_optimal_budget`` signals
    whether the knapsack optimiser was applied.  ``metrics`` is a free‑form
    dict that callers may forward to monitoring systems.
    """

    prompt: str
    snippets: List[ScoredSnippet]
    token_count: int
    used_optimal_budget: bool
    metrics: Dict[str, Any]


@dataclass(frozen=True)
class ContextFeedback:
    """Feedback supplied after the LLM answer has been consumed.

    ``doc_id`` identifies the source snippet the feedback refers to.  ``tenant_id``
    and ``user_id`` allow downstream analytics to be scoped per tenant.
    ``success`` indicates whether the snippet contributed positively.  ``score``
    is a numeric rating (e.g. 0‑5 stars).  ``timestamp`` records when the
    feedback was created.
    """

    doc_id: str
    tenant_id: str
    user_id: str
    success: bool
    score: float
    timestamp: datetime = datetime.utcnow()


def snippet_as_dict(snippet: ScoredSnippet) -> Dict[str, Any]:
    """Return a plain ``dict`` version of a ``ScoredSnippet``.

    ``dataclasses.asdict`` recursively converts nested dataclasses, which is
    useful for Prometheus label values or JSON payloads.
    """

    return asdict(snippet)


__all__ = [
    "ContextRequest",
    "RetrievedDoc",
    "ScoredSnippet",
    "ContextResult",
    "ContextFeedback",
    "snippet_as_dict",
]
