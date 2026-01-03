#!/usr/bin/env python3
"""Benchmark harness for the ContextBuilder pipeline.

Synthetic Somabrain responses are used so the benchmark can run offline while
still exercising the full token-budget logic and degraded-mode behaviours.
"""

from __future__ import annotations

import argparse
import asyncio
import random
import statistics
import time
from typing import Any, Dict, List

from admin.core.observability.metrics import ContextBuilderMetrics
from python.somaagent.context_builder import ContextBuilder, SomabrainHealthState


class SyntheticSomabrain:
    """Synthetic Somabrain that returns deterministic snippet payloads."""

    def __init__(self, snippet_pool: List[Dict[str, Any]]) -> None:
        self.snippet_pool = snippet_pool
        self.calls: List[Dict[str, Any]] = []

    async def context_evaluate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.calls.append(payload)
        top_k = int(payload.get("top_k", len(self.snippet_pool)))
        ranked = sorted(self.snippet_pool, key=lambda item: item.get("score", 0), reverse=True)
        await asyncio.sleep(0)
        return {"candidates": ranked[:top_k]}


def build_snippet_pool(count: int) -> List[Dict[str, Any]]:
    pool: List[Dict[str, Any]] = []
    for idx in range(count):
        pool.append(
            {
                "id": f"snippet-{idx}",
                "score": random.uniform(0.2, 1.0),
                "text": f"Synthetic memory #{idx}",
                "metadata": {"source": random.choice(["doc", "memory", "note"])},
            }
        )
    return pool


async def run_iteration(
    builder: ContextBuilder, envelope: Dict[str, Any], max_tokens: int
) -> float:
    start = time.perf_counter()
    await builder.build_for_turn(dict(envelope), max_prompt_tokens=max_tokens)
    return time.perf_counter() - start


async def benchmark(args: argparse.Namespace) -> None:
    random.seed(args.seed)
    snippet_pool = build_snippet_pool(args.snippets)
    somabrain = SyntheticSomabrain(snippet_pool)
    metrics = ContextBuilderMetrics()

    def _health() -> SomabrainHealthState:
        return SomabrainHealthState.DEGRADED if args.degraded else SomabrainHealthState.NORMAL

    builder = ContextBuilder(
        somabrain=somabrain,
        metrics=metrics,
        token_counter=lambda text: max(1, len(text.split())),
        health_provider=_health,
    )

    envelope = {
        "tenant_id": "benchmark",
        "session_id": "bench-session",
        "system_prompt": "You are SomaAgent01.",
        "user_message": "Summarise the latest updates for the benchmark.",
        "history": [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
        ],
    }

    samples = []
    for _ in range(args.iterations):
        samples.append(await run_iteration(builder, envelope, args.max_tokens))

    mean = statistics.mean(samples)
    p95 = statistics.quantiles(samples, n=20)[18] if len(samples) >= 20 else max(samples)
    print(f"Iterations: {args.iterations}")
    print(f"Somabrain state: {'degraded' if args.degraded else 'normal'}")
    print(f"Average latency: {mean*1000:.2f} ms")
    print(f"P95 latency: {p95*1000:.2f} ms")
    if somabrain.calls:
        print(f"Last top_k requested: {somabrain.calls[-1]['top_k']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark the ContextBuilder pipeline")
    parser.add_argument("--iterations", type=int, default=25, help="Number of prompts to build")
    parser.add_argument(
        "--max-tokens", type=int, default=4096, help="Prompt budget to pass to the builder"
    )
    parser.add_argument(
        "--snippets", type=int, default=12, help="Size of the synthetic snippet pool"
    )
    parser.add_argument("--degraded", action="store_true", help="Force Somabrain degraded mode")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic RNG seed")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    asyncio.run(benchmark(args))


if __name__ == "__main__":
    main()
