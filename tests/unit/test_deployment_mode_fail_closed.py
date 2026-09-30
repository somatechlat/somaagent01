"""Deployment mode — the dispatch must not guess.

``SA01_DEPLOYMENT_MODE`` is what decides which identity source answers for a
login: local credentials in Standalone and DEV, federation in AAAS. That
makes the resolver part of the authentication seam, and a resolver that
silently reinterprets an unrecognised value is a fail-open: ``PROD`` — a
value other parts of this codebase accept — would quietly become ``DEV``
and the agent would authenticate people against the wrong authority.

The documented chain is untouched: an unset variable still resolves to
``DEV``. What must change is that a value which is *not* one of the three
declared modes is refused and names itself, rather than being folded into
one of them (Rule 91).

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
        ("AAAS", DeploymentModeEnum.AAAS),
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
    """The chain is documented as "default → DEV". A declared default for a
    mode is not the same as silently folding an unrecognised value into
    one; only the latter hides an operator's mistake."""
    monkeypatch.delenv("SA01_DEPLOYMENT_MODE", raising=False)
    monkeypatch.delenv("SOMA_AAAS_MODE", raising=False)
    monkeypatch.setattr(DeploymentMode, "_mode", None)
    monkeypatch.setattr(DeploymentMode, "_resolved", False)
    assert DeploymentMode.get() == "DEV"


def test_the_legacy_flag_still_selects_aaas(monkeypatch):
    monkeypatch.delenv("SA01_DEPLOYMENT_MODE", raising=False)
    monkeypatch.setenv("SOMA_AAAS_MODE", "true")
    monkeypatch.setattr(DeploymentMode, "_mode", None)
    monkeypatch.setattr(DeploymentMode, "_resolved", False)
    assert DeploymentMode.is_aaas() is True


# ---------------------------------------------------------------------------
# An unrecognised value is refused, not reinterpreted
# ---------------------------------------------------------------------------


def test_an_unknown_mode_is_refused_and_names_itself(monkeypatch):
    """``PROD`` is the dangerous case: it is a real value elsewhere in this
    codebase (``config/settings_registry``), so an operator can set it in
    good faith. Silently running it as ``DEV`` would pick an identity source
    nobody chose. The refusal must name the value so the operator can see
    what was wrong."""
    monkeypatch.setenv("SA01_DEPLOYMENT_MODE", "PROD")
    monkeypatch.setattr(DeploymentMode, "_mode", None)
    monkeypatch.setattr(DeploymentMode, "_resolved", False)

    with pytest.raises(ValueError) as excinfo:
        DeploymentMode._resolve()

    assert "PROD" in str(excinfo.value)


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


def test_the_mode_vocabulary_is_exactly_the_declared_three():
    assert {mode.value for mode in DeploymentModeEnum} == {
        "AAAS",
        "STANDALONE",
        "DEV",
    }


def test_the_predicates_partition_the_modes(monkeypatch):
    """Exactly one predicate holds for any mode the resolver accepts. If two
    could hold, a login dispatch would have two answers."""
    for value in ("AAAS", "STANDALONE", "DEV"):
        monkeypatch.setenv("SA01_DEPLOYMENT_MODE", value)
        monkeypatch.setattr(DeploymentMode, "_mode", None)
        monkeypatch.setattr(DeploymentMode, "_resolved", False)
        held = [
            DeploymentMode.is_aaas(),
            DeploymentMode.is_standalone(),
            DeploymentMode.is_dev(),
        ]
        assert held.count(True) == 1, f"{value} matched {held}"
