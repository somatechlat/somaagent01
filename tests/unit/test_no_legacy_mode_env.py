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
        assert "SOMA_AGENT_MODE" not in content, f"Legacy SOMA_AGENT_MODE found in: {p}"
        assert "SA01_ENV" not in content, f"Legacy SA01_ENV found in: {p}"
    # POLICY_FAIL_OPEN may appear in comments, but should not influence logic.


def test_no_policy_bypass_functions_present():
    import services.common.runtime_config as rc

    # Hard delete: no policy bypass functions should remain
    assert not hasattr(rc, "conversation_policy_bypass_enabled")
    assert not hasattr(rc, "test_policy_bypass_enabled")
