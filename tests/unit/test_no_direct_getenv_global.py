"""Global guard: disallow direct os.getenv usage outside approved bootstrap.

Approved allowlist modules:
- services/common/runtime_config.py (defines env accessor)
- services/common/settings_sa01.py (initial settings load)
- services/common/features.py (descriptor env references)
- tests/ (test code may use os.getenv for setup)

All other business logic must use `services.common.runtime_config.env()`.
"""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

ALLOWLIST = {
    REPO_ROOT / "services/common/runtime_config.py",
    REPO_ROOT / "services/common/settings_sa01.py",
    REPO_ROOT / "services/common/features.py",
}

def _is_allowed(path: Path) -> bool:
    if path in ALLOWLIST:
        return True
    parts = set(path.parts)
    if "tests" in parts:
        return True
    if ".venv" in str(path) or "site/" in str(path):
        return True
    return False


def test_no_direct_getenv_outside_allowlist() -> None:
    offending: list[str] = []
    # Phase 1 enforcement: limit scan to gateway service only
    gateway_root = REPO_ROOT / "services" / "gateway"
    for py in gateway_root.rglob("*.py"):
        if _is_allowed(py):
            continue
        try:
            text = py.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if "os.getenv(" in text:
            for line_no, line in enumerate(text.splitlines(), start=1):
                if "os.getenv(" in line:
                    offending.append(f"{py.relative_to(REPO_ROOT)}:{line_no}:{line.strip()}")
    assert not offending, (
        "Direct os.getenv usage found outside allowlist. Use runtime_config.env():\n" + "\n".join(offending)
    )
