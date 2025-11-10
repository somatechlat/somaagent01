import os
import re
from pathlib import Path


def test_no_legacy_mode_env_in_python_sources():
    repo_root = Path(__file__).resolve().parents[2]
    this_test = Path(__file__).resolve()
    python_files = list(repo_root.rglob("*.py"))
    # Exclude generated site, venv paths, and this test file itself
    python_files = [
        p
        for p in python_files
        if ".venv" not in str(p)
        and "site/" not in str(p)
        and "/tmp/" not in str(p)
        and p.resolve() != this_test
    ]
    for p in python_files:
        content = p.read_text(encoding="utf-8", errors="ignore")
        assert (
            "SOMA_AGENT_MODE" not in content
        ), f"Legacy SOMA_AGENT_MODE found in: {p}"
        assert "SA01_ENV" not in content, f"Legacy SA01_ENV found in: {p}"
    # POLICY_FAIL_OPEN may appear in comments, but should not influence logic.


def test_policy_bypass_is_centralized():
    from services.common.runtime_config import conversation_policy_bypass_enabled, init_runtime_config

    os.environ["SOMA_AGENT_ENV"] = "DEV"
    # No longer set DISABLE_CONVERSATION_POLICY (removed legacy env)
    init_runtime_config()
    assert conversation_policy_bypass_enabled() is True

    os.environ["SOMA_AGENT_ENV"] = "PROD"
    # Legacy bypass env removed; ensure PROD still denies bypass
    init_runtime_config()
    assert (
        conversation_policy_bypass_enabled() is False
    ), "Bypass must be disabled in PROD regardless of env flag"
