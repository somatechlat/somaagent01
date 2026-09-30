"""Unit tests for DeploymentMode singleton.

Tests the canonical deployment mode resolution with priority chain:
SA01_DEPLOYMENT_MODE > SOMA_AAAS_MODE > DEV default.
"""

import pytest


class TestDeploymentMode:
    """Test DeploymentMode singleton behavior."""

    def test_default_is_dev(self, monkeypatch):
        """Without env vars, mode defaults to DEV."""
        monkeypatch.delenv("SA01_DEPLOYMENT_MODE", raising=False)
        monkeypatch.delenv("SOMA_AAAS_MODE", raising=False)

        # Reset singleton
        from services.common.deployment_mode import DeploymentMode

        DeploymentMode._resolved = False
        DeploymentMode._mode = None

        assert DeploymentMode.get() == "DEV"
        assert DeploymentMode.is_dev() is True
        assert DeploymentMode.is_aaas() is False
        assert DeploymentMode.is_standalone() is False

    def test_aaas_mode(self, monkeypatch):
        """SA01_DEPLOYMENT_MODE=AAAS sets AAAS mode."""
        monkeypatch.setenv("SA01_DEPLOYMENT_MODE", "AAAS")

        from services.common.deployment_mode import DeploymentMode

        DeploymentMode._resolved = False
        DeploymentMode._mode = None

        assert DeploymentMode.get() == "AAAS"
        assert DeploymentMode.is_aaas() is True
        assert DeploymentMode.is_standalone() is False

    def test_standalone_mode(self, monkeypatch):
        """SA01_DEPLOYMENT_MODE=STANDALONE sets standalone mode."""
        monkeypatch.setenv("SA01_DEPLOYMENT_MODE", "STANDALONE")

        from services.common.deployment_mode import DeploymentMode

        DeploymentMode._resolved = False
        DeploymentMode._mode = None

        assert DeploymentMode.get() == "STANDALONE"
        assert DeploymentMode.is_standalone() is True
        assert DeploymentMode.is_aaas() is False

    def test_legacy_soma_aaas_mode(self, monkeypatch):
        """SOMA_AAAS_MODE=true triggers AAAS when SA01_DEPLOYMENT_MODE is unset."""
        monkeypatch.delenv("SA01_DEPLOYMENT_MODE", raising=False)
        monkeypatch.setenv("SOMA_AAAS_MODE", "true")

        from services.common.deployment_mode import DeploymentMode

        DeploymentMode._resolved = False
        DeploymentMode._mode = None

        assert DeploymentMode.get() == "AAAS"
        assert DeploymentMode.is_aaas() is True

    def test_sa01_overrides_soma_aaas(self, monkeypatch):
        """SA01_DEPLOYMENT_MODE takes priority over SOMA_AAAS_MODE."""
        monkeypatch.setenv("SA01_DEPLOYMENT_MODE", "STANDALONE")
        monkeypatch.setenv("SOMA_AAAS_MODE", "true")

        from services.common.deployment_mode import DeploymentMode

        DeploymentMode._resolved = False
        DeploymentMode._mode = None

        assert DeploymentMode.get() == "STANDALONE"
        assert DeploymentMode.is_standalone() is True

    def test_case_insensitive(self, monkeypatch):
        """Mode resolution is case-insensitive."""
        monkeypatch.setenv("SA01_DEPLOYMENT_MODE", "aaas")

        from services.common.deployment_mode import DeploymentMode

        DeploymentMode._resolved = False
        DeploymentMode._mode = None

        assert DeploymentMode.get() == "AAAS"
        assert DeploymentMode.is_aaas() is True

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
