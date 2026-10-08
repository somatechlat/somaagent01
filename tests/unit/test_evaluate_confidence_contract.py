"""TG-04 — chat_orchestrator must not fabricate `confidence` from eval_result.

Plan 1.7 (SOMA-PM-RAPID-WIRING-001): "Evaluate contract: one shape both
sides; stop inventing ``confidence=0.5``". When SomaBrain's
``POST /context/evaluate`` returns no confidence, the orchestrator must not
paper over the hole with ``eval_result.get("confidence", 0.5)`` — a made-up
number would flow into the turn as if the brain had scored it.

Status note: this pattern existed when the gate was demanded (W1.5 still in
flight). W1.5 landed the evaluate contract while these tests were being
written — ``admin/core/chat_orchestrator.py`` now keeps confidence on the
declared setting (``SOMABRAIN_CONTEXT_CONFIDENCE_DEFAULT``) and only *comments*
about the banned form. The gate therefore runs GREEN on the current tree and
turns red the moment any ``.get("confidence", <number literal>)`` fabrication
is reintroduced. The check is AST-based, so prose comments that quote the
banned pattern cannot false-trigger.

Pure source analysis: parses the orchestrator with ``ast``, never imports it
(importing pulls in Django settings → Vault).

Run (no Vault needed):

    python3 -m pytest -c /dev/null --noconftest -p no:cacheprovider \\
        tests/unit/test_evaluate_confidence_contract.py -v

Run with the full stack up (Vault reachable), like the rest of the suite:

    pytest tests/unit/test_evaluate_confidence_contract.py -v
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ORCHESTRATOR = REPO / "admin" / "core" / "chat_orchestrator.py"


def _fabrications(tree: ast.AST) -> list[str]:
    """Calls ``<anything>.get("confidence", <number literal>)`` — a score the
    brain never gave, invented at the call site."""
    offenders: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "get"):
            continue
        if len(node.args) < 2:
            continue
        key, default = node.args[0], node.args[1]
        if not (isinstance(key, ast.Constant) and key.value == "confidence"):
            continue
        if (
            isinstance(default, ast.Constant)
            and isinstance(default.value, (int, float))
            and not isinstance(default.value, bool)
        ):
            offenders.append(f"line {node.lineno}: .get('confidence', {default.value!r})")
    return offenders


def test_orchestrator_exists():
    assert ORCHESTRATOR.exists(), f"{ORCHESTRATOR} missing — gate scope moved?"


def test_no_fabricated_confidence_default():
    src = ORCHESTRATOR.read_text(encoding="utf-8")
    offenders = _fabrications(ast.parse(src, filename=str(ORCHESTRATOR)))
    assert not offenders, (
        "chat_orchestrator fabricates a confidence value when the brain eval "
        "omits it — the evaluate contract (W1.5 / plan 1.7) requires the "
        "absence to surface, not be papered over with a number literal:\n  "
        + "\n  ".join(offenders)
    )


def test_gate_fails_on_a_fabrication():
    """Meta: the detector must flag the known offending form.

    Guards against the detector silently rotting into zero matches, which
    would turn this gate into a permanent free pass.
    """
    bad = ast.parse(
        "async def f(eval_result):\n"
        "    brain = eval_result.get('confidence', 0.5)\n"
        "    other = payload.get(\"confidence\", 0)\n"
    )
    hits = _fabrications(bad)
    assert len(hits) == 2, f"detector missed a fabrication: {hits}"

    good = ast.parse(
        "async def f(eval_result):\n"
        '    brain_confidence = float(_mem_setting("SOMABRAIN_CONTEXT_CONFIDENCE_DEFAULT"))\n'
        "    bare = eval_result.get('confidence')\n"
    )
    assert not _fabrications(good), "detector flagged non-fabricated code"
