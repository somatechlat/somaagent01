# Degraded Mode Testing & Benchmarks

This document captures the test strategy for the Somabrain-aware context builder plus the new benchmark harness.

## Unit Tests

| Test | Location | Purpose |
|------|----------|---------|
| `test_context_builder_limits_snippets_when_degraded` | `tests/unit/test_context_builder_degraded.py` | Verifies degraded health enforces the reduced `top_k` and surfaces the correct debug metadata. |
| `test_context_builder_skips_retrieval_when_down` | `tests/unit/test_context_builder_degraded.py` | Ensures no Somabrain calls occur when the service is marked DOWN and that history-only prompts are assembled. |
| `test_context_builder_marks_normal_state_when_available` | `tests/unit/test_context_builder_degraded.py` | Guards the normal pipeline and confirms snippet counts propagate to the debug payload. |

Run the focused suite with:

```bash
pytest tests/unit/test_context_builder_degraded.py -q
```

## Benchmark Harness

`scripts/benchmarks/context_builder_benchmark.py` exercises the full context-building pipeline with a synthetic Somabrain backend. Useful flags:

```bash
# Normal mode, 25 iterations
scripts/benchmarks/context_builder_benchmark.py --iterations 25

# Force degraded mode with a bigger snippet pool
scripts/benchmarks/context_builder_benchmark.py --iterations 50 --snippets 20 --degraded
```

The script reports average and P95 latency along with the final `top_k` requested so we can confirm degraded-mode clipping under load.

## Suggested Workflow

1. **Unit tests** – run before every change touching the builder, the worker, or Somabrain health plumbing.
2. **Benchmark** – run on feature branches to capture latency regressions (paste console output in PRs for quick comparison).
3. **Integration smoke** – after changing worker/LLM code paths, trigger `scripts/smoke_test_essential.sh` to exercise the streaming/chat stack end-to-end.

Documenting these steps keeps the degraded-mode implementation grounded in repeatable signals and makes regression analysis trivial.
