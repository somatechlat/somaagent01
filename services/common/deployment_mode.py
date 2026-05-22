"""Deployment Mode — Single Source of Truth.

VIBE COMPLIANT:
- ONE env var chain: SA01_DEPLOYMENT_MODE > SOMA_AAAS_MODE > default
- NO other module reimplements mode detection
- Replaces 4 inconsistent implementations across the codebase

Usage:
    from services.common.deployment_mode import DeploymentMode

    if DeploymentMode.is_aaas():
        ...
"""

from __future__ import annotations

import os
from enum import Enum


class DeploymentModeEnum(str, Enum):
    """Canonical deployment modes."""

    AAAS = "AAAS"
    STANDALONE = "STANDALONE"
    DEV = "DEV"


class DeploymentMode:
    """Singleton deployment mode resolver.

    Priority chain (highest to lowest):
    1. SA01_DEPLOYMENT_MODE environment variable (canonical)
    2. SOMA_AAAS_MODE=true → AAAS
    3. Default → DEV
    """

    _mode: DeploymentModeEnum | None = None
    _resolved: bool = False

    @classmethod
    def _resolve(cls) -> DeploymentModeEnum:
        if cls._resolved:
            return cls._mode or DeploymentModeEnum.DEV

        mode = os.environ.get("SA01_DEPLOYMENT_MODE", "").strip().upper()
        if not mode:
            if os.environ.get("SOMA_AAAS_MODE", "").lower() == "true":
                mode = "AAAS"
        if not mode:
            mode = "DEV"

        try:
            cls._mode = DeploymentModeEnum(mode)
        except ValueError:
            cls._mode = DeploymentModeEnum.DEV

        cls._resolved = True
        return cls._mode

    @classmethod
    def get(cls) -> str:
        """Get deployment mode string."""
        return cls._resolve().value

    @classmethod
    def is_aaas(cls) -> bool:
        """Running in AAAS (cluster) mode."""
        return cls._resolve() == DeploymentModeEnum.AAAS

    @classmethod
    def is_standalone(cls) -> bool:
        """Running in Standalone mode."""
        return cls._resolve() == DeploymentModeEnum.STANDALONE

    @classmethod
    def is_dev(cls) -> bool:
        """Running in development mode."""
        return cls._resolve() == DeploymentModeEnum.DEV


__all__ = ["DeploymentMode", "DeploymentModeEnum"]
