"""TG-02 — `SA01_TEMPORAL_URI` must not exist in infra/ or services/.

F03 (SOMA-RPT-STATUS-001): compose exported ``SA01_TEMPORAL_URI`` while the
workers read ``SA01_TEMPORAL_HOST`` → workers refused to start. W1.10 made
the host key the one authority and removed the URI key everywhere. This gate
fails if the banned key reappears in either production tree — one key, one
reader, no drift.

Pure source scan: reads files as bytes, never imports project code, never
touches Django settings or Vault.

Run (no Vault needed):

    python3 -m pytest -c /dev/null --noconftest -p no:cacheprovider \\
        tests/unit/test_temporal_uri_ban.py -v

Run with the full stack up (Vault reachable), like the rest of the suite:

    pytest tests/unit/test_temporal_uri_ban.py -v
"""

from __future__ import annotations

import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

BANNED_KEY = b"SA01_TEMPORAL_URI"

# Trees where the ban is enforced. Documentation (docs/, reports, ledger) may
# mention the key when describing the incident — that is history, not config.
BANNED_TREES = ("infra", "services")
SKIP_PARTS = {"__pycache__", "node_modules", ".git", ".venv", "secrets"}
SKIP_SUFFIXES = {".pyc", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".woff"}


def _offenders_in(base: Path) -> list[str]:
    if not base.exists():
        return [f"<missing: {base}>"]
    hits: list[str] = []
    for path in sorted(base.rglob("*")):
        if not path.is_file() or SKIP_PARTS.intersection(path.parts):
            continue
        if path.suffix in SKIP_SUFFIXES:
            continue
        if BANNED_KEY in path.read_bytes():
            hits.append(path.relative_to(base).as_posix())
    return hits


def _offenders(tree_rel: str) -> list[str]:
    base = REPO / tree_rel
    assert base.exists(), f"{tree_rel}/ missing — gate scope moved?"
    return _offenders_in(base)


def test_banned_temporal_uri_key_absent_from_infra():
    hits = _offenders("infra")
    assert not hits, (
        "SA01_TEMPORAL_URI reappeared in infra/ — W1.10 made SA01_TEMPORAL_HOST "
        "the sole authority (one key, one reader). Remove the URI key:\n  "
        + "\n  ".join(hits)
    )


def test_banned_temporal_uri_key_absent_from_services():
    hits = _offenders("services")
    assert not hits, (
        "SA01_TEMPORAL_URI reappeared in services/ — workers must read "
        "SA01_TEMPORAL_HOST only (F03 regression):\n  " + "\n  ".join(hits)
    )


def test_gate_fails_on_a_planted_key():
    """Meta: run the production scan against a synthetic tree holding the key.

    Proves the byte walk can fail — a gate that has never been seen to fail
    is not evidence of anything. The synthetic tree is a temp directory,
    not a mutation of infra/ or services/.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "compose.yml").write_text("environment:\n  KEY: fine\n", encoding="utf-8")
        assert not _offenders_in(root), "clean probe tree must pass"
        (root / "compose.yml").write_text(
            "environment:\n  SA01_TEMPORAL_URI: bad\n", encoding="utf-8"
        )
        hits = _offenders_in(root)
        assert hits, "gate failed to detect a planted SA01_TEMPORAL_URI"
        assert hits == ["compose.yml"]
