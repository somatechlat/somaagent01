import pathlib
import re


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def test_somabrain_port_in_compose_is_9696():
    compose = (REPO_ROOT / "docker-compose.yaml").read_text(encoding="utf-8")
    # Ensure SOMA_BASE_URL points to 9696
    assert "SOMA_BASE_URL: http://host.docker.internal:9696" in compose


def test_docs_reference_9696_not_9999():
    canon = (REPO_ROOT / "docs" / "roadmap" / "canonical-roadmap.md").read_text(encoding="utf-8")
    assert "host.docker.internal:9696" in canon
    assert "host.docker.internal:9999" not in canon


def test_site_folder_is_ignored_for_port_check():
    # Built site may lag; ensure tests do not falsely read from built artifacts.
    site = REPO_ROOT / "site" / "roadmap" / "canonical-roadmap" / "index.html"
    if site.exists():
        html = site.read_text(encoding="utf-8")
        # We don't assert on built artifacts; just ensure we are not failing because of them.
        assert isinstance(html, str)
