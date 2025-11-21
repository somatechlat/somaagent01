"""Guardrail: do not introduce new imports of the legacy runtime_config shim.

The legacy module ``services.common.runtime_config`` is slated for removal.
This test fails if the number of import sites grows beyond the current
baseline (50). As files migrate to ``orchestrator.config``/``src.core.config``
the threshold should be lowered accordingly.
"""

from __future__ import annotations

import re
from pathlib import Path


def test_runtime_config_imports_do_not_increase():
    repo_root = Path(__file__).resolve().parents[1]
    pattern = re.compile(r"from\\s+services\\.common\\s+import\\s+runtime_config")
    count = 0
    for path in repo_root.rglob("*.py"):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        count += len(pattern.findall(text))

    baseline = 0  # no legacy imports allowed.
    assert (
        count <= baseline
    ), f"runtime_config imports increased (found {count}, baseline {baseline}); migrate to src.core.config"
