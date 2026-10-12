"""Unit tests for DeploymentMode singleton.

Single source: SA01_DEPLOYMENT_MODE. Modes: STANDALONE | DEV.
There is no Soma Platform mode and no second flag.
"""

import pytest


class TestDeploymentMode:
    """Test DeploymentMode singleton behavior."""

    def test_default_is_dev(self, monkeypatch):
        """Without the env var, mode defaults to DEV."""
        monkeypatch.delenv("SA01_DEPLOYMENT_MODE", raising=False)

        from services.common.deployment_mode import DeploymentMode

        DeploymentMode._resolved = False
        DeploymentMode._mode = None

        assert DeploymentMode.get() == "DEV"
        assert DeploymentMode.is_dev() is True
        assert DeploymentMode.is_standalone() is False

    def test_standalone_mode(self, monkeypatch):
        """SA01_DEPLOYMENT_MODE=STANDALONE sets standalone mode."""
        monkeypatch.setenv("SA01_DEPLOYMENT_MODE", "STANDALONE")

        from services.common.deployment_mode import DeploymentMode

        DeploymentMode._resolved = False
        DeploymentMode._mode = None

        assert DeploymentMode.get() == "STANDALONE"
        assert DeploymentMode.is_standalone() is True

    def test_case_insensitive(self, monkeypatch):
        """Mode resolution is case-insensitive."""
        monkeypatch.setenv("SA01_DEPLOYMENT_MODE", "standalone")

        from services.common.deployment_mode import DeploymentMode

        DeploymentMode._resolved = False
        DeploymentMode._mode = None

        assert DeploymentMode.get() == "STANDALONE"
        assert DeploymentMode.is_standalone() is True

    def test_aaas_is_not_a_mode(self, monkeypatch):
        """Soma Platform was removed. Setting it must refuse, not silently map."""
        monkeypatch.setenv("SA01_DEPLOYMENT_MODE", "Soma Platform")

        from services.common.deployment_mode import DeploymentMode

        DeploymentMode._resolved = False
        DeploymentMode._mode = None

        with pytest.raises(ValueError) as excinfo:
            DeploymentMode.get()
        assert "Soma Platform" in str(excinfo.value)

    def test_invalid_mode_is_refused(self, monkeypatch):
        """An unrecognised mode raises and names itself.

        It must not default to DEV. This resolver decides which identity
        source answers for a login, so folding an unrecognised value into one
        of the declared modes would authenticate people against an authority
        nobody chose. ``PROD`` is the dangerous case: it is a real value
        elsewhere in this codebase, so an operator can set it in good faith.
        Rule 91: unknown configuration raises.
        """
        monkeypatch.setenv("SA01_DEPLOYMENT_MODE", "INVALID_MODE")

        from services.common.deployment_mode import DeploymentMode

        DeploymentMode._resolved = False
        DeploymentMode._mode = None

        with pytest.raises(ValueError) as excinfo:
            DeploymentMode.get()

        assert "INVALID_MODE" in str(excinfo.value)

        # Not cached as a resolution: the next call refuses again.
        DeploymentMode._resolved = False
        DeploymentMode._mode = None
        with pytest.raises(ValueError):
            DeploymentMode.get()
