"""LLM metrics and usage tracking for conversation worker."""

from __future__ import annotations

from typing import Any, Dict

from observability.metrics import (
    llm_call_latency_seconds,
    llm_calls_total,
    llm_input_tokens_total,
    llm_output_tokens_total,
)


def normalize_usage(raw: Dict[str, Any] | None) -> dict[str, int]:
    """Coerce provider usage payloads into {input_tokens, output_tokens} ints.

    Args:
        raw: Raw usage data from LLM provider

    Returns:
        Normalized usage dict with input_tokens and output_tokens
    """
    payload: Dict[str, Any] = raw or {}
    prompt = payload.get("input_tokens", payload.get("prompt_tokens", 0))
    completion = payload.get("output_tokens", payload.get("completion_tokens", 0))

    try:
        prompt_val = int(prompt) if prompt is not None else 0
    except Exception:
        prompt_val = 0

    try:
        completion_val = int(completion) if completion is not None else 0
    except Exception:
        completion_val = 0

    return {"input_tokens": max(prompt_val, 0), "output_tokens": max(completion_val, 0)}


def record_llm_success(
    model: str | None, input_tokens: int, output_tokens: int, elapsed: float
) -> None:
    """Record successful LLM call metrics.

    Args:
        model: Model name
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        elapsed: Call duration in seconds
    """
    label = (model or "unknown").strip() or "unknown"
    llm_calls_total.labels(model=label, result="success").inc()
    llm_call_latency_seconds.labels(model=label).observe(max(elapsed, 0.0))
    if input_tokens:
        llm_input_tokens_total.labels(model=label).inc(max(input_tokens, 0))
    if output_tokens:
        llm_output_tokens_total.labels(model=label).inc(max(output_tokens, 0))


def record_llm_failure(model: str | None) -> None:
    """Record failed LLM call metrics.

    Args:
        model: Model name
    """
    label = (model or "unknown").strip() or "unknown"
    llm_calls_total.labels(model=label, result="error").inc()


def compose_outbound_metadata(
    base: Dict[str, Any] | None,
    *,
    source: str,
    status: str | None = None,
    error: str | None = None,
    model: str | None = None,
    usage: Dict[str, int] | None = None,
) -> Dict[str, Any]:
    """Compose metadata for outbound messages.

    Args:
        base: Base metadata dict
        source: Source identifier
        status: Optional status string
        error: Optional error message
        model: Optional model name
        usage: Optional usage stats

    Returns:
        Composed metadata dict
    """
    metadata = dict(base or {})
    metadata["source"] = source

    if status:
        metadata["status"] = status
    if error:
        metadata["error"] = error
    if model:
        metadata["model"] = model
    if usage:
        metadata["usage"] = usage

    return metadata
