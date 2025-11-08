import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def read(p: pathlib.Path) -> str:
    return p.read_text(encoding="utf-8")


def test_canonical_roadmap_exists_and_has_sections():
    path = REPO_ROOT / "docs" / "roadmap" / "canonical-roadmap.md"
    assert path.exists(), "canonical-roadmap.md must exist"
    content = read(path)
    # Key sections expected in the canonical roadmap
    for heading in [
        "System Overview",
        "Data and Event Contracts",
        "SomaBrain Integration",
        "Rollout Plan and Milestones",
        "Concrete Next Steps",
    ]:
        assert heading in content, f"Missing section heading: {heading}"


def test_sprint_roadmap_exists_and_has_sprints():
    path = REPO_ROOT / "docs" / "roadmap" / "sprint-roadmap.md"
    assert path.exists(), "sprint-roadmap.md must exist"
    content = read(path)
    # Ensure multiple sprints and acceptance tests are defined
    assert "Sprint 0" in content and "Sprint 5" in content
    assert "Acceptance tests" in content
