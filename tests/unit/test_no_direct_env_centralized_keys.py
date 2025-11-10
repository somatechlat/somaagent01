from __future__ import annotations

from pathlib import Path

# Keys that have been centralized to runtime_config.env() usage
CENTRALIZED_KEYS = {
    "EXPORT_JOBS_DIR",
    "GATEWAY_EXPORT_REQUIRE_TENANT",
    "MEMORY_EXPORT_MAX_ROWS",
    "MEMORY_EXPORT_PAGE_SIZE",
    "EXPORT_JOBS_MAX_ROWS",
    "EXPORT_JOBS_PAGE_SIZE",
    "UPLOAD_TMP_DIR",
}

REPO_ROOT = Path(__file__).resolve().parents[2]

# Allowlist modules where env access patterns may be declared or wrapped
ALLOWLIST = {
    REPO_ROOT / "services/common/runtime_config.py",
    REPO_ROOT / "services/common/features.py",
}


def _scan_for_direct_getenv(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []
    hits: list[str] = []
    if "os.getenv" not in text:
        return hits
    for line_no, line in enumerate(text.splitlines(), start=1):
        if "os.getenv" not in line:
            continue
        for key in CENTRALIZED_KEYS:
            if f'os.getenv("{key}"' in line or f"os.getenv('{key}'" in line:
                hits.append(f"{path.relative_to(REPO_ROOT)}:{line_no}:{line.strip()}")
                break
    return hits


def test_no_direct_env_for_centralized_keys() -> None:
    offending: list[str] = []
    for py in REPO_ROOT.rglob("*.py"):
        # allow test code and virtual envs/site-packages
        if "tests" in py.parts or ".venv" in str(py) or "site/" in str(py):
            continue
        if py in ALLOWLIST:
            continue
        offending.extend(_scan_for_direct_getenv(py))
    assert not offending, (
        "Direct os.getenv detected for centralized keys. Use services.common.runtime_config.env() instead:\n"
        + "\n".join(offending)
    )
