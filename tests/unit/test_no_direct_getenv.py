import pathlib

ALLOWED = set()


def test_no_direct_getenv_outside_allowed():
    repo = pathlib.Path(__file__).resolve().parents[2]
    offenders: list[str] = []
    for path in repo.rglob("*.py"):
        rel = path.relative_to(repo).as_posix()
        if rel.startswith("tests/") or rel.startswith("scripts/") or rel.startswith("python/"):
            continue
        if not rel.startswith("services/"):
            continue
        if rel in ALLOWED:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if "os.getenv(" in text or "os.environ[" in text:
            offenders.append(rel)
    assert not offenders, f"Direct getenv usage in: {', '.join(sorted(set(offenders)))}"
