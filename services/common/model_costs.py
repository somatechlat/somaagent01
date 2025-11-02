"""Cost estimation helpers for model usage."""

from __future__ import annotations

from typing import Optional

ESCALATION_MODEL_RATES = {
    "mistralai/Mixtral-8x7B-Instruct-v0.1": {"prompt": 0.6, "completion": 0.6},
    "Qwen/Qwen2-72B-Instruct": {"prompt": 2.0, "completion": 2.0},
    "01-ai/Yi-34B-Chat": {"prompt": 1.2, "completion": 1.2},
    "deepseek-ai/DeepSeek-Coder-V2-Instruct": {"prompt": 0.8, "completion": 0.8},
    "microsoft/Phi-3-medium-4k-instruct": {"prompt": 0.3, "completion": 0.3},
}


def estimate_escalation_cost(
    model: str,
    *,
    input_tokens: int,
    output_tokens: int,
) -> Optional[float]:
    rates = ESCALATION_MODEL_RATES.get(model)
    if not rates:
        return None
    prompt_cost = (input_tokens / 1000.0) * rates.get("prompt", 0.0)
    completion_cost = (output_tokens / 1000.0) * rates.get("completion", 0.0)
    total = prompt_cost + completion_cost
    return round(total, 4)
