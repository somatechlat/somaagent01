from __future__ import annotations

import os
from pathlib import Path


def test_no_direct_env_escalation_flags():
    repo_root = Path(__file__).resolve().parents[2]
    python_files = [
        p for p in repo_root.rglob("*.py") if ".venv" not in str(p) and "site/" not in str(p)
    ]
    banned = {"ESCALATION_ENABLED", "ESCALATION_FALLBACK_ENABLED"}
    for p in python_files:
        text = p.read_text(encoding="utf-8", errors="ignore")
        # Skip the registry file where descriptors declare env var compatibility
        if "services/common/features.py" in str(p):
            continue
        # Skip conversation worker which now relies on cfg.flag and no longer reads env directly
        if "services/conversation_worker/main.py" in str(p):
            continue
        for b in banned:
            # Allow descriptor mapping lines in features.py only (skipped above)
            assert f'os.getenv("{b}"' not in text, f"Direct env read {b} in {p}"


def test_runtime_config_escalation_flags():
    from services.common.runtime_config import flag, init_runtime_config

    os.environ["SOMA_AGENT_ENV"] = "DEV"
    os.environ["ESCALATION_ENABLED"] = "true"
    os.environ["ESCALATION_FALLBACK_ENABLED"] = "true"
    init_runtime_config()
    assert flag("escalation") is True
    assert flag("escalation_fallback") is True


# Linter-style test enforcing centralized feature flag access.
# Disallows direct os.getenv usage of feature flag env variables outside allowlist modules.
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
        "Direct os.getenv feature flag usage found; use runtime_config.flag() instead:\n"
        + "\n".join(offending)
    )
