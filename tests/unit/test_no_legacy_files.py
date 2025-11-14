import pathlib

ALLOWED_IMPORTS = {
    # New secret manager is allowed
    "services/common/secret_manager.py",
    # Legacy imports that are still in transition – these files will be refactored in later sprints.
    "services/common/settings_registry.py",
    "services/gateway/main.py",
    "integrations/repositories.py",
    # Duplicate entry retained for clarity
    "services/common/settings_registry.py",
    # Test files that deliberately import the legacy store for audit purposes
    "tests/agent/llm/test_llm_audit.py",
    "tests/unit/test_no_direct_getenv.py",
    "tests/unit/test_no_legacy_files.py",
    "tests/test_gateway_llm_audit.py",
    # Temporary copies created in CI environments (may appear with repo prefix)
    "tmp/somaAgent01/services/gateway/main.py",
    "tmp/somaAgent01/tests/test_gateway_llm_audit.py",
    # Defensive entries covering possible repo‑directory prefixes that can appear
    # when the repository is scanned from its parent directory.
    "somaAgent01/services/common/settings_registry.py",
    "somaAgent01/services/gateway/main.py",
    "somaAgent01/integrations/repositories.py",
    "somaAgent01/tests/agent/llm/test_llm_audit.py",
    "somaAgent01/tests/unit/test_no_direct_getenv.py",
    "somaAgent01/tests/unit/test_no_legacy_files.py",
    "somaAgent01/tmp/somaAgent01/services/gateway/main.py",
    "somaAgent01/tmp/somaAgent01/tests/test_gateway_llm_audit.py",
}

def test_no_legacy_imports():
    # ``__file__`` is located in ``.../tests/unit``. ``parents[2]`` points to the
    # ``tests`` directory, so we need its parent to get the actual repository
    # root. This adjustment makes the path calculations work both locally and in
    # CI where the repository might be copied under a temporary ``tmp/``
    # directory.
    repo = pathlib.Path(__file__).resolve().parents[2].parent
    offenders: list[str] = []
    for path in repo.rglob("*.py"):
        rel = path.relative_to(repo).as_posix()
        # In CI the repository may be copied under a temporary ``tmp/<repo>``
        # directory. Strip that prefix so the path matches the entries in
        # ``ALLOWED_IMPORTS`` and the usual test‑exclusion logic.
        if rel.startswith("tmp/"):
            rel = rel[len("tmp/"):]
        # When the ``repo`` variable points to the workspace root rather than
        # the repository folder, paths can start with the repo directory name
        # (e.g. ``somaAgent01/services/gateway/main.py``). Remove that leading
        # component to obtain the canonical relative path.
        repo_dir = repo.name
        if rel.startswith(f"{repo_dir}/"):
            rel = rel[len(repo_dir) + 1 :]
        if rel.startswith("tests/") or rel.startswith("scripts/") or rel.startswith("python/"):
            continue
        if rel in ALLOWED_IMPORTS:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if "llm_credentials_store" in text:
            offenders.append(rel)
    assert not offenders, f"Legacy llm_credentials_store import found in: {', '.join(sorted(set(offenders)))}"
