"""Deployment mode — the dispatch must not guess.

``SA01_DEPLOYMENT_MODE`` is what decides which identity source answers for a
login: local credentials in Standalone and DEV. That makes the resolver part
of the authentication seam, and a resolver that silently reinterprets an
unrecognised value is a fail-open.

Modes: STANDALONE | DEV. There is no Soma Platform mode and no second flag
(``SOMA_AAAS_MODE`` is deleted). An unset variable resolves to ``DEV``. A
value that is not one of the two declared modes is refused and names itself
(Rule 91).

Run:
    pytest tests/unit/test_deployment_mode_fail_closed.py -v
"""

from __future__ import annotations

import pytest

from services.common.deployment_mode import DeploymentMode, DeploymentModeEnum


@pytest.fixture(autouse=True)
def _fresh_resolver(monkeypatch):
    """``DeploymentMode`` caches its first resolution. Each test must start
    from an empty cache or the first test would decide for all of them."""
    monkeypatch.setattr(DeploymentMode, "_mode", None)
    monkeypatch.setattr(DeploymentMode, "_resolved", False)
    yield
    monkeypatch.setattr(DeploymentMode, "_mode", None)
    monkeypatch.setattr(DeploymentMode, "_resolved", False)


# ---------------------------------------------------------------------------
# The declared modes still resolve
# ---------------------------------------------------------------------------


def test_the_declared_modes_resolve(monkeypatch):
    for value, expected in (
        ("STANDALONE", DeploymentModeEnum.STANDALONE),
        ("DEV", DeploymentModeEnum.DEV),
    ):
        monkeypatch.setenv("SA01_DEPLOYMENT_MODE", value)
        monkeypatch.setattr(DeploymentMode, "_mode", None)
        monkeypatch.setattr(DeploymentMode, "_resolved", False)
        assert DeploymentMode._resolve() is expected


def test_the_value_is_case_insensitive_but_the_name_is_canonical(monkeypatch):
    monkeypatch.setenv("SA01_DEPLOYMENT_MODE", "standalone")
    monkeypatch.setattr(DeploymentMode, "_mode", None)
    monkeypatch.setattr(DeploymentMode, "_resolved", False)
    assert DeploymentMode.get() == "STANDALONE"


def test_an_unset_mode_still_resolves_to_the_documented_default(monkeypatch):
    """An unset variable resolves to DEV. A declared default for a mode is
    not the same as silently folding an unrecognised value into one."""
    monkeypatch.delenv("SA01_DEPLOYMENT_MODE", raising=False)
    monkeypatch.setattr(DeploymentMode, "_mode", None)
    monkeypatch.setattr(DeploymentMode, "_resolved", False)
    assert DeploymentMode.get() == "DEV"


def test_the_removed_aaas_flag_is_not_a_second_source(monkeypatch):
    """SOMA_AAAS_MODE is deleted. It must not select a mode."""
    monkeypatch.delenv("SA01_DEPLOYMENT_MODE", raising=False)
    monkeypatch.setenv("SOMA_AAAS_MODE", "true")
    monkeypatch.setattr(DeploymentMode, "_mode", None)
    monkeypatch.setattr(DeploymentMode, "_resolved", False)
    assert DeploymentMode.get() == "DEV"
    assert DeploymentMode.is_standalone() is False


# ---------------------------------------------------------------------------
# An unrecognised value is refused, not reinterpreted
# ---------------------------------------------------------------------------


def test_an_unknown_mode_is_refused_and_names_itself(monkeypatch):
    """``PROD`` and the removed ``Soma Platform`` must refuse and name themselves."""
    for value in ("PROD", "Soma Platform"):
        monkeypatch.setenv("SA01_DEPLOYMENT_MODE", value)
        monkeypatch.setattr(DeploymentMode, "_mode", None)
        monkeypatch.setattr(DeploymentMode, "_resolved", False)

        with pytest.raises(ValueError) as excinfo:
            DeploymentMode._resolve()

        assert value in str(excinfo.value)


def test_a_typo_does_not_silently_select_an_identity_source(monkeypatch):
    monkeypatch.setenv("SA01_DEPLOYMENT_MODE", "STANDLONE")
    monkeypatch.setattr(DeploymentMode, "_mode", None)
    monkeypatch.setattr(DeploymentMode, "_resolved", False)

    with pytest.raises(ValueError):
        DeploymentMode.get()


def test_the_refusal_is_not_cached_as_a_resolution(monkeypatch):
    """A refusal must not leave the resolver half-updated, or the next call
    would silently return the default instead of refusing again."""
    monkeypatch.setenv("SA01_DEPLOYMENT_MODE", "PROD")
    monkeypatch.setattr(DeploymentMode, "_mode", None)
    monkeypatch.setattr(DeploymentMode, "_resolved", False)

    with pytest.raises(ValueError):
        DeploymentMode.get()

    assert DeploymentMode._resolved is False

    with pytest.raises(ValueError):
        DeploymentMode.get()


# ---------------------------------------------------------------------------
# The mode vocabulary stays closed
# ---------------------------------------------------------------------------


def test_the_mode_vocabulary_is_exactly_the_declared_two():
    assert {mode.value for mode in DeploymentModeEnum} == {
        "STANDALONE",
        "DEV",
    }


def test_the_predicates_partition_the_modes(monkeypatch):
    """Exactly one predicate holds for any mode the resolver accepts. If two
    could hold, a login dispatch would have two answers."""
    for value in ("STANDALONE", "DEV"):
        monkeypatch.setenv("SA01_DEPLOYMENT_MODE", value)
        monkeypatch.setattr(DeploymentMode, "_mode", None)
        monkeypatch.setattr(DeploymentMode, "_resolved", False)
        held = [
            DeploymentMode.is_standalone(),
            DeploymentMode.is_dev(),
        ]
        assert held.count(True) == 1, f"{value} matched {held}"
