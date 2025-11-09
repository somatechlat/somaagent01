"""Linter-style test enforcing centralized feature flag access.

Disallows direct ``os.getenv`` usage of feature flag environment variables
outside the allowlist modules. All feature gate checks must use
``services.common.runtime_config.flag``.

Allowlist:
 - services/common/features.py (descriptor declarations only)
 - tests (may set env vars via monkeypatch.setenv; this test only scans for os.getenv)

Failing patterns: os.getenv("ENABLE_EMBED_ON_INGEST" ...), os.getenv("SA01_ENABLE_...")
"""
from __future__ import annotations

import os
from pathlib import Path

FEATURE_ENV_PREFIXES = ["ENABLE_EMBED_ON_INGEST", "SA01_ENABLE_"]
REPO_ROOT = Path(os.getcwd())
ALLOWLIST = {
    REPO_ROOT / "services/common/features.py",
}

def _scan_file(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []
    hits: list[str] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if "os.getenv" not in line:
            continue
        for prefix in FEATURE_ENV_PREFIXES:
            if f'"{prefix}' in line or f"'{prefix}" in line:
                hits.append(f"{path.relative_to(REPO_ROOT)}:{line_no}:{line.strip()}")
                break
    return hits

def test_no_direct_env_feature_flags() -> None:
    offending: list[str] = []
    for py in REPO_ROOT.rglob("*.py"):
        if py in ALLOWLIST:
            continue
        if "tests" in py.parts:  # allow test code to use os.getenv for setup
            continue
        offending.extend(_scan_file(py))
    assert not offending, (
        "Direct os.getenv feature flag usage found; use runtime_config.flag() instead:\n" + "\n".join(offending)
    )
